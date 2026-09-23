"""Deterministic generator for the Northwind Field Service spare-parts warehouse (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/warehouse.sqlite

The same module builds the hidden extracts and the exact truth for the verifier. Design draws
(stock, demand, timing) and presentation draws (row order, identifiers) use separate streams.

Operational state that decides what is actually available for next week's jobs:
  * stock rows carry a status: AVAILABLE, QUARANTINE (QA hold) or CONSIGNMENT (customer-owned);
  * open allocations reserve stock for work orders already in flight;
  * a depot must retain its contractual safety stock, which may serve its own jobs but may not be shipped;
  * a confirmed purchase order is usable only once received and put away (dock-to-stock);
  * a transfer can only serve a job if the lane's transit time still lands before the job's need-by date.
"""
from __future__ import annotations

import copy
import hashlib
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

DEPOTS = ("NW-ANCHOR", "NW-BRIDGE", "NW-CEDAR", "NW-DELTA", "NW-ELM", "NW-FORGE", "NW-GRANITE", "NW-HARROW")
REGIONS = ("NORTH", "NORTH", "CENTRAL", "CENTRAL", "CENTRAL", "SOUTH", "SOUTH", "SOUTH")
PARTS = ("PMP-SEAL-12", "PMP-BRG-40", "CTRL-BRD-7", "VLV-ACT-3", "HTR-ELEM-9")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 8143207,
    "extract_date": "2026-09-18",          # Friday; the plan covers the following week
    "horizon_days": 7,
    "dock_to_stock_days": 1,               # policy: receipt is usable one day after ETA
    "n_jobs": 230,
    "job_qty": (1, 5),
    "quarantine_share": 0.12,              # share of stock rows on QA hold
    "consignment_share": 0.08,
    "alloc_share": 0.45,                   # share of available units reserved by open work orders
    "cancelled_alloc_share": 0.25,         # of allocation rows, the share already cancelled (not reserving)
    "inbound_per_depot": (1, 3),
    "inbound_late_share": 0.45,            # share of inbound POs that land too late to help
    "cancelled_po_share": 0.20,
    "transit_days": (1, 4),
    "safety_stock": (2, 8),
    "stock_units": (3, 16),
    "cost_per_unit": (9.0, 26.0),
    "sla_shortfall_limit": 40,             # service contract: expedite if the week's shortfall exceeds this
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def build(spec: dict) -> dict:
    d = _rng(spec["seed"], "design")
    t0 = date.fromisoformat(spec["extract_date"])
    depots = list(DEPOTS)

    lanes = {}
    for i, a in enumerate(depots):
        for j, b in enumerate(depots):
            if a == b:
                continue
            same = REGIONS[i] == REGIONS[j]
            lo, hi = spec["transit_days"]
            tr = d.randint(lo, max(lo, hi - 2)) if same else d.randint(lo + 1, hi)
            lanes[(a, b)] = {"transit_days": tr, "cost_per_unit": round(d.uniform(*spec["cost_per_unit"]) * (1.0 if same else 1.4), 2)}

    stock, allocations, inbound, safety = [], [], [], {}
    for dep in depots:
        for p in PARTS:
            safety[(dep, p)] = d.randint(*spec["safety_stock"])
            n_lots = d.randint(1, 3)
            for _ in range(n_lots):
                q = d.randint(*spec["stock_units"])
                u = d.random()
                status = "QUARANTINE" if u < spec["quarantine_share"] else ("CONSIGNMENT" if u < spec["quarantine_share"] + spec["consignment_share"] else "AVAILABLE")
                stock.append({"depot": dep, "part": p, "qty": q, "status": status})
            avail = sum(s["qty"] for s in stock if s["depot"] == dep and s["part"] == p and s["status"] == "AVAILABLE")
            if avail > 0 and d.random() < 0.8:
                res = int(avail * spec["alloc_share"] * d.uniform(0.5, 1.5))
                res = max(0, min(res, avail))
                if res:
                    allocations.append({"depot": dep, "part": p, "qty": res, "status": "OPEN"})
                if d.random() < spec["cancelled_alloc_share"]:
                    allocations.append({"depot": dep, "part": p, "qty": d.randint(1, 6), "status": "CANCELLED"})
            for _ in range(d.randint(*spec["inbound_per_depot"])):
                late = d.random() < spec["inbound_late_share"]
                eta = t0 + timedelta(days=d.randint(spec["horizon_days"] + 1, spec["horizon_days"] + 6) if late else d.randint(1, spec["horizon_days"] - 2))
                inbound.append({"depot": dep, "part": p, "qty": d.randint(4, 20), "eta": eta,
                                "status": "CANCELLED" if d.random() < spec["cancelled_po_share"] else "CONFIRMED"})

    jobs = []
    for k in range(spec["n_jobs"]):
        dep = d.choice(depots); p = d.choice(PARTS)
        need = t0 + timedelta(days=d.randint(1, spec["horizon_days"]))
        jobs.append({"job": f"WO-{100000 + k}", "depot": dep, "part": p, "qty": d.randint(*spec["job_qty"]),
                     "need_by": need, "status": "CANCELLED" if d.random() < 0.06 else "SCHEDULED"})

    return {"spec": spec, "t0": t0, "depots": depots, "lanes": lanes, "stock": stock,
            "allocations": allocations, "inbound": inbound, "jobs": jobs, "safety": safety}


# ------------------------------------------------------------------ the operational state, then the optimum
def state(w: dict) -> dict:
    """Available-to-promise by depot and part, split into shippable and retained (safety stock)."""
    spec, t0 = w["spec"], w["t0"]
    onhand = {}
    for s in w["stock"]:
        if s["status"] == "AVAILABLE":
            onhand[(s["depot"], s["part"])] = onhand.get((s["depot"], s["part"]), 0) + s["qty"]
    for a in w["allocations"]:
        if a["status"] == "OPEN":
            k = (a["depot"], a["part"])
            onhand[k] = onhand.get(k, 0) - a["qty"]
    atp = {k: max(0, v) for k, v in onhand.items()}
    ship = {k: max(0, v - w["safety"].get(k, 0)) for k, v in atp.items()}
    inb = []
    for p in w["inbound"]:
        if p["status"] == "CONFIRMED":
            inb.append({"depot": p["depot"], "part": p["part"], "qty": p["qty"],
                        "usable_from": p["eta"] + timedelta(days=spec["dock_to_stock_days"])})
    jobs = [j for j in w["jobs"] if j["status"] == "SCHEDULED"]
    return {"atp": atp, "shippable": ship, "inbound": inb, "jobs": jobs}


def optimum(w: dict) -> dict:
    """Minimum unmet units over the week, then minimum transfer cost among the plans achieving it.

    Min-cost maximum flow (successive shortest paths with SPFA on residual costs). Integral optimum:
    all capacities are integers and the network matrix is totally unimodular.

      SRC -> supply(qty)            each on-hand ATP pool and each usable inbound receipt
      supply -> job                 same depot, if the units are usable by the job's need-by date
      supply -> shippable(ship_qty) safety stock may serve the depot's own jobs but may not be shipped
      shippable -> job              other depot, if lane transit still lands before need-by; cost = lane cost
      job -> SNK(qty)
    """
    st = state(w); t0 = w["t0"]; lanes = w["lanes"]
    sup = []
    for (dep, part), q in sorted(st["atp"].items()):
        if q:
            sup.append({"depot": dep, "part": part, "from": t0, "qty": q, "ship_qty": st["shippable"].get((dep, part), 0)})
    for r in sorted(st["inbound"], key=lambda x: (x["depot"], x["part"], x["usable_from"])):
        sup.append({"depot": r["depot"], "part": r["part"], "from": r["usable_from"], "qty": r["qty"], "ship_qty": r["qty"]})
    dem = sorted(st["jobs"], key=lambda j: (j["need_by"], j["job"]))

    n_s, n_d = len(sup), len(dem)
    SRC, SNK = 0, 1 + n_s + n_s + n_d
    sup_node = lambda i: 1 + i
    ship_node = lambda i: 1 + n_s + i
    job_node = lambda j: 1 + 2 * n_s + j
    N = SNK + 1
    graph = [[] for _ in range(N)]

    def add(u, v, cap, cost):
        graph[u].append([v, cap, cost, len(graph[v])])
        graph[v].append([u, 0, -cost, len(graph[u]) - 1])

    for i, s in enumerate(sup):
        add(SRC, sup_node(i), s["qty"], 0.0)
        if s["ship_qty"] > 0:
            add(sup_node(i), ship_node(i), s["ship_qty"], 0.0)
    for j, jb in enumerate(dem):
        add(job_node(j), SNK, jb["qty"], 0.0)
    for i, s in enumerate(sup):
        for j, jb in enumerate(dem):
            if s["part"] != jb["part"]:
                continue
            if s["depot"] == jb["depot"]:
                if s["from"] <= jb["need_by"]:
                    add(sup_node(i), job_node(j), 10 ** 6, 0.0)
            else:
                ln = lanes.get((s["depot"], jb["depot"]))
                if ln is None or s["ship_qty"] <= 0:
                    continue
                if max(s["from"], t0) + timedelta(days=ln["transit_days"]) <= jb["need_by"]:
                    add(ship_node(i), job_node(j), 10 ** 6, float(ln["cost_per_unit"]))

    flow, cost = 0, 0.0
    INF = float("inf")
    while True:                                    # successive shortest path (SPFA; costs are non-negative)
        dist = [INF] * N; inq = [False] * N; prevv = [-1] * N; preve = [-1] * N
        dist[SRC] = 0.0; queue = [SRC]; inq[SRC] = True
        while queue:
            u = queue.pop(0); inq[u] = False
            for ei, e in enumerate(graph[u]):
                v, cap, c, _ = e
                if cap > 0 and dist[u] + c < dist[v] - 1e-12:
                    dist[v] = dist[u] + c; prevv[v] = u; preve[v] = ei
                    if not inq[v]:
                        queue.append(v); inq[v] = True
        if dist[SNK] == INF:
            break
        f = INF; v = SNK
        while v != SRC:
            f = min(f, graph[prevv[v]][preve[v]][1]); v = prevv[v]
        v = SNK
        while v != SRC:
            e = graph[prevv[v]][preve[v]]
            e[1] -= f; graph[v][e[3]][1] += f; v = prevv[v]
        flow += f; cost += f * dist[SNK]

    delivered_by_job = [0] * n_d
    transfers = {}
    for i, s in enumerate(sup):
        for e in graph[ship_node(i)]:
            v, cap, c, rev = e
            if 1 + 2 * n_s <= v < 1 + 2 * n_s + n_d:
                sent = graph[v][rev][1]
                if sent > 0:
                    k = (s["depot"], dem[v - (1 + 2 * n_s)]["depot"], s["part"])
                    transfers[k] = transfers.get(k, 0) + sent
                    delivered_by_job[v - (1 + 2 * n_s)] += sent
        for e in graph[sup_node(i)]:
            v, cap, c, rev = e
            if 1 + 2 * n_s <= v < 1 + 2 * n_s + n_d:
                delivered_by_job[v - (1 + 2 * n_s)] += graph[v][rev][1]

    short = sum(jb["qty"] for jb in dem) - flow
    by_depot = {}
    for j, jb in enumerate(dem):
        miss = jb["qty"] - delivered_by_job[j]
        if miss:
            by_depot[jb["depot"]] = by_depot.get(jb["depot"], 0) + miss
    return {"shortfall": int(short), "shortfall_by_depot": by_depot, "transfer_units": int(sum(transfers.values())),
            "transfer_cost": round(cost, 2),
            "transfers": [{"from": k[0], "to": k[1], "part": k[2], "qty": v} for k, v in sorted(transfers.items())],
            "decision": "expedite" if short > w["spec"]["sla_shortfall_limit"] else "no_expedite",
            "demand_units": int(sum(jb["qty"] for jb in dem))}


def truth(w: dict) -> dict:
    return optimum(w)


def write_sqlite(w: dict, out_dir: str) -> str:
    spec = w["spec"]; p = _rng(spec["seed"], "presentation")
    data_dir = os.path.join(out_dir, "data"); os.makedirs(data_dir, exist_ok=True)
    db = os.path.join(data_dir, "warehouse.sqlite")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db); c = con.cursor()
    c.execute("CREATE TABLE depots (depot_id TEXT PRIMARY KEY, region TEXT)")
    c.execute("CREATE TABLE parts (part_id TEXT PRIMARY KEY, description TEXT)")
    c.execute("CREATE TABLE stock_on_hand (lot_id TEXT PRIMARY KEY, depot_id TEXT, part_id TEXT, qty INTEGER, stock_status TEXT)")
    c.execute("CREATE TABLE allocations (alloc_id TEXT PRIMARY KEY, depot_id TEXT, part_id TEXT, qty INTEGER, work_order_id TEXT, alloc_status TEXT)")
    c.execute("CREATE TABLE inbound_orders (po_id TEXT PRIMARY KEY, depot_id TEXT, part_id TEXT, qty INTEGER, eta_date TEXT, po_status TEXT)")
    c.execute("CREATE TABLE service_jobs (job_id TEXT PRIMARY KEY, depot_id TEXT, part_id TEXT, qty INTEGER, need_by_date TEXT, job_status TEXT)")
    c.execute("CREATE TABLE transfer_lanes (from_depot TEXT, to_depot TEXT, transit_days INTEGER, cost_per_unit REAL)")
    c.execute("CREATE TABLE safety_stock (depot_id TEXT, part_id TEXT, min_units INTEGER)")
    c.execute("CREATE TABLE extract_meta (key TEXT, value TEXT)")

    labels = list(range(200000, 200000 + 6000)); p.shuffle(labels); it = iter(labels)
    dep_rows = [(d, REGIONS[i]) for i, d in enumerate(w["depots"])]
    part_rows = [(x, f"{x} service part") for x in PARTS]
    stock_rows = [(f"LOT-{next(it)}", s["depot"], s["part"], s["qty"], s["status"]) for s in w["stock"]]
    alloc_rows = [(f"ALC-{next(it)}", a["depot"], a["part"], a["qty"], f"WO-{next(it)}", a["status"]) for a in w["allocations"]]
    po_rows = [(f"PO-{next(it)}", b["depot"], b["part"], b["qty"], b["eta"].isoformat(), b["status"]) for b in w["inbound"]]
    job_rows = [(j["job"], j["depot"], j["part"], j["qty"], j["need_by"].isoformat(), j["status"]) for j in w["jobs"]]
    lane_rows = [(a, b, v["transit_days"], v["cost_per_unit"]) for (a, b), v in w["lanes"].items()]
    safe_rows = [(k[0], k[1], v) for k, v in w["safety"].items()]
    for rows in (stock_rows, alloc_rows, po_rows, job_rows, lane_rows, safe_rows):
        p.shuffle(rows)
    c.executemany("INSERT INTO depots VALUES (?,?)", dep_rows)
    c.executemany("INSERT INTO parts VALUES (?,?)", part_rows)
    c.executemany("INSERT INTO stock_on_hand VALUES (?,?,?,?,?)", stock_rows)
    c.executemany("INSERT INTO allocations VALUES (?,?,?,?,?,?)", alloc_rows)
    c.executemany("INSERT INTO inbound_orders VALUES (?,?,?,?,?,?)", po_rows)
    c.executemany("INSERT INTO service_jobs VALUES (?,?,?,?,?,?)", job_rows)
    c.executemany("INSERT INTO transfer_lanes VALUES (?,?,?,?)", lane_rows)
    c.executemany("INSERT INTO safety_stock VALUES (?,?,?)", safe_rows)
    c.executemany("INSERT INTO extract_meta VALUES (?,?)", [
        ("extract_date", w["t0"].isoformat()),
        ("planning_horizon_days", str(spec["horizon_days"])),
        ("dock_to_stock_days", str(spec["dock_to_stock_days"])),
        ("stock_status_values", "AVAILABLE | QUARANTINE (QA hold) | CONSIGNMENT (customer-owned)"),
        ("alloc_status_values", "OPEN (reserves stock) | CANCELLED (does not reserve)"),
        ("po_status_values", "CONFIRMED | CANCELLED"),
        ("job_status_values", "SCHEDULED | CANCELLED"),
    ])
    con.commit(); con.close()
    return db


def db_digest(db_path: str) -> str:
    con = sqlite3.connect(db_path); h = hashlib.sha256()
    for t in ("depots", "parts", "stock_on_hand", "allocations", "inbound_orders", "service_jobs", "transfer_lanes", "safety_stock", "extract_meta"):
        for row in con.execute("SELECT * FROM %s ORDER BY 1,2" % t):
            h.update(repr(row).encode())
    con.close(); return h.hexdigest()[:16]


def main(argv):
    out = argv[1]
    spec = copy.deepcopy(VISIBLE_SPEC)
    if len(argv) > 2 and argv[2] != "visible":
        import scenarios
        spec = scenarios.by_name(argv[2])
    w = build(spec); db = write_sqlite(w, out)
    sys.stderr.write("wrote %s  digest=%s\n" % (db, db_digest(db)))


if __name__ == "__main__":
    main(sys.argv)
