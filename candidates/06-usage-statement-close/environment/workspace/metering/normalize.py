"""Turn raw collector deliveries into usage rows."""
from __future__ import annotations

import pandas as pd


def normalize(deliveries: pd.DataFrame, redelivery_ttl_hours: int) -> pd.DataFrame:
    """Drop collector redeliveries.

    The collector retries sends it could not confirm. Like the platform dedupe store, an event id is remembered for
    `redelivery_ttl_hours` after it was last seen; a delivery of an event id seen within that period is a redelivery.
    """
    df = deliveries.sort_values(["received_at", "delivery_id"], kind="mergesort")
    previous = df.groupby("event_id")["received_at"].shift()
    redelivered = previous.notna() & ((df["received_at"] - previous) <= pd.Timedelta(hours=redelivery_ttl_hours))
    return df.loc[~redelivered].reset_index(drop=True)
