"""Usage mart: usage per customer, meter and service month, as currently known."""
from __future__ import annotations

from decimal import Decimal

import pandas as pd

from metering.normalize import current_records

MART_COLUMNS = ["customer_id", "meter", "service_month", "quantity"]


def build_usage_mart(records: pd.DataFrame) -> pd.DataFrame:
    current = current_records(records)
    out = (current.groupby(["customer_id", "meter", "service_month"], sort=True)["quantity"]
                  .agg(lambda s: sum((Decimal(x) for x in s), Decimal(0)))
                  .reset_index())
    out["quantity"] = out["quantity"].map(lambda d: f"{d:.3f}")
    return out[MART_COLUMNS]
