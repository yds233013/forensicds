#!/usr/bin/env python3
"""Dev diagnostic: reconcile a workspace's warehouse output against the reference semantics.

usage: reconcile.py <workspace_root>
Prints monthly billing truth vs pipeline, the multiplied source rows, and account-level diffs.
"""
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / "candidates/01-revenue-reconciliation"
sys.path.insert(0, str(TASK / "tests"))
from reference import compute_expected  # noqa: E402

root = Path(sys.argv[1])
exp = compute_expected(root)
con = sqlite3.connect(root / "warehouse/analytics.db")
got_month = dict(con.execute("SELECT revenue_month, recognized_revenue_usd FROM rpt_monthly_recognized_revenue"))
print(f"{'month':8} {'billing_truth':>15} {'pipeline':>15} {'diff':>13} {'diff%':>7}")
for m in exp.months:
    t, g = exp.monthly[m], got_month.get(m, 0.0)
    print(f"{m:8} {t:15,.2f} {g:15,.2f} {g - t:13,.2f} {100 * (g - t) / t:7.3f}")

keys = Counter(con.execute("SELECT source_type, source_id, revenue_month FROM fct_recognized_revenue"))
dups = {k: c for k, c in keys.items() if c > 1}
missing = [k for k in exp.fct if k not in keys]
print(f"\nfct rows={sum(keys.values())} distinct keys={len(keys)} expected keys={len(exp.fct)} "
      f"multiplied keys={len(dups)} missing keys={len(missing)}")
by_month_ba = defaultdict(lambda: [0, 0.0])
for (st, sid, m), c in dups.items():
    row = exp.fct[(st, sid, m)]
    by_month_ba[(m, row["billing_account_id"])][0] += 1
    by_month_ba[(m, row["billing_account_id"])][1] += (c - 1) * row["amount_usd"]
for (m, ba), (n, extra) in sorted(by_month_ba.items()):
    print(f"  {m} {ba}: {n} source rows multiplied, excess ${extra:,.2f}")

got_acct = dict(((m, a), v) for m, a, v in con.execute(
    "SELECT revenue_month, account_id, recognized_revenue_usd FROM rpt_account_monthly_revenue"))
bad = [(k, exp.account_month.get(k, 0.0), got_acct.get(k, 0.0)) for k in set(exp.account_month) | set(got_acct)
       if abs(exp.account_month.get(k, 0.0) - got_acct.get(k, 0.0)) > 0.011]
print(f"\naccount-month mismatches: {len(bad)}; months affected: {sorted(Counter(k[0] for k, *_ in bad).items())}")
