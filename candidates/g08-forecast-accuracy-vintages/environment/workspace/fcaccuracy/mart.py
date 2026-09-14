"""Evaluation examples: one row per model, region, portfolio, delivery day and horizon."""
from __future__ import annotations

import sqlite3

import pandas as pd

from fcaccuracy import warehouse

KEY = ["model", "region", "portfolio", "target_date", "horizon"]


def build_examples(con: sqlite3.Connection, closed_months: list[str]) -> pd.DataFrame:
    df = warehouse.read_sql_file(con, "accuracy_examples.sql")
    df["kpi_month"] = df["run_date"].str.slice(0, 7)
    df = df[df["kpi_month"].isin(closed_months)].copy()
    df["actual_run_ids"] = df["actual_run_ids"].map(lambda s: ";".join(sorted(s.split(";"))))
    df["status"] = "scored"
    df["abs_error_mwh"] = (df["forecast_mwh"] - df["actual_mwh"]).abs()
    return df.sort_values(KEY).reset_index(drop=True)
