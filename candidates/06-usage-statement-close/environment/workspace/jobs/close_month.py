"""python -m jobs.close_month --month YYYY-MM

Rebuilds the usage mart from the landing zone and assembles the usage statement for the month.
"""
from __future__ import annotations

import argparse
import configparser
import logging
from pathlib import Path

from metering.landing import read_deliveries
from metering.normalize import normalize
from metering.usage_mart import build_usage_mart
from statements.assemble import assemble_statement
from statements.calendar import statement_close
from statements.export import write_statement
from statements.terms import load_rate_cards

ROOT = Path(__file__).resolve().parents[1]
log = logging.getLogger("close_month")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="close_month")
    ap.add_argument("--month", required=True, help="statement month, YYYY-MM")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / "config/pipeline.ini")
    paths = cfg["paths"]
    out = ROOT / paths["out"]

    deliveries = read_deliveries(ROOT / paths["landing"])
    usage = normalize(deliveries, cfg.getint("collector", "redelivery_ttl_hours"))
    log.info("deliveries=%d usage_rows=%d", len(deliveries), len(usage))

    mart = build_usage_mart(usage)
    (out / "usage_mart").mkdir(parents=True, exist_ok=True)
    mart.to_csv(out / "usage_mart/usage_by_service_month.csv", index=False, lineterminator="\n")

    close_hours = cfg.getint("statements", "close_hours_after_month_end")
    cards = load_rate_cards(ROOT / paths["rate_cards"])
    lines = assemble_statement(usage, cards, args.month, close_hours)
    write_statement(lines, out / "statements" / args.month, args.month, statement_close(args.month, close_hours))
    log.info("statement %s: %d lines", args.month, len(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
