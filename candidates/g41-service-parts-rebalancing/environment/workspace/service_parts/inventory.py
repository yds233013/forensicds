"""Depot stock picture for the planning week.

House method since the 2024 planner rewrite: take what the depots are holding and add what is on its
way during the week, then subtract the week's scheduled demand.
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


def supply(f: dict) -> pd.DataFrame:
    """Units the planner counts as usable this week, by depot and part."""
    t0 = pd.Timestamp(f["meta"]["extract_date"])
    horizon = int(f["meta"]["planning_horizon_days"])
    on_hand = f["stock_on_hand"].groupby(["depot_id", "part_id"], as_index=False)["qty"].sum()
    inb = f["inbound_orders"].copy()
    inb["eta_date"] = pd.to_datetime(inb["eta_date"])
    inb = inb[inb["eta_date"] <= t0 + pd.Timedelta(days=horizon)]
    inb = inb.groupby(["depot_id", "part_id"], as_index=False)["qty"].sum()
    s = pd.concat([on_hand, inb]).groupby(["depot_id", "part_id"], as_index=False)["qty"].sum()
    return s.rename(columns={"qty": "units"})


def demand(f: dict) -> pd.DataFrame:
    jobs = f["service_jobs"]
    jobs = jobs[jobs["job_status"] == "SCHEDULED"]
    return jobs.groupby(["depot_id", "part_id"], as_index=False)["qty"].sum().rename(columns={"qty": "units"})
