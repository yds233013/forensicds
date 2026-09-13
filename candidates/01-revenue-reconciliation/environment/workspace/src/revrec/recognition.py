"""Revenue recognition schedule (see docs/finance/revenue_recognition_policy.md).

Output grain: one row per (source_type, source_id, revenue_month)
  * invoice lines are recognized ratably by day across their service period;
  * credit notes reduce revenue in full in the month they are issued.
Amounts are in the document currency (``amount_local``).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SCHEDULE_COLUMNS = [
    "revenue_month", "period_start", "period_end", "source_type", "source_id", "invoice_id",
    "billing_account_id", "currency", "amount_local",
]


def _line_schedule(lines: pd.DataFrame) -> pd.DataFrame:
    if lines.empty:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)
    start = pd.to_datetime(lines["service_period_start"])
    end = pd.to_datetime(lines["service_period_end"])
    n_months = (end.dt.year - start.dt.year) * 12 + (end.dt.month - start.dt.month) + 1
    idx = np.repeat(lines.index.to_numpy(), n_months.to_numpy())
    rows = lines.loc[idx].reset_index(drop=True)
    offset = rows.groupby(idx).cumcount().to_numpy()
    s = pd.to_datetime(rows["service_period_start"])
    e = pd.to_datetime(rows["service_period_end"])
    first_month = s.dt.to_period("M")
    month = first_month + offset
    m_start = month.dt.start_time.dt.normalize()
    m_end = month.dt.end_time.dt.normalize()
    overlap = (np.minimum(e, m_end) - np.maximum(s, m_start)).dt.days + 1
    total = (e - s).dt.days + 1
    out = pd.DataFrame({
        "revenue_month": month.astype(str),
        "period_start": m_start,
        "period_end": m_end,
        "source_type": "invoice_line",
        "source_id": rows["invoice_line_id"],
        "invoice_id": rows["invoice_id"],
        "billing_account_id": rows["billing_account_id"],
        "currency": rows["currency"],
        "amount_local": rows["amount_minor"] / 100.0 * overlap / total,
    })
    return out


def _credit_schedule(credits: pd.DataFrame) -> pd.DataFrame:
    if credits.empty:
        return pd.DataFrame(columns=SCHEDULE_COLUMNS)
    month = pd.to_datetime(credits["issued_date"]).dt.to_period("M")
    return pd.DataFrame({
        "revenue_month": month.astype(str),
        "period_start": month.dt.start_time.dt.normalize(),
        "period_end": month.dt.end_time.dt.normalize(),
        "source_type": "credit_note",
        "source_id": credits["credit_note_id"],
        "invoice_id": credits["invoice_id"],
        "billing_account_id": credits["billing_account_id"],
        "currency": credits["currency"],
        "amount_local": -credits["amount_minor"] / 100.0,
    })


def build_schedule(invoice_lines: pd.DataFrame, credit_notes: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    schedule = pd.concat([_line_schedule(invoice_lines), _credit_schedule(credit_notes)], ignore_index=True)
    schedule = schedule[schedule["revenue_month"].isin(months)]
    return schedule[SCHEDULE_COLUMNS].reset_index(drop=True)
