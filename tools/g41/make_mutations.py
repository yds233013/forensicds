"""Generate the G41 mutation suite.

Each mutation is the oracle solution with one defect applied by textual substitution, so the mutant
differs from the oracle only in the stated way. M00 is behaviour-preserving (a different optimal
vertex of the same LP) and must still score 1: the verifier grades the quantities and the plan's
executability, not the implementation or a particular tie-break. Every other mutation is a correct
optimisation over a wrong operational state, or a correct state with a plan that cannot be executed,
and must score 0 on at least one graded extract.
"""
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "candidates/g41-service-parts-rebalancing/solution/service_parts"
OUT = pathlib.Path(__file__).resolve().parent / "mutations"

INV = (SRC / "inventory.py").read_text()
NET = (SRC / "network.py").read_text()

# (id, file, old, new, expected reward)
EDITS = [
    ("M00_alternate_optimal_vertex", "network.py",
     "    n_arc, n_job = len(arcs), len(jobs)",
     "    arcs = arcs[::-1]\n    n_arc, n_job = len(arcs), len(jobs)", 1),
    ("M01_open_allocations_ignored", "inventory.py",
     'al[al["alloc_status"] == "OPEN"]', 'al[al["alloc_status"] == "__NONE__"]', 0),
    ("M02_quarantine_counted", "inventory.py",
     'st[st["stock_status"] == "AVAILABLE"]', 'st[st["stock_status"].isin(["AVAILABLE", "QUARANTINE"])]', 0),
    ("M03_consignment_counted", "inventory.py",
     'st[st["stock_status"] == "AVAILABLE"]', 'st[st["stock_status"].isin(["AVAILABLE", "CONSIGNMENT"])]', 0),
    ("M04_safety_stock_shippable", "inventory.py",
     'keep = int(safety.get((dep, part), 0))', 'keep = 0', 0),
    ("M05_cancelled_pos_counted", "inventory.py",
     'inb[inb["po_status"] == "CONFIRMED"]', 'inb[inb["po_status"].isin(["CONFIRMED", "CANCELLED"])]', 0),
    ("M06_dock_to_stock_ignored", "inventory.py",
     'dock = int(f["meta"]["dock_to_stock_days"])', 'dock = 0', 0),
    ("M07_inbound_usable_immediately", "inventory.py",
     'inb["usable_from"] = pd.to_datetime(inb["eta_date"]) + pd.Timedelta(days=dock)',
     'inb["usable_from"] = pd.Series([t0] * len(inb), index=inb.index)', 0),
    ("M08_transit_time_ignored", "network.py",
     'arrive = max(p["from"], t0) + pd.Timedelta(days=ln[0])', 'arrive = max(p["from"], t0)', 0),
    ("M09_no_transfers_local_only", "network.py",
     'if ln is None or p["ship_qty"] <= 0:', 'if True:', 0),
    ("M11_cancelled_jobs_in_demand", "inventory.py",
     'j = j[j["job_status"] == "SCHEDULED"].copy()',
     'j = j[j["job_status"].isin(["SCHEDULED", "CANCELLED"])].copy()', 0),
    ("M12_cheapest_shortfall_wrong_lanes", "network.py",
     'arcs.append((pi, ji, ln[1], True))', 'arcs.append((pi, ji, float(ln[0]), True))', 0),
    ("M13_plan_directions_reversed", "network.py",
     '    plan = pd.DataFrame([{"from_depot": a, "to_depot": b, "part_id": p, "qty": q}',
     '    plan = pd.DataFrame([{"from_depot": b, "to_depot": a, "part_id": p, "qty": q}', 0),
]

# M12 optimises on transit days but must still report what the plan actually costs.
M12_COST_FIX = ('            cost += q * a[2]',
                '            cost += q * lane[(pools[a[0]]["depot"], jobs[a[1]]["depot_id"])][1]')

# M10 replaces the network solve entirely: demand netted against network-wide supply, per part.
M10_NETWORK = '''"""Pooled netting: the network is treated as one warehouse per part."""
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
'''


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    expected = {}
    for mid, fname, old, new, reward in EDITS:
        d = OUT / mid
        d.mkdir(parents=True)
        text = {"inventory.py": INV, "network.py": NET}[fname]
        assert text.count(old) == 1, f"{mid}: anchor not unique in {fname}"
        text = text.replace(old, new)
        if mid.startswith("M12"):
            assert text.count(M12_COST_FIX[0]) == 1
            text = text.replace(*M12_COST_FIX)
        (d / fname).write_text(text)
        expected[mid] = reward
    d = OUT / "M10_pooled_network_netting"
    d.mkdir(parents=True)
    (d / "network.py").write_text(M10_NETWORK)
    expected["M10_pooled_network_netting"] = 0
    (OUT / "expected.txt").write_text("".join(f"{k} {v}\n" for k, v in sorted(expected.items())))
    print(f"wrote {len(expected)} mutations to {OUT}")


if __name__ == "__main__":
    main()
