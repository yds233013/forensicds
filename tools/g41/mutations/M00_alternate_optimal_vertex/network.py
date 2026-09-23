"""Minimum unmet units, then minimum transfer cost, as a linear program.

Lexicographic objective by a big-M weight on unmet units: every plan that leaves one more job unit
uncovered costs more than any transfer plan could. The constraint matrix is a network matrix, so the
LP has an integral optimal vertex.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import linprog

BIG_M = 1_000_000.0


def solve(pools, jobs, lanes, t0):
    lane = {(r.from_depot, r.to_depot): (int(r.transit_days), float(r.cost_per_unit)) for r in lanes.itertuples()}
    arcs = []                                     # (pool index, job index, cost, is_transfer)
    for pi, p in enumerate(pools):
        for ji, j in enumerate(jobs):
            if p["part"] != j["part_id"]:
                continue
            if p["depot"] == j["depot_id"]:
                if p["from"] <= j["need_by"]:
                    arcs.append((pi, ji, 0.0, False))
            else:
                ln = lane.get((p["depot"], j["depot_id"]))
                if ln is None or p["ship_qty"] <= 0:
                    continue
                arrive = max(p["from"], t0) + pd.Timedelta(days=ln[0])
                if arrive <= j["need_by"]:
                    arcs.append((pi, ji, ln[1], True))
    arcs = arcs[::-1]
    n_arc, n_job = len(arcs), len(jobs)
    c = np.array([a[2] for a in arcs] + [BIG_M] * n_job)
    A_ub, b_ub = [], []
    for pi, p in enumerate(pools):                # pool capacity, and the shippable sub-capacity
        row = np.zeros(n_arc + n_job)
        for k, a in enumerate(arcs):
            if a[0] == pi:
                row[k] = 1
        A_ub.append(row); b_ub.append(p["qty"])
        if any(a[0] == pi and a[3] for a in arcs):
            row = np.zeros(n_arc + n_job)
            for k, a in enumerate(arcs):
                if a[0] == pi and a[3]:
                    row[k] = 1
            A_ub.append(row); b_ub.append(p["ship_qty"])
    A_eq = np.zeros((n_job, n_arc + n_job)); b_eq = np.zeros(n_job)
    for ji, j in enumerate(jobs):
        for k, a in enumerate(arcs):
            if a[1] == ji:
                A_eq[ji, k] = 1
        A_eq[ji, n_arc + ji] = 1
        b_eq[ji] = j["qty"]
    res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), A_eq=A_eq, b_eq=b_eq,
                  bounds=[(0, None)] * (n_arc + n_job), method="highs")
    x = np.round(res.x, 6)
    transfers, cost = {}, 0.0
    for k, a in enumerate(arcs):
        q = int(round(x[k]))
        if q > 0 and a[3]:
            key = (pools[a[0]]["depot"], jobs[a[1]]["depot_id"], pools[a[0]]["part"])
            transfers[key] = transfers.get(key, 0) + q
            cost += q * a[2]
    short_by_job = [int(round(v)) for v in x[n_arc:]]
    by_depot = {}
    for j, s in zip(jobs, short_by_job):
        if s:
            by_depot[j["depot_id"]] = by_depot.get(j["depot_id"], 0) + s
    plan = pd.DataFrame([{"from_depot": a, "to_depot": b, "part_id": p, "qty": q}
                         for (a, b, p), q in sorted(transfers.items())],
                        columns=["from_depot", "to_depot", "part_id", "qty"])
    return plan, round(cost, 2), int(sum(short_by_job)), by_depot
