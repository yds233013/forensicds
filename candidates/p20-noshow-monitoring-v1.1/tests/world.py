"""Deterministic generator for the Halcyon Health Partners no-show extract (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/appointments.sqlite

Structure of the world:

  * 38 outpatient clinics, 52 weeks of appointments.
  * A no-show risk model `noshow-v3.1` scores every appointment at booking from features as they stood then.
    Its coefficients are published in the model registry, so any vintage of the features can be re-scored.
  * From `policy_start_week` the reminder programme calls the top `call_percentile` of scores. The programme
    was ramped by clinic group, and a stratified subset of clinics was left out of it entirely.
  * A reminder multiplies the odds of not attending by `reminder_or`, so the programme's own successes change
    the outcomes of exactly the appointments the model ranks highest.
  * On `backfill_date` an upstream job recomputed `prior_no_show_count` over all history instead of a rolling
    twelve months. `attendance_events` is append-only, so the value as it stood at booking is recoverable.
  * A new referral source appears in month `new_source_month`, which moves the feature distribution without
    changing the relationship the model learned.
  * `noshow-v4.0` was retrained on post-policy data including reminded outcomes, and its scores are shipped.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

PRIOR_CAP = 3          # the model card caps the rolling no-show count at three

AGE_BANDS = ("18-29", "30-44", "45-59", "60-74", "75+")
APPT_TYPES = ("FIRST", "FOLLOWUP", "PROCEDURE", "DIAGNOSTIC")
SIZE_BANDS = ("SMALL", "MEDIUM", "LARGE")
REGIONS = ("NORTH", "CENTRAL", "SOUTH")

# Published coefficients of noshow-v3.1 (model card). Features are centred as described in the registry.
COEF = {
    "intercept": -2.90,
    "prior_no_shows_12m": 0.387,
    "lead_time_days_c": 0.0428,
    "deprivation_decile_c": 0.173,
    "distance_km_c": 0.0265,
    "age_18-29": 0.775, "age_30-44": 0.326, "age_45-59": 0.0, "age_60-74": -0.449, "age_75+": -0.694,
    "type_FIRST": 0.490, "type_FOLLOWUP": 0.0, "type_PROCEDURE": -0.632, "type_DIAGNOSTIC": 0.184,
}

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 20260417,
    "n_clinics": 38,
    "n_weeks": 52,
    "appts_per_week": 2600,
    "first_monday": "2025-07-07",
    "policy_start_week": 27,
    "ramp_weeks": 6,
    "call_percentile": 0.45,
    "reminder_or": 0.32,          # a reminder multiplies the odds of not attending by this
    "call_reach_rate": 0.92,      # share of called patients actually reached; only those get the effect
    "control_clinics": 5,         # left out of the programme, stratified by size band
    "backfill_week": 33,
    "new_source_month": 4,
    "new_source_share": 0.14,
    "score_noise_sd": 0.35,       # tunes the model's discrimination on an untreated population
    "recent_weeks": 12,           # the monitoring window the readout covers
    # Model risk standard: a model may be retained only while its discrimination on a policy-invariant
    # population stays within `auc_tolerance` of its validation figure and never below `auc_floor`.
    "auc_tolerance": 0.04,
    "auc_floor": 0.70,
    "feed_defect_material_share": 0.05,
    "candidate_margin": 0.02,
    "v4_trained_from_week": 27,
    "v4_policy_leak": 0.85,       # how strongly v4.0 picks up the policy footprint
    # Concept drift: from this week the relationship between the features and attendance weakens, so the
    # model's discrimination falls on ANY population, including one the policy never touched.
    "drift_from_week": None,
    "drift_coef": {},             # per-coefficient multipliers in force from drift_from_week
    # A new driver of attendance that the served model cannot see because it postdates the model. From
    # `interpreter_effect_from_week` it moves the outcome; v3.1 has no coefficient for it, so v3.1's
    # discrimination genuinely falls on every population, and a model fitted on recent data recovers it.
    "interpreter_share": 0.18,
    "interpreter_effect_from_week": None,
    "interpreter_coef": 0.0,
    # An upstream join failure that defaults a feature for a share of appointments from a given week. The
    # served scores lose that signal while the outcome still depends on it, so this too is genuine
    # degradation - but the remedy is the feed, not the model.
    "feed_break_from_week": None,
    "feed_break_share": 0.0,
    # Which served feature the failed join defaults. "prior_no_shows_12m" defaults to 0 (the history join
    # returned nothing); "deprivation_decile" defaults to the mid decile.
    "feed_break_column": "prior_no_shows_12m",
    # Patients arrive with attendance history predating the extract; it is in attendance_events, so the
    # rolling-twelve-month feature is reconstructible, and its divergence from an all-history count is what
    # the backfill changed.
    "appts_per_patient": 9,
    # Seeded so that a patient's twelve-month history at week 1 already matches its steady state, which keeps
    # the feature distribution stationary across the extract.
    "seed_history_days": 548,
    "seed_history_appts": (9, 17),
    "seed_dna_rate": 0.115,
    # The model's feature is a rolling twelve months. The backfill replaced it with a longer window; how much
    # further back it reaches is what decides the size of the vintage effect.
    "asof_window_days": 365,
    "current_window_days": 730,   # None means all history
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _logistic(x):
    if x < -35:
        return 0.0
    if x > 35:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def _drifted(spec):
    """The relationship in force after the drift date: the same features, weighted differently. This is a
    rotation rather than a shrinkage, so the achievable discrimination is unchanged and a model fitted on the
    new period can recover it - which is what makes replacing the model the right answer where it happens."""
    out = dict(COEF)
    for k, m in spec["drift_coef"].items():
        out[k] = out[k] * m
    return out


def _eta(feat, coef=COEF):
    return (coef["intercept"]
            + coef["prior_no_shows_12m"] * min(feat["prior_no_shows"], PRIOR_CAP)
            + coef["lead_time_days_c"] * (feat["lead_time_days"] - 21.0)
            + coef["deprivation_decile_c"] * (feat["deprivation_decile"] - 5.5)
            + coef["distance_km_c"] * (feat["distance_km"] - 8.0)
            + coef[f"age_{feat['age_band']}"]
            + coef[f"type_{feat['appointment_type']}"])


def build(spec: dict) -> dict:
    d = _rng(spec["seed"], "design")
    monday = date.fromisoformat(spec["first_monday"])

    clinics = []
    for i in range(spec["n_clinics"]):
        clinics.append({"clinic_id": f"CL-{i + 1:03d}",
                        "name": f"Halcyon Clinic {i + 1}",
                        "size_band": SIZE_BANDS[i % 3],
                        "region": REGIONS[(i // 3) % 3],
                        "ramp_group": (i % spec["ramp_weeks"]) + 1})
    # The control arm is drawn stratified by size band so the two arms are comparable.
    control = []
    by_band = {}
    for c in clinics:
        by_band.setdefault(c["size_band"], []).append(c)
    picker = _rng(spec["seed"], "control-arm")
    bands = list(by_band)
    k = 0
    while len(control) < spec["control_clinics"]:
        band = bands[k % len(bands)]
        pool = [c for c in by_band[band] if c["clinic_id"] not in control]
        control.append(picker.choice(pool)["clinic_id"])
        k += 1
    control = sorted(set(control))
    for c in clinics:
        c["in_programme"] = c["clinic_id"] not in control

    # Patients carry a stable propensity offset and an attendance history.
    n_patients = spec["appts_per_week"] * spec["n_weeks"] // spec["appts_per_patient"]
    patients = []
    for i in range(n_patients):
        patients.append({"patient_id": f"PT-{i + 1:07d}",
                         "age_band": AGE_BANDS[d.randrange(len(AGE_BANDS))],
                         "deprivation_decile": d.randint(1, 10),
                         "distance_km": round(max(0.4, d.gauss(8.0, 4.2)), 1),
                         "offset": d.gauss(0.0, 0.55),
                         "history": []})
    # Attendance history predating the extract.
    seed_start = date.fromisoformat(spec["first_monday"]) - timedelta(days=spec["seed_history_days"])
    lo, hi = spec["seed_history_appts"]
    seeded_events = []
    for pt in patients:
        for _ in range(d.randint(lo, hi)):
            when = seed_start + timedelta(days=d.randrange(spec["seed_history_days"]))
            kind = "DID_NOT_ATTEND" if d.random() < spec["seed_dna_rate"] else "ATTENDED"
            pt["history"].append((when, kind))
            seeded_events.append((pt["patient_id"], when.isoformat(), kind))
        pt["history"].sort()

    # One chronological pass: each appointment's features are computed from the patient's realised history at
    # booking, the score follows, the calling decision follows the score, and the outcome follows the score and
    # whether a reminder was reached. History therefore accumulates correctly and the as-of feature is
    # reproducible from attendance_events alone.
    appointments, events, calls = [], [], []
    o = _rng(spec["seed"], "outcome")
    cut = None
    aid = 0
    for wk in range(1, spec["n_weeks"] + 1):
        wk_start = monday + timedelta(days=7 * (wk - 1))
        if wk == spec["policy_start_week"]:
            # The policy configuration fixes the calling threshold from the score distribution observed before
            # the programme started.
            pre = sorted(a["_score"] for a in appointments)
            cut = pre[int((1.0 - spec["call_percentile"]) * len(pre))] if pre else 0.5
        for _ in range(spec["appts_per_week"]):
            aid += 1
            c = clinics[d.randrange(len(clinics))]
            pt = patients[d.randrange(len(patients))]
            new_source = (wk > spec["new_source_month"] * 4 and d.random() < spec["new_source_share"])
            lead = max(1, int(d.gauss(28.0 if new_source else 20.0, 9.0)))
            appt_on = wk_start + timedelta(days=d.randrange(5))
            booked_on = appt_on - timedelta(days=lead)
            atype = APPT_TYPES[d.randrange(len(APPT_TYPES))]
            if new_source:
                atype = "FIRST" if d.random() < 0.7 else atype
            interpreter = 1 if d.random() < spec["interpreter_share"] else 0
            broken = (spec["feed_break_from_week"] is not None and wk >= spec["feed_break_from_week"]
                      and d.random() < spec["feed_break_share"])
            # A failed enrichment join leaves the scorer with the defaults for every column it supplies.
            col = spec["feed_break_column"]
            break_decile = broken and col in ("deprivation_decile", "both", "all")
            break_prior = broken and col in ("prior_no_shows_12m", "both", "all")
            break_demog = broken and col == "all"
            served_decile = 5 if break_decile else pt["deprivation_decile"]
            served_age = "45-59" if break_demog else pt["age_band"]
            served_type = "FOLLOWUP" if break_demog else atype

            # History known at booking: events strictly before the booking date. Exactly reconstructible
            # from attendance_events, which is what makes the serving vintage auditable.
            cutoff = booked_on - timedelta(days=spec["asof_window_days"])
            prior_12m = sum(1 for e in pt["history"]
                            if e[1] == "DID_NOT_ATTEND" and cutoff <= e[0] < booked_on)
            cw = spec["current_window_days"]
            cur_cut = booked_on - timedelta(days=cw) if cw else date(1900, 1, 1)
            prior_all = sum(1 for e in pt["history"]
                            if e[1] == "DID_NOT_ATTEND" and cur_cut <= e[0] < booked_on)

            prior_served = 0 if break_prior else prior_12m
            feat = {"prior_no_shows": prior_served, "lead_time_days": lead,
                    "deprivation_decile": served_decile, "distance_km": pt["distance_km"],
                    "age_band": served_age, "appointment_type": served_type}
            feat_true = {"prior_no_shows": prior_12m, "lead_time_days": lead,
                         "deprivation_decile": pt["deprivation_decile"], "distance_km": pt["distance_km"],
                         "age_band": pt["age_band"], "appointment_type": atype}
            eta_score = _eta(feat) + pt["offset"]
            score = _logistic(eta_score + d.gauss(0.0, spec["score_noise_sd"]))
            eta_out = _eta(feat_true, _drifted(spec)
                           if (spec["drift_from_week"] and wk >= spec["drift_from_week"]) else COEF) \
                + pt["offset"]
            if spec["interpreter_effect_from_week"] and wk >= spec["interpreter_effect_from_week"]:
                eta_out += spec["interpreter_coef"] * interpreter

            in_policy = wk >= spec["policy_start_week"]
            called = bool(in_policy and c["in_programme"] and cut is not None and score >= cut
                          and wk >= spec["policy_start_week"] + (c["ramp_group"] - 1))
            reached = called and o.random() < spec["call_reach_rate"]
            no_show = 1 if o.random() < _logistic(eta_out + (math.log(spec["reminder_or"]) if reached else 0.0)) else 0

            appointments.append({
                "appt_id": f"AP-{aid:07d}", "clinic_id": c["clinic_id"], "patient_id": pt["patient_id"],
                "booked_on": booked_on.isoformat(), "appointment_on": appt_on.isoformat(), "week": wk,
                "appointment_type": atype, "lead_time_days": lead, "age_band": pt["age_band"],
                "deprivation_decile": pt["deprivation_decile"],
                "deprivation_decile_served": served_decile, "interpreter_required": interpreter,
                "distance_km": pt["distance_km"],
                "prior_no_show_count": prior_all, "prior_no_show_count_12m_asof": prior_12m,
                "prior_no_shows_served": prior_served, "age_band_served": served_age,
                "appointment_type_served": served_type,
                "referral_source": "PARTNERSHIP-7" if new_source else "GP",
                "no_show": no_show, "called": 1 if called else 0,
                "_eta": eta_score, "_eta_out": eta_out, "_score": score, "_clinic": c,
                "_in_policy": in_policy, "_reached": reached,
            })
            kind = "DID_NOT_ATTEND" if no_show else "ATTENDED"
            pt["history"].append((appt_on, kind))
            events.append({"patient_id": pt["patient_id"], "event_on": appt_on.isoformat(),
                           "event_type": kind, "appt_id": f"AP-{aid:07d}"})
            if called:
                calls.append({"appt_id": f"AP-{aid:07d}",
                              "called_on": (appt_on - timedelta(days=2)).isoformat(),
                              "outcome": "REACHED" if reached else
                                         ("NO_ANSWER" if o.random() < 0.7 else "VOICEMAIL")})

    # noshow-v4.0: retrained on post-policy data, so it partly learns "high score -> attends".
    for a in appointments:
        leak = spec["v4_policy_leak"] if a["week"] >= spec["v4_trained_from_week"] else 0.0
        # v4.0 was fitted on post-policy data: it tracks the relationship that actually held in that period
        # (which helps where there has been genuine drift) and also picks up the policy's footprint on the
        # outcomes of the appointments the incumbent model ranked highest (which hurts everywhere).
        a["_score_v4"] = _logistic(a["_eta_out"] - leak * (a["_score"] - 0.5) * 4.0
                                   + d.gauss(0.0, spec["score_noise_sd"] * 1.05))

    return {"spec": spec, "clinics": clinics, "control_clinics": control,
            "appointments": appointments, "events": events, "seeded_events": seeded_events,
            "calls": calls, "cut": cut}


# --------------------------------------------------------------------------- metrics
def auc(scores, labels) -> float:
    """Rank-based AUC with ties handled by mid-ranks (identical to the Mann-Whitney statistic)."""
    pairs = sorted(zip(scores, labels))
    n = len(pairs)
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and pairs[j + 1][0] == pairs[i][0]:
            j += 1
        r = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = r
        i = j + 1
    pos = sum(1 for _, y in pairs if y == 1)
    neg = n - pos
    if pos == 0 or neg == 0:
        return float("nan")
    s = sum(r for r, (_, y) in zip(ranks, pairs) if y == 1)
    return (s - pos * (pos + 1) / 2.0) / (pos * neg)


def rescore(w, prior_key: str, use_true: bool) -> dict:
    """Score noshow-v3.1 from the published coefficients over a chosen feature vintage.

    prior_key         "prior_no_show_count" for the current feature table, "prior_no_show_count_12m_asof"
                      for the value as it stood at booking.
    use_true          True to take every feature from the patient and appointment record; False to take the
                      values the feature feed delivered to the scorer, defaults included.
    """
    out = {}
    for a in w["appointments"]:
        feat = {"prior_no_shows": a[prior_key], "lead_time_days": a["lead_time_days"],
                "distance_km": a["distance_km"],
                "deprivation_decile": a["deprivation_decile"] if use_true else a["deprivation_decile_served"],
                "age_band": a["age_band"] if use_true else a["age_band_served"],
                "appointment_type": a["appointment_type"] if use_true else a["appointment_type_served"]}
        out[a["appt_id"]] = _logistic(_eta(feat))
    return out


def rescore_current_vintage(w) -> dict:
    """What the vendor's monitoring computes: the published coefficients applied to the feature store as it
    now stands - the values it served, with the no-show count recomputed over the widened window."""
    return rescore(w, "prior_no_show_count", False)


def _recent(w):
    spec = w["spec"]
    lo = spec["n_weeks"] - spec["recent_weeks"] + 1
    return [a for a in w["appointments"] if a["week"] >= lo]


def truth(w) -> dict:
    spec = w["spec"]
    control = set(w["control_clinics"])
    recent = _recent(w)
    cur = rescore_current_vintage(w)

    prog = [a for a in recent if a["clinic_id"] not in control]
    ctrl = [a for a in recent if a["clinic_id"] in control]

    # What the dashboard reports: the whole network, on the feature store as it now stands. The dashboard does
    # not separate the clinics the programme never touched.
    deployed = auc([cur[a["appt_id"]] for a in recent], [a["no_show"] for a in recent])
    programme_auc_current = auc([cur[a["appt_id"]] for a in prog], [a["no_show"] for a in prog])
    hb_cur = auc([cur[a["appt_id"]] for a in ctrl], [a["no_show"] for a in ctrl])
    hb_asof = auc([a["_score"] for a in ctrl], [a["no_show"] for a in ctrl])
    hb_v4 = auc([a["_score_v4"] for a in ctrl], [a["no_show"] for a in ctrl])
    prog_asof = auc([a["_score"] for a in prog], [a["no_show"] for a in prog])

    validation = validation_auc(w)

    # Programme effect in the band the policy acts on, stratified by clinic size band.
    band_cut = _policy_cut(w, recent)
    sizes = {c["clinic_id"]: c["size_band"] for c in w["clinics"]}
    num = den = 0.0
    per_band = {}
    for band in sorted({c["size_band"] for c in w["clinics"]}):
        cb = [a for a in ctrl if sizes[a["clinic_id"]] == band and a["_score"] >= band_cut]
        pb = [a for a in prog if sizes[a["clinic_id"]] == band and a["_score"] >= band_cut]
        if len(cb) < 50 or len(pb) < 50:
            continue
        rc = 100.0 * sum(a["no_show"] for a in cb) / len(cb)
        rp = 100.0 * sum(a["no_show"] for a in pb) / len(pb)
        per_band[band] = {"n_control": len(cb), "n_programme": len(pb), "diff_pp": rc - rp}
        num += (rc - rp) * len(cb)
        den += len(cb)
    effect = num / den if den else float("nan")

    # The model risk standard's floor, and the clauses in the order the standard states them.
    floor = max(validation - spec["auc_tolerance"], spec["auc_floor"])
    served = [a for a in w["appointments"] if a["clinic_id"] in control]
    recent_all = recent
    # A served feature value that disagrees with what the append-only event log implies for that booking, or
    # with the patient record, is a defect in the feed rather than a property of the population.
    defect_share = (sum(1 for a in recent_all
                        if a["deprivation_decile_served"] != a["deprivation_decile"]
                        or a["prior_no_shows_served"] != a["prior_no_show_count_12m_asof"]
                        or a["age_band_served"] != a["age_band"]
                        or a["appointment_type_served"] != a["appointment_type"])
                    / len(recent_all))
    rep = rescore(w, "prior_no_show_count_12m_asof", True)   # as-of window, record values
    hb_repaired = auc([rep[a["appt_id"]] for a in ctrl], [a["no_show"] for a in ctrl])

    # A chain on one population, so the parts add to the whole by construction:
    #   validation -> (drift) -> repaired feed -> (feed defect) -> as served -> (vintage) -> current -> (policy)
    attribution = {
        "population_drift": validation - hb_repaired,
        "feature_feed_defect": hb_repaired - hb_asof,
        "feature_vintage": hb_asof - hb_cur,
        "policy_feedback": hb_cur - deployed,
        "other": 0.0,
    }
    if hb_asof >= floor:
        decision = "retain_model"
    elif defect_share > spec["feed_defect_material_share"] and hb_repaired >= floor:
        decision = "remediate_feature_pipeline"
    elif hb_v4 > hb_asof + spec["candidate_margin"]:
        decision = "replace_with_v4"
    else:
        decision = "retrain_on_recent_data"

    return {
        "deployed_auc_v31": deployed,
        "holdback_auc_v31_asof_features": hb_asof,
        "holdback_auc_v31_current_features": hb_cur,
        "holdback_auc_v40": hb_v4,
        "programme_auc_v31_asof_features": prog_asof,
        "programme_auc_v31_current_features": programme_auc_current,
        "reminder_effect_pp": effect,
        "reminder_effect_by_band": per_band,
        "attribution_auc": attribution,
        "monitoring_population": sorted(control),
        "n_recent_control": len(ctrl),
        "n_recent_programme": len(prog),
        "decision": decision,
        "validation_auc": validation,
        "retention_floor_auc": floor,
        "feed_defect_share": 100.0 * defect_share,
        "holdback_auc_v31_repaired_feed": hb_repaired,
        "policy_score_cut": w["cut"],
    }


def validation_auc(w) -> float:
    """The model card's figure: discrimination of the served scores over the period before the reminder
    programme started, when no outcome in the extract had been influenced by the model's use."""
    pre = [a for a in w["appointments"] if a["week"] < w["spec"]["policy_start_week"]]
    return auc([a["_score"] for a in pre], [a["no_show"] for a in pre])


def _policy_cut(w, rows):
    """The score threshold the reminder policy used: the top `call_percentile` of scores over the programme
    period, as recorded in the policy configuration."""
    return w["cut"]


def latent_check(w) -> dict:
    """Cross-derivation from the design: the realised effect of actually reaching a patient, which no
    estimator on the shipped tables can see directly."""
    reached = [a for a in _recent(w) if a["_reached"]]
    not_reached = [a for a in _recent(w) if a["called"] and not a["_reached"]]
    f = lambda rows: 100.0 * sum(a["no_show"] for a in rows) / len(rows) if rows else float("nan")
    return {"design_reminder_or": w["spec"]["reminder_or"],
            "reached_no_show_pct": f(reached), "unreached_called_no_show_pct": f(not_reached)}


# --------------------------------------------------------------------------- output
SCHEMA = """
CREATE TABLE clinics (clinic_id TEXT PRIMARY KEY, name TEXT, size_band TEXT, region TEXT,
    ramp_group INTEGER);
CREATE TABLE appointments (
    appt_id TEXT PRIMARY KEY, clinic_id TEXT, patient_id TEXT, booked_on TEXT, appointment_on TEXT,
    week INTEGER, appointment_type TEXT, lead_time_days INTEGER, age_band TEXT,
    deprivation_decile INTEGER, distance_km REAL, interpreter_required INTEGER, referral_source TEXT,
    prior_no_show_count INTEGER, attended INTEGER, no_show INTEGER);
CREATE TABLE feature_snapshots (
    appt_id TEXT PRIMARY KEY, scored_on TEXT, prior_no_shows_12m INTEGER, lead_time_days INTEGER,
    deprivation_decile INTEGER, distance_km REAL, age_band TEXT, appointment_type TEXT);
CREATE TABLE attendance_events (patient_id TEXT, event_on TEXT, event_type TEXT, appt_id TEXT);
CREATE TABLE model_scores (appt_id TEXT, model_version TEXT, score REAL);
CREATE TABLE model_registry (model_version TEXT PRIMARY KEY, trained_from TEXT, trained_to TEXT,
    validation_auc REAL, feature_window_days INTEGER, coefficients_json TEXT, notes TEXT);
CREATE TABLE reminder_calls (appt_id TEXT PRIMARY KEY, called_on TEXT, outcome TEXT);
CREATE TABLE policy_config (key TEXT, value TEXT, effective_from TEXT, note TEXT);
CREATE TABLE monitoring_metrics (week INTEGER, population TEXT, metric TEXT, value REAL);
CREATE INDEX ix_scores ON model_scores(appt_id, model_version);
CREATE INDEX ix_events ON attendance_events(patient_id, event_on);
"""


def write_sqlite(w, out_dir: str) -> str:
    spec = w["spec"]
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "appointments.sqlite")
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    p = _rng(spec["seed"], "presentation")

    con.executemany("INSERT INTO clinics VALUES (?,?,?,?,?)",
                    [(c["clinic_id"], c["name"], c["size_band"], c["region"], c["ramp_group"])
                     for c in w["clinics"]])

    appts = list(w["appointments"])
    p.shuffle(appts)
    con.executemany("INSERT INTO appointments VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [(a["appt_id"], a["clinic_id"], a["patient_id"], a["booked_on"], a["appointment_on"],
                      a["week"], a["appointment_type"], a["lead_time_days"], a["age_band"],
                      a["deprivation_decile"], a["distance_km"], a["interpreter_required"],
                      a["referral_source"], a["prior_no_show_count"],
                      0 if a["no_show"] else 1, a["no_show"]) for a in appts])
    con.executemany("INSERT INTO feature_snapshots VALUES (?,?,?,?,?,?,?,?)",
                    [(a["appt_id"], a["booked_on"], a["prior_no_shows_served"], a["lead_time_days"],
                      a["deprivation_decile_served"], a["distance_km"], a["age_band_served"],
                      a["appointment_type_served"]) for a in appts])
    ev = list(w["events"])
    p.shuffle(ev)
    con.executemany("INSERT INTO attendance_events VALUES (?,?,?,?)",
                    [(e["patient_id"], e["event_on"], e["event_type"], e["appt_id"]) for e in ev]
                    + [(pid, d0, k, None) for pid, d0, k in w["seeded_events"]])
    rows = [(a["appt_id"], "noshow-v3.1", round(a["_score"], 6)) for a in appts] + \
           [(a["appt_id"], "noshow-v4.0", round(a["_score_v4"], 6)) for a in appts]
    p.shuffle(rows)
    con.executemany("INSERT INTO model_scores VALUES (?,?,?)", rows)

    first = date.fromisoformat(spec["first_monday"])
    pol = first + timedelta(days=7 * (spec["policy_start_week"] - 1))
    con.executemany("INSERT INTO model_registry VALUES (?,?,?,?,?,?,?)", [
        ("noshow-v3.1", (first - timedelta(days=540)).isoformat(),
         (first - timedelta(days=30)).isoformat(), round(validation_auc(w), 4), spec["asof_window_days"],
         json.dumps(COEF, sort_keys=True),
         "Logistic. prior_no_shows_12m is the count of did-not-attend events in the rolling "
         f"{spec['asof_window_days']} days before booking, capped at {PRIOR_CAP}. Continuous features are "
         "centred: lead_time_days-21, deprivation_decile-5.5, distance_km-8. Scores in model_scores are the "
         "values produced at booking."),
        ("noshow-v4.0", pol.isoformat(),
         (first + timedelta(days=7 * spec["n_weeks"])).isoformat(), None, spec["asof_window_days"],
         None,
         "Vendor retrain on data from the reminder programme period onward. Scores in model_scores are a "
         "batch rescore of every appointment in the extract. Coefficients not released."),
    ])
    con.executemany("INSERT INTO reminder_calls VALUES (?,?,?)",
                    [(c["appt_id"], c["called_on"], c["outcome"]) for c in w["calls"]])

    excl = ",".join(sorted(w["control_clinics"]))
    con.executemany("INSERT INTO policy_config VALUES (?,?,?,?)", [
        ("programme.name", "Outpatient reminder calls", pol.isoformat(), None),
        ("programme.start_week", str(spec["policy_start_week"]), pol.isoformat(), None),
        ("programme.score_model", "noshow-v3.1", pol.isoformat(), None),
        ("programme.score_percentile", f"{spec['call_percentile']:.2f}", pol.isoformat(),
         "call the top share of scores by risk"),
        ("programme.ramp_weeks", str(spec["ramp_weeks"]), pol.isoformat(),
         "clinics join in ramp_group order, one group per week"),
        ("programme.excluded_clinics", excl, pol.isoformat(),
         "drawn stratified by size_band at programme start; these clinics receive no score-driven calling"),
        ("feature_store.prior_no_show_window_days", str(spec["current_window_days"] or 0),
         (first + timedelta(days=7 * (spec["backfill_week"] - 1))).isoformat(),
         "window used by the current feature table; 0 means all available history"),
    ])

    # The vendor's dashboard: weekly AUC on the population it monitors.
    cur = rescore_current_vintage(w)
    by_week = {}
    for a in w["appointments"]:
        by_week.setdefault(a["week"], []).append(a)
    mm = []
    for wk in sorted(by_week):
        rows_wk = by_week[wk]
        if len(rows_wk) < 200:
            continue
        v = auc([cur[a["appt_id"]] for a in rows_wk], [a["no_show"] for a in rows_wk])
        mm.append((wk, "all_clinics", "auc", round(v, 4)))
        mm.append((wk, "all_clinics", "no_show_rate",
                   round(sum(a["no_show"] for a in rows_wk) / len(rows_wk), 4)))
    con.executemany("INSERT INTO monitoring_metrics VALUES (?,?,?,?)", mm)

    con.commit()
    con.close()
    return path


def db_digest(db_path: str) -> str:
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for (name,) in sorted(con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()):
        h.update(name.encode())
        for row in con.execute(f"SELECT * FROM {name}"):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()


def generate(spec):
    return build(spec)


def main(argv):
    out = argv[1] if len(argv) > 1 else "/workspace"
    name = argv[2] if len(argv) > 2 else "visible"
    if name == "visible":
        spec = copy.deepcopy(VISIBLE_SPEC)
    else:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import scenarios
        spec = scenarios.by_name(name)
    w = build(spec)
    print(write_sqlite(w, out))


if __name__ == "__main__":
    main(sys.argv)
