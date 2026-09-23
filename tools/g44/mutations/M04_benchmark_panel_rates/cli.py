"""`python -m screen_perf report --warehouse data/warehouse.sqlite --out out`"""
from __future__ import annotations

import argparse
from pathlib import Path

from screen_perf import labels, metrics, report


def run(warehouse: Path, out: Path) -> None:
    t = labels.terms(warehouse)
    floor = float(t["precision_floor"])
    merchant_rate = float(t["merchant_fraud_rate"])

    txn = labels.transactions(warehouse)
    rev = labels.sample_reviews(warehouse)
    pan = labels.panel(warehouse).rename(columns={'label': 'outcome'})
    pan['weight'] = 1.0
    c = metrics.weighted_confusion(pan)
    se, sp = metrics.rates(c)
    contract = metrics.precision_at_rate(se, sp, merchant_rate)

    payload = {
        "window_start": t["window_start"],
        "window_end": t["window_end"],
        "flagged_transactions": int((txn["screen_decision"] == "FLAG").sum()),
        "adjudicated_sample_reviews": int(len(rev)),
        "sensitivity": round(se, 6),
        "specificity": round(sp, 6),
        "observed_precision": round(metrics.precision(c), 6),
        "contract_precision": round(contract, 6),
        "decision": "remediate" if contract < floor else "accept",
    }
    report.write(out, payload)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="screen_perf")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("report", help="quarterly performance certificate")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    run(Path(a.warehouse), Path(a.out))
