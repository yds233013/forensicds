"""Generate the P22 mutation suite.

Each mutation is the reference solution with one defect applied by textual substitution, so a mutant differs
from the reference only in the stated way. M00 is a *different legitimate route* to the same quantity and must
still score 1: the verifier grades the numbers, not the estimator. Every other mutation is a scientifically
plausible mistake a competent but mistaken analyst could make, and must score 0.

Each entry records why the mistake is plausible, what evidence in the workspace disproves it, and which graded
criterion is expected to catch it.
"""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOL = ROOT / "candidates/p22-gauge-recalibration/solution/quality"
OUT = pathlib.Path(__file__).resolve().parent / "mutations"

CONF = (SOL / "conformance.py").read_text()
ATTR = (SOL / "attribution.py").read_text()
REP = (SOL / "report.py").read_text()
DISP = (SOL / "dispositions.py").read_text()
SOURCES = {"conformance.py": CONF, "attribution.py": ATTR, "report.py": REP, "dispositions.py": DISP}

# (id, file, anchor, replacement, expected reward, rationale, disproving evidence, criterion)
EDITS = [
    ("M00_offset_from_certified_departure", "conformance.py",
     """    dates = sorted({r["measured_on"] for r in rows})
    if len(dates) < 2:
        return {}
    first, last = dates[0], dates[-1]
    by = {}
    for r in rows:
        if r["measured_on"] in (first, last):
            by.setdefault((r["machine_id"], r["measured_on"]), {}).setdefault(r["artefact_id"], []).append(
                r["measured_um"])
    out = {}
    for machine in sorted({r["machine_id"] for r in rows}):
        pre = by.get((machine, first), {})
        post = by.get((machine, last), {})
        shared = sorted(set(pre) & set(post))
        if not shared:
            continue
        out[machine] = mean(mean(post[a]) - mean(pre[a]) for a in shared)
    return out""",
     """    # A different legitimate route: the departure of the post-adjustment artefact readings from the NML
    # certified values. Uses no pre-adjustment round at all.
    joined = con.execute(
        "SELECT m.machine_id, m.measured_on, m.measured_um, p.certified_um "
        "FROM reference_measurements m JOIN reference_parts p ON p.artefact_id = m.artefact_id"
    ).fetchall()
    last = max(r["measured_on"] for r in joined)
    by = {}
    for r in joined:
        if r["measured_on"] == last:
            by.setdefault(r["machine_id"], []).append(r["measured_um"] - r["certified_um"])
    return {k: mean(v) for k, v in sorted(by.items())}""",
     1, "the same physical quantity from the certified values rather than the paired rounds",
     "nothing - it is valid", "none (must pass)"),

    ("M01_no_offset_at_all", "conformance.py",
     "    rows = con.execute(\n        \"SELECT machine_id, artefact_id, measured_on, measured_um FROM reference_measurements\"\n    ).fetchall()",
     "    return {}\n    rows = con.execute(\n        \"SELECT machine_id, artefact_id, measured_on, measured_um FROM reference_measurements\"\n    ).fetchall()",
     0, "the incumbent's frame: dispositions are taken as measured, so the readings need no correction",
     "the retained artefacts read systematically larger on CMM-1 after the adjustment",
     "scientific_object, identification, decision"),

    ("M02_offset_from_certificate", "conformance.py",
     "    rows = con.execute(\n        \"SELECT machine_id, artefact_id, measured_on, measured_um FROM reference_measurements\"\n    ).fetchall()",
     """    # Read the offset off the calibration certificate and scale it from the standard's length to the bore.
    cal = con.execute(
        "SELECT machine_id, as_left_um FROM calibration_events WHERE event_type LIKE '%ADJUST%'"
    ).fetchall()
    return {r["machine_id"]: r["as_left_um"] * 42.0 / 100.0 for r in cal}
    rows = con.execute(
        "SELECT machine_id, artefact_id, measured_on, measured_um FROM reference_measurements"
    ).fetchall()""",
     0, "the certificate is the obvious document and a length ratio is the obvious scaling",
     "QP-07 section 4 states the figure does not map to a feature offset by a fixed factor, and the artefacts show it does not",
     "scientific_object"),

    ("M03_offset_on_wrong_machine", "report.py",
     "        offsets = {m: round(v, 3) for m, v in offsets.items()}",
     "        offsets = {m: round(v, 3) for m, v in offsets.items()}\n        offsets = {\"CMM-1\": offsets.get(\"CMM-2\", 0.0), \"CMM-2\": offsets.get(\"CMM-1\", 0.0)}",
     0, "a transcription slip when the machine that was adjusted is not the machine named first in the table",
     "the calibration event names CMM-1; the artefact rounds show the change on CMM-1 only",
     "scientific_object, identification, independent_validation"),

    ("M04_offset_sign_reversed", "report.py",
     "        offsets = {m: round(v, 3) for m, v in offsets.items()}",
     "        offsets = {m: round(-v, 3) for m, v in offsets.items()}",
     0, "confusing 'the machine reads large' with 'the part is large', a standard sign trap in gauge work",
     "correcting in the wrong direction makes the corrected rate worse than the reported one, which the second machine contradicts",
     "scientific_object, identification, independent_validation, decision"),

    ("M05_offset_applied_to_baseline", "attribution.py",
     "    baseline = 100.0 * sum(1 for r in pre if abs(r[\"measured_um\"]) > tol_um) / len(pre)",
     "    baseline = 100.0 * sum(1 for r in pre\n                           if abs(r[\"measured_um\"] - offsets.get(r[\"machine_id\"], 0.0)) > tol_um) / len(pre)",
     0, "treating the offset as a standing property of the machine rather than as something the adjustment created",
     "the pre-adjustment artefact round reads the certified values, so the baseline window carries no offset",
     "evidence_reconstruction, quantitative_results"),

    ("M06_all_material", "attribution.py",
     """        "material": r3 - baseline,
            "measurement_system": r0 - r1,
            "tooling": r1 - r2,
            "operator": r2 - r3,""",
     """        "material": r0 - baseline,
            "measurement_system": 0.0,
            "tooling": 0.0,
            "operator": 0.0,""",
     0, "the week-19 heat changeover is real and significant, so the whole step is credited to material",
     "the artefacts and the un-adjusted machine both show most of the step is not in the parts",
     "quantitative_results"),

    ("M07_all_measurement", "attribution.py",
     """        "material": r3 - baseline,
            "measurement_system": r0 - r1,
            "tooling": r1 - r2,
            "operator": r2 - r3,""",
     """        "material": 0.0,
            "measurement_system": r0 - baseline,
            "tooling": 0.0,
            "operator": 0.0,""",
     0, "having found the gauge offset, crediting the entire step to it and stopping",
     "the un-adjusted machine's own rate rose too, so part of the step is in the parts",
     "quantitative_results"),

    ("M08_wear_slope_on_week", "attribution.py",
     """    xs, ys = [], []
    for r in rows:
        xs.append(r["tool_hours"])
        ys.append(r["measured_um"] - offsets.get(r["machine_id"], 0.0))""",
     """    xs, ys = [], []
    for r in rows:
        xs.append(r["week"])
        ys.append(r["measured_um"] - offsets.get(r["machine_id"], 0.0))""",
     0, "wear is naturally thought of as a trend over time, so the slope is fitted on production week",
     "inserts are changed weekly, so a slope on week absorbs any step at the window boundary; tool_hours identifies it within week",
     "quantitative_results"),

    ("M09_operator_absolute_not_contrast", "attribution.py",
     """    deltas = {k: b[k] - a[k] for k in shared}
    base = mean(deltas.values())
    return {k: v - base for k, v in deltas.items()}""",
     """    return {k: b[k] - a[k] for k in shared}""",
     0, "taking each operator's own before/after change as that operator's effect",
     "a shift common to every operator is not separable from a shift in the material, so only contrasts are identifiable",
     "quantitative_results"),

    ("M10_decision_on_corrected_rate", "report.py",
     "        material_rate = d[\"r3\"]",
     "        material_rate = d[\"r1\"]",
     0, "reading Schedule 3 as the rate against the conformance reference rather than the rate attributable to material",
     "Schedule 3 section 3.2 names the rate attributable to the supplied material",
     "decision"),

    ("M11_decision_on_reported_rate", "report.py",
     "        material_rate = d[\"r3\"]",
     "        material_rate = d[\"r0\"]",
     0, "the incumbent's reading: the rate as currently dispositioned",
     "the agreement names a rate measured against the drawing's conformance reference",
     "decision"),

    ("M12_corrected_on_cmm1_only", "report.py",
     "            \"corrected_nonconforming_rate_pct\": round(d[\"r1\"], 2),",
     "            \"corrected_nonconforming_rate_pct\": round(\n                100.0 * sum(1 for r in post if r[\"machine_id\"] == \"CMM-1\"\n                            and abs(r[\"measured_um\"] - offsets.get(\"CMM-1\", 0.0)) > tol) /\n                max(1, sum(1 for r in post if r[\"machine_id\"] == \"CMM-1\")), 2),",
     0, "restricting to the machine that was adjusted, as though the correction only applied there",
     "the agreement's population is the affected feature, not one machine's share of it; the csv covers all parts",
     "identification, estimator_implementation"),

    ("M13_window_off_by_one", "dispositions.py",
     "POST_WINDOW = (19, 24)",
     "POST_WINDOW = (20, 24)",
     0, "reading 'since week 19' as 'after week 19'",
     "the report, the calibration event and the notes all place the step at the start of week 19",
     "evidence_reconstruction, estimator_implementation"),

    ("M14_hedged_attribution", "attribution.py",
     """        "material": r3 - baseline,
            "measurement_system": r0 - r1,
            "tooling": r1 - r2,
            "operator": r2 - r3,
            "other": 0.0,""",
     """        # Spread the change over every cause so that whichever one is right is covered.
            "material": (r0 - baseline) / 4.0,
            "measurement_system": (r0 - baseline) / 4.0,
            "tooling": (r0 - baseline) / 4.0,
            "operator": (r0 - baseline) / 4.0,
            "other": 0.0,""",
     0, "hedging: name every cause so that the right one is always included",
     "each component is graded against its own value, and the sum constraint prevents inflating them all",
     "quantitative_results"),
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    expected, notes = {}, []
    for mid, fname, old, new, reward, why, disproof, crit in EDITS:
        text = SOURCES[fname]
        assert text.count(old) == 1, f"{mid}: anchor not unique in {fname} (found {text.count(old)})"
        d = OUT / mid
        d.mkdir(parents=True)
        (d / fname).write_text(text.replace(old, new))
        expected[mid] = reward
        notes.append({"id": mid, "file": fname, "expected_reward": reward, "why_plausible": why,
                      "disproved_by": disproof, "criterion": crit})
    (OUT / "expected.txt").write_text("".join(f"{k} {v}\n" for k, v in sorted(expected.items())))
    import json
    (OUT / "rationale.json").write_text(json.dumps(notes, indent=1) + "\n")
    print(f"wrote {len(expected)} mutations to {OUT}")


if __name__ == "__main__":
    main()
