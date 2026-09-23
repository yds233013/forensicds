"""Review evidence for the quarter, as the review-queue SOP defines it.

The quality programme's evidence is the flagged cases (every one reviewed) together with the systematic
one-in-N sample of passed transactions. Ad-hoc cases arrive because something already went wrong and
belong to no sampling design, so they are not evidence about what the screen passes. A case that is
still PENDING has no adjudication.

Each case carries the weight its selection implies: 1 for a flagged case, N for a sampled pass.
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


def transactions(db: Path) -> pd.DataFrame:
    con = connect(db)
    try:
        return pd.read_sql_query("SELECT txn_id, authorized_at, screen_decision FROM transactions", con)
    finally:
        con.close()


def sample_reviews(db: Path) -> pd.DataFrame:
    n = 10
    con = connect(db)
    try:
        df = pd.read_sql_query(
            "SELECT r.review_id, r.txn_id, r.review_source, r.outcome, t.screen_decision "
            "FROM reviews r JOIN transactions t ON t.txn_id = r.txn_id", con)
    finally:
        con.close()
    df = df[df["review_source"].isin(["QUEUE_FLAGGED", "QUALITY_SAMPLE"])]
    df = df[df["outcome"] != "PENDING"].copy()
    df["weight"] = df["review_source"].map({"QUEUE_FLAGGED": 1.0, "QUALITY_SAMPLE": float(n)})
    return df


def panel(db: Path) -> pd.DataFrame:
    con = connect(db)
    try:
        return pd.read_sql_query("SELECT case_id, label, screen_decision FROM benchmark_panel", con)
    finally:
        con.close()
