"""`python -m recs_eval.cli ope --logs data/logs.sqlite --out out/ope`"""
from __future__ import annotations

import argparse
from pathlib import Path

from recs_eval import ope as ope_impl


def ope(db: Path, out: Path) -> None:
    from recs_eval import yaml_lite
    ttl = yaml_lite.ttl_seconds(Path("serving/config/serving.yaml"))
    ope_impl.run(db, out, ttl)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="recs_eval")
    sub = ap.add_subparsers(dest="command", required=True)
    r = sub.add_parser("ope", help="evaluate the candidate rankers and write the launch recommendation")
    r.add_argument("--logs", default="data/logs.sqlite")
    r.add_argument("--out", default="out/ope")
    args = ap.parse_args(argv)
    ope(Path(args.logs), Path(args.out))


if __name__ == "__main__":
    main()
