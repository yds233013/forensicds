"""Sales pipeline signals from CRM opportunities.

Renewal opportunity: the CRM opportunity of type `renewal` attached to the renewing contract.
Expansion opportunities: open `expansion` opportunities on the account.
"""
from __future__ import annotations

import pandas as pd

from renewal_risk.sources.warehouse import Warehouse

STAGE_ORDINAL = {"Closed Lost": 0, "Qualification": 1, "Discovery": 2, "Proposal": 3, "Negotiation": 4,
                 "Verbal": 5, "Closed Won": 6}
CLOSED_STAGES = {"Closed Won", "Closed Lost"}
NO_OPP = {"renewal_stage_ordinal": -1, "renewal_amount_ratio": 1.0, "days_to_opp_close": 90}


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    opps = wh.opportunities
    renewal = opps[opps["opportunity_type"] == "renewal"][
        ["contract_id", "created_at", "stage", "forecast_category", "amount_usd", "close_date", "competitor"]]
    m = examples[["contract_id", "prediction_date", "arr_usd"]].merge(renewal, on="contract_id", how="left")
    exists = m["created_at"].notna() & (m["created_at"] < m["prediction_date"])

    out = pd.DataFrame({"contract_id": m["contract_id"]})
    out["has_renewal_opp"] = exists.astype(int)
    out["renewal_stage_ordinal"] = m["stage"].map(STAGE_ORDINAL).where(exists, NO_OPP["renewal_stage_ordinal"]).astype(int)
    for col, value in (("forecast_commit", "Commit"), ("forecast_best_case", "Best Case"), ("forecast_omitted", "Omitted")):
        out[col] = ((m["forecast_category"] == value) & exists).astype(int)
    out["renewal_amount_ratio"] = (m["amount_usd"] / m["arr_usd"]).where(exists, NO_OPP["renewal_amount_ratio"])
    out["days_to_opp_close"] = (m["close_date"] - m["prediction_date"]).dt.days.where(exists, NO_OPP["days_to_opp_close"]).astype(int)
    out["competitor_flagged"] = (m["competitor"].fillna("").ne("") & exists).astype(int)

    expansion = opps[opps["opportunity_type"] == "expansion"][["account_id", "created_at", "stage"]]
    e = examples[["contract_id", "account_id", "prediction_date"]].merge(expansion, on="account_id")
    e = e[(e["created_at"] < e["prediction_date"]) & ~e["stage"].isin(CLOSED_STAGES)]
    out["open_expansion_opps"] = out["contract_id"].map(e.groupby("contract_id").size()).fillna(0).astype(int)
    return out
