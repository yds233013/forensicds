"""Sales pipeline signals from CRM opportunities, as known at each example's prediction time.

Renewal opportunity: the CRM opportunity of type `renewal` attached to the renewing contract.
Expansion opportunities: open `expansion` opportunities on the account.
Opportunity state is reconstructed from field history (sources/history.py); the current-state
object is only used for identity attributes that never change (account, contract, type).
"""
from __future__ import annotations

import pandas as pd

from renewal_risk.sources.history import state_as_of
from renewal_risk.sources.warehouse import Warehouse

STAGE_ORDINAL = {"Closed Lost": 0, "Qualification": 1, "Discovery": 2, "Proposal": 3, "Negotiation": 4,
                 "Verbal": 5, "Closed Won": 6}
CLOSED_STAGES = {"Closed Won", "Closed Lost"}
NO_OPP = {"renewal_stage_ordinal": -1, "renewal_amount_ratio": 1.0, "days_to_opp_close": 90}
FIELDS = ["stage", "forecast_category", "amount_usd", "close_date", "competitor"]


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    opps = wh.opportunities
    hist = wh.opportunity_history

    renewal = opps.loc[opps["opportunity_type"] == "renewal", ["contract_id", "opportunity_id"]]
    m = examples[["contract_id", "prediction_date", "arr_usd"]].merge(renewal, on="contract_id", how="left")
    req = m.loc[m["opportunity_id"].notna(), ["contract_id", "opportunity_id", "prediction_date"]].rename(
        columns={"contract_id": "request_id", "prediction_date": "cutoff"})
    st = state_as_of(hist, "opportunity_id", req, FIELDS).rename(columns={"request_id": "contract_id"})
    m = m.merge(st, on="contract_id", how="left")
    exists = m["exists"].fillna(False).astype(bool)

    out = pd.DataFrame({"contract_id": m["contract_id"]})
    out["has_renewal_opp"] = exists.astype(int)
    out["renewal_stage_ordinal"] = m["stage"].map(STAGE_ORDINAL).where(exists, NO_OPP["renewal_stage_ordinal"]).astype(int)
    for col, value in (("forecast_commit", "Commit"), ("forecast_best_case", "Best Case"), ("forecast_omitted", "Omitted")):
        out[col] = ((m["forecast_category"] == value) & exists).astype(int)
    amount = pd.to_numeric(m["amount_usd"], errors="coerce")
    out["renewal_amount_ratio"] = (amount / m["arr_usd"]).where(exists, NO_OPP["renewal_amount_ratio"])
    close = pd.to_datetime(m["close_date"], errors="coerce")
    out["days_to_opp_close"] = (close - m["prediction_date"]).dt.days.where(exists, NO_OPP["days_to_opp_close"]).astype(int)
    out["competitor_flagged"] = (m["competitor"].fillna("").ne("") & exists).astype(int)

    expansion = opps.loc[opps["opportunity_type"] == "expansion", ["account_id", "opportunity_id"]]
    e = examples[["contract_id", "account_id", "prediction_date"]].merge(expansion, on="account_id")
    if len(e):
        e = e.reset_index(drop=True)
        e["request_id"] = e.index
        est = state_as_of(hist, "opportunity_id", e.rename(columns={"prediction_date": "cutoff"}), ["stage"])
        e = e.merge(est, on="request_id")
        open_now = e[e["exists"] & ~e["stage"].isin(CLOSED_STAGES)]
        counts = open_now.groupby("contract_id").size()
    else:
        counts = pd.Series(dtype=int)
    out["open_expansion_opps"] = out["contract_id"].map(counts).fillna(0).astype(int)
    return out
