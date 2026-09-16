"""`python -m recs_eval.cli ope --logs data/logs.sqlite --out out/ope`"""
from __future__ import annotations

import argparse
from pathlib import Path

from recs_eval import logs, metrics, replay, report


def ope(db: Path, out: Path) -> None:
    con = logs.connect(db)
    try:
        imp = logs.impressions(con)
        cand = logs.candidates(con)
    finally:
        con.close()

    targets = replay.target_slates(cand)
    decisions = imp.rename(columns={"serve_id": "decision_id"})[
        ["decision_id", "stream", "device", "served_at", "position", "item_id", "clicked"]
    ].rename(columns={"served_at": "decided_at"})
    gate = imp[imp["stream"] == "prod_rank"]
    values = metrics.with_intervals(metrics.ctr_at_5(replay.matched(gate, targets)))
    targets = targets.rename(columns={"serve_id": "decision_id"})
    report.write_all(out, decisions, targets, values)


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
