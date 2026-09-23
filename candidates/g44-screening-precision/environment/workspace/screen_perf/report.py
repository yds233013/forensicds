"""Write the output described in docs/outputs/performance_contract.md."""
from __future__ import annotations

import json
from pathlib import Path


def write(out: Path, payload: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "performance.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
