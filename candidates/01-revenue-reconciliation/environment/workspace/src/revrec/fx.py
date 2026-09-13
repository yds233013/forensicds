"""Currency conversion to the reporting currency at the monthly average rate of the revenue month."""
from __future__ import annotations

import pandas as pd


def to_reporting_currency(rows: pd.DataFrame, fx_rates: pd.DataFrame) -> pd.DataFrame:
    rates = fx_rates.rename(columns={"rate_month": "revenue_month", "usd_per_unit": "fx_usd_per_unit"})
    out = rows.merge(rates, on=["currency", "revenue_month"], how="left", validate="many_to_one")
    out["amount_usd"] = out["amount_local"] * out["fx_usd_per_unit"]
    return out
