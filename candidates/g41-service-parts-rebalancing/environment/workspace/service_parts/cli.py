"""`python -m service_parts plan --warehouse data/warehouse.sqlite --out out`"""
from __future__ import annotations

import argparse
from pathlib import Path

from service_parts import inventory, network, report


def plan(warehouse: Path, out: Path) -> None:
    f = inventory.frames(warehouse)
    sup, dem = inventory.supply(f), inventory.demand(f)
    transfers, cost, net = network.rebalance(sup, dem, f["transfer_lanes"])
    short = net.groupby("depot_id")["unmet"].sum()
    short = {k: int(v) for k, v in short.items() if v > 0}
    total = int(sum(short.values()))
    readout = {
        "extract_date": f["meta"]["extract_date"],
        "demand_units": int(dem["units"].sum()),
        "total_shortfall_units": total,
        "shortfall_by_depot": short,
        "transfer_units": int(transfers["qty"].sum()) if len(transfers) else 0,
        "transfer_cost": cost,
        "expedite_recommendation": "expedite" if total > report.SLA_SHORTFALL_LIMIT else "no_expedite",
    }
    report.write(out, transfers, readout)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="service_parts")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("plan", help="weekly rebalance plan")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    plan(Path(a.warehouse), Path(a.out))
