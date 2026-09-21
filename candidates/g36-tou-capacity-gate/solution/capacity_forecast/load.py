"""Load the utility extract into tidy frames."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

PILOT_YEAR = 2026


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def frames(db: Path):
    con = connect(db)
    try:
        cm = pd.read_sql_query("SELECT household_id, segment_code FROM customer_master", con)
        wx = pd.read_sql_query("SELECT service_date, cooling_degree_days FROM weather_daily", con)
        ld = pd.read_sql_query(
            "SELECT household_id, service_date, peak_kw FROM peak_window_load", con)
        en = pd.read_sql_query(
            "SELECT household_id, assigned_arm FROM tou_pilot_enrolment", con)
        fc = pd.read_sql_query(
            "SELECT service_date, cooling_degree_days_forecast FROM weather_forecast_2027", con)
    finally:
        con.close()

    ld["year"] = ld["service_date"].str.slice(0, 4).astype(int)
    df = ld.merge(wx, on="service_date", how="left").merge(cm, on="household_id", how="left")
    df = df.merge(en, on="household_id", how="left")
    df["assigned_arm"] = df["assigned_arm"].fillna("not_enrolled")
    # a household is ON the tariff only in the pilot season and only in the treatment arm
    df["on_tariff"] = (df["year"] == PILOT_YEAR) & (df["assigned_arm"] == "treatment")
    return dict(loads=df, customers=cm, weather=wx, enrolment=en, forecast=fc)
