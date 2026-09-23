"""Review outcomes for the quarter.

Every review case in the window with an adjudication is evidence about the screen; the queue is the
system of record for what reviewers found.
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


def adjudicated(db: Path) -> pd.DataFrame:
    """Reviews joined to the transaction they cover, adjudications only."""
    con = connect(db)
    try:
        df = pd.read_sql_query(
            "SELECT r.review_id, r.txn_id, r.review_source, r.outcome, t.screen_decision, t.authorized_at "
            "FROM reviews r JOIN transactions t ON t.txn_id = r.txn_id", con)
    finally:
        con.close()
    return df[df["outcome"] != "PENDING"]


def panel(db: Path) -> pd.DataFrame:
    con = connect(db)
    try:
        return pd.read_sql_query("SELECT case_id, label, screen_decision FROM benchmark_panel", con)
    finally:
        con.close()
