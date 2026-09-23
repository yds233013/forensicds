"""Write the outputs described in docs/outputs/plan_contract.md."""
from __future__ import annotations

import json
from pathlib import Path

SLA_SHORTFALL_LIMIT = 40


def write(out: Path, plan, readout: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    plan.to_csv(out / "plan.csv", index=False)
    (out / "readout.json").write_text(json.dumps(readout, indent=2, sort_keys=True) + "\n")
