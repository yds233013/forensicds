"""Contract and account tenure features."""
from __future__ import annotations

import numpy as np
import pandas as pd

from renewal_risk.sources.warehouse import Warehouse

DAYS_PER_MONTH = 30.4375


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    ex = examples.merge(wh.accounts[["account_id", "created_date"]], on="account_id", how="left")
    out = pd.DataFrame({"contract_id": ex["contract_id"]})
    out["arr_usd_log"] = np.log1p(ex["arr_usd"])
    out["seats_licensed"] = ex["seats"].astype(float)
    out["plan_enterprise"] = (ex["plan"] == "Enterprise").astype(int)
    out["tenure_months"] = (ex["prediction_date"] - ex["created_date"]).dt.days / DAYS_PER_MONTH

    # renewals already decided (and loaded) before the prediction date
    prior = examples[["contract_id", "account_id", "prediction_date"]].merge(
        wh.renewal_outcomes[["account_id", "outcome", "synced_at"]], on="account_id")
    prior = prior[(prior["outcome"] == "renewed") & (prior["synced_at"] < prior["prediction_date"])]
    counts = prior.groupby("contract_id").size()
    out["prior_renewals"] = out["contract_id"].map(counts).fillna(0).astype(int)
    return out
