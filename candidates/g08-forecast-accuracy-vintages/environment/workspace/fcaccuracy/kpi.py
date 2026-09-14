"""Monthly KPI (WAPE) and model head-to-head."""
from __future__ import annotations

import itertools

import pandas as pd


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


def head_to_head(examples: pd.DataFrame, models: pd.DataFrame) -> list[dict]:
    """Each pair of models, each measured over its own production period."""
    scored = examples[examples["status"] == "scored"]
    out = []
    names = sorted(scored["model"].unique())
    periods = models.set_index("model")[["production_from", "production_to"]].to_dict("index")
    for a, b in itertools.combinations(names, 2):
        sides = []
        for m in (a, b):
            p = periods.get(m, {})
            rows = scored[scored["model"] == m]
            if p.get("production_from"):
                rows = rows[rows["run_date"] >= p["production_from"]]
            if p.get("production_to"):
                rows = rows[rows["run_date"] <= p["production_to"]]
            sides.append(rows)
        if sides[0].empty or sides[1].empty:
            continue
        wa = sides[0]["abs_error_mwh"].sum() / sides[0]["actual_mwh"].sum()
        wb = sides[1]["abs_error_mwh"].sum() / sides[1]["actual_mwh"].sum()
        months = pd.concat(sides)["kpi_month"]
        out.append({"model_a": a, "model_b": b, "n_pairs": int(len(sides[1])), "first_month": months.min(),
                    "last_month": months.max(), "wape_a": float(wa), "wape_b": float(wb),
                    "relative_change": float(wb / wa - 1)})
    return out
