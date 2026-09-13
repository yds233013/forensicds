"""Write warehouse tables and executive dashboard extracts (full refresh)."""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

FCT_COLUMNS = [
    "revenue_month", "source_type", "source_id", "invoice_id", "billing_account_id", "account_id",
    "account_name", "segment", "region", "currency", "amount_local", "fx_usd_per_unit", "amount_usd",
]


def build_reports(fct: pd.DataFrame) -> dict[str, pd.DataFrame]:
    monthly = (
        fct.assign(
            gross_recognized_usd=fct["amount_usd"].where(fct["source_type"] == "invoice_line", 0.0),
            credit_notes_usd=fct["amount_usd"].where(fct["source_type"] == "credit_note", 0.0),
        )
        .groupby("revenue_month", as_index=False)
        .agg(gross_recognized_usd=("gross_recognized_usd", "sum"),
             credit_notes_usd=("credit_notes_usd", "sum"),
             recognized_revenue_usd=("amount_usd", "sum"))
        .sort_values("revenue_month")
    )
    account = (
        fct.groupby(["revenue_month", "account_id"], as_index=False)
        .agg(account_name=("account_name", "first"), segment=("segment", "first"), region=("region", "first"),
             recognized_revenue_usd=("amount_usd", "sum"))
        .sort_values(["revenue_month", "account_id"])
    )
    segment = (
        fct.groupby(["revenue_month", "segment"], as_index=False)
        .agg(recognized_revenue_usd=("amount_usd", "sum"))
        .sort_values(["revenue_month", "segment"])
    )
    for df in (monthly, account, segment):
        for col in df.columns:
            if col.endswith("_usd"):
                df[col] = df[col].round(2)
    return {
        "rpt_monthly_recognized_revenue": monthly.reset_index(drop=True),
        "rpt_account_monthly_revenue": account.reset_index(drop=True),
        "rpt_segment_monthly_revenue": segment.reset_index(drop=True),
    }


def write_warehouse(db_path: Path, fct: pd.DataFrame, reports: dict[str, pd.DataFrame]) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        fct[FCT_COLUMNS].to_sql("fct_recognized_revenue", con, if_exists="replace", index=False)
        for name, df in reports.items():
            df.to_sql(name, con, if_exists="replace", index=False)
        con.commit()
    finally:
        con.close()


def write_dashboard(out_dir: Path, reports: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    monthly = reports["rpt_monthly_recognized_revenue"][["revenue_month", "recognized_revenue_usd"]].copy()
    monthly["mom_change_pct"] = (monthly["recognized_revenue_usd"].pct_change() * 100).round(2)
    monthly.to_csv(out_dir / "recognized_revenue_by_month.csv", index=False)
    reports["rpt_segment_monthly_revenue"].to_csv(out_dir / "recognized_revenue_by_segment.csv", index=False)
    acct = reports["rpt_account_monthly_revenue"]
    latest = acct[acct["revenue_month"] == acct["revenue_month"].max()]
    latest.sort_values("recognized_revenue_usd", ascending=False).head(25).to_csv(
        out_dir / "top_accounts_latest_period.csv", index=False)
