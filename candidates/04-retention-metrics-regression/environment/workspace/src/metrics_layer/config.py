from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path
    warehouse_db: Path
    analytics_db: Path
    models_dir: Path
    board_dir: Path
    as_of: date
    n_quarters: int


def load_config(path) -> Config:
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text())
    root = path.parent.parent
    p = raw["paths"]
    return Config(root=root, warehouse_db=root / p["warehouse_db"], analytics_db=root / p["analytics_db"],
                  models_dir=root / p["models_dir"], board_dir=root / p["board_dir"],
                  as_of=date.fromisoformat(raw["build"]["as_of"]), n_quarters=int(raw["build"]["n_quarters"]))
