"""Readers for the product warehouse extract (data/product.db)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd

TS_COLS = {"created_at", "joined_at", "assigned_at", "exposed_at", "event_at"}


def _read(con, sql: str, params=()) -> pd.DataFrame:
    df = pd.read_sql_query(sql, con, params=params)
    for c in df.columns:
        if c in TS_COLS:
            df[c] = pd.to_datetime(df[c])
    return df


@dataclass
class Product:
    workspaces: pd.DataFrame
    memberships: pd.DataFrame
    assignments: pd.DataFrame
    exposures: pd.DataFrame
    events: pd.DataFrame


def load_product(db_path, experiment_id: str) -> Product:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return Product(
            workspaces=_read(con, "SELECT workspace_id, created_at, plan, signup_channel, size_band, region, is_internal "
                                  "FROM workspaces"),
            memberships=_read(con, "SELECT user_id, workspace_id, joined_at, role FROM memberships"),
            assignments=_read(con, "SELECT assignment_id, experiment_id, unit_type, unit_id, variant, stratum, assigned_at "
                                   "FROM xp_assignments WHERE experiment_id = ?", (experiment_id,)),
            exposures=_read(con, "SELECT exposure_id, experiment_id, user_id, workspace_id, variant, exposed_at "
                                 "FROM exposure_events WHERE experiment_id = ?", (experiment_id,)),
            events=_read(con, "SELECT event_id, user_id, workspace_id, event_type, event_at FROM product_events "
                              "WHERE event_type = 'core_action'"),
        )
    finally:
        con.close()
