"""Usage mart: usage per customer, meter and month (read by the customer usage console and capacity dashboards)."""
from __future__ import annotations

from decimal import Decimal

import pandas as pd

MART_COLUMNS = ["customer_id", "meter", "service_month", "quantity"]


def build_usage_mart(usage: pd.DataFrame) -> pd.DataFrame:
    df = usage.assign(service_month=usage["received_at"].dt.strftime("%Y-%m"))
    out = (df.groupby(["customer_id", "meter", "service_month"], sort=True)["quantity"]
             .agg(lambda s: sum((Decimal(x) for x in s), Decimal(0)))
             .reset_index())
    out["quantity"] = out["quantity"].map(lambda d: f"{d:.3f}")
    return out[MART_COLUMNS]
