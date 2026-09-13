"""python -m metrics_layer build --config config/metrics_layer.toml [--as-of YYYY-MM-DD]"""
from __future__ import annotations

import argparse
from datetime import date

from metrics_layer.build import build
from metrics_layer.config import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="metrics_layer")
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build", help="rebuild semantic-layer models and board extracts")
    b.add_argument("--config", required=True)
    b.add_argument("--as-of", type=date.fromisoformat, default=None,
                   help="build date; reporting covers the last n_quarters complete quarters before it")
    args = parser.parse_args(argv)
    cfg = load_config(args.config)
    build(cfg, args.as_of or cfg.as_of)
    return 0
