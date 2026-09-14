"""Statement calendar."""
from __future__ import annotations

import pandas as pd


def month_start(month: str) -> pd.Timestamp:
    return pd.Timestamp(f"{month}-01T00:00:00Z")


def previous_month(month: str) -> str:
    return (month_start(month) - pd.Timedelta(days=1)).strftime("%Y-%m")


def statement_close(month: str, hours_after_month_end: int) -> pd.Timestamp:
    return month_start(month) + pd.offsets.MonthBegin(1) + pd.Timedelta(hours=hours_after_month_end)
