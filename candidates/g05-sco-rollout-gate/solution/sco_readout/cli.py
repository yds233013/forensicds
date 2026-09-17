"""`python -m sco_readout gate --warehouse data/warehouse.sqlite --out out/`"""
from __future__ import annotations

import argparse
from pathlib import Path

from sco_readout import estimate, panel, report


def gate(warehouse: Path, out: Path) -> None:
    tables = panel.load(warehouse)
    p = panel.build(tables)
    report.write_all(out, p, estimate.estimate(p, tables))


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="sco_readout")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("gate", help="programme readout and continuation-gate figure")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    args = ap.parse_args(argv)
    gate(Path(args.warehouse), Path(args.out))


if __name__ == "__main__":
    main()
