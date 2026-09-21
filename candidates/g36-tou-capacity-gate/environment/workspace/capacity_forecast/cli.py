"""Command line entry point for the residential peak-capacity readout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from capacity_forecast import incumbent, load

CAPACITY_GATE_KW = 3.057


def analyse(warehouse: Path, out: Path) -> None:
    fr = load.frames(warehouse)
    fc = incumbent.fit_and_forecast(fr)
    payload = {
        "n_households": int(fr["customers"].shape[0]),
        "estate_segment_shares": fc["shares"],
        "target_cdd_mean": fc["target_cdd_mean"],
        "target_peak_kw": fc["target_peak_kw"],
        "segment_target_peak_kw": fc["segment_target_peak_kw"],
        "estate_tou_response_at_target_cdd": 0.0,
        "procurement_decision": "procure" if fc["target_peak_kw"] >= CAPACITY_GATE_KW else "defer",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis_results.json").write_text(json.dumps(payload, indent=2) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="capacity_forecast")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("analyse")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    analyse(Path(a.warehouse), Path(a.out))
