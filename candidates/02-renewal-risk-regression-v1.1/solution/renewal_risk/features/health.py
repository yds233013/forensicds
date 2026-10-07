"""Customer Success health features, as known at each example's prediction time.

Health state is reconstructed from `cs_account_health_history` (sources/history.py).
"""
from __future__ import annotations

import pandas as pd

from renewal_risk.sources.history import state_as_of
from renewal_risk.sources.warehouse import Warehouse

DEFAULTS = {"health_score": 50.0, "nps_last": 0.0}
FIELDS = ["health_score", "health_color", "nps_last", "csm_sentiment"]


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    req = examples[["contract_id", "account_id", "prediction_date"]].rename(
        columns={"contract_id": "request_id", "prediction_date": "cutoff"})
    m = state_as_of(wh.health_history, "account_id", req, FIELDS).rename(columns={"request_id": "contract_id"})
    m = examples[["contract_id"]].merge(m, on="contract_id", how="left")
    out = pd.DataFrame({"contract_id": m["contract_id"]})
    out["health_score"] = pd.to_numeric(m["health_score"].replace("", None)).fillna(DEFAULTS["health_score"]).astype(float)
    out["health_red"] = (m["health_color"] == "Red").astype(int)
    out["nps_last"] = pd.to_numeric(m["nps_last"].replace("", None)).fillna(DEFAULTS["nps_last"]).astype(float)
    out["csm_sentiment_negative"] = (m["csm_sentiment"] == "Negative").astype(int)
    return out
