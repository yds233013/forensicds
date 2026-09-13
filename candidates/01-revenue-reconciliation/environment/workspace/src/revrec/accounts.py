"""Customer attribution for recognized revenue.

Billing records money against billing accounts; Finance reports revenue by
customer (CRM account). The CRM export is a slowly changing history of account
records and the billing accounts linked to them, so each revenue row is matched
to the account record in effect at the end of its revenue month. Accounts that
have been migrated are reported under their successor account.
"""
from __future__ import annotations

import pandas as pd

from revrec.extract import Sources

ACCOUNT_COLUMNS = ["account_id", "account_name", "segment", "region"]


def _account_history(crm: pd.DataFrame) -> pd.DataFrame:
    hist = crm[[
        "billing_account_id", "account_id", "record_version", "valid_from", "valid_to", "account_name",
        "segment", "region", "lifecycle_status", "successor_account_id",
    ]].copy()
    hist["valid_from"] = pd.to_datetime(hist["valid_from"])
    hist["valid_to"] = pd.to_datetime(hist["valid_to"].replace("", None))
    return hist


def attribute_accounts(schedule: pd.DataFrame, sources: Sources) -> pd.DataFrame:
    """Attach customer account attributes to each revenue row."""
    hist = _account_history(sources.crm_accounts)
    rows = schedule.merge(hist, on="billing_account_id", how="left")

    in_effect = (rows["valid_from"] <= rows["period_end"]) & (
        rows["valid_to"].isna() | (rows["valid_to"] >= rows["period_end"])
    )
    rows = rows[in_effect].copy()

    successor = rows["successor_account_id"].replace("", pd.NA)
    rows["account_id"] = successor.fillna(rows["account_id"])

    return rows.drop(columns=["record_version", "valid_from", "valid_to", "lifecycle_status",
                              "successor_account_id"]).reset_index(drop=True)
