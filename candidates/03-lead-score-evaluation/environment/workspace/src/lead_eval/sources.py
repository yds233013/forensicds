"""Readers for the RevOps warehouse extract (data/revops.db)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd

TS_COLS = {"created_at", "scored_at", "routed_at", "activity_at", "closed_won_at", "first_worked_at", "converted_at"}


def _read(con, sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, con)
    for c in df.columns:
        if c in TS_COLS:
            df[c] = pd.to_datetime(df[c])
    return df


@dataclass
class RevOps:
    leads: pd.DataFrame
    scores: pd.DataFrame
    routing_events: pd.DataFrame
    activities: pd.DataFrame
    conversions: pd.DataFrame
    lifecycle: pd.DataFrame


def load_revops(db_path) -> RevOps:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return RevOps(
            leads=_read(con, "SELECT lead_id, created_at, source, company_size, country, intake_status, campaign FROM leads"),
            scores=_read(con, "SELECT lead_id, model_version, scored_at, score FROM lead_scores"),
            routing_events=_read(con, "SELECT routing_event_id, lead_id, routed_at, policy, queue, router_version, threshold "
                                      "FROM routing_events"),
            activities=_read(con, "SELECT activity_id, lead_id, activity_at, activity_type, rep FROM sdr_activities"),
            conversions=_read(con, "SELECT opportunity_id, lead_id, closed_won_at, channel FROM conversions"),
            lifecycle=_read(con, "SELECT lead_id, created_at, current_queue, first_worked_at, qualified, converted_at, "
                                 "converted_60d, lifecycle_stage FROM lead_lifecycle"),
        )
    finally:
        con.close()
