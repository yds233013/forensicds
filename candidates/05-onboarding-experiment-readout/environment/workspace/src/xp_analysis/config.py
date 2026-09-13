"""Readout configuration. Paths are relative to the workspace root (parent of config/)."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path
    product_db: Path
    artifacts_dir: Path
    reports_dir: Path
    analysis_date: date
    experiment_id: str
    outcome_window_days: int
    min_active_users: int
    z: float
    treatment_share: float


def load_config(path: str | Path) -> Config:
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text())
    root = path.parent.parent
    p, r, e = raw["paths"], raw["run"], raw["experiment"]
    return Config(
        root=root,
        product_db=root / p["product_db"],
        artifacts_dir=root / p["artifacts_dir"],
        reports_dir=root / p["reports_dir"],
        analysis_date=date.fromisoformat(r["analysis_date"]),
        experiment_id=e["experiment_id"],
        outcome_window_days=int(e["outcome_window_days"]),
        min_active_users=int(e["min_active_users"]),
        z=float(e["z"]),
        treatment_share=float(e["treatment_share"]),
    )
