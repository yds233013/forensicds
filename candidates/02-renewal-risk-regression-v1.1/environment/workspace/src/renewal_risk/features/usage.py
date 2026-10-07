"""Product usage features from weekly usage rollups.

A week's rollup is loaded the morning after the week closes, so only weeks that ended strictly
before the prediction date are used.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from renewal_risk.sources.warehouse import Warehouse


def _slope(g: pd.DataFrame) -> float:
    if len(g) < 3:
        return 0.0
    x = g["x"].to_numpy(dtype=float)
    y = g["ratio"].to_numpy(dtype=float)
    xm = x - x.mean()
    return float((xm * (y - y.mean())).sum() / (xm ** 2).sum())


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    m = examples[["contract_id", "account_id", "prediction_date", "seats"]].merge(wh.usage_weekly, on="account_id")
    m = m[m["week_start"] + pd.Timedelta(days=7) < m["prediction_date"]]
    m = m.sort_values(["contract_id", "week_start"], ascending=[True, False])
    m["recency"] = m.groupby("contract_id").cumcount()
    m["ratio"] = m["active_users"] / m["seats"]

    last4 = m[m["recency"] < 4].groupby("contract_id").agg(
        active=("active_users", "mean"), seats=("seats", "first"), api=("api_calls", "sum"),
        logins=("logins", "sum"), active_sum=("active_users", "sum"))
    last12 = m[m["recency"] < 12].copy()
    n = last12.groupby("contract_id")["recency"].transform("count")
    last12["x"] = (n - 1) - last12["recency"]
    trend = last12.groupby("contract_id")[["x", "ratio"]].apply(_slope)

    out = pd.DataFrame({"contract_id": examples["contract_id"]})
    out["active_user_ratio_4w"] = out["contract_id"].map(last4["active"] / last4["seats"]).fillna(0.0)
    out["active_user_trend_12w"] = out["contract_id"].map(trend).fillna(0.0)
    out["api_calls_4w_log"] = np.log1p(out["contract_id"].map(last4["api"]).fillna(0.0))
    out["logins_per_active_user_4w"] = out["contract_id"].map(
        last4["logins"] / last4["active_sum"].clip(lower=1)).fillna(0.0)
    return out
