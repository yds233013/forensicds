"""Command line entry point for the residential peak-capacity readout."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from capacity_forecast import estimators, load

CAPACITY_GATE_KW = 3.057


def analyse(warehouse: Path, out: Path) -> None:
    fr = load.frames(warehouse)
    point, detail = estimators.f1_stratified(fr)
    shares = estimators.estate_shares(fr).to_dict()
    tcdd = float(estimators.target_cdd(fr).mean())
    seg_fc, seg_r = estimators.segment_breakdown(fr, detail)
    payload = {
        "n_households": int(fr["customers"].shape[0]),
        "estate_segment_shares": {k: float(v) for k, v in shares.items()},
        "target_cdd_mean": tcdd,
        "target_peak_kw": point,
        "segment_target_peak_kw": seg_fc,
        "estate_tou_response_at_target_cdd": estimators.estate_response_at_target_cdd(fr, detail),
        "procurement_decision": "procure" if point >= CAPACITY_GATE_KW else "defer",
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
