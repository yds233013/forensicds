"""Exposure hours for the reporting window.

Hours come straight from the payroll export in shift_entries: the crews are paid for the time they
book, and the monthly payroll reconciliation ties to this total.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def terms(db: Path) -> dict:
    con = connect(db)
    try:
        t = pd.read_sql_query("SELECT key, value FROM contract_terms", con)
    finally:
        con.close()
    return dict(zip(t["key"], t["value"]))


def window(db: Path):
    t = terms(db)
    end = pd.Timestamp(t["reporting_window_end"])
    return end - pd.DateOffset(months=int(t["reporting_window_months"])), end


def hours(db: Path) -> pd.DataFrame:
    lo, hi = window(db)
    con = connect(db)
    try:
        df = pd.read_sql_query("SELECT worker_id, site_id, work_date, hours FROM shift_entries", con)
    finally:
        con.close()
    df["work_date"] = pd.to_datetime(df["work_date"])
    return df[(df["work_date"] >= lo) & (df["work_date"] < hi)]
