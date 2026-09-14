"""Independent reference for G08: the accuracy mart's expected outputs, computed from the warehouse only.

Standard library only; shares no code with the generator.

- Closed months: kpi_close_log rows with closed_at <= as-of.
- Forecast in force: for each model, run date and forecast unit (region, portfolio, target date), the value from the
  latest issue published before 11:00 UK time on the run date.
- Portfolio classes: portfolio_membership effective on the target date.
- Actual: for each class, the IS run whose status at the close of the target's month was `published`; the example is
  unsettled if any class has none. A status counts from when it was recorded (the charge basis as it stood), not
  from the settlement time it takes effect.
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta


def _ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def _last_sunday(year: int, month: int) -> date:
    d = date(year, month, 31)
    return d - timedelta(days=(d.weekday() + 1) % 7)


def _uk_offset(utc: datetime) -> int:
    begin = datetime(utc.year, 3, _last_sunday(utc.year, 3).day, 1)
    end = datetime(utc.year, 10, _last_sunday(utc.year, 10).day, 1)
    return 1 if begin <= utc < end else 0


def gate_utc(run_date: str) -> datetime:
    local = datetime.strptime(run_date, "%Y-%m-%d").replace(hour=11)
    guess = local - timedelta(hours=1)
    return guess if _uk_offset(guess) == 1 else local


def expected(db_path, as_of: str) -> dict:
    as_of_t = _ts(as_of) if as_of.endswith("Z") else datetime.fromisoformat(as_of)
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        closes = {m: _ts(t) for m, t in con.execute("SELECT kpi_month, closed_at FROM kpi_close_log") if _ts(t) <= as_of_t}

        hist = defaultdict(list)
        for run_id, status, recorded in con.execute("SELECT run_id, status, recorded_at FROM run_status_history"):
            hist[run_id].append((_ts(recorded), status))
        for v in hist.values():
            v.sort()
        mwh = dict(con.execute("SELECT run_id, mwh FROM settlement_volumes"))
        is_runs = defaultdict(list)
        for run_id, region, cls, day, pub in con.execute(
                "SELECT run_id, region, settlement_class, delivery_date, published_at FROM settlement_runs WHERE run_type = 'IS'"):
            is_runs[(region, cls, day)].append((run_id, _ts(pub)))

        membership = defaultdict(list)
        for p, c, f, t in con.execute("SELECT portfolio, settlement_class, effective_from, effective_to FROM portfolio_membership"):
            membership[p].append((c, f, t))

        issue_time = {}
        for issue_id, t in con.execute("SELECT issue_id, issued_at FROM forecast_issues"):
            issue_time[issue_id] = _ts(t)
        locked = {}
        for model, run_date, issue_id, region, portfolio, target, value in con.execute(
                "SELECT i.model, i.run_date, i.issue_id, v.region, v.portfolio, v.target_date, v.mwh "
                "FROM forecast_values v JOIN forecast_issues i ON i.issue_id = v.issue_id"):
            if target[:7] not in closes:
                continue
            if issue_time[issue_id] >= gate_utc(run_date):
                continue
            k = (model, run_date, region, portfolio, target)
            if k not in locked or issue_time[issue_id] > issue_time[locked[k][0]]:
                locked[k] = (issue_id, value)
    finally:
        con.close()

    def status_at(run_id: str, t: datetime):
        s = None
        for ct, st in hist[run_id]:
            if ct <= t:
                s = st
            else:
                break
        return s

    def basis(region: str, cls: str, day: str, close: datetime):
        live = [rid for rid, pub in is_runs.get((region, cls, day), []) if pub <= close and status_at(rid, close) == "published"]
        if len(live) > 1:
            raise AssertionError(f"two charge-basis runs for {(region, cls, day)} at {close}: {live}")
        return live[0] if live else None

    examples = {}
    for (model, run_date, region, portfolio, target), (issue_id, fvalue) in locked.items():
        horizon = (date.fromisoformat(target) - date.fromisoformat(run_date)).days
        kpi_month = target[:7]
        close = closes[kpi_month]
        classes = sorted(c for c, f, t in membership[portfolio] if f <= target and (t is None or target <= t))
        ids = [basis(region, c, target, close) for c in classes]
        row = {"run_date": run_date, "issue_id": issue_id, "forecast_mwh": fvalue, "kpi_month": kpi_month}
        if classes and all(ids):
            actual = sum(mwh[i] for i in ids)
            row.update(status="scored", actual_run_ids=";".join(sorted(ids)), actual_mwh=actual,
                       abs_error_mwh=abs(fvalue - actual))
        else:
            row.update(status="unsettled", actual_run_ids="", actual_mwh=None, abs_error_mwh=None)
        examples[(model, region, portfolio, target, horizon)] = row

    monthly = {}
    for (model, region, portfolio, target, horizon), row in examples.items():
        k = (model, row["kpi_month"], portfolio, horizon)
        agg = monthly.setdefault(k, {"n_examples": 0, "n_scored": 0, "abs_error_mwh": 0.0, "actual_mwh": 0.0})
        agg["n_examples"] += 1
        if row["status"] == "scored":
            agg["n_scored"] += 1
            agg["abs_error_mwh"] += row["abs_error_mwh"]
            agg["actual_mwh"] += row["actual_mwh"]
    for agg in monthly.values():
        agg["wape"] = agg["abs_error_mwh"] / agg["actual_mwh"] if agg["n_scored"] else None

    by_unit = defaultdict(dict)
    for (model, region, portfolio, target, horizon), row in examples.items():
        if row["status"] == "scored":
            by_unit[(region, portfolio, target, horizon)][model] = row
    models = sorted({k[0] for k in examples})
    h2h = {}
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            both = [(u[a], u[b]) for u in by_unit.values() if a in u and b in u]
            if not both:
                continue
            ea = sum(x["abs_error_mwh"] for x, _ in both)
            aa = sum(x["actual_mwh"] for x, _ in both)
            eb = sum(y["abs_error_mwh"] for _, y in both)
            ab = sum(y["actual_mwh"] for _, y in both)
            months = sorted(x["kpi_month"] for x, _ in both)
            h2h[(a, b)] = {"n_pairs": len(both), "first_month": months[0], "last_month": months[-1],
                           "wape_a": ea / aa, "wape_b": eb / ab, "relative_change": (eb / ab) / (ea / aa) - 1}
    return {"closed_months": sorted(closes), "examples": examples, "monthly": monthly, "head_to_head": h2h}
