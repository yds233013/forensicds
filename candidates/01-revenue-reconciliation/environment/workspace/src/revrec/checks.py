"""Data quality gates run before anything is published."""
from __future__ import annotations

import logging

import pandas as pd

from revrec.extract import Sources

log = logging.getLogger("revrec.checks")

KNOWN_SEGMENTS = {"Enterprise", "Mid-Market", "SMB"}


class DataQualityError(RuntimeError):
    pass


def run_checks(fct: pd.DataFrame, sources: Sources) -> None:
    failures: list[str] = []
    passed = 0

    def check(name: str, ok: bool, detail: str = "") -> None:
        nonlocal passed
        if ok:
            passed += 1
            log.info("DQ pass: %s", name)
        else:
            failures.append(f"{name}: {detail}")
            log.error("DQ FAIL: %s %s", name, detail)

    check("account_id populated", fct["account_id"].notna().all() and (fct["account_id"] != "").all(),
          f"{int(fct['account_id'].isna().sum())} rows without account")
    check("fx rate available", fct["fx_usd_per_unit"].notna().all(),
          f"{int(fct['fx_usd_per_unit'].isna().sum())} rows without fx rate")
    unknown = set(fct["segment"].dropna()) - KNOWN_SEGMENTS
    check("segments recognized", not unknown, f"unknown segments {sorted(unknown)}")
    months = set(fct["revenue_month"])
    missing = [m for m in sources.reportable_months if m not in months]
    check("every reportable period has revenue", not missing, f"missing {missing}")
    check("revenue months are reportable", months <= set(sources.reportable_months),
          f"unexpected {sorted(months - set(sources.reportable_months))}")

    reg = sources.account_migrations
    effective = reg[reg["status"] != "scheduled"]
    crm_ids = set(sources.crm_accounts["account_id"])
    dangling = sorted(set(effective["successor_account_id"]) - crm_ids)
    if dangling:
        log.warning("migration register references successor accounts missing from CRM export: %s", dangling)

    if failures:
        raise DataQualityError("; ".join(failures))
    log.info("DQ checks passed (%d)", passed)
