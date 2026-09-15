"""Writes the review outputs described in docs/outputs/review_outputs.md."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HISTORY_COLUMNS = ["store_id", "sku_id", "date", "units_sold", "expected_demand", "lost_units"]
TREND_COLUMNS = ["category", "baseline_pre", "baseline_post", "baseline_change_pct", "action"]


def write_all(out: Path, history: pd.DataFrame, trends: pd.DataFrame, impact: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    history[HISTORY_COLUMNS].to_csv(out / "demand_history.csv", index=False)
    trends[TREND_COLUMNS].to_csv(out / "category_trends.csv", index=False)
    (out / "programme_impact.json").write_text(json.dumps(impact, indent=2) + "\n")
