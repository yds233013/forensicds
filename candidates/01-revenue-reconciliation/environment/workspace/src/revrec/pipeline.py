"""Orchestration for the recognized revenue pipeline."""
from __future__ import annotations

import logging
import os
import sys
import time
from datetime import datetime, timezone

from revrec import __version__
from revrec.accounts import attribute_accounts
from revrec.checks import run_checks
from revrec.config import Config
from revrec.extract import load_sources
from revrec.fx import to_reporting_currency
from revrec.publish import build_reports, write_dashboard, write_warehouse
from revrec.recognition import build_schedule

log = logging.getLogger("revrec")


def _setup_logging(cfg: Config) -> None:
    run_ts = os.environ.get("REVREC_RUN_TS") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    root = logging.getLogger("revrec")
    root.handlers.clear()
    root.setLevel(logging.INFO)
    for handler in (logging.StreamHandler(sys.stdout), logging.FileHandler(cfg.log_dir / f"revrec_{run_ts}.log")):
        handler.setFormatter(fmt)
        root.addHandler(handler)


def run_pipeline(cfg: Config) -> None:
    _setup_logging(cfg)
    t0 = time.time()
    log.info("revrec %s starting full refresh (root=%s)", __version__, cfg.root)

    sources = load_sources(cfg)
    log.info("extract: invoice_lines=%d credit_notes=%d billing_accounts=%d crm_rows=%d migrations=%d",
             len(sources.invoice_lines), len(sources.credit_notes), len(sources.billing_accounts),
             len(sources.crm_accounts), len(sources.account_migrations))
    log.info("extract: reportable periods %s..%s (%d)", sources.reportable_months[0],
             sources.reportable_months[-1], len(sources.reportable_months))

    schedule = build_schedule(sources.invoice_lines, sources.credit_notes, sources.reportable_months)
    log.info("recognition: schedule_rows=%d", len(schedule))

    attributed = attribute_accounts(schedule, sources)
    fct = to_reporting_currency(attributed, sources.fx_rates)
    fct = fct.sort_values(["revenue_month", "source_type", "source_id"], kind="stable").reset_index(drop=True)

    run_checks(fct, sources)

    reports = build_reports(fct)
    write_warehouse(cfg.warehouse_db, fct, reports)
    write_dashboard(cfg.dashboard_dir, reports)
    log.info("publish: fct_recognized_revenue rows=%d -> %s", len(fct), cfg.warehouse_db.relative_to(cfg.root))
    latest = reports["rpt_monthly_recognized_revenue"].iloc[-1]
    log.info("publish: %s recognized_revenue_usd=%.2f", latest["revenue_month"], latest["recognized_revenue_usd"])
    log.info("done in %.1fs", time.time() - t0)
