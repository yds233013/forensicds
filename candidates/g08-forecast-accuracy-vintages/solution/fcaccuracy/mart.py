"""Evaluation examples as the forecast accuracy KPI defines them.

For each model, forecast run day and forecast unit (region, portfolio, delivery day):
  - forecast: the value locked at that run day's 11:00 UK gate closure, i.e. from the latest issue published before
    the gate that covers the unit (a scoped re-issue only replaces its own region);
  - portfolio classes: portfolio membership effective on the delivery day;
  - actual: per settlement class, the Initial Settlement run that was the charge basis when the delivery month's KPI
    was closed (published by the close and still published at the close, taking withdrawal notices and data corrections received by then
    into account). A forecast whose classes were not all settled at the close is unsettled.
"""
from __future__ import annotations

import sqlite3

import pandas as pd

KEY = ["model", "region", "portfolio", "target_date", "horizon"]
UNIT = ["model", "run_date", "region", "portfolio", "target_date"]


def _utc(col: pd.Series) -> pd.Series:
    return pd.to_datetime(col, utc=True)


def kpi_closes(con: sqlite3.Connection, closed_months: list[str]) -> pd.DataFrame:
    log = pd.read_sql_query("SELECT kpi_month, closed_at FROM kpi_close_log", con)
    log["closed_at"] = _utc(log["closed_at"])
    return log[log["kpi_month"].isin(closed_months)]


def locked_forecasts(con: sqlite3.Connection, closed_months: list[str]) -> pd.DataFrame:
    issues = pd.read_sql_query("SELECT issue_id, model, run_date, issued_at FROM forecast_issues", con)
    values = pd.read_sql_query(
        "SELECT issue_id, region, portfolio, target_date, mwh AS forecast_mwh FROM forecast_values", con)
    issues["issued_at"] = _utc(issues["issued_at"])
    gates = pd.DataFrame({"run_date": sorted(issues["run_date"].unique())})
    gates["gate_at"] = ((pd.to_datetime(gates["run_date"]) + pd.Timedelta(hours=11))
                        .dt.tz_localize("Europe/London").dt.tz_convert("UTC"))
    issues = issues.merge(gates, on="run_date")
    issues = issues[issues["issued_at"] < issues["gate_at"]]
    values = values[values["target_date"].str.slice(0, 7).isin(closed_months)]
    fc = values.merge(issues, on="issue_id")
    fc = fc.sort_values(["issued_at", "issue_id"]).drop_duplicates(UNIT, keep="last")
    fc["horizon"] = (pd.to_datetime(fc["target_date"]) - pd.to_datetime(fc["run_date"])).dt.days
    fc["kpi_month"] = fc["target_date"].str.slice(0, 7)
    return fc[UNIT + ["horizon", "kpi_month", "issue_id", "forecast_mwh"]]


def charge_basis_at_close(con: sqlite3.Connection, closes: pd.DataFrame) -> pd.DataFrame:
    runs = pd.read_sql_query(
        "SELECT r.run_id, r.region, r.settlement_class, r.delivery_date, r.published_at, v.mwh "
        "FROM settlement_runs r JOIN settlement_volumes v ON v.run_id = r.run_id WHERE r.run_type = 'IS'", con)
    runs["kpi_month"] = runs["delivery_date"].str.slice(0, 7)
    runs = runs.merge(closes, on="kpi_month")
    runs = runs[_utc(runs["published_at"]) <= runs["closed_at"]]
    # the charge basis as it stood at the close: status changes count from when they were recorded (a withdrawal notice
    # voids the run from its publication, but the charge stood until the notice arrived)
    hist = pd.read_sql_query("SELECT run_id, status, recorded_at FROM run_status_history", con)
    hist = hist.merge(runs[["run_id", "closed_at"]], on="run_id")
    hist["recorded_at"] = _utc(hist["recorded_at"])
    hist = hist[hist["recorded_at"] <= hist["closed_at"]].sort_values(["run_id", "recorded_at"])
    at_close = hist.drop_duplicates("run_id", keep="last")
    live = at_close.loc[at_close["status"] == "published", ["run_id"]]
    basis = runs.merge(live, on="run_id")
    dup = basis.duplicated(["region", "settlement_class", "delivery_date"], keep=False)
    if dup.any():
        raise RuntimeError(f"more than one charge-basis run at close for {int(dup.sum())} rows")
    return basis[["region", "settlement_class", "delivery_date", "run_id", "mwh"]]


def build_examples(con: sqlite3.Connection, closed_months: list[str]) -> pd.DataFrame:
    fc = locked_forecasts(con, closed_months)
    closes = kpi_closes(con, closed_months)
    basis = charge_basis_at_close(con, closes)
    memb = pd.read_sql_query("SELECT portfolio, settlement_class, effective_from, effective_to FROM portfolio_membership", con)

    units = fc[UNIT].drop_duplicates()
    cls = units.merge(memb, on="portfolio")
    cls = cls[(cls["effective_from"] <= cls["target_date"])
              & (cls["effective_to"].isna() | (cls["target_date"] <= cls["effective_to"]))]
    cls = cls.merge(basis, how="left", left_on=["region", "settlement_class", "target_date"],
                    right_on=["region", "settlement_class", "delivery_date"])
    cls = cls.sort_values(UNIT + ["run_id"])
    agg = cls.groupby(UNIT, as_index=False).agg(
        n_classes=("settlement_class", "size"), n_settled=("run_id", "count"), actual_mwh=("mwh", "sum"),
        actual_run_ids=("run_id", lambda s: ";".join(s.dropna())))

    ex = fc.merge(agg, on=UNIT, how="left")
    settled = ex["n_classes"].fillna(0).gt(0) & ex["n_settled"].eq(ex["n_classes"])
    ex["status"] = settled.map({True: "scored", False: "unsettled"})
    ex["actual_mwh"] = ex["actual_mwh"].where(settled)
    ex["actual_run_ids"] = ex["actual_run_ids"].where(settled, "")
    ex["abs_error_mwh"] = (ex["forecast_mwh"] - ex["actual_mwh"]).abs()
    return ex.sort_values(KEY).reset_index(drop=True)
