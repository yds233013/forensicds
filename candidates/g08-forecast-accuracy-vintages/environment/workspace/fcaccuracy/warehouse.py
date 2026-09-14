"""Warehouse access (read-only)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def read_sql_file(con: sqlite3.Connection, name: str, **params) -> pd.DataFrame:
    return pd.read_sql_query((SQL_DIR / name).read_text(), con, params=params or None)


def closed_months(con: sqlite3.Connection, as_of: str) -> list[str]:
    """KPI months whose close is recorded at or before `as_of`."""
    log = pd.read_sql_query("SELECT kpi_month, closed_at FROM kpi_close_log", con)
    cutoff = pd.Timestamp(as_of)
    if cutoff.tzinfo is None:
        cutoff = cutoff.tz_localize("UTC")
    log["closed_at"] = pd.to_datetime(log["closed_at"], utc=True)
    return sorted(log.loc[log["closed_at"] <= cutoff, "kpi_month"])


def models(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query("SELECT * FROM models", con)
