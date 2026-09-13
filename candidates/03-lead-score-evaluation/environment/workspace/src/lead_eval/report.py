"""Report writers."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd


def write_cohort(cohort: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = cohort.copy()
    out["created_at"] = out["created_at"].dt.strftime("%Y-%m-%d %H:%M:%S")
    out.to_csv(path, index=False)


def write_report(reports_dir: Path, as_of: date, report: dict) -> Path:
    out = reports_dir / "model_monitoring"
    out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    path = out / f"lead_score_eval_{as_of.isoformat()}.json"
    path.write_text(text)
    (out / "latest.json").write_text(text)
    return path
