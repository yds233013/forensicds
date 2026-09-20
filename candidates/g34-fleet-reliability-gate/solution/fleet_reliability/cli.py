"""`python -m fleet_reliability analyse --warehouse data/warehouse.sqlite --out out`"""
from __future__ import annotations

import argparse
from pathlib import Path

from fleet_reliability import estimate, history, report


def analyse(warehouse: Path, out: Path) -> None:
    df = history.build(warehouse)
    h = report.HORIZON

    shares = estimate.outcome_shares(df, h)
    fail_rate = shares["UNPL_FAIL"]

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
            "unplanned_failure_rate_36m": fail_rate,
            "overhaul_rate_36m": shares["PM_OVHL"],
            "retirement_rate_36m": shares["ASSET_RET"],
            "still_original_assembly_36m": shares["still_original"],
        },
        "engineering": {"assembly_failure_rate_36m": estimate.assembly_life_failure_rate(df, h)},
        "recommendation": "expanded" if fail_rate > report.TRIGGER else "baseline",
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
