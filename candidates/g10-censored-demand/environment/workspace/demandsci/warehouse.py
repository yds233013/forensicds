"""Warehouse access (read-only)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


def connect(db: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)


def trading_days(con: sqlite3.Connection) -> pd.DataFrame:
    """One row per store x SKU x date on which the store traded, with category, promotion flag, programme arm and
    period (pre / post LEAN-26 go-live)."""
    days = pd.read_sql_query(
        """
        SELECT i.store_id, i.sku_id, i.date, s.category, c.open_time, c.close_time, p.arm, p.go_live_date
        FROM inventory_daily i
        JOIN store_calendar c ON c.store_id = i.store_id AND c.date = i.date AND c.status = 'open'
        JOIN skus s ON s.sku_id = i.sku_id
        JOIN programme_assignment p ON p.store_id = i.store_id
        """, con)
    promos = pd.read_sql_query("SELECT sku_id, start_date, end_date FROM promotions", con)
    days["promo"] = False
    for r in promos.itertuples():
        m = (days["sku_id"] == r.sku_id) & (days["date"] >= r.start_date) & (days["date"] <= r.end_date)
        days.loc[m, "promo"] = True
    days["period"] = (days["date"] >= days["go_live_date"]).map({True: "post", False: "pre"})
    return days


def daily_sales(con: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT store_id, sku_id, date, SUM(units) AS units_sold FROM sales_hourly GROUP BY store_id, sku_id, date", con)


def stockout_days(con: sqlite3.Connection) -> pd.DataFrame:
    """Store x SKU x date with an out-of-stock event during trading hours, or no stock at opening."""
    return pd.read_sql_query(
        """
        SELECT DISTINCT i.store_id, i.sku_id, i.date
        FROM inventory_daily i
        JOIN store_calendar c ON c.store_id = i.store_id AND c.date = i.date AND c.status = 'open'
        LEFT JOIN availability_events e
          ON e.store_id = i.store_id AND e.sku_id = i.sku_id AND substr(e.event_time, 1, 10) = i.date
         AND e.event_type = 'out_of_stock'
         AND substr(e.event_time, 12, 5) >= c.open_time AND substr(e.event_time, 12, 5) < c.close_time
        WHERE i.on_hand_open = 0 OR e.event_time IS NOT NULL
        """, con)
