"""Evaluation report writers."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path


def write_report(reports_dir: Path, as_of: date, report: dict) -> Path:
    out = reports_dir / "model_evaluation"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"eval_{as_of.isoformat()}.json"
    text = json.dumps(report, indent=2, sort_keys=True)
    path.write_text(text + "\n")
    (out / "latest.json").write_text(text + "\n")
    return path
