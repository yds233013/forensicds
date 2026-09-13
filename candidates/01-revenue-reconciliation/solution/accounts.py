"""Customer attribution for recognized revenue.

Billing records money against billing accounts; Finance reports revenue by
customer (CRM account). Attribution follows docs/data/account_identity_standard.md:

  1. The owning CRM account of a billing account is the account recorded on the
     billing account in the billing system (billing_accounts.crm_account_id).
  2. The canonical account is reached by following effective migrations in the
     Billing Ops migration register (legacy -> successor) to the end of the chain.
     Scheduled migrations have no effect yet.
  3. Reporting attributes (name, segment, region) come from the canonical
     account's current CRM record.

The resulting mapping has exactly one row per billing account, so enrichment can
never change the grain of the monetary rows it is joined to.
"""
from __future__ import annotations

import pandas as pd

from revrec.extract import Sources

ACCOUNT_COLUMNS = ["account_id", "account_name", "segment", "region"]


class AccountResolutionError(RuntimeError):
    pass


def _successors(register: pd.DataFrame) -> dict[str, str]:
    effective = register[register["status"] != "scheduled"]
    successors: dict[str, str] = {}
    for legacy, successor in effective[["legacy_account_id", "successor_account_id"]].itertuples(index=False):
        if successors.get(legacy, successor) != successor:
            raise AccountResolutionError(f"account {legacy} has more than one successor in the migration register")
        successors[legacy] = successor
    return successors


def _canonical(account_id: str, successors: dict[str, str]) -> str:
    seen = {account_id}
    while account_id in successors:
        account_id = successors[account_id]
        if account_id in seen:
            raise AccountResolutionError(f"migration cycle involving {account_id}")
        seen.add(account_id)
    return account_id


def build_account_mapping(sources: Sources) -> pd.DataFrame:
    """One row per billing account: billing_account_id -> canonical account and its reporting attributes."""
    successors = _successors(sources.account_migrations)
    mapping = sources.billing_accounts[["billing_account_id", "crm_account_id"]].copy()
    mapping["account_id"] = [_canonical(a, successors) for a in mapping["crm_account_id"]]

    crm = sources.crm_accounts
    current = crm.loc[crm["is_current"] == "true", ACCOUNT_COLUMNS].drop_duplicates()
    if current["account_id"].duplicated().any():
        raise AccountResolutionError("CRM export has conflicting current records for an account")

    mapping = mapping.merge(current, on="account_id", how="left", validate="many_to_one")
    unresolved = mapping[mapping["segment"].isna()]
    if not unresolved.empty:
        raise AccountResolutionError(
            f"canonical accounts missing from CRM export: {sorted(unresolved['account_id'].unique())[:10]}")
    return mapping[["billing_account_id"] + ACCOUNT_COLUMNS]


def attribute_accounts(schedule: pd.DataFrame, sources: Sources) -> pd.DataFrame:
    """Attach canonical customer attributes to each revenue row without changing the row grain."""
    mapping = build_account_mapping(sources)
    rows = schedule.merge(mapping, on="billing_account_id", how="left", validate="many_to_one")
    if len(rows) != len(schedule):
        raise AccountResolutionError("account attribution changed the number of revenue rows")
    missing = rows["account_id"].isna()
    if missing.any():
        raise AccountResolutionError(
            f"revenue rows on unknown billing accounts: {sorted(rows.loc[missing, 'billing_account_id'].unique())}")
    return rows
