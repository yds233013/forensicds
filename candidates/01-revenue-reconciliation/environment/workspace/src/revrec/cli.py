"""Command line entry point: ``python -m revrec run --config config/pipeline.toml``."""
from __future__ import annotations

import argparse

from revrec.config import load_config
from revrec.pipeline import run_pipeline


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="revrec", description="Recognized revenue reporting pipeline")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Full refresh of warehouse revenue tables and dashboard extracts")
    run.add_argument("--config", required=True, help="Path to pipeline.toml")
    args = parser.parse_args(argv)

    if args.command == "run":
        run_pipeline(load_config(args.config))
    return 0
