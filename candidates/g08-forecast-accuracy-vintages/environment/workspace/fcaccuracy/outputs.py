"""Writes the mart outputs described in docs/mart/accuracy_mart.md."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

EXAMPLE_COLUMNS = ["model", "run_date", "issue_id", "region", "portfolio", "target_date", "horizon", "kpi_month",
                   "forecast_mwh", "status", "actual_run_ids", "actual_mwh", "abs_error_mwh"]
MONTHLY_COLUMNS = ["model", "kpi_month", "portfolio", "horizon", "n_examples", "n_scored", "abs_error_mwh",
                   "actual_mwh", "wape"]


def write_all(out: Path, as_of: str, closed: list[str], examples: pd.DataFrame, monthly: pd.DataFrame,
              h2h: list[dict]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    examples[EXAMPLE_COLUMNS].to_csv(out / "evaluation_examples.csv", index=False)
    monthly.sort_values(["model", "kpi_month", "portfolio", "horizon"])[MONTHLY_COLUMNS].to_csv(
        out / "monthly_kpi.csv", index=False)
    summary = {"as_of": as_of, "closed_months": list(closed), "head_to_head": h2h}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
