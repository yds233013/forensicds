"""Read source extracts: billing (SQLite, authoritative for money) and CRM exports."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass

import pandas as pd

from revrec.config import Config


@dataclass
class Sources:
    invoice_lines: pd.DataFrame      # one row per revenue-bearing invoice line on a recognized invoice
    credit_notes: pd.DataFrame       # one row per issued credit note
    billing_accounts: pd.DataFrame   # one row per billing account
    fx_rates: pd.DataFrame           # one row per (currency, rate_month)
    reportable_months: list[str]     # accounting periods included in reporting, ascending
    crm_accounts: pd.DataFrame       # CRM export, see docs/data/data_dictionary.md
    account_migrations: pd.DataFrame  # Billing Ops migration register


def _read_sql(con: sqlite3.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    return pd.read_sql_query(sql, con, params=params)


def load_sources(cfg: Config) -> Sources:
    con = sqlite3.connect(f"file:{cfg.billing_db}?mode=ro", uri=True)
    try:
        types = ",".join("?" * len(cfg.revenue_line_types))
        statuses = ",".join("?" * len(cfg.invoice_statuses))
        invoice_lines = _read_sql(
            con,
            f"""
            SELECT l.invoice_line_id, l.invoice_id, i.billing_account_id, i.invoice_date, i.currency,
                   l.line_type, l.amount_minor, l.service_period_start, l.service_period_end
            FROM invoice_lines l
            JOIN invoices i ON i.invoice_id = l.invoice_id
            WHERE i.status IN ({statuses}) AND l.line_type IN ({types})
            ORDER BY l.invoice_line_id
            """,
            cfg.invoice_statuses + cfg.revenue_line_types,
        )
        credit_notes = _read_sql(
            con,
            f"""
            SELECT c.credit_note_id, c.invoice_id, c.invoice_line_id, i.billing_account_id, c.issued_date,
                   c.currency, c.amount_minor
            FROM credit_notes c
            JOIN invoices i ON i.invoice_id = c.invoice_id
            WHERE c.status = 'issued' AND i.status IN ({statuses})
            ORDER BY c.credit_note_id
            """,
            cfg.invoice_statuses,
        )
        billing_accounts = _read_sql(con, "SELECT * FROM billing_accounts ORDER BY billing_account_id")
        fx_rates = _read_sql(con, "SELECT currency, rate_month, usd_per_unit FROM fx_rates")
        pstat = ",".join("?" * len(cfg.reportable_period_statuses))
        months = _read_sql(
            con,
            f"SELECT period_month FROM accounting_periods WHERE status IN ({pstat}) ORDER BY period_month",
            cfg.reportable_period_statuses,
        )["period_month"].tolist()
    finally:
        con.close()

    crm_accounts = pd.read_csv(cfg.crm_accounts, dtype=str, keep_default_na=False)
    account_migrations = pd.read_csv(cfg.account_migrations, dtype=str, keep_default_na=False)
    return Sources(invoice_lines, credit_notes, billing_accounts, fx_rates, months, crm_accounts, account_migrations)
