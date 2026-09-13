"""python -m lead_eval run --config config/evaluation.toml [--as-of YYYY-MM-DD]"""
from __future__ import annotations

import argparse
from datetime import date

from lead_eval.config import load_config
from lead_eval.pipeline import run_evaluation


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lead_eval")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="build the evaluation cohort, compute metrics, write reports")
    run.add_argument("--config", required=True)
    run.add_argument("--as-of", type=date.fromisoformat, default=None,
                     help="evaluation date (defaults to [run].as_of); the scheduler passes the 1st of each month")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    run_evaluation(cfg, args.as_of or cfg.as_of)
    return 0
