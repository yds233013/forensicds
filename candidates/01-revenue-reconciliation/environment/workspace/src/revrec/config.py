"""Pipeline configuration.

Paths in pipeline.toml are relative to the workspace root, i.e. the parent of the
directory containing the config file.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    root: Path
    billing_db: Path
    crm_accounts: Path
    account_migrations: Path
    warehouse_db: Path
    dashboard_dir: Path
    log_dir: Path
    revenue_line_types: tuple[str, ...]
    invoice_statuses: tuple[str, ...]
    reportable_period_statuses: tuple[str, ...]
    reporting_currency: str


def load_config(path: str | Path) -> Config:
    path = Path(path).resolve()
    raw = tomllib.loads(path.read_text())
    root = path.parent.parent
    src, out, rec = raw["sources"], raw["outputs"], raw["recognition"]
    return Config(
        root=root,
        billing_db=root / src["billing_db"],
        crm_accounts=root / src["crm_accounts"],
        account_migrations=root / src["account_migrations"],
        warehouse_db=root / out["warehouse_db"],
        dashboard_dir=root / out["dashboard_dir"],
        log_dir=root / out["log_dir"],
        revenue_line_types=tuple(rec["revenue_line_types"]),
        invoice_statuses=tuple(rec["invoice_statuses"]),
        reportable_period_statuses=tuple(rec["reportable_period_statuses"]),
        reporting_currency=rec["reporting_currency"],
    )
