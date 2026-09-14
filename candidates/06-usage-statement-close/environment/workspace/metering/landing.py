"""Read collector deliveries from the landing zone (raw/landing/received_date=YYYY-MM-DD/*.jsonl.gz)."""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

RECORD_FIELDS = ["event_id", "rev", "customer_id", "meter", "window_start", "window_end", "quantity"]


def read_deliveries(landing_dir: Path) -> pd.DataFrame:
    rows = []
    for part in sorted(Path(landing_dir).glob("received_date=*/*.jsonl.gz")):
        with gzip.open(part, "rt", encoding="utf-8") as fh:
            for line in fh:
                obj = json.loads(line)
                rec = obj["record"]
                rows.append([obj["delivery_id"], obj["received_at"], obj["collector"]] + [rec[f] for f in RECORD_FIELDS])
    df = pd.DataFrame(rows, columns=["delivery_id", "received_at", "collector"] + RECORD_FIELDS)
    for col in ("received_at", "window_start", "window_end"):
        df[col] = pd.to_datetime(df[col], utc=True)
    df["rev"] = df["rev"].astype(int)
    return df  # quantity stays a decimal string
