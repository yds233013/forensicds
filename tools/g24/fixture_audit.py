#!/usr/bin/env python3
"""Build-time audit of the four frozen G24 extracts (dev tool).

For every extract: exact policy values, lifts, reference standard errors, and the distance of each candidate's lift
from the launch rule's boundary in reference SEs (lift / SE_ref - 1.96). Requirement: |distance| >= 3 for every
candidate, so a correct estimator's launch decision does not depend on sampling luck.

usage: fixture_audit.py CACHE_DIR OUT.json
"""
import json
import pickle
import sys
from pathlib import Path

REQUIRED = 3.0


def main(cache: Path, out: Path) -> int:
    report, ok = {}, True
    for name in ("visible", "hidden_a", "hidden_b", "hidden_c"):
        t = pickle.load(open(cache / name / "truth.pkl", "rb"))
        margins = {p: t["lifts"][p] / t["se_lift"][p] - 1.96 for p in ("v7", "v7_pd")}
        passed = all(abs(v) >= REQUIRED for v in margins.values())
        ok &= passed
        report[name] = {
            "values": {k: round(v, 5) for k, v in t["values"].items()},
            "lifts": {k: round(v, 5) for k, v in t["lifts"].items()},
            "se_ref": {k: round(v, 5) for k, v in t["se"].items()},
            "se_lift_ref": {k: round(v, 5) for k, v in t["se_lift"].items()},
            "boundary_distance_sd": {k: round(v, 2) for k, v in margins.items()},
            "launch": t["launch"],
            "n_decisions": t["n_decisions"],
            "n_exploration": t["n_exploration"],
            "margin_requirement_met": passed,
        }
        print(name, report[name]["launch"], report[name]["boundary_distance_sd"], "OK" if passed else "FAIL")
    out.write_text(json.dumps(report, indent=1) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
