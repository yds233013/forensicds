"""Offline gate metrics."""
from __future__ import annotations

import numpy as np
import pandas as pd

SLOTS = 5


def ctr_at_5(matched: pd.DataFrame) -> pd.DataFrame:
    """Clicks per matched impression, scaled to a five-slot row."""
    g = matched.groupby("policy")["clicked"]
    out = pd.DataFrame({"impressions": g.size(), "clicks": g.sum()})
    out["ctr"] = out["clicks"] / out["impressions"]
    out["value"] = SLOTS * out["ctr"]
    out["se"] = SLOTS * np.sqrt(out["ctr"] * (1 - out["ctr"]) / out["impressions"])
    return out.reset_index()


def with_intervals(values: pd.DataFrame) -> pd.DataFrame:
    v = values.set_index("policy")
    base = v.loc["v6"]
    rows = []
    for policy, r in v.iterrows():
        lift = r["value"] - base["value"]
        lift_se = float(np.sqrt(r["se"] ** 2 + base["se"] ** 2))
        rows.append({"policy": policy, "value": r["value"],
                     "ci_low": r["value"] - 1.96 * r["se"], "ci_high": r["value"] + 1.96 * r["se"],
                     "lift_vs_v6": lift, "lift_ci_low": lift - 1.96 * lift_se,
                     "lift_ci_high": lift + 1.96 * lift_se})
    return pd.DataFrame(rows)
