"""Writes out/readout.json and out/part_dispositions.csv for the six-week windows either side of week 19."""
import csv
import json
import os

from quality import attribution, conformance, dispositions

MATERIAL_ESCALATION_LIMIT_PCT = 5.5   # supply quality agreement, Schedule 3 section 3.2


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = dispositions.connect(db_path)
    try:
        tol = dispositions.tolerance_um(con)
        pre = dispositions.parts(con, dispositions.PRE_WINDOW)
        post = dispositions.parts(con, dispositions.POST_WINDOW)

        # QP-07 section 3: what the drawing's tolerance is stated against.
        offsets = conformance.offsets_um(con)
        offsets = {m: round(v, 3) for m, v in offsets.items()}

        slope = attribution.wear_slope_um_per_hour(list(pre) + list(post), offsets)
        centre = _median_tool_hours(pre)
        wear = lambda row: slope * (row["tool_hours"] - centre)
        op_shifts = attribution.operator_shifts_um(pre, post, offsets, wear)
        d = attribution.decompose(pre, post, offsets, tol, wear, op_shifts)

        strata = {
            "by_machine": _strata(post, tol, "machine_id"),
            "by_shift": _strata(post, tol, "shift"),
            "by_heat_family": _strata(post, tol, "heat_family"),
            "by_operator": _strata(post, tol, "operator_id"),
        }
        material_rate = d["r3"]
        readout = {
            "part_number": "MAN-4471",
            "window_pre": list(dispositions.PRE_WINDOW),
            "window_post": list(dispositions.POST_WINDOW),
            "baseline_nonconforming_rate_pct": round(d["baseline"], 2),
            "reported_nonconforming_rate_pct": round(d["r0"], 2),
            "corrected_nonconforming_rate_pct": round(
                100.0 * sum(1 for r in post if r["machine_id"] == "CMM-1"
                            and abs(r["measured_um"] - offsets.get("CMM-1", 0.0)) > tol) /
                max(1, sum(1 for r in post if r["machine_id"] == "CMM-1")), 2),
            "conformance_reference_offset_um": {m: round(offsets.get(m, 0.0), 2) for m in ("CMM-1", "CMM-2")},
            "strata_nonconforming_rate_pct": strata,
            "attribution_pp": {k: round(v, 2) for k, v in d["attribution_pp"].items()},
            "supplier_decision": ("raise_supplier_nonconformance"
                                  if material_rate > MATERIAL_ESCALATION_LIMIT_PCT else "no_supplier_action"),
            "diagnostics": {
                "material_attributable_rate_pct": round(material_rate, 2),
                "tool_wear_um_per_hour": round(slope, 4),
                "operator_shift_um": {k: round(v, 2) for k, v in sorted(op_shifts.items())},
                "artefact_departure_from_certified_um": {
                    k: round(v, 2) for k, v in conformance.offset_check_against_certified(con, offsets).items()},
                "heat_family_effect": attribution.family_effect(post),
            },
        }
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")

        with open(os.path.join(out_dir, "part_dispositions.csv"), "w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["part_id", "machine_id", "measured_um", "disposition_reference"])
            for r in sorted(post, key=lambda x: x["part_id"]):
                m = r["measured_um"] - offsets.get(r["machine_id"], 0.0)
                wr.writerow([r["part_id"], r["machine_id"], r["measured_um"],
                             "PASS" if abs(m) <= tol else "FAIL"])
    finally:
        con.close()


def _median_tool_hours(rows):
    v = sorted(r["tool_hours"] for r in rows)
    return v[len(v) // 2]


def _strata(rows, tol, col):
    by = {}
    for r in rows:
        by.setdefault(r[col], []).append(r)
    return {k: round(100.0 * sum(1 for r in v if abs(r["measured_um"]) > tol) / len(v), 2)
            for k, v in sorted(by.items())}
