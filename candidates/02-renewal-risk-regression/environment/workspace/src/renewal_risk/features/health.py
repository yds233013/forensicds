"""Customer Success health features."""
from __future__ import annotations

import pandas as pd

from renewal_risk.sources.warehouse import Warehouse

DEFAULTS = {"health_score": 50.0, "nps_last": 0.0}


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    m = examples[["contract_id", "account_id"]].merge(wh.account_health, on="account_id", how="left")
    out = pd.DataFrame({"contract_id": m["contract_id"]})
    out["health_score"] = pd.to_numeric(m["health_score"]).fillna(DEFAULTS["health_score"]).astype(float)
    out["health_red"] = (m["health_color"] == "Red").astype(int)
    out["nps_last"] = pd.to_numeric(m["nps_last"]).fillna(DEFAULTS["nps_last"]).astype(float)
    out["csm_sentiment_negative"] = (m["csm_sentiment"] == "Negative").astype(int)
    return out
