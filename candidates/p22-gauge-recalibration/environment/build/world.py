"""Deterministic generator for the Kelvin Works MAN-4471 bore-inspection extract (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/inspection.sqlite

The same module builds the hidden extracts and the truth used by the verifier. Design draws (true part
geometry, heat properties, tool wear) and presentation draws (row order, identifiers) use separate streams,
so a change to presentation cannot move a graded quantity.

Physical model, all lengths in micrometres of deviation from the nominal bore diameter:

    true deviation      X = heat_shift + tool_wear + operator_shift + N(0, sigma_p^2)
    measured deviation  M = X + machine_bias(machine, week) + N(0, sigma_m^2)
    disposition         PASS iff |M| <= tol_um        (the drawing's tolerance; unchanged all year)

CMM-1 is recalibrated at the start of `recal_week` and its bias moves from 0 to `bias_um`; CMM-2 is not
recalibrated and its bias stays 0. Parts are assigned to a measuring machine by the inspection rota, so the
two machines see comparable populations. Retained reference artefacts with certified deviations are measured
on both machines before and after the recalibration; those paired differences identify the bias exactly.
A functional leak test on a sample depends on X alone and so is independent of both machines.
"""
from __future__ import annotations

import copy
import hashlib
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

MACHINES = ("CMM-1", "CMM-2")
OPERATORS = ("OP-114", "OP-207", "OP-318", "OP-421")
SHIFTS = ("DAY", "NIGHT")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 4471903,
    "part_number": "MAN-4471",
    "feature": "BORE_DIA_42",
    "tol_um": 30.0,              # drawing: nominal 42.000 mm, +/- 0.030 mm
    "first_week": 13,
    "last_week": 24,
    "recal_week": 19,            # CMM-1 recalibrated at the start of this week
    "parts_per_week": 2000,
    "cmm2_share": 0.25,          # share of parts routed to CMM-2 by the inspection rota
    "sigma_p": 13.3,             # within-heat part-to-part standard deviation
    "sigma_m": 3.0,              # gauge repeatability (one reading)
    "bias_um": 8.2,              # CMM-1 as-left bias after the week-19 recalibration
    "heat_families": {           # family -> (mean shift um, extra sd um)
        "H2": (0.0, 0.0),
        "H3": (1.2, 4.0),        # a small, genuine melt-route difference
    },
    "family_switch_week": 19,    # H2 heats run out and H3 heats start (a genuine confound)
    # Inserts are changed weekly, so wear is a within-week effect carried by tool_hours, not a trend on
    # production week. Centring on the midpoint of the baseline change interval keeps the baseline process on
    # nominal; an extended change interval in the post window is what makes tooling move the rate.
    "tool_wear_um_per_hour": 0.17,
    "tool_hours_centre": 20.0,
    "tool_hours_pre": (2.0, 38.0),
    "tool_hours_post": (2.0, 38.0),
    "operator_shift_um": 0.0,
    "operator_shift_who": None,
    "operator_shift_from_week": None,   # the shift applies only from this week (a cell change)
    "functional_share": 0.08,
    "functional_error_um": 4.0,  # the leak rig's own measurement error
    "n_reference_parts": 20,
    "reference_reps": 5,
    "supplier_rate_limit_pct": 5.5,
    # The certificate reports deviation at the standard's length (100 mm) after a compensation write. The
    # error is neither a pure offset nor a pure scale, so the figure does not map to a 42 mm bore offset by
    # any factor the workspace discloses: cert_scale_k is a nuisance parameter of the adjustment.
    "cert_scale_k": 1.27,
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _week_start(week):
    # 2026 week 13 begins Monday 2026-03-23; weeks are consecutive Mondays.
    return date(2026, 3, 23) + timedelta(days=7 * (week - 13))


def build(spec: dict) -> dict:
    d = _rng(spec["seed"], "design")
    weeks = list(range(spec["first_week"], spec["last_week"] + 1))

    # Heats: one or two lots consumed per week, family switching at family_switch_week.
    heats = []
    for w in weeks:
        fam = "H2" if w < spec["family_switch_week"] else "H3"
        for k in range(2):
            heats.append({
                "heat_id": f"{fam}-{w:02d}{k}",
                "family": fam,
                "week": w,
                "supplier_lot": f"BAR-{d.randint(10000, 99999)}",
                "hardness_hv": round(d.uniform(182, 196) + (6.0 if fam == "H3" else 0.0), 1),
                "cert_no": f"MTC-{d.randint(200000, 299999)}",
            })
    heats_by_week = {}
    for h in heats:
        heats_by_week.setdefault(h["week"], []).append(h)

    parts = []
    functional = []
    pid = 0
    for w in weeks:
        wk_heats = heats_by_week[w]
        hr_lo, hr_hi = spec["tool_hours_pre"] if w < spec["recal_week"] else spec["tool_hours_post"]
        for _ in range(spec["parts_per_week"]):
            pid += 1
            h = wk_heats[d.randrange(len(wk_heats))]
            fam_shift, fam_extra = spec["heat_families"][h["family"]]
            op = OPERATORS[d.randrange(len(OPERATORS))]
            shift = SHIFTS[0] if d.random() < 0.62 else SHIFTS[1]
            op_shift = (spec["operator_shift_um"]
                        if (spec["operator_shift_who"] and op == spec["operator_shift_who"]
                            and w >= (spec["operator_shift_from_week"] or 0)) else 0.0)
            tool_hours = round(d.uniform(hr_lo, hr_hi), 1)
            wear = spec["tool_wear_um_per_hour"] * (tool_hours - spec["tool_hours_centre"])
            sd = (spec["sigma_p"] ** 2 + fam_extra ** 2) ** 0.5
            x = d.gauss(fam_shift + wear + op_shift, sd)
            machine = MACHINES[1] if d.random() < spec["cmm2_share"] else MACHINES[0]
            bias = spec["bias_um"] if (machine == "CMM-1" and w >= spec["recal_week"]) else 0.0
            m = x + bias + d.gauss(0.0, spec["sigma_m"])
            parts.append({
                "part_id": f"P{pid:06d}",
                "week": w,
                "inspected_on": (_week_start(w) + timedelta(days=d.randrange(5))).isoformat(),
                "heat_id": h["heat_id"],
                "machine_id": machine,
                "operator_id": op,
                "shift": shift,
                "tool_hours": tool_hours,
                "spindle_rpm": d.randrange(2100, 2400, 10),
                "feed_mm_min": round(d.uniform(118.0, 132.0), 1),
                "coolant_temp_c": round(d.uniform(19.5, 24.5), 1),
                "measured_um": round(m, 2),
                "_true_um": x,
            })
            if d.random() < spec["functional_share"]:
                fx = x + d.gauss(0.0, spec["functional_error_um"])
                functional.append({
                    "part_id": f"P{pid:06d}",
                    "tested_on": (_week_start(w) + timedelta(days=d.randrange(5, 7))).isoformat(),
                    "rig_id": "LEAK-02",
                    "result": "FAIL" if abs(fx) > spec["tol_um"] else "PASS",
                })

    # Retained reference artefacts: certified deviations, measured on both machines before and after.
    refs, ref_meas = [], []
    for i in range(spec["n_reference_parts"]):
        cert = round(d.uniform(-22.0, 22.0), 2)
        aid = f"REF-{i + 1:02d}"
        refs.append({
            "artefact_id": aid,
            "certified_um": cert,
            "certified_by": "NML-UKAS-0812",
            "certificate_no": f"CAL-{d.randint(70000, 79999)}",
            "uncertainty_um": 0.6,
        })
        for w in (spec["recal_week"] - 2, spec["recal_week"] + 1):
            when = (_week_start(w) + timedelta(days=1)).isoformat()
            for machine in MACHINES:
                bias = spec["bias_um"] if (machine == "CMM-1" and w >= spec["recal_week"]) else 0.0
                for rep in range(1, spec["reference_reps"] + 1):
                    ref_meas.append({
                        "artefact_id": aid,
                        "machine_id": machine,
                        "measured_on": when,
                        "rep": rep,
                        "measured_um": round(cert + bias + d.gauss(0.0, spec["sigma_m"]), 2),
                    })

    # Calibration history. The as-found/as-left pair on the week-19 event is the factual record of the change;
    # its magnitude is recorded at the standard's length, not as a bore bias.
    cal = [
        {"machine_id": "CMM-1", "event_date": "2025-11-14", "event_type": "PERIODIC",
         "standard_id": "GB-100.000", "as_found_um": 0.4, "as_left_um": 0.1,
         "certificate_no": "CC-118204", "technician": "MetrologyPartners Ltd"},
        {"machine_id": "CMM-2", "event_date": "2026-01-23", "event_type": "PERIODIC",
         "standard_id": "GB-100.000", "as_found_um": -0.3, "as_left_um": -0.2,
         "certificate_no": "CC-121550", "technician": "MetrologyPartners Ltd"},
        {"machine_id": "CMM-1", "event_date": _week_start(spec["recal_week"]).isoformat(),
         "event_type": "PERIODIC+ADJUST", "standard_id": "GB-100.000",
         "as_found_um": round(-spec["bias_um"] * 0.11, 2),
         "as_left_um": round(spec["bias_um"] * (100.0 / 42.0) * spec["cert_scale_k"], 2),
         "certificate_no": "CC-124471", "technician": "MetrologyPartners Ltd"},
    ]

    tools = []
    for w in weeks:
        hi = (spec["tool_hours_pre"] if w < spec["recal_week"] else spec["tool_hours_post"])[1]
        tools.append({"machine_id": "MC-07", "changed_on": _week_start(w).isoformat(),
                      "tool_id": f"INS-{d.randint(400, 499)}", "reason": "SCHEDULED",
                      "cumulative_hours": round(d.uniform(hi, hi + 3.0), 1)})

    return {"spec": spec, "heats": heats, "parts": parts, "functional": functional,
            "reference_parts": refs, "reference_measurements": ref_meas,
            "calibration_events": cal, "tool_changes": tools}


# --------------------------------------------------------------------------- truth
def _rate(rows, tol, adj=None):
    """Nonconforming share (%) of `rows`, optionally after subtracting a per-machine offset."""
    if not rows:
        return None
    bad = 0
    for r in rows:
        m = r["measured_um"] - (adj.get(r["machine_id"], 0.0) if adj else 0.0)
        if abs(m) > tol:
            bad += 1
    return 100.0 * bad / len(rows)


def bias_from_reference(w) -> float:
    """Paired reference-artefact bridge: CMM-1's post-adjustment reading of a certified artefact less its
    pre-adjustment reading of the same artefact, averaged over artefacts and repeats. Uses no production data
    and does not depend on the certified values themselves."""
    pre_date, post_date = sorted({m["measured_on"] for m in w["reference_measurements"]})
    pre, post = {}, {}
    for m in w["reference_measurements"]:
        if m["machine_id"] != "CMM-1":
            continue
        (pre if m["measured_on"] == pre_date else post).setdefault(m["artefact_id"], []).append(m["measured_um"])
    diffs = [sum(post[a]) / len(post[a]) - sum(pre[a]) / len(pre[a]) for a in post if a in pre]
    return sum(diffs) / len(diffs)


def bias_from_second_machine(w) -> float:
    """Two-sample bridge: the CMM-1 minus CMM-2 contrast in mean reading after the adjustment, net of the same
    contrast before it. Unbiased because the inspection rota assigns parts to machines independently of
    geometry, so a difference-in-differences removes any standing inter-machine difference."""
    spec = w["spec"]
    recal = spec["recal_week"]
    mean = lambda rows: sum(r["measured_um"] for r in rows) / len(rows)
    sel = lambda mc, post: [p for p in w["parts"]
                            if p["machine_id"] == mc and ((p["week"] >= recal) == post)]
    return (mean(sel("CMM-1", True)) - mean(sel("CMM-2", True))) - \
           (mean(sel("CMM-1", False)) - mean(sel("CMM-2", False)))


def _wear(spec, part):
    return spec["tool_wear_um_per_hour"] * (part["tool_hours"] - spec["tool_hours_centre"])


def _op_shift(spec, part):
    if not spec["operator_shift_who"] or spec["operator_shift_um"] == 0.0:
        return 0.0
    if part["operator_id"] != spec["operator_shift_who"]:
        return 0.0
    if part["week"] < (spec["operator_shift_from_week"] or 0):
        return 0.0
    return spec["operator_shift_um"]


def _op_shift_relative(spec, part, mean_shift):
    """Only operator *contrasts* are identifiable from the extract: a shift common to every operator is
    indistinguishable from a shift in the material, because there is no untreated operator to compare against.
    The attribution therefore credits the contrast to `operator` and the common part to `material`, which is
    what any legitimate estimator (a per-operator difference in differences) recovers."""
    return _op_shift(spec, part) - mean_shift


def truth(w) -> dict:
    """Every graded quantity.

    The decomposition is sequential and each step is a rate on the post window with one more effect removed:

        r0  as dispositioned                                 -> reported_nonconforming_rate_pct
        r1  machine offsets removed                          -> corrected_nonconforming_rate_pct (QP-07 ref)
        r2  and the tool-wear increment over the pre window removed
        r3  and the operator shift removed                   -> the material-attributable rate

        measurement_system = r0 - r1 ; tooling = r1 - r2 ; operator = r2 - r3 ; material = r3 - baseline

    Effects are removed using the design's own values, so the target is the physically correct decomposition
    rather than any one estimator's output. `routes()` records what each legitimate estimator recovers.
    """
    spec = w["spec"]
    tol, recal = spec["tol_um"], spec["recal_week"]
    pre = [p for p in w["parts"] if p["week"] < recal]
    post = [p for p in w["parts"] if p["week"] >= recal]
    b = spec["bias_um"]
    off = {"CMM-1": b, "CMM-2": 0.0}
    wear_pre = sum(_wear(spec, p) for p in pre) / len(pre)
    op_mean_post = sum(_op_shift(spec, p) for p in post) / len(post)

    def rate(remove_bias=False, remove_wear=False, remove_op=False):
        bad = 0
        for p in post:
            m = p["measured_um"]
            if remove_bias:
                m -= off[p["machine_id"]]
            if remove_wear:
                m -= _wear(spec, p) - wear_pre
            if remove_op:
                m -= _op_shift_relative(spec, p, op_mean_post)
            if abs(m) > tol:
                bad += 1
        return 100.0 * bad / len(post)

    baseline = _rate(pre, tol)
    r0, r1 = rate(), rate(True)
    r2 = rate(True, True)
    r3 = rate(True, True, True)

    strata = {}
    for key, col in (("by_machine", "machine_id"), ("by_shift", "shift"),
                     ("by_operator", "operator_id"), ("by_heat_family", None)):
        groups = {}
        for p in post:
            v = _family(w, p) if col is None else p[col]
            groups.setdefault(v, []).append(p)
        strata[key] = {k: _rate(v, tol) for k, v in sorted(groups.items())}

    return {
        "bias_um": b,
        "conformance_reference_offset_um": {"CMM-1": b, "CMM-2": 0.0},
        "baseline_nonconforming_rate_pct": baseline,
        "reported_nonconforming_rate_pct": r0,
        "corrected_nonconforming_rate_pct": r1,
        "material_attributable_rate_pct": r3,
        "cmm2_nonconforming_rate_pct": _rate([p for p in post if p["machine_id"] == "CMM-2"], tol),
        "strata_nonconforming_rate_pct": strata,
        "attribution_pp": {
            "material": r3 - baseline,
            "measurement_system": r0 - r1,
            "tooling": r1 - r2,
            "operator": r2 - r3,
            "other": 0.0,
        },
        "observed_change_pp": r0 - baseline,
        "supplier_decision": ("raise_supplier_nonconformance"
                              if r3 > spec["supplier_rate_limit_pct"] else "no_supplier_action"),
        "n_pre": len(pre), "n_post": len(post),
    }


def _family(w, part):
    if not hasattr(w, "_fam"):
        pass
    fam = w.setdefault("_fam_map", {h["heat_id"]: h["family"] for h in w["heats"]})
    return fam[part["heat_id"]]


def routes(w) -> dict:
    """What each legitimate estimator recovers for the two quantities that need one. All of these must land
    inside the graded tolerance of `truth()`; that is the multiple-valid-method audit."""
    spec = w["spec"]
    tol, recal = spec["tol_um"], spec["recal_week"]
    post = [p for p in w["parts"] if p["week"] >= recal]
    out = {}
    for name, b in (("reference_bridge", bias_from_reference(w)),
                    ("second_machine_did", bias_from_second_machine(w)),
                    ("design", spec["bias_um"])):
        out[name] = {"bias_um": b,
                     "corrected_nonconforming_rate_pct": _rate(post, tol, adj={"CMM-1": b})}
    out["second_machine_direct"] = {
        "bias_um": None,
        "corrected_nonconforming_rate_pct": _rate([p for p in post if p["machine_id"] == "CMM-2"], tol)}
    return out


def latent_check(w) -> dict:
    """Cross-derivation from the latent geometry: the nonconforming rate the true parts imply, which no
    estimator sees. Used by the gates and the verifier self-check, never shipped."""
    spec = w["spec"]
    tol, recal = spec["tol_um"], spec["recal_week"]
    f = lambda rows: 100.0 * sum(1 for p in rows if abs(p["_true_um"]) > tol) / len(rows)
    return {"true_pre_pct": f([p for p in w["parts"] if p["week"] < recal]),
            "true_post_pct": f([p for p in w["parts"] if p["week"] >= recal]),
            "design_bias_um": spec["bias_um"]}


# --------------------------------------------------------------------------- output
SCHEMA = """
CREATE TABLE inspection_results (
    part_id TEXT PRIMARY KEY, week INTEGER, inspected_on TEXT, heat_id TEXT, machine_id TEXT,
    operator_id TEXT, shift TEXT, tool_hours REAL, spindle_rpm INTEGER, feed_mm_min REAL,
    coolant_temp_c REAL, measured_um REAL, disposition TEXT);
CREATE TABLE heats (heat_id TEXT PRIMARY KEY, family TEXT, first_week INTEGER, supplier_lot TEXT,
    hardness_hv REAL, cert_no TEXT);
CREATE TABLE reference_parts (artefact_id TEXT PRIMARY KEY, certified_um REAL, certified_by TEXT,
    certificate_no TEXT, uncertainty_um REAL);
CREATE TABLE reference_measurements (artefact_id TEXT, machine_id TEXT, measured_on TEXT, rep INTEGER,
    measured_um REAL);
CREATE TABLE calibration_events (machine_id TEXT, event_date TEXT, event_type TEXT, standard_id TEXT,
    as_found_um REAL, as_left_um REAL, certificate_no TEXT, technician TEXT);
CREATE TABLE functional_tests (part_id TEXT PRIMARY KEY, tested_on TEXT, rig_id TEXT, result TEXT);
CREATE TABLE tool_changes (machine_id TEXT, changed_on TEXT, tool_id TEXT, reason TEXT,
    cumulative_hours REAL);
CREATE TABLE drawing_limits (part_number TEXT, feature TEXT, nominal_mm REAL, tol_um REAL,
    revision TEXT, effective_from TEXT);
"""


def write_sqlite(w, out_dir: str) -> str:
    spec = w["spec"]
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "inspection.sqlite")
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    p = _rng(spec["seed"], "presentation")
    rows = list(w["parts"])
    p.shuffle(rows)
    con.executemany(
        "INSERT INTO inspection_results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(r["part_id"], r["week"], r["inspected_on"], r["heat_id"], r["machine_id"], r["operator_id"],
          r["shift"], r["tool_hours"], r["spindle_rpm"], r["feed_mm_min"], r["coolant_temp_c"],
          r["measured_um"], "PASS" if abs(r["measured_um"]) <= spec["tol_um"] else "FAIL") for r in rows])
    con.executemany("INSERT INTO heats VALUES (?,?,?,?,?,?)",
                    [(h["heat_id"], h["family"], h["week"], h["supplier_lot"], h["hardness_hv"], h["cert_no"])
                     for h in w["heats"]])
    con.executemany("INSERT INTO reference_parts VALUES (?,?,?,?,?)",
                    [(r["artefact_id"], r["certified_um"], r["certified_by"], r["certificate_no"],
                      r["uncertainty_um"]) for r in w["reference_parts"]])
    rm = list(w["reference_measurements"])
    p.shuffle(rm)
    con.executemany("INSERT INTO reference_measurements VALUES (?,?,?,?,?)",
                    [(r["artefact_id"], r["machine_id"], r["measured_on"], r["rep"], r["measured_um"])
                     for r in rm])
    con.executemany("INSERT INTO calibration_events VALUES (?,?,?,?,?,?,?,?)",
                    [(c["machine_id"], c["event_date"], c["event_type"], c["standard_id"], c["as_found_um"],
                      c["as_left_um"], c["certificate_no"], c["technician"]) for c in w["calibration_events"]])
    ft = list(w["functional"])
    p.shuffle(ft)
    con.executemany("INSERT INTO functional_tests VALUES (?,?,?,?)",
                    [(f["part_id"], f["tested_on"], f["rig_id"], f["result"]) for f in ft])
    con.executemany("INSERT INTO tool_changes VALUES (?,?,?,?,?)",
                    [(t["machine_id"], t["changed_on"], t["tool_id"], t["reason"], t["cumulative_hours"])
                     for t in w["tool_changes"]])
    con.execute("INSERT INTO drawing_limits VALUES (?,?,?,?,?,?)",
                (spec["part_number"], spec["feature"], 42.0, spec["tol_um"], "F", "2024-02-19"))
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
