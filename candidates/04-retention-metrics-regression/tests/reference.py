"""Independent reference for Task 04 (pure Python + sqlite3; shares no code with the workspace SQL models).

Definitions follow docs/finance/metrics_handbook.md:
  ARR(a, D)       sum of arr_usd of the account's recurring lines with start_date <= D < end_date
  quarter Q       [S, E) where S = first day of the quarter and E = first day of the next quarter
  cohort(Q)       accounts with ARR(S) > 0
  movement        cohort: churned (ARR(E) = 0) / expanded (ARR(E) > ARR(S)) / contracted (ARR(E) < ARR(S)) / retained
                  non-cohort with ARR(E) > 0: reactivated if the account had ARR on any day before S, else new
  segment         cohort only, from ARR(S): SMB < 25,000 <= Mid-Market < 100,000 <= Enterprise
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

SEGMENTS = [("SMB", 0, 25_000), ("Mid-Market", 25_000, 100_000), ("Enterprise", 100_000, float("inf"))]
MOVEMENTS = ["new", "reactivated", "expanded", "contracted", "churned", "retained"]


def quarter_start(y: int, q: int) -> date:
    return date(y, 3 * (q - 1) + 1, 1)


def quarters(last_complete_before: date, n: int) -> list[tuple[str, date, date]]:
    y, q = last_complete_before.year, (last_complete_before.month - 1) // 3 + 1
    out = []
    for _ in range(n):
        q -= 1
        if q == 0:
            y, q = y - 1, 4
        s = quarter_start(y, q)
        e = quarter_start(y + (q == 4), 1 if q == 4 else q + 1)
        out.append((f"{y}-Q{q}", s, e))
    return sorted(out, key=lambda t: t[1])


def load_lines(root: Path):
    con = sqlite3.connect(f"file:{Path(root) / 'data/warehouse.db'}?mode=ro", uri=True)
    lines = defaultdict(list)
    for acc, s, e, arr in con.execute("SELECT account_id, start_date, end_date, arr_usd FROM subscription_lines "
                                      "WHERE line_type = 'recurring' AND arr_usd > 0 AND end_date > start_date"):
        lines[acc].append((date.fromisoformat(s), date.fromisoformat(e), arr))
    con.close()
    return lines


def arr_at(ls, day: date) -> float:
    return round(sum(a for s, e, a in ls if s <= day < e), 2)


def segment(arr: float) -> str:
    return next(name for name, lo, hi in SEGMENTS if lo <= arr < hi)


def compute(root: Path, as_of: date, n_quarters: int = 8) -> dict:
    lines = load_lines(root)
    qs = quarters(as_of, n_quarters)
    rows, quarterly, by_segment = [], [], []
    for name, s, e in qs:
        qrows = []
        for acc in sorted(lines):
            ls = lines[acc]
            a0, a1 = arr_at(ls, s), arr_at(ls, e)
            if a0 <= 0 and a1 <= 0:
                continue
            if a0 > 0:
                mv = "churned" if a1 <= 0 else "expanded" if a1 > a0 else "contracted" if a1 < a0 else "retained"
                seg = segment(a0)
            else:
                mv = "reactivated" if any(ls_s < s for ls_s, _e, _a in ls) else "new"
                seg = None
            qrows.append(dict(quarter=name, account_id=acc, start_arr=a0, end_arr=a1, movement=mv, segment=seg))
        rows += qrows
        cohort = [r for r in qrows if r["start_arr"] > 0]

        def agg(group):
            start = sum(r["start_arr"] for r in group)
            return dict(cohort_customers=len(group), starting_arr=start,
                        cohort_ending_arr=sum(r["end_arr"] for r in group),
                        nrr=sum(r["end_arr"] for r in group) / start if start else None,
                        grr=sum(min(r["end_arr"], r["start_arr"]) for r in group) / start if start else None,
                        churned_customers=sum(r["movement"] == "churned" for r in group),
                        logo_churn_rate=sum(r["movement"] == "churned" for r in group) / len(group) if group else None)

        q = dict(quarter=name, **agg(cohort))
        q.update(new_arr=sum(r["end_arr"] for r in qrows if r["movement"] == "new"),
                 reactivated_arr=sum(r["end_arr"] for r in qrows if r["movement"] == "reactivated"),
                 expansion_arr=sum(r["end_arr"] - r["start_arr"] for r in cohort if r["end_arr"] > r["start_arr"]),
                 contraction_arr=sum(r["start_arr"] - r["end_arr"] for r in cohort if 0 < r["end_arr"] < r["start_arr"]),
                 churned_arr=sum(r["start_arr"] for r in cohort if r["end_arr"] <= 0),
                 ending_arr=sum(r["end_arr"] for r in qrows),
                 new_customers=sum(r["movement"] == "new" for r in qrows),
                 reactivated_customers=sum(r["movement"] == "reactivated" for r in qrows))
        quarterly.append(q)
        for segname, _lo, _hi in SEGMENTS:
            g = [r for r in cohort if r["segment"] == segname]
            by_segment.append(dict(quarter=name, segment=segname, **agg(g)))
    return dict(quarters=qs, customer_quarter=rows, quarterly=quarterly, by_segment=by_segment)
