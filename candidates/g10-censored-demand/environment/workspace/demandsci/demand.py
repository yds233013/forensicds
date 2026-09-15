"""Demand history (release 2.3): one row per trading store x SKU x day.

Demand is taken from recorded sales. Days with a stockout are flagged so that baselines can be computed on clean
days (see RELEASES.md).
"""
from __future__ import annotations

import sqlite3

import pandas as pd

from demandsci import warehouse

KEY = ["store_id", "sku_id", "date"]


def build_history(con: sqlite3.Connection, days: pd.DataFrame) -> pd.DataFrame:
    sales = warehouse.daily_sales(con)
    hist = days.merge(sales, on=KEY, how="left")
    hist["units_sold"] = hist["units_sold"].fillna(0).astype(int)
    so = warehouse.stockout_days(con)
    so["stockout_day"] = True
    hist = hist.merge(so, on=KEY, how="left")
    hist["stockout_day"] = hist["stockout_day"].eq(True)
    hist["expected_demand"] = hist["units_sold"].astype(float)
    hist["lost_units"] = hist["expected_demand"] - hist["units_sold"]
    return hist.sort_values(KEY).reset_index(drop=True)
