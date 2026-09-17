"""Store x week analysis panel: actual go-live, comparable trading weeks, log net sales."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def load(db: Path) -> dict:
    con = connect(db)
    try:
        q = lambda s: pd.read_sql_query(s, con)
        kpi = q("SELECT store_id, week_start, net_sales, customer_txns FROM kpi_store_week")
        stores = q("SELECT store_id, format FROM stores")
        plan = q("SELECT store_id, wave, planned_kit FROM rollout_plan")
        go = q("SELECT store_id, event_date AS go_live_week, kit FROM install_log WHERE event = 'go_live'")
        clo = q("SELECT store_id, closure_date FROM store_closures")
    finally:
        con.close()
    return dict(kpi=kpi, stores=stores, plan=plan, go=go, closures=clo)


def build(tables: dict) -> pd.DataFrame:
    p = tables["kpi"].merge(tables["plan"][["store_id", "wave"]], on="store_id", how="left")
    p = p.merge(tables["go"][["store_id", "go_live_week"]], on="store_id", how="left")
    ws = pd.to_datetime(p["week_start"])
    ev = (ws - pd.to_datetime(p["go_live_week"])).dt.days // 7
    p["event_week"] = ev.astype("Int64")
    # a comparable trading week has no closure record on any of its seven days (KPI handbook)
    c = tables["closures"].copy()
    cd = pd.to_datetime(c["closure_date"])
    c["week_start"] = (cd - pd.to_timedelta(cd.dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
    closed = set(zip(c["store_id"], c["week_start"]))
    p["comparable"] = [0 if k in closed else 1 for k in zip(p["store_id"], p["week_start"])]
    p["log_net_sales"] = np.log(p["net_sales"])
    return p.sort_values(["store_id", "week_start"]).reset_index(drop=True)
