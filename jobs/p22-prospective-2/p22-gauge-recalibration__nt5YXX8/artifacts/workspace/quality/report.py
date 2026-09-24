"""Writes out/readout.json for the six-week windows either side of the week-19 step."""
import csv
import json
import os

from quality import attribution, dispositions


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = dispositions.connect(db_path)
    try:
        offsets = dispositions.get_offsets(con)
        
        pre = dispositions.parts(con, dispositions.PRE_WINDOW)
        post = dispositions.parts(con, dispositions.POST_WINDOW, offsets=offsets)
        
        baseline = dispositions.nonconforming_rate_pct(pre)
        reported = dispositions.nonconforming_rate_pct(post)
        corrected = dispositions.nonconforming_rate_pct(post, col="disposition_reference")
        
        # Strata: by_machine, by_shift, by_heat_family, by_operator
        strata = {}
        for s, col in [
            ("by_machine", "machine_id"),
            ("by_shift", "shift"),
            ("by_heat_family", "heat_family"),
            ("by_operator", "operator_id"),
        ]:
            by_val = {}
            for r in post:
                by_val.setdefault(r[col], []).append(r)
            strata[s] = {v: dispositions.nonconforming_rate_pct(p) for v, p in by_val.items()}

        readout = {
            "part_number": "MAN-4471",
            "window_pre": list(dispositions.PRE_WINDOW),
            "window_post": list(dispositions.POST_WINDOW),
            "baseline_nonconforming_rate_pct": round(baseline, 2),
            "reported_nonconforming_rate_pct": round(reported, 2),
            "corrected_nonconforming_rate_pct": round(corrected, 2),
            "conformance_reference_offset_um": {
                m: round(o, 2) for m, o in offsets.items()
            },
            "strata_nonconforming_rate_pct": strata,
            "attribution_pp": attribution.attribute(baseline, reported, corrected),
            "supplier_decision": (
                "raise_supplier_nonconformance" if corrected > 5.5 else "no_supplier_action"
            ),
        }
        
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        with open(os.path.join(out_dir, "part_dispositions.csv"), "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["part_id", "machine_id", "measured_um", "disposition_reference"])
            for r in post:
                writer.writerow([
                    r["part_id"], r["machine_id"], r["measured_um"], r["disposition_reference"]
                ])
                
    finally:
        con.close()
