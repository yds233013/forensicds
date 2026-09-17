"""Readout files (docs/outputs/readout_contract.md)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

HURDLE = 0.025          # continuation hurdle, business case section 3
PANEL_COLS = ["store_id", "week_start", "wave", "go_live_week", "event_week", "comparable", "log_net_sales"]


def write_all(out: Path, panel: pd.DataFrame, effects: dict) -> None:
    out.mkdir(parents=True, exist_ok=True)
    panel[PANEL_COLS].to_csv(out / "analysis_panel.csv", index=False)
    readout = dict(effects)
    readout["decision"] = "continue" if effects["gate_effect"]["estimate"] >= HURDLE else "stop"
    (out / "readout.json").write_text(json.dumps(readout, indent=2) + "\n")
