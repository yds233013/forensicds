"""Writes out/readout.json for the six-week windows either side of the week-19 step."""
import csv
import json
import os

from quality import attribution, dispositions


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = dispositions.connect(db_path)
    try:
        tol = dispositions.tolerance_um(con)
        pre = dispositions.parts(con, dispositions.PRE_WINDOW)
        post = dispositions.parts(con, dispositions.POST_WINDOW)
        
        baseline = dispositions.nonconforming_rate_pct(pre)
        reported = dispositions.nonconforming_rate_pct(post)
        
        post_offsets = dispositions.machine_offsets_um(con, dispositions.POST_WINDOW)
        corrected = dispositions.corrected_rate_pct(post, post_offsets, tol)
        
        # Strata calculation
        strata = {
            "by_machine": {},
            "by_shift": {},
            "by_heat_family": {},
            "by_operator": {},
        }
        for r in post:
            strata["by_machine"].setdefault(r["machine_id"], []).append(r)
            strata["by_shift"].setdefault(str(r["shift"]), []).append(r)
            strata["by_heat_family"].setdefault(r["heat_family"], []).append(r)
            strata["by_operator"].setdefault(r["operator_id"], []).append(r)
            
        strata_rates = {}
        for s_key, s_dict in strata.items():
            strata_rates[s_key] = {
                val: round(dispositions.nonconforming_rate_pct(rows), 2)
                for val, rows in s_dict.items()
            }

        # Attribution
        attr = attribution.attribute(baseline, reported, corrected)
        
        # Schedule 3 §3.2: Escalation ... where the nonconforming rate ... attributable to the supplied material ... exceeds 5.5 %
        # material_rate_post = corrected_post - corrected_pre (approx)
        # But wait, the agreement says: "where the nonconforming rate for the affected feature that is attributable to the supplied material ... exceeds 5.5%"
        # The baseline rate (3.0%) is also for the same feature.
        # So is it the absolute rate of material-attributable NCs, or the increase?
        # "nonconforming rate ... attributable to the supplied material ... exceeds 5.5%"
        # If the corrected rate is 4.5%, then the material-attributable rate is at most 4.5%.
        # If the corrected rate is 6.0%, and the baseline was 3.0%, the rate attributable to material in the post window is 6.0%.
        # Usually it means the absolute rate.
        
        decision = "raise_supplier_nonconformance" if corrected > 5.5 else "no_supplier_action"

        readout = {
            "part_number": "MAN-4471",
            "window_pre": list(dispositions.PRE_WINDOW),
            "window_post": list(dispositions.POST_WINDOW),
            "baseline_nonconforming_rate_pct": round(baseline, 2),
            "reported_nonconforming_rate_pct": round(reported, 2),
            "corrected_nonconforming_rate_pct": round(corrected, 2),
            "conformance_reference_offset_um": {k: round(v, 2) for k, v in post_offsets.items()},
            "strata_nonconforming_rate_pct": strata_rates,
            "attribution_pp": attr,
            "supplier_decision": decision,
        }
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        # Write CSV
        with open(os.path.join(out_dir, "part_dispositions.csv"), "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["part_id", "machine_id", "measured_um", "disposition_reference"])
            for r in post:
                disp_ref = dispositions.corrected_disposition(r["measured_um"], post_offsets[r["machine_id"]], tol)
                writer.writerow([r["part_id"], r["machine_id"], r["measured_um"], disp_ref])
                
    finally:
        con.close()
