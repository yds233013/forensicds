"""Store x week analysis panel from the warehouse."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def build(db: Path) -> pd.DataFrame:
    con = connect(db)
    try:
        kpi = pd.read_sql_query("SELECT store_id, week_start, net_sales, customer_txns FROM kpi_store_week", con)
        plan = pd.read_sql_query("SELECT store_id, wave, planned_go_live FROM rollout_plan", con)
    finally:
        con.close()
    p = kpi.merge(plan, on="store_id", how="left")
    last_week = p["week_start"].max()
    live = p["planned_go_live"] <= last_week
    p["go_live_week"] = p["planned_go_live"].where(live)
    weeks = (pd.to_datetime(p["week_start"]) - pd.to_datetime(p["go_live_week"])).dt.days // 7
    p["event_week"] = weeks.astype("Int64")
    p["comparable"] = (p["customer_txns"] > 0).astype(int)
    p["log_net_sales"] = np.log(p["net_sales"])
    p["log_basket"] = np.log(p["net_sales"] / p["customer_txns"])
    p["treated"] = (p["event_week"].fillna(-1) >= 0).astype(int)
    return p.sort_values(["store_id", "week_start"]).reset_index(drop=True)
