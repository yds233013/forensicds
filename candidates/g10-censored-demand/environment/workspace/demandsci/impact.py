"""LEAN-26 programme impact: lost units by period and arm, production forecast bias against demand."""
from __future__ import annotations

import sqlite3

import pandas as pd


def programme_impact(con: sqlite3.Connection, history: pd.DataFrame) -> dict:
    h = history
    lost_units, lost_share = {}, {}
    for period in ("pre", "post"):
        lost_units[period], lost_share[period] = {}, {}
        for arm in ("lean26", "holdout"):
            m = (h["period"] == period) & (h["arm"] == arm)
            lu = float(h.loc[m, "lost_units"].sum())
            lost_units[period][arm] = lu
            lost_share[period][arm] = lu / float(h.loc[m, "expected_demand"].sum())
    fc = pd.read_sql_query("SELECT model, store_id, sku_id, date, forecast_units FROM forecasts", con)
    fc = fc.pivot_table(index=["store_id", "sku_id", "date"], columns="model", values="forecast_units").reset_index()
    j = h.merge(fc, on=["store_id", "sku_id", "date"], how="left")
    pre = j["period"] == "pre"
    post_lean = (j["period"] == "post") & (j["arm"] == "lean26")
    bias = {
        "v3_pre_all_stores": float(100 * (j.loc[pre, "v3"].sum() - j.loc[pre, "expected_demand"].sum()) / j.loc[pre, "expected_demand"].sum()),
        "v4_post_lean26": float(100 * (j.loc[post_lean, "v4"].sum() - j.loc[post_lean, "expected_demand"].sum()) / j.loc[post_lean, "expected_demand"].sum()),
    }
    return {"go_live_date": str(h["go_live_date"].iloc[0]), "lost_units": lost_units, "lost_share": lost_share,
            "forecast_bias_pct": bias}
