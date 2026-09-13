"""Readers for the analytics warehouse extract (data/warehouse.db).

Customer relationship data comes from the CRM v3 objects (`crm_opportunities`) and the
Customer Success platform (`cs_account_health`). These replaced the daily snapshot tables
that were decommissioned after the CRM v3 migration (docs/ops/2026-01_crm_v3_migration.md).
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd

TS_COLS = {"synced_at", "decided_at", "opened_at", "closed_at", "created_at", "last_modified_at", "changed_at",
           "last_changed_at"}
DATE_COLS = {"start_date", "renewal_date", "week_start", "created_date", "close_date"}


def _read(con: sqlite3.Connection, sql: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, con)
    for c in df.columns:
        if c in TS_COLS or c in DATE_COLS:
            df[c] = pd.to_datetime(df[c])
    return df


@dataclass
class Warehouse:
    accounts: pd.DataFrame
    contracts: pd.DataFrame
    renewal_outcomes: pd.DataFrame
    usage_weekly: pd.DataFrame
    support_tickets: pd.DataFrame
    opportunities: pd.DataFrame
    account_health: pd.DataFrame


def load_warehouse(db_path) -> Warehouse:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return Warehouse(
            accounts=_read(con, "SELECT account_id, segment, region, industry, created_date FROM accounts"),
            contracts=_read(con, "SELECT contract_id, account_id, start_date, renewal_date, seats, arr_usd, plan FROM contracts"),
            renewal_outcomes=_read(con, "SELECT contract_id, account_id, renewal_date, outcome, decided_at, synced_at "
                                        "FROM renewal_outcomes"),
            usage_weekly=_read(con, "SELECT account_id, week_start, active_users, api_calls, logins FROM usage_weekly"),
            support_tickets=_read(con, "SELECT ticket_id, account_id, opened_at, severity, closed_at FROM support_tickets"),
            opportunities=load_opportunities(con),
            account_health=load_account_health(con),
        )
    finally:
        con.close()


def load_opportunities(con: sqlite3.Connection) -> pd.DataFrame:
    """CRM v3 opportunity object."""
    return _read(con, "SELECT opportunity_id, account_id, contract_id, opportunity_type, created_at, stage, "
                      "forecast_category, amount_usd, close_date, competitor FROM crm_opportunities")


def load_account_health(con: sqlite3.Connection) -> pd.DataFrame:
    """Customer Success account health object."""
    return _read(con, "SELECT account_id, health_score, health_color, nps_last, csm_sentiment FROM cs_account_health")
