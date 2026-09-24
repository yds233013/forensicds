"""Writes out/readout.json and out/part_dispositions.csv for the six-week windows."""
import csv
import json
import os

from quality import attribution, dispositions


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = dispositions.connect(db_path)
    try:
        tol_um = dispositions.tolerance_um(con)
        offsets = dispositions.get_offsets(con)
        
        pre = dispositions.parts(con, dispositions.PRE_WINDOW)
        post = dispositions.parts(con, dispositions.POST_WINDOW)
        
        baseline = dispositions.nonconforming_rate_pct(pre)
        reported = dispositions.nonconforming_rate_pct(post)
        corrected = dispositions.corrected_nonconforming_rate_pct(post, offsets, tol_um)
        
        # Strata calculation
        strata = {}
        for key, col in [
            ("by_machine", "machine_id"),
            ("by_shift", "shift"),
            ("by_heat_family", "heat_family"),
            ("by_operator", "operator_id"),
        ]:
            by_val = {}
            for r in post:
                by_val.setdefault(r[col], []).append(r)
            strata[key] = {
                val: round(dispositions.nonconforming_rate_pct(rows), 2)
                for val, rows in by_val.items()
            }

        # Material-attributable rate is the corrected rate minus baseline (if positive)
        # Actually Schedule 3 §3.2 says "the nonconforming rate ... attributable to the supplied material ... measured against the drawing's conformance reference"
        # This is interpreted as the corrected nonconforming rate.
        material_attr_rate = corrected
        
        readout = {
            "part_number": "MAN-4471",
            "window_pre": list(dispositions.PRE_WINDOW),
            "window_post": list(dispositions.POST_WINDOW),
            "baseline_nonconforming_rate_pct": round(baseline, 2),
            "reported_nonconforming_rate_pct": round(reported, 2),
            "corrected_nonconforming_rate_pct": round(corrected, 2),
            "conformance_reference_offset_um": {m: round(o, 3) for m, o in offsets.items()},
            "strata_nonconforming_rate_pct": strata,
            "attribution_pp": attribution.attribute(baseline, reported, corrected),
            "supplier_decision": (
                "raise_supplier_nonconformance" if material_attr_rate > 5.5 else "no_supplier_action"
            ),
        }
        
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        with open(os.path.join(out_dir, "part_dispositions.csv"), "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["part_id", "machine_id", "measured_um", "disposition_reference"])
            for r in post:
                offset = offsets.get(r["machine_id"], 0.0)
                disp_ref = "PASS" if abs(r["measured_um"] - offset) <= tol_um else "FAIL"
                writer.writerow([r["part_id"], r["machine_id"], r["measured_um"], disp_ref])
                
    finally:
        con.close()
