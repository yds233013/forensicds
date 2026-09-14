"""Parameterised accuracy mart for the G08 mutation suite (dev tool, never shipped to agents).

With VARIANT = {} this is a correct, independently written mart (plain Python over sqlite3). Each key switches one
component to a realistic wrong repair. The mutation suite copies this file over `fcaccuracy/cli.py` with VARIANT set.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

VARIANT: dict = {}

V = {
    "actual": "basis_at_close",   # latest_current | est_first | is_current_status | is_scheduled | latest_any_at_close |
                                  # dc_any_type | is_pub_le_close_current_status | status_effective_from | status_by_effective_time | loaded_at |
                                  # is_at_asof | at_forecast_creation
    "unsettled": "status",        # drop | fallback_latest
    "gate": "uk",                 # utc | none | scheduled_only
    "lock_grain": "unit",         # issue
    "mapping": "target_date",     # current | run_date
    "kpi_month": "target",        # run
    "pairing": "paired",          # production_periods
    "drop_revised": False,
    "hardcoded_closes": None,     # {month: closed_at}
    "hardcoded_membership": None,  # [(portfolio, class, from, to)]
    "hardcoded_models": None,     # ["v3", "v4"]
    "hardcoded_horizons": None,   # [1..7]
    "hardcoded_as_of": None,
}


def ts(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")


def fts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


def uk_gate(run_date: str) -> datetime:
    from zoneinfo import ZoneInfo
    local = datetime.fromisoformat(run_date + "T11:00:00").replace(tzinfo=ZoneInfo("Europe/London"))
    return local.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)


def compute(db: Path, as_of: str) -> dict:
    cfg = dict(V)
    cfg.update(VARIANT)
    if cfg["hardcoded_as_of"]:
        as_of = cfg["hardcoded_as_of"]
    as_of_t = ts(as_of) if as_of.endswith("Z") else datetime.fromisoformat(as_of)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    q = lambda sql, *a: con.execute(sql, a).fetchall()  # noqa: E731

    if cfg["hardcoded_closes"]:
        closes = {m: ts(t) for m, t in cfg["hardcoded_closes"].items() if ts(t) <= as_of_t}
    else:
        closes = {r["kpi_month"]: ts(r["closed_at"]) for r in q("SELECT * FROM kpi_close_log") if ts(r["closed_at"]) <= as_of_t}

    runs = {r["run_id"]: dict(r) for r in q("SELECT r.*, v.mwh, v.loaded_at FROM settlement_runs r JOIN settlement_volumes v USING (run_id)")}
    hist = defaultdict(list)
    hist_eff = defaultdict(list)
    for r in q("SELECT * FROM run_status_history ORDER BY recorded_at"):
        hist[r["run_id"]].append((ts(r["recorded_at"]), r["status"]))
        hist_eff[r["run_id"]].append((ts(r["effective_from"]), ts(r["recorded_at"]), r["status"]))
    by_key = defaultdict(list)
    for r in runs.values():
        by_key[(r["region"], r["settlement_class"], r["delivery_date"])].append(r)

    def status_at(run, t):
        s = None
        for ct, st in hist[run["run_id"]]:
            if ct <= t:
                s = st
        return s

    def status_eff(run, t):
        s = None
        for eff, _rec, st in sorted(hist_eff[run["run_id"]]):
            if eff <= t:
                s = st
        return s

    def latest(lst):
        return max(lst, key=lambda x: x["published_at"]) if lst else None

    def actual_run(region, cls, day, close, issued_at):
        lst = by_key.get((region, cls, day), [])
        mode = cfg["actual"]
        if cfg["drop_revised"] and len([r for r in lst if r["run_type"] == "IS"]) > 1:
            return None
        if mode == "basis_at_close":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= close and status_at(r, close) == "published"])
        if mode == "latest_current":
            return latest([r for r in lst if r["run_type"] != "EST" and r["status"] == "published"])
        if mode == "est_first":
            return latest([r for r in lst if r["run_type"] == "EST"])
        if mode == "is_current_status":
            return latest([r for r in lst if r["run_type"] == "IS" and r["status"] == "published"])
        if mode == "is_scheduled":
            c = [r for r in lst if r["run_type"] == "IS" and r["reason"] == "scheduled"]
            return c[0] if c else None
        if mode == "latest_any_at_close":
            return latest([r for r in lst if r["run_type"] != "EST" and ts(r["published_at"]) <= close and status_at(r, close) == "published"])
        if mode == "dc_any_type":
            dc = [r for r in lst if r["reason"] == "data_correction" and ts(r["published_at"]) <= close and status_at(r, close) == "published"]
            if dc:
                return latest(dc)
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= close and status_at(r, close) == "published"])
        if mode == "is_pub_le_close_current_status":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= close and r["status"] == "published"])
        if mode == "status_effective_from":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= close
                           and (r["status"] == "published" or ts(r["status_effective_from"]) > close)])
        if mode == "is_latest_published_by_close":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= close])
        if mode == "status_by_effective_time":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= close and status_eff(r, close) == "published"])
        if mode == "loaded_at":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["loaded_at"]) <= close and status_at(r, close) == "published"])
        if mode == "is_at_asof":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= as_of_t and status_at(r, as_of_t) == "published"])
        if mode == "at_forecast_creation":
            return latest([r for r in lst if r["run_type"] == "IS" and ts(r["published_at"]) <= issued_at and status_at(r, issued_at) == "published"])
        raise ValueError(mode)

    if cfg["hardcoded_membership"]:
        memb = cfg["hardcoded_membership"]
    else:
        memb = [(r["portfolio"], r["settlement_class"], r["effective_from"], r["effective_to"]) for r in q("SELECT * FROM portfolio_membership")]
    current = defaultdict(list)
    for r in q("SELECT * FROM dim_portfolio"):
        current[r["portfolio"]].append(r["settlement_class"])

    def classes(portfolio, target, run_date):
        if cfg["mapping"] == "current":
            return sorted(current.get(portfolio, []))
        day = run_date if cfg["mapping"] == "run_date" else target
        return sorted(c for p, c, f, t in memb if p == portfolio and f <= day and (t is None or day <= t))

    issues = {r["issue_id"]: dict(r) for r in q("SELECT * FROM forecast_issues")}
    models_allowed = cfg["hardcoded_models"]
    cand = defaultdict(list)
    for r in q("SELECT * FROM forecast_values"):
        i = issues[r["issue_id"]]
        if models_allowed and i["model"] not in models_allowed:
            continue
        cand[(i["model"], i["run_date"])].append((i, r))

    chosen = {}
    for (model, run_date), lst in cand.items():
        gate = uk_gate(run_date) if cfg["gate"] in ("uk", "scheduled_only") else ts(run_date + "T11:00:00Z")
        if cfg["gate"] == "none":
            ok = lst
        elif cfg["gate"] == "scheduled_only":
            ok = [(i, r) for i, r in lst if i["issue_kind"] == "scheduled"]
        else:
            ok = [(i, r) for i, r in lst if ts(i["issued_at"]) < gate]
        if cfg["lock_grain"] == "issue" and ok:
            last = max(i["issued_at"] for i, _ in ok)
            ok = [(i, r) for i, r in ok if i["issued_at"] == last]
        for i, r in ok:
            k = (model, run_date, r["region"], r["portfolio"], r["target_date"])
            if k not in chosen or i["issued_at"] > chosen[k][0]["issued_at"]:
                chosen[k] = (i, r)

    examples = {}
    for (model, _run, region, portfolio, target), (i, r) in chosen.items():
        run_date = i["run_date"]
        horizon = (date.fromisoformat(target) - date.fromisoformat(run_date)).days
        if cfg["hardcoded_horizons"] and horizon not in cfg["hardcoded_horizons"]:
            continue
        kpi_month = target[:7] if cfg["kpi_month"] == "target" else run_date[:7]
        if kpi_month not in closes:
            continue
        close = closes[kpi_month]
        cls = classes(portfolio, target, run_date)
        picks = [actual_run(region, c, target, close, ts(i["issued_at"])) for c in cls]
        row = {"run_date": run_date, "issue_id": i["issue_id"], "forecast_mwh": r["mwh"], "kpi_month": kpi_month}
        if cls and all(picks):
            act = sum(p["mwh"] for p in picks)
            row.update(status="scored", actual_run_ids=";".join(sorted(p["run_id"] for p in picks)), actual_mwh=act,
                       abs_error_mwh=abs(r["mwh"] - act))
        else:
            if cfg["unsettled"] == "drop":
                continue
            if cfg["unsettled"] == "fallback_latest" and cls:
                fb = [latest([x for x in by_key.get((region, c, target), []) if x["run_type"] != "EST" and x["status"] == "published"]) for c in cls]
                if all(fb):
                    act = sum(p["mwh"] for p in fb)
                    row.update(status="scored", actual_run_ids=";".join(sorted(p["run_id"] for p in fb)), actual_mwh=act,
                               abs_error_mwh=abs(r["mwh"] - act))
                    examples[(model, region, portfolio, target, horizon)] = row
                    continue
            row.update(status="unsettled", actual_run_ids="", actual_mwh=None, abs_error_mwh=None)
        examples[(model, region, portfolio, target, horizon)] = row
    con.close()

    monthly = {}
    for (model, region, portfolio, target, horizon), row in examples.items():
        k = (model, row["kpi_month"], portfolio, horizon)
        a = monthly.setdefault(k, {"n_examples": 0, "n_scored": 0, "abs_error_mwh": 0.0, "actual_mwh": 0.0})
        a["n_examples"] += 1
        if row["status"] == "scored":
            a["n_scored"] += 1
            a["abs_error_mwh"] += row["abs_error_mwh"]
            a["actual_mwh"] += row["actual_mwh"]
    for a in monthly.values():
        a["wape"] = a["abs_error_mwh"] / a["actual_mwh"] if a["n_scored"] else None

    h2h = {}
    models = sorted({k[0] for k in examples})
    if cfg["pairing"] == "paired":
        units = defaultdict(dict)
        for (model, region, portfolio, target, horizon), row in examples.items():
            if row["status"] == "scored":
                units[(region, portfolio, target, horizon)][model] = row
        for x, a in enumerate(models):
            for b in models[x + 1:]:
                both = [(u[a], u[b]) for u in units.values() if a in u and b in u]
                if not both:
                    continue
                wa = sum(p["abs_error_mwh"] for p, _ in both) / sum(p["actual_mwh"] for p, _ in both)
                wb = sum(p["abs_error_mwh"] for _, p in both) / sum(p["actual_mwh"] for _, p in both)
                ms = sorted(p["kpi_month"] for p, _ in both)
                h2h[(a, b)] = {"n_pairs": len(both), "first_month": ms[0], "last_month": ms[-1], "wape_a": wa, "wape_b": wb,
                               "relative_change": wb / wa - 1}
    else:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        prod = {m: (f, t) for m, f, t in con.execute("SELECT model, production_from, production_to FROM models")}
        con.close()

        def own(model):
            f, t = prod.get(model, (None, None))
            return [row for (m, *_), row in examples.items() if m == model and row["status"] == "scored"
                    and (f is None or row["run_date"] >= f) and (t is None or row["run_date"] <= t)]
        for x, a in enumerate(models):
            for b in models[x + 1:]:
                ra, rb = own(a), own(b)
                if not ra or not rb:
                    continue
                wa = sum(p["abs_error_mwh"] for p in ra) / sum(p["actual_mwh"] for p in ra)
                wb = sum(p["abs_error_mwh"] for p in rb) / sum(p["actual_mwh"] for p in rb)
                ms = sorted(p["kpi_month"] for p in ra + rb)
                h2h[(a, b)] = {"n_pairs": len(rb), "first_month": ms[0], "last_month": ms[-1], "wape_a": wa, "wape_b": wb,
                               "relative_change": wb / wa - 1}
    return {"closed_months": sorted(closes), "examples": examples, "monthly": monthly, "head_to_head": h2h, "as_of": as_of}


EXAMPLE_COLS = ["model", "run_date", "issue_id", "region", "portfolio", "target_date", "horizon", "kpi_month",
                "forecast_mwh", "status", "actual_run_ids", "actual_mwh", "abs_error_mwh"]
MONTHLY_COLS = ["model", "kpi_month", "portfolio", "horizon", "n_examples", "n_scored", "abs_error_mwh", "actual_mwh", "wape"]


def fmt(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(round(v, 9))
    return str(v)


def write(res: dict, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "evaluation_examples.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(EXAMPLE_COLS)
        for (model, region, portfolio, target, horizon), row in sorted(res["examples"].items()):
            wr.writerow([model, row["run_date"], row["issue_id"], region, portfolio, target, horizon, row["kpi_month"],
                         fmt(row["forecast_mwh"]), row["status"], row["actual_run_ids"], fmt(row["actual_mwh"]),
                         fmt(row["abs_error_mwh"])])
    with open(out / "monthly_kpi.csv", "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(MONTHLY_COLS)
        for (model, m, p, h), a in sorted(res["monthly"].items()):
            wr.writerow([model, m, p, h, a["n_examples"], a["n_scored"], fmt(a["abs_error_mwh"]), fmt(a["actual_mwh"]), fmt(a["wape"])])
    summary = {"as_of": res["as_of"], "closed_months": res["closed_months"],
               "head_to_head": [dict(model_a=a, model_b=b, **v) for (a, b), v in sorted(res["head_to_head"].items())]}
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fcaccuracy")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--as-of", required=True)
    b.add_argument("--db", default="data/warehouse.sqlite")
    b.add_argument("--out", default="out/accuracy")
    a = ap.parse_args(argv)
    write(compute(Path(a.db), a.as_of), Path(a.out))


if __name__ == "__main__":
    main()
