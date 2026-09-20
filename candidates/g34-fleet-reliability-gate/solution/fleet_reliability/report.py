from __future__ import annotations

import json
from pathlib import Path

HORIZON = 36.0
TRIGGER = 0.28


def write(out: Path, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis_results.json").write_text(json.dumps(payload, indent=2) + "\n")
