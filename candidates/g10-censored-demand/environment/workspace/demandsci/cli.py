"""`python -m demandsci review --db data/warehouse.sqlite --out out/review`"""
from __future__ import annotations

import argparse
from pathlib import Path

from demandsci import demand, impact, outputs, trends, warehouse


def review(db: Path, out: Path) -> None:
    con = warehouse.connect(db)
    try:
        days = warehouse.trading_days(con)
        history = demand.build_history(con, days)
        cat_trends = trends.category_trends(history)
        prog = impact.programme_impact(con, history)
    finally:
        con.close()
    outputs.write_all(out, history, cat_trends, prog)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="demandsci")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("review", help="rebuild the demand review outputs")
    r.add_argument("--db", default="data/warehouse.sqlite")
    r.add_argument("--out", default="out/review")
    args = ap.parse_args(argv)
    review(Path(args.db), Path(args.out))
