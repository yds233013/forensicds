"""Cover depot gaps from depot surpluses on the cheapest lanes."""
from __future__ import annotations

import pandas as pd


def rebalance(sup: pd.DataFrame, dem: pd.DataFrame, lanes: pd.DataFrame):
    net = dem.merge(sup, on=["depot_id", "part_id"], how="outer", suffixes=("_dem", "_sup")).fillna(0)
    net["gap"] = (net["units_dem"] - net["units_sup"]).clip(lower=0)
    net["surplus"] = (net["units_sup"] - net["units_dem"]).clip(lower=0)
    lane_cost = {(r.from_depot, r.to_depot): r.cost_per_unit for r in lanes.itertuples()}
    plan, cost = [], 0.0
    for part, g in net.groupby("part_id"):
        need = {r.depot_id: int(r.gap) for r in g.itertuples() if r.gap > 0}
        have = {r.depot_id: int(r.surplus) for r in g.itertuples() if r.surplus > 0}
        arcs = sorted(((lane_cost.get((s, d), 1e9), s, d) for s in have for d in need), key=lambda x: x[:3])
        for c, s, d in arcs:
            if have.get(s, 0) <= 0 or need.get(d, 0) <= 0 or c >= 1e9:
                continue
            q = min(have[s], need[d])
            have[s] -= q; need[d] -= q; cost += q * c
            plan.append({"from_depot": s, "to_depot": d, "part_id": part, "qty": int(q)})
        for d, r in need.items():
            if r:
                net.loc[(net["part_id"] == part) & (net["depot_id"] == d), "unmet"] = r
    net["unmet"] = net.get("unmet", pd.Series(0, index=net.index)).fillna(0).astype(int)
    return pd.DataFrame(plan, columns=["from_depot", "to_depot", "part_id", "qty"]), round(cost, 2), net
