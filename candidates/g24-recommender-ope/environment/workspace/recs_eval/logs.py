"""Reading the home-row logs."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

SLOTS = 5
SLOT_COLS = [f"slot_{k}" for k in range(1, SLOTS + 1)]


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def serves(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        f"SELECT serve_id, session_id, user_id, device, surface, served_at, stream, ab_arm, "
        f"{', '.join(SLOT_COLS)}, propensity, candidate_count FROM rec_serves", con)


def impressions(con: sqlite3.Connection) -> pd.DataFrame:
    """One row per served response and slot, with the click flag joined on (serve_id, position)."""
    s = serves(con)
    long = s.melt(id_vars=["serve_id", "session_id", "device", "served_at", "stream", "ab_arm", "propensity",
                           "candidate_count"],
                  value_vars=SLOT_COLS, var_name="slot", value_name="item_id")
    long["position"] = long["slot"].str.slice(5).astype(int)
    clicks = pd.read_sql_query("SELECT serve_id, position, 1 AS clicked FROM click_events", con)
    long = long.merge(clicks, on=["serve_id", "position"], how="left")
    long["clicked"] = long["clicked"].fillna(0).astype(int)
    return long.drop(columns=["slot"]).sort_values(["serve_id", "position"]).reset_index(drop=True)


def candidates(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT serve_id, item_id, score_v6, score_v7, score_v7_pd, filter_reason FROM rec_candidates", con)
