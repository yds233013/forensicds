"""Turn raw collector deliveries into meter records."""
from __future__ import annotations

import pandas as pd


def normalize(deliveries: pd.DataFrame, redelivery_ttl_hours: int | None = None) -> pd.DataFrame:
    """One row per record revision (event_id, rev), with the time it was first received.

    Delivery is at-least-once and repeated deliveries of a revision are identical, so a repeat is the same record no
    matter how much later it arrives. Revisions are distinct records; which one is current is decided downstream from
    `rev`, not from arrival order. (`redelivery_ttl_hours` is kept for interface compatibility and not used.)
    """
    df = deliveries.sort_values(["received_at", "delivery_id"], kind="mergesort")
    return df.drop_duplicates(["event_id", "rev"], keep="first").reset_index(drop=True)


def current_records(records: pd.DataFrame, received_before: pd.Timestamp | None = None) -> pd.DataFrame:
    """The current revision of every event among records received before `received_before` (all when None)."""
    if received_before is not None:
        records = records[records["received_at"] < received_before]
    latest = records.sort_values(["event_id", "rev"], kind="mergesort").drop_duplicates("event_id", keep="last")
    return latest.assign(service_month=latest["window_start"].dt.strftime("%Y-%m")).reset_index(drop=True)
