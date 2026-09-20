"""`python -m fleet_reliability analyse --warehouse data/warehouse.sqlite --out out`"""
from __future__ import annotations

import argparse
from pathlib import Path

from fleet_reliability import estimate, history, report


def analyse(warehouse: Path, out: Path) -> None:
    df = history.build(warehouse)
    h = report.HORIZON

    fail = estimate.outcome_rate(df, "UNPL_FAIL", h)
    ovhl = estimate.outcome_rate(df, "PM_OVHL", h)
    ret = estimate.outcome_rate(df, "ASSET_RET", h)

    payload = {
        "horizon_months": int(h),
        "installed_base_units": int(len(df)),
        "event_counts": {
            "UNPL_FAIL": int((df["wo_type"] == "UNPL_FAIL").sum()),
            "PM_OVHL": int((df["wo_type"] == "PM_OVHL").sum()),
            "ASSET_RET": int((df["wo_type"] == "ASSET_RET").sum()),
            "no_work_order": int((df["wo_type"] == "").sum()),
        },
        "units_at_risk": {str(a): estimate.at_risk(df, a) for a in (12, 24, 36)},
        "aftermarket": {
            "unplanned_failure_rate_36m": fail,
            "overhaul_rate_36m": ovhl,
            "retirement_rate_36m": ret,
            "still_original_assembly_36m": 1.0 - fail,
        },
        "engineering": {"assembly_failure_rate_36m": fail},
        "recommendation": "expanded" if fail > report.TRIGGER else "baseline",
    }
    report.write(out, payload)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="fleet_reliability")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("analyse", help="installed-base reliability run")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    analyse(Path(args.warehouse), Path(args.out))
