"""Command line interface.

    python -m renewal_risk run      --config config/pipeline.toml [--as-of YYYY-MM-DD]
    python -m renewal_risk features --config config/pipeline.toml [--as-of YYYY-MM-DD]
    python -m renewal_risk score    --config config/pipeline.toml --score-date YYYY-MM-DD
"""
from __future__ import annotations

import argparse
from datetime import date

from renewal_risk.config import load_config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="renewal_risk")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_ in (("run", "build examples and features, train, evaluate, report"),
                        ("features", "build examples and features only")):
        p = sub.add_parser(name, help=help_)
        p.add_argument("--config", required=True)
        p.add_argument("--as-of", type=date.fromisoformat, default=None,
                       help="training run date (defaults to [run].as_of in the config)")
    s = sub.add_parser("score", help="score renewals due horizon_days after --score-date with the trained model")
    s.add_argument("--config", required=True)
    s.add_argument("--score-date", type=date.fromisoformat, required=True)
    args = parser.parse_args(argv)
    cfg = load_config(args.config)

    if args.command == "run":
        from renewal_risk.pipeline import run_training
        run_training(cfg, args.as_of or cfg.as_of)
    elif args.command == "features":
        from renewal_risk.pipeline import run_features
        run_features(cfg, args.as_of or cfg.as_of)
    elif args.command == "score":
        from renewal_risk.scoring import score_renewals
        score_renewals(cfg, args.score_date)
    return 0
