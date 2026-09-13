"""Oracle helper: reconcile the built semantic layer with an independent Python computation of the handbook.

--diagnose also compares the layer's quarterly NRR and cohort size with the published FP&A figures. Always prints
customer_quarter rows whose movement, cohort flag or segment differ from a Python computation of the handbook; without
--diagnose exits non-zero if any differ.
"""
import csv
import sqlite3
import sys
from collections import defaultdict

wh = sqlite3.connect("file:data/warehouse.db?mode=ro", uri=True)
an = sqlite3.connect("analytics/analytics.db")
lines = defaultdict(list)
for acc, s, e, a in wh.execute("SELECT account_id, start_date, end_date, arr_usd FROM subscription_lines "
                               "WHERE line_type='recurring' AND arr_usd > 0 AND end_date > start_date"):
    lines[acc].append((s, e, a))
arr = lambda acc, d: round(sum(a for s, e, a in lines[acc] if s <= d < e), 2)  # noqa: E731
created = dict(wh.execute("SELECT account_id, substr(created_at, 1, 10) FROM crm_accounts"))

mismatch = defaultdict(int)
for quarter, s, e in an.execute("SELECT quarter, start_date, end_date FROM dim_quarters"):
    got = {r[0]: r[1:] for r in an.execute("SELECT account_id, movement, in_cohort, segment FROM customer_quarter WHERE quarter = ?", (quarter,))}
    for acc in lines:
        a0, a1 = arr(acc, s), arr(acc, e)
        if a0 <= 0 and a1 <= 0:
            continue
        if a0 > 0:
            mv = "churned" if a1 <= 0 else "expanded" if a1 > a0 else "contracted" if a1 < a0 else "retained"
            seg = "SMB" if a0 < 25000 else "Mid-Market" if a0 < 100000 else "Enterprise"
        else:
            mv = "reactivated" if any(ls < s for ls, _e, _a in lines[acc]) else "new"
            seg = None
        g = got.get(acc)
        if g is None:
            mismatch["missing row"] += 1
            continue
        if g[0] != mv:
            mismatch[f"movement {g[0]} should be {mv}" + (" (CRM account created before quarter)" if created[acc] < s and a0 <= 0 else "")] += 1
        if int(g[1]) != int(a0 > 0):
            mismatch["in_cohort"] += 1
        if g[2] != seg:
            mismatch["segment"] += 1
for k, v in sorted(mismatch.items(), key=lambda kv: -kv[1]):
    print(f"{v:6d}  {k}")
if "--diagnose" in sys.argv:
    pub = {r["quarter"]: r for r in csv.DictReader(open("reports/finance/retention_workbook_published.csv"))}
    for q, nrr, n in an.execute("SELECT quarter, nrr, cohort_customers FROM retention_quarterly ORDER BY quarter"):
        if q in pub:
            print(f"{q} layer NRR {nrr:.4f} cohort {n}  published NRR {float(pub[q]['nrr']):.4f} cohort {pub[q]['cohort_customers']}")
    sys.exit(0)
print("reconciliation:", "OK" if not mismatch else "FAILED")
sys.exit(1 if mismatch else 0)
