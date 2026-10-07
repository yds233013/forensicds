"""Support ticket features."""
from __future__ import annotations

import pandas as pd

from renewal_risk.sources.warehouse import Warehouse


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    m = examples[["contract_id", "account_id", "prediction_date"]].merge(wh.support_tickets, on="account_id")
    before = m[m["opened_at"] < m["prediction_date"]]
    age = before["prediction_date"] - before["opened_at"]

    out = pd.DataFrame({"contract_id": examples["contract_id"]})
    out["tickets_90d"] = out["contract_id"].map(before[age <= pd.Timedelta(days=90)].groupby("contract_id").size())
    sev1 = before[(age <= pd.Timedelta(days=180)) & (before["severity"] == "sev1")]
    out["sev1_tickets_180d"] = out["contract_id"].map(sev1.groupby("contract_id").size())
    still_open = before[before["closed_at"].isna() | (before["closed_at"] >= before["prediction_date"])]
    out["open_tickets_at_prediction"] = out["contract_id"].map(still_open.groupby("contract_id").size())
    for c in ["tickets_90d", "sev1_tickets_180d", "open_tickets_at_prediction"]:
        out[c] = out[c].fillna(0).astype(int)
    return out
