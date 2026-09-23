"""Depot stock picture for the planning week, under the availability policy.

Available to promise = AVAILABLE stock, less units reserved by OPEN allocations. Quarantined and
consignment lots are not ours to plan with. A confirmed inbound receipt becomes usable
dock_to_stock_days after its ETA; a cancelled PO never arrives. Safety stock may serve the depot's own
jobs but may not be shipped out.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def frames(db: Path) -> dict:
    con = connect(db)
    try:
        f = {t: pd.read_sql_query(f"SELECT * FROM {t}", con) for t in
             ("depots", "parts", "stock_on_hand", "allocations", "inbound_orders", "service_jobs",
              "transfer_lanes", "safety_stock")}
        meta = pd.read_sql_query("SELECT key, value FROM extract_meta", con)
    finally:
        con.close()
    f["meta"] = dict(zip(meta["key"], meta["value"]))
    return f


def supply_pools(f: dict):
    """One pool per (depot, part) of on-hand ATP, plus one pool per usable inbound receipt."""
    t0 = pd.Timestamp(f["meta"]["extract_date"])
    dock = int(f["meta"]["dock_to_stock_days"])
    st = f["stock_on_hand"]
    avail = st[st["stock_status"] == "AVAILABLE"].groupby(["depot_id", "part_id"])["qty"].sum()
    al = f["allocations"]
    open_alloc = al[al["alloc_status"] == "OPEN"].groupby(["depot_id", "part_id"])["qty"].sum()
    atp = avail.subtract(open_alloc, fill_value=0).clip(lower=0)
    safety = f["safety_stock"].set_index(["depot_id", "part_id"])["min_units"]
    pools = []
    for (dep, part), q in atp.items():
        if q > 0:
            keep = int(safety.get((dep, part), 0))
            pools.append({"depot": dep, "part": part, "from": t0, "qty": int(q),
                          "ship_qty": max(0, int(q) - keep)})
    inb = f["inbound_orders"]
    inb = inb[inb["po_status"] == "CONFIRMED"].copy()
    inb["usable_from"] = pd.to_datetime(inb["eta_date"]) + pd.Timedelta(days=dock)
    for r in inb.itertuples():
        pools.append({"depot": r.depot_id, "part": r.part_id, "from": r.usable_from,
                      "qty": int(r.qty), "ship_qty": int(r.qty)})
    return pools


def jobs(f: dict):
    j = f["service_jobs"]
    j = j[j["job_status"] == "SCHEDULED"].copy()
    j["need_by"] = pd.to_datetime(j["need_by_date"])
    return j.sort_values(["need_by", "job_id"]).to_dict("records")
