"""Pipeline configuration (TOML). Paths are relative to the workspace root (parent of config/)."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path
    warehouse_db: Path
    artifacts_dir: Path
    reports_dir: Path
    as_of: date
    horizon_days: int
    label_grace_days: int
    eval_window_days: int
    train_window_days: int
    model_C: float
    class_weight: str | None
    winsor_lower: float
    winsor_upper: float
    max_iter: int
    calibration_bins: int


def load_config(path: str | Path) -> Config:
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text())
    root = path.parent.parent
    p, run, ex, m = raw["paths"], raw["run"], raw["examples"], raw["model"]
    return Config(
        root=root,
        warehouse_db=root / p["warehouse_db"],
        artifacts_dir=root / p["artifacts_dir"],
        reports_dir=root / p["reports_dir"],
        as_of=date.fromisoformat(run["as_of"]),
        horizon_days=int(ex["horizon_days"]),
        label_grace_days=int(ex["label_grace_days"]),
        eval_window_days=int(ex["eval_window_days"]),
        train_window_days=int(ex["train_window_days"]),
        model_C=float(m["C"]),
        class_weight=m.get("class_weight") or None,
        winsor_lower=float(m["winsor_lower"]),
        winsor_upper=float(m["winsor_upper"]),
        max_iter=int(m["max_iter"]),
        calibration_bins=int(m["calibration_bins"]),
    )
