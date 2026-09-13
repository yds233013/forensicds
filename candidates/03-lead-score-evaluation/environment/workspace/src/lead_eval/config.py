"""Evaluation configuration. Paths are relative to the workspace root (parent of config/)."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path
    revops_db: Path
    artifacts_dir: Path
    reports_dir: Path
    as_of: date
    champion_model: str
    outcome_window_days: int
    eval_window_days: int
    n_bins: int
    target_conversion_rate: float


def load_config(path: str | Path) -> Config:
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text())
    root = path.parent.parent
    p, r, e = raw["paths"], raw["run"], raw["evaluation"]
    return Config(
        root=root,
        revops_db=root / p["revops_db"],
        artifacts_dir=root / p["artifacts_dir"],
        reports_dir=root / p["reports_dir"],
        as_of=date.fromisoformat(r["as_of"]),
        champion_model=e["champion_model"],
        outcome_window_days=int(e["outcome_window_days"]),
        eval_window_days=int(e["eval_window_days"]),
        n_bins=int(e["n_bins"]),
        target_conversion_rate=float(e["target_conversion_rate"]),
    )
