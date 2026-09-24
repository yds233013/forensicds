"""Writes out/readout.json for the six-week windows either side of the week-19 step."""
import json
import os

from quality import attribution, dispositions


def write_report(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = dispositions.connect(db_path)
    try:
        pre = dispositions.parts(con, dispositions.PRE_WINDOW)
        post = dispositions.parts(con, dispositions.POST_WINDOW)
        baseline = dispositions.nonconforming_rate_pct(pre)
        reported = dispositions.nonconforming_rate_pct(post)
        readout = {
            "part_number": "MAN-4471",
            "window_pre": list(dispositions.PRE_WINDOW),
            "window_post": list(dispositions.POST_WINDOW),
            "baseline_nonconforming_rate_pct": round(baseline, 2),
            "reported_nonconforming_rate_pct": round(reported, 2),
            "attribution_pp": attribution.attribute(baseline, reported, pre, post),
            "family_effect": attribution.family_effect(list(pre) + list(post)),
            "supplier_decision": (
                "raise_supplier_nonconformance" if reported > 5.5 else "no_supplier_action"
            ),
        }
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
    finally:
        con.close()
