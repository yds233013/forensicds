"""Recordable cases for the reporting window, as docs/recordable_case_standard.md defines them.

One row per injured person (no de-duplication by event), classification `RECORDABLE` only (first aid
and cases still under review do not count), placed in the window by the date the incident OCCURRED,
and attributed to the site where it happened.
"""
from __future__ import annotations

import pandas as pd

from safety_rate.exposure import connect, window


def recordable(db) -> pd.DataFrame:
    lo, hi = window(db)
    con = connect(db)
    try:
        df = pd.read_sql_query(
            "SELECT case_id, event_id, worker_id, site_id, occurred_on, recorded_on, classification "
            "FROM incident_cases", con)
    finally:
        con.close()
    df["recorded_on"] = pd.to_datetime(df["recorded_on"])
    df = df[(df["recorded_on"] >= lo) & (df["recorded_on"] < hi)]
    return df[df["classification"] == "RECORDABLE"]
