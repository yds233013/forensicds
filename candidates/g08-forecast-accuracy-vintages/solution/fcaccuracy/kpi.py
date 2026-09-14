"""Monthly KPI (WAPE) and model head-to-head."""
from __future__ import annotations

import itertools

import pandas as pd

UNIT = ["region", "portfolio", "target_date", "horizon"]


def monthly_kpi(examples: pd.DataFrame) -> pd.DataFrame:
    ex = examples.copy()
    scored = ex["status"] == "scored"
    ex["n_scored"] = scored.astype(int)
    ex["abs_error_scored"] = ex["abs_error_mwh"].where(scored, 0.0)
    ex["actual_scored"] = ex["actual_mwh"].where(scored, 0.0)
    g = ex.groupby(["model", "kpi_month", "portfolio", "horizon"], as_index=False).agg(
        n_examples=("status", "size"), n_scored=("n_scored", "sum"),
        abs_error_mwh=("abs_error_scored", "sum"), actual_mwh=("actual_scored", "sum"))
    g["wape"] = (g["abs_error_mwh"] / g["actual_mwh"]).where(g["n_scored"] > 0)
    return g


def head_to_head(examples: pd.DataFrame, models: pd.DataFrame | None = None) -> list[dict]:
    """Each pair of models compared on the forecasts both have scored (same region, portfolio, delivery day, horizon)."""
    scored = examples[examples["status"] == "scored"]
    out = []
    for a, b in itertools.combinations(sorted(examples["model"].unique()), 2):
        both = scored[scored["model"] == a].merge(scored[scored["model"] == b], on=UNIT, suffixes=("_a", "_b"))
        if both.empty:
            continue
        wa = both["abs_error_mwh_a"].sum() / both["actual_mwh_a"].sum()
        wb = both["abs_error_mwh_b"].sum() / both["actual_mwh_b"].sum()
        out.append({"model_a": a, "model_b": b, "n_pairs": int(len(both)), "first_month": both["kpi_month_a"].min(),
                    "last_month": both["kpi_month_a"].max(), "wape_a": float(wa), "wape_b": float(wb),
                    "relative_change": float(wb / wa - 1)})
    return out
