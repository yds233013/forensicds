"""Load the dispatch experiment extract into plain Python structures."""
from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def blocks(db: Path):
    """One record per dispatch block, carrying the per-merchant rows for that block."""
    con = connect(db)
    try:
        assign = {r[0]: r for r in con.execute(
            "SELECT block_id, city_id, service_date, assigned_saturation FROM block_assignment")}
        prio = {}
        for bid, mid, flag in con.execute(
                "SELECT block_id, merchant_id, assigned_priority FROM merchant_assignment"):
            prio[(bid, mid)] = flag
        act = {}
        for bid, mid, flag in con.execute(
                "SELECT block_id, merchant_id, activated FROM priority_activation"):
            act[(bid, mid)] = flag
        rows = list(con.execute("SELECT block_id, merchant_id, orders_requested, orders_delivered "
                                "FROM merchant_day_orders"))
    finally:
        con.close()

    out = {}
    for bid, mid, req, deliv in rows:
        b = out.setdefault(bid, {"block_id": bid, "city_id": assign[bid][1],
                                 "service_date": assign[bid][2],
                                 "assigned_saturation": assign[bid][3], "rows": []})
        b["rows"].append({"merchant_id": mid, "orders_requested": req, "orders_delivered": deliv,
                          "assigned_priority": prio.get((bid, mid), 0),
                          "activated": act.get((bid, mid), 0)})
    return list(out.values())
