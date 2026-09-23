"""Pooled netting: the network is treated as one warehouse per part."""
from __future__ import annotations

import pandas as pd


def solve(pools, jobs, lanes, t0):
    parts = {j["part_id"] for j in jobs}
    short = 0
    for part in parts:
        dem = sum(j["qty"] for j in jobs if j["part_id"] == part)
        sup = sum(p["qty"] for p in pools if p["part"] == part)
        short += max(0, dem - sup)
    by_depot = {}
    if short:
        dep = sorted({j["depot_id"] for j in jobs})[0]
        by_depot[dep] = short
    plan = pd.DataFrame([], columns=["from_depot", "to_depot", "part_id", "qty"])
    return plan, 0.0, int(short), by_depot
