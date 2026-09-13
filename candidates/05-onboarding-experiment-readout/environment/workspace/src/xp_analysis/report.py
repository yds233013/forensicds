"""Readout writers."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd


def write_units(units: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    units.to_csv(path, index=False, lineterminator="\n")


def write_readout(reports_dir: Path, experiment_id: str, analysis_date: date, readout: dict) -> Path:
    reports_dir.mkdir(parents=True, exist_ok=True)
    text = json.dumps(readout, indent=2, sort_keys=True) + "\n"
    path = reports_dir / f"{experiment_id}_readout_{analysis_date.isoformat()}.json"
    path.write_text(text)
    (reports_dir / f"{experiment_id}_latest.json").write_text(text)
    return path
