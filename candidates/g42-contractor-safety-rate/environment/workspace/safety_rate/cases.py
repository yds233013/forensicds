"""Incidents for the reporting window.

The HSE log is the system of record. One row is opened per injured person, so the log is collapsed to
one row per incident event before counting - the monthly HSE pack reports incidents, not rows - and
the window is taken on the date the incident went into the log.
"""
from __future__ import annotations

import pandas as pd

from safety_rate.exposure import connect, window


def incidents(db) -> pd.DataFrame:
    lo, hi = window(db)
    con = connect(db)
    try:
        df = pd.read_sql_query(
            "SELECT case_id, event_id, worker_id, site_id, occurred_on, recorded_on, classification "
            "FROM incident_cases", con)
        wk = pd.read_sql_query("SELECT worker_id, home_site_id FROM workers", con)
    finally:
        con.close()
    df["recorded_on"] = pd.to_datetime(df["recorded_on"])
    df = df[(df["recorded_on"] >= lo) & (df["recorded_on"] < hi)]
    df = df[df["classification"] == "RECORDABLE"]
    df = df.merge(wk, on="worker_id", how="left")
    df["site_id"] = df["home_site_id"].fillna(df["site_id"])
    return df.drop_duplicates(subset=["event_id"])
