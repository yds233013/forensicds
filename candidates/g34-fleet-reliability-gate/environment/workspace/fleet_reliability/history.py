"""Unit service histories from the warehouse extract."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

MONTH = 30.4375


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def build(db: Path) -> pd.DataFrame:
    con = connect(db)
    try:
        assets = pd.read_sql_query("SELECT unit_id, model_code, site_id, commissioned_on FROM asset_register", con)
        wos = pd.read_sql_query("SELECT unit_id, wo_date, wo_type FROM work_orders", con)
        meta = pd.read_sql_query("SELECT key, value FROM extract_meta", con)
    finally:
        con.close()

    cut = pd.Timestamp(meta.set_index("key").loc["extract_cut_off", "value"])
    df = assets.merge(wos, on="unit_id", how="left")
    df["commissioned_on"] = pd.to_datetime(df["commissioned_on"])
    df["wo_date"] = pd.to_datetime(df["wo_date"])
    df["age_at_cut_off"] = (cut - df["commissioned_on"]).dt.days / MONTH
    df["age_at_wo"] = (df["wo_date"] - df["commissioned_on"]).dt.days / MONTH
    df["exit_age"] = df["age_at_wo"].fillna(df["age_at_cut_off"])
    df["wo_type"] = df["wo_type"].fillna("")
    return df
