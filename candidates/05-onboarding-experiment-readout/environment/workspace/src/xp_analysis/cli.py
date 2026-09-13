"""python -m xp_analysis readout --config config/xp231.toml [--analysis-date YYYY-MM-DD]"""
from __future__ import annotations

import argparse
from datetime import date

from xp_analysis.config import load_config
from xp_analysis.pipeline import run_readout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="xp_analysis")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("readout", help="build analysis units, estimate the effect, write the readout")
    run.add_argument("--config", required=True)
    run.add_argument("--analysis-date", type=date.fromisoformat, default=None,
                     help="analysis date (defaults to [run].analysis_date)")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    run_readout(cfg, args.analysis_date or cfg.analysis_date)
    return 0
