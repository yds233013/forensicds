"""Category baseline trends and buy-plan actions (docs/planning/buy_plan_process.md)."""
from __future__ import annotations

import pandas as pd

REDUCE_AT = -5.0
INCREASE_AT = 5.0


def category_trends(history: pd.DataFrame) -> pd.DataFrame:
    base = history[(~history["promo"]) & (~history["stockout_day"])]   # clean, non-promotional days
    series = base.groupby(["category", "period", "store_id", "sku_id"], as_index=False)["expected_demand"].mean()
    cat = series.groupby(["category", "period"])["expected_demand"].sum().unstack("period")
    out = pd.DataFrame({"category": cat.index, "baseline_pre": cat["pre"].values, "baseline_post": cat["post"].values})
    out["baseline_change_pct"] = 100 * (out["baseline_post"] / out["baseline_pre"] - 1)
    out["action"] = out["baseline_change_pct"].map(
        lambda x: "reduce" if x <= REDUCE_AT else "increase" if x >= INCREASE_AT else "maintain")
    return out.sort_values("category").reset_index(drop=True)
