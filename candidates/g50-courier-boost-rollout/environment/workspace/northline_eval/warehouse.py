"""Warehouse loaders. Metric population and market attribution follow docs/metric_definitions.md."""
import sqlite3
import pandas as pd

WEEK_ORIGIN = "2026-04-06"


def connect(db):
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    return con


def orders(con):
    """Delivered orders with market attribution, week_start and the phase-2 arm where one exists."""
    df = pd.read_sql_query(
        """
        SELECT o.order_id, o.zone_id, z.market_id, o.placed_at, o.order_channel,
               o.promised_minutes, o.accepted_after_sec, o.delivered_after_min, o.status, a.arm
          FROM orders o
          JOIN zones z ON z.zone_id = o.zone_id
          LEFT JOIN experiment_assignment a ON a.order_id = o.order_id
        """,
        con,
    )
    df["placed_at"] = pd.to_datetime(df["placed_at"])
    df = df[df["status"] == "delivered"].copy()
    df = df[df["order_channel"] == "standard"].copy()   # programme metric population
    df["is_late"] = (df["delivered_after_min"] > df["promised_minutes"]).astype(int)
    origin = pd.Timestamp(WEEK_ORIGIN)
    df["week_start"] = (origin + pd.to_timedelta(
        ((df["placed_at"] - origin).dt.days // 7) * 7, unit="D")).dt.strftime("%Y-%m-%d")
    df["hour"] = df["placed_at"].dt.hour
    df["order_date"] = df["placed_at"].dt.strftime("%Y-%m-%d")
    return df


def config(con):
    df = pd.read_sql_query("SELECT * FROM experiment_config", con)
    return df


def courier_hours(con):
    df = pd.read_sql_query(
        """SELECT market_id, shift_date, hour_start, SUM(online_minutes)/60.0 AS courier_hours
             FROM courier_shifts GROUP BY market_id, shift_date, hour_start""", con)
    origin = pd.Timestamp(WEEK_ORIGIN)
    d = pd.to_datetime(df["shift_date"])
    df["week_start"] = (origin + pd.to_timedelta(((d - origin).dt.days // 7) * 7,
                                                 unit="D")).dt.strftime("%Y-%m-%d")
    return df


def baseline(con):
    return pd.read_sql_query("SELECT * FROM market_week_baseline", con)


def ledger(con):
    return pd.read_sql_query("SELECT * FROM incentive_ledger", con)
