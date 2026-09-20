"""G34 pilot: overhaul-interval decision on a rotating-equipment fleet (research only).

CORE MECHANISM: time origin + delayed entry (left truncation).

A condition-monitoring platform went live at calendar month `mon_start`. Units already in service
entered the observable record at their CURRENT AGE, not at age zero. The risk clock the business
decision depends on is AGE SINCE COMMISSIONING, which lives in the asset register, not in the
monitoring feed.

Removal reasons in the work-order system do not map one-to-one onto statistical categories:
  unplanned_failure   -> the target event
  planned_overhaul    -> independent censoring (age-based policy, not condition-based)
  site_decommission   -> independent censoring (calendar-driven, unrelated to unit age)
  sensor_dropout      -> NOT an exit; the unit stays in service and at risk
"""
from __future__ import annotations
import copy
import numpy as np

A_WINDOW, B_WINDOW = 18.0, 30.0        # decision window: extend overhaul interval 18 -> 30 months

BASE = {
    "name": "visible",
    "n_units": 9000,
    "mon_start": 36.0,                 # calendar month the monitoring platform went live
    "study_len": 24.0,                 # observation window length
    "wb_shape": 2.3,
    "wb_scale": 34.0,
    "frailty_sd": 0.45,
    "pm_age": 18.0,                    # planned overhaul due age
    "pm_slack_mean": 3.0,              # scheduling slack
    "p_site_decom": 0.05,              # calendar-driven site closures
    "p_sensor_dropout": 0.12,          # monitoring gap - NOT a removal from service
    "gate": 0.30,                      # extend the interval only if net failure risk in (18,30] < 30%
}

REGIMES = {
    "visible": {},
    "older_fleet": {"mon_start": 54.0},                          # more delayed entry, more truncation
    "young_fleet": {"mon_start": 14.0},                          # little truncation
    "robust_units": {"wb_scale": 48.0},                          # decision flips: risk below the gate
    "noisy_monitoring": {"p_sensor_dropout": 0.30, "p_site_decom": 0.10},
}


def regime(name):
    s = copy.deepcopy(BASE); s.update(copy.deepcopy(REGIMES[name])); s["name"] = name
    return s


def draw_world(spec, seed):
    rng = np.random.default_rng(seed)
    n = spec["n_units"]
    comm = rng.uniform(0, spec["mon_start"] + spec["study_len"], n)      # commissioning calendar month
    frail = rng.lognormal(0, spec["frailty_sd"], n)
    Tf = spec["wb_scale"] * rng.weibull(spec["wb_shape"], n) / frail ** (1 / spec["wb_shape"])
    Tpm = spec["pm_age"] + rng.exponential(spec["pm_slack_mean"], n)     # age-based, condition-independent
    Tdec = np.where(rng.random(n) < spec["p_site_decom"],
                    rng.uniform(0, spec["mon_start"] + spec["study_len"], n) - comm, np.inf)
    Tdec = np.where(Tdec > 0, Tdec, np.inf)
    entry = np.maximum(0.0, spec["mon_start"] - comm)
    Tadmin = (spec["mon_start"] + spec["study_len"]) - comm
    in_fleet = (Tf > entry) & (Tpm > entry) & (Tdec > entry) & (Tadmin > entry)

    exit_ = np.minimum.reduce([Tf, Tpm, Tdec, Tadmin])
    cause = np.select([(Tf <= Tpm) & (Tf <= Tdec) & (Tf <= Tadmin),
                       (Tpm <= Tdec) & (Tpm <= Tadmin),
                       (Tdec <= Tadmin)],
                      [1, 2, 3], default=0)                            # 1 fail 2 overhaul 3 decom 0 admin
    dropout = rng.random(n) < spec["p_sensor_dropout"]
    drop_age = entry + rng.uniform(0, 1, n) * np.maximum(exit_ - entry, 0)
    return dict(spec=spec, seed=seed, comm=comm, Tf=Tf, entry=entry, exit=exit_, cause=cause,
                fleet=in_fleet, dropout=dropout, drop_age=drop_age, frail=frail)


def truth(w):
    """Net probability of unplanned failure in (18,30] given failure-free at 18, fleet-wide."""
    Tf = w["Tf"]
    p = float(np.mean(Tf[Tf > A_WINDOW] <= B_WINDOW))
    return {"p_fail_18_30": p, "decision": "extend" if p < w["spec"]["gate"] else "hold"}


REASON = {1: "unplanned_failure", 2: "planned_overhaul", 3: "site_decommission", 0: "study_end"}


def observed(w):
    """Analyst-visible records. Age is NOT precomputed: commissioning date is in the asset register,
    the monitoring feed carries calendar timestamps only."""
    m = w["fleet"]
    ms = w["spec"]["mon_start"]
    rows = []
    for i in np.flatnonzero(m):
        rows.append({
            "unit_id": int(i),
            "commissioned_month": float(w["comm"][i]),                       # asset register
            "monitoring_from_month": float(max(ms, w["comm"][i])),           # monitoring feed start
            "removed_month": float(w["comm"][i] + w["exit"][i]) if w["cause"][i] != 0 else None,
            "removal_reason": REASON[int(w["cause"][i])] if w["cause"][i] != 0 else None,
            "last_seen_month": float(w["comm"][i] + w["exit"][i]),
            "sensor_gap": bool(w["dropout"][i]),
        })
    return {"spec": w["spec"], "units": rows, "mon_start": ms,
            "study_end": ms + w["spec"]["study_len"], "gate": w["spec"]["gate"]}
