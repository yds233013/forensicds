"""Independent correct accuracy mart (dev tool): the vintage logic is one SQLite query with window functions.

Python only prepares the gate-closure and KPI-close instants and writes the outputs. Installed over
`fcaccuracy/cli.py` by the mutation suite.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

QUERY = """
WITH locked AS (
  SELECT i.model, i.run_date, v.region, v.portfolio, v.target_date, i.issue_id, v.mwh,
         ROW_NUMBER() OVER (PARTITION BY i.model, i.run_date, v.region, v.portfolio, v.target_date
                            ORDER BY i.issued_at DESC, i.issue_id DESC) AS rn
  FROM forecast_values v
  JOIN forecast_issues i ON i.issue_id = v.issue_id
  JOIN temp.gates g ON g.run_date = i.run_date
  JOIN temp.closes c ON c.kpi_month = substr(v.target_date, 1, 7)
  WHERE i.issued_at < g.gate_at
),
ex AS (SELECT * FROM locked WHERE rn = 1),
classes AS (
  SELECT e.*, m.settlement_class
  FROM ex e
  LEFT JOIN portfolio_membership m
    ON m.portfolio = e.portfolio AND m.effective_from <= e.target_date
   AND (m.effective_to IS NULL OR e.target_date <= m.effective_to)
),
status_at_close AS (
  SELECT h.run_id, h.status,
         ROW_NUMBER() OVER (PARTITION BY h.run_id ORDER BY h.recorded_at DESC) AS rn
  FROM run_status_history h
  JOIN settlement_runs r ON r.run_id = h.run_id AND r.run_type = 'IS'
  JOIN temp.closes c ON c.kpi_month = substr(r.delivery_date, 1, 7)
  WHERE h.recorded_at <= c.closed_at
),
basis AS (
  SELECT r.region, r.settlement_class, r.delivery_date, r.run_id, sv.mwh
  FROM settlement_runs r
  JOIN settlement_volumes sv ON sv.run_id = r.run_id
  JOIN status_at_close s ON s.run_id = r.run_id AND s.rn = 1 AND s.status = 'published'
)
SELECT c.model, c.run_date, c.issue_id, c.region, c.portfolio, c.target_date, c.mwh AS forecast_mwh,
       COUNT(c.settlement_class) AS n_classes, COUNT(b.run_id) AS n_settled, SUM(b.mwh) AS actual_mwh,
       GROUP_CONCAT(b.run_id, ';') AS run_ids
FROM classes c
LEFT JOIN basis b
  ON b.region = c.region AND b.settlement_class = c.settlement_class AND b.delivery_date = c.target_date
GROUP BY c.model, c.run_date, c.issue_id, c.region, c.portfolio, c.target_date, c.mwh
"""


def z(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build(db: Path, as_of: str, out: Path) -> None:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    con.execute("CREATE TEMP TABLE gates (run_date TEXT PRIMARY KEY, gate_at TEXT)")
    con.execute("CREATE TEMP TABLE closes (kpi_month TEXT PRIMARY KEY, closed_at TEXT)")
    london = ZoneInfo("Europe/London")
    run_dates = [r[0] for r in con.execute("SELECT DISTINCT run_date FROM forecast_issues")]
    con.executemany("INSERT INTO temp.gates VALUES (?, ?)",
                    [(d, z(datetime.fromisoformat(d + "T11:00:00").replace(tzinfo=london))) for d in run_dates])
    cutoff = z(datetime.fromisoformat(as_of.replace("Z", "+00:00")))
    con.execute("INSERT INTO temp.closes SELECT kpi_month, closed_at FROM kpi_close_log WHERE closed_at <= ?", (cutoff,))
    months = sorted(r[0] for r in con.execute("SELECT kpi_month FROM temp.closes"))
    rows = con.execute(QUERY).fetchall()
    con.close()

    examples = []
    for model, run_date, issue_id, region, portfolio, target, fmwh, n_cls, n_set, act, ids in rows:
        horizon = (datetime.fromisoformat(target) - datetime.fromisoformat(run_date)).days
        ok = n_cls > 0 and n_cls == n_set
        examples.append({"model": model, "run_date": run_date, "issue_id": issue_id, "region": region,
                         "portfolio": portfolio, "target_date": target, "horizon": horizon, "kpi_month": target[:7],
                         "forecast_mwh": fmwh, "status": "scored" if ok else "unsettled",
                         "actual_run_ids": ";".join(sorted(ids.split(";"))) if ok else "",
                         "actual_mwh": act if ok else None, "abs_error_mwh": abs(fmwh - act) if ok else None})
    examples.sort(key=lambda e: (e["model"], e["region"], e["portfolio"], e["target_date"], e["horizon"]))

    monthly = defaultdict(lambda: [0, 0, 0.0, 0.0])
    for e in examples:
        m = monthly[(e["model"], e["kpi_month"], e["portfolio"], e["horizon"])]
        m[0] += 1
        if e["status"] == "scored":
            m[1] += 1
            m[2] += e["abs_error_mwh"]
            m[3] += e["actual_mwh"]
    units = defaultdict(dict)
    for e in examples:
        if e["status"] == "scored":
            units[(e["region"], e["portfolio"], e["target_date"], e["horizon"])][e["model"]] = e
    models = sorted({e["model"] for e in examples})
    h2h = []
    for i, a in enumerate(models):
        for b in models[i + 1:]:
            both = [(u[a], u[b]) for u in units.values() if a in u and b in u]
            if both:
                wa = sum(x["abs_error_mwh"] for x, _ in both) / sum(x["actual_mwh"] for x, _ in both)
                wb = sum(y["abs_error_mwh"] for _, y in both) / sum(y["actual_mwh"] for _, y in both)
                km = sorted(x["kpi_month"] for x, _ in both)
                h2h.append({"model_a": a, "model_b": b, "n_pairs": len(both), "first_month": km[0], "last_month": km[-1],
                            "wape_a": wa, "wape_b": wb, "relative_change": wb / wa - 1})

    out.mkdir(parents=True, exist_ok=True)
    cols = ["model", "run_date", "issue_id", "region", "portfolio", "target_date", "horizon", "kpi_month",
            "forecast_mwh", "status", "actual_run_ids", "actual_mwh", "abs_error_mwh"]
    with open(out / "evaluation_examples.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for e in examples:
            w.writerow({k: ("" if e[k] is None else e[k]) for k in cols})
    with open(out / "monthly_kpi.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "kpi_month", "portfolio", "horizon", "n_examples", "n_scored", "abs_error_mwh", "actual_mwh", "wape"])
        for k in sorted(monthly):
            n, s, ae, ac = monthly[k]
            w.writerow([*k, n, s, ae, ac, (ae / ac) if s else ""])
    (out / "summary.json").write_text(json.dumps({"as_of": as_of, "closed_months": months, "head_to_head": h2h}, indent=2))


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
