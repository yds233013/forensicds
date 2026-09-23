"""`python -m safety_rate rate --warehouse data/warehouse.sqlite --out out`"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from safety_rate import cases, exposure, report


def rate(warehouse: Path, out: Path) -> None:
    t = exposure.terms(warehouse)
    basis = float(t["rate_basis_hours"])
    limit = float(t["rate_limit"])
    lo, hi = exposure.window(warehouse)
    h = exposure.hours(warehouse)
    c = cases.recordable(warehouse)

    total_hours = round(2000.0 * h["worker_id"].nunique(), 2)
    n = int(len(c))
    company = round(basis * n / total_hours, 4) if total_hours else 0.0   # pooled, not a mean of sites

    hs = h.groupby("site_id")["hours"].sum()
    cs = c.groupby("site_id")["case_id"].count()
    rows = []
    for site, hh in hs.items():
        hh = round(float(hh), 2)
        if hh <= 0:
            continue
        k = int(cs.get(site, 0))
        rows.append({"site_id": site, "hours_worked": hh, "recordable_cases": k,
                     "rate": round(basis * k / hh, 4)})
    by_site = pd.DataFrame(rows).sort_values("site_id")

    readout = {
        "window_start": lo.date().isoformat(),
        "window_end": hi.date().isoformat(),
        "hours_worked": total_hours,
        "recordable_cases": n,
        "rate": company,
        "rate_by_site": {r["site_id"]: r["rate"] for r in rows},
        "access_decision": "suspend" if company > limit else "clear",
    }
    report.write(out, readout, by_site)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="safety_rate")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("rate", help="trailing-twelve-month recordable rate")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    rate(Path(a.warehouse), Path(a.out))
