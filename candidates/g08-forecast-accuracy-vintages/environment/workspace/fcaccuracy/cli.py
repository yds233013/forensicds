"""Command line entry point: `python -m fcaccuracy build --as-of 2026-09-22T06:00:00Z`."""
from __future__ import annotations

import argparse
from pathlib import Path

from fcaccuracy import kpi, mart, outputs, warehouse


def build(db: Path, as_of: str, out: Path) -> None:
    con = warehouse.connect(db)
    try:
        closed = warehouse.closed_months(con, as_of)
        examples = mart.build_examples(con, closed)
        monthly = kpi.monthly_kpi(examples)
        h2h = kpi.head_to_head(examples, warehouse.models(con))
    finally:
        con.close()
    outputs.write_all(out, as_of, closed, examples, monthly, h2h)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="fcaccuracy")
    sub = ap.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="rebuild the accuracy mart outputs")
    b.add_argument("--as-of", required=True, help="UTC timestamp, e.g. 2026-09-22T06:00:00Z")
    b.add_argument("--db", default="data/warehouse.sqlite")
    b.add_argument("--out", default="out/accuracy")
    args = ap.parse_args(argv)
    build(Path(args.db), args.as_of, Path(args.out))
