"""Readout files (docs/outputs/readout_contract.md)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HURDLE = 0.025          # continuation hurdle, business case section 3
PANEL_COLS = ["store_id", "week_start", "wave", "go_live_week", "event_week", "comparable", "log_net_sales"]


def _ci(e: dict) -> dict:
    return {"estimate": e["estimate"], "ci_low": e["estimate"] - 1.96 * e["se"],
            "ci_high": e["estimate"] + 1.96 * e["se"]}


def write_all(out: Path, panel: pd.DataFrame, by_wave: dict, overall: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    panel[PANEL_COLS].to_csv(out / "analysis_panel.csv", index=False)
    gate = _ci(overall)
    readout = {
        "effect_by_wave": {w: _ci(e) for w, e in by_wave.items()},
        "gate_effect": gate,
        "decision": "continue" if gate["estimate"] >= HURDLE else "stop",
    }
    (out / "readout.json").write_text(json.dumps(readout, indent=2) + "\n")
