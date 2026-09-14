"""Independent correct accuracy mart (dev tool): chronological replay.

Settlement: replay every Initial Settlement status event in time order and snapshot the published run per region,
class and delivery day whenever a KPI close is reached. Forecasts: replay issues in time order per run day until the
UK gate closes. Installed over `fcaccuracy/cli.py` by the mutation suite.
"""
from __future__ import annotations

import argparse
import csv
import heapq
import json
import sqlite3
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LONDON = ZoneInfo("Europe/London")


def parse(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def build(db: Path, as_of: str, out: Path) -> None:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cutoff = parse(as_of if ("Z" in as_of or "+" in as_of) else as_of + "Z")
    closes = sorted((parse(t), m) for m, t in con.execute("SELECT kpi_month, closed_at FROM kpi_close_log") if parse(t) <= cutoff)
    close_months = {m for _, m in closes}

    # ---- settlement replay
    run_key = {rid: (reg, cls, day) for rid, reg, cls, day in con.execute(
        "SELECT run_id, region, settlement_class, delivery_date FROM settlement_runs WHERE run_type = 'IS'")}
    mwh = dict(con.execute("SELECT run_id, mwh FROM settlement_volumes"))
    events = [(parse(t), rid, st) for rid, st, t in con.execute("SELECT run_id, status, recorded_at FROM run_status_history")
              if rid in run_key]
    events.sort()
    live = defaultdict(set)  # (region, class, day) -> published run ids
    basis_at = {}  # month -> {(region, class, day): run_id}
    ei = 0
    for close_t, month in closes:
        while ei < len(events) and events[ei][0] <= close_t:
            _t, rid, st = events[ei]
            if st == "published":
                live[run_key[rid]].add(rid)
            else:
                live[run_key[rid]].discard(rid)
            ei += 1
        snap = {}
        for k, ids in live.items():
            if k[2][:7] == month and ids:
                if len(ids) != 1:
                    raise RuntimeError(f"ambiguous charge basis {k}: {ids}")
                snap[k] = next(iter(ids))
        basis_at[month] = snap

    # ---- forecast replay
    issues = defaultdict(list)
    for iid, model, run_date, issued in con.execute("SELECT issue_id, model, run_date, issued_at FROM forecast_issues"):
        issues[(model, run_date)].append((parse(issued), iid))
    values = defaultdict(list)
    for iid, reg, port, tgt, v in con.execute("SELECT issue_id, region, portfolio, target_date, mwh FROM forecast_values"):
        values[iid].append((reg, port, tgt, v))
    membership = defaultdict(list)
    for port, cls, f, t in con.execute("SELECT portfolio, settlement_class, effective_from, effective_to FROM portfolio_membership"):
        membership[port].append((date.fromisoformat(f), date.fromisoformat(t) if t else date.max, cls))
    con.close()

    examples = []
    for (model, run_date), lst in sorted(issues.items()):
        gate = datetime.combine(date.fromisoformat(run_date), datetime.min.time()).replace(hour=11, tzinfo=LONDON)
        state = {}
        for issued, iid in sorted(lst):
            if issued >= gate:
                break
            for reg, port, tgt, v in values[iid]:
                state[(reg, port, tgt)] = (iid, v)
        for (reg, port, tgt), (iid, v) in state.items():
            month = tgt[:7]
            if month not in close_months:
                continue
            day = date.fromisoformat(tgt)
            cls = sorted(c for f, t, c in membership[port] if f <= day <= t)
            ids = [basis_at[month].get((reg, c, tgt)) for c in cls]
            ok = bool(cls) and all(ids)
            act = sum(mwh[i] for i in ids) if ok else None
            examples.append((model, reg, port, tgt, (day - date.fromisoformat(run_date)).days, run_date, iid, month, v,
                             "scored" if ok else "unsettled", ";".join(sorted(ids)) if ok else "", act,
                             abs(v - act) if ok else None))
    examples.sort()

    out.mkdir(parents=True, exist_ok=True)
    with open(out / "evaluation_examples.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "region", "portfolio", "target_date", "horizon", "run_date", "issue_id", "kpi_month",
                    "forecast_mwh", "status", "actual_run_ids", "actual_mwh", "abs_error_mwh"])
        for e in examples:
            w.writerow(["" if x is None else x for x in e])
    agg = defaultdict(lambda: [0, 0, 0.0, 0.0])
    units = defaultdict(dict)
    for (model, reg, port, tgt, h, run_date, iid, month, v, st, ids, act, err) in examples:
        a = agg[(model, month, port, h)]
        a[0] += 1
        if st == "scored":
            a[1] += 1
            a[2] += err
            a[3] += act
            units[(reg, port, tgt, h)][model] = (err, act, month)
    with open(out / "monthly_kpi.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "kpi_month", "portfolio", "horizon", "n_examples", "n_scored", "abs_error_mwh", "actual_mwh", "wape"])
        for k in sorted(agg):
            n, s, e, a = agg[k]
            w.writerow([*k, n, s, e, a, e / a if s else ""])
    models = sorted({e[0] for e in examples})
    h2h = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            both = [(u[a], u[b]) for u in units.values() if a in u and b in u]
            if not both:
                continue
            wa = sum(x[0] for x, _ in both) / sum(x[1] for x, _ in both)
            wb = sum(y[0] for _, y in both) / sum(y[1] for _, y in both)
            km = sorted(x[2] for x, _ in both)
            h2h.append({"model_a": a, "model_b": b, "n_pairs": len(both), "first_month": km[0], "last_month": km[-1],
                        "wape_a": wa, "wape_b": wb, "relative_change": wb / wa - 1})
    (out / "summary.json").write_text(json.dumps({"as_of": as_of, "closed_months": sorted(close_months),
                                                  "head_to_head": h2h}, indent=1))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fcaccuracy")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--as-of", required=True)
    b.add_argument("--db", default="data/warehouse.sqlite")
    b.add_argument("--out", default="out/accuracy")
    a = ap.parse_args(argv)
    build(Path(a.db), a.as_of, Path(a.out))


if __name__ == "__main__":
    main()
