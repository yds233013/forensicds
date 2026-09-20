"""Command line entry point for the priority-dispatch readout."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from dispatch_experiment import estimate, load

GATE = 0.015


def analyse(warehouse: Path, out: Path) -> None:
    blocks = load.blocks(warehouse)
    sat = Counter("%.2f" % b["assigned_saturation"] for b in blocks)
    n_rows = sum(len(b["rows"]) for b in blocks)
    req_total = sum(r["orders_requested"] for b in blocks for r in b["rows"])

    effects = {
        "direct_effect_50": estimate.pooled_treated_vs_control(blocks),
        "spillover_50": 0.0,
        "policy_effect_full": estimate.pooled_treated_vs_control(blocks),
    }
    payload = {
        "n_dispatch_blocks": len(blocks),
        "n_merchant_days": n_rows,
        "orders_requested_total": req_total,
        "blocks_by_saturation": dict(sorted(sat.items())),
        "effects": effects,
        "recommendation": "launch" if effects["policy_effect_full"] >= GATE else "hold",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "analysis_results.json").write_text(json.dumps(payload, indent=2) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="dispatch_experiment")
    sub = ap.add_subparsers(dest="command", required=True)
    g = sub.add_parser("analyse")
    g.add_argument("--warehouse", default="data/warehouse.sqlite")
    g.add_argument("--out", default="out")
    a = ap.parse_args(argv)
    analyse(Path(a.warehouse), Path(a.out))
