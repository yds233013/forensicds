"""Validate the revenue pipeline output against billing (oracle helper).

Recomputes billing recognized revenue per month directly from billing.db with SQL
and checks the warehouse: fct grain unique and complete, monthly totals tie,
segment and account reports sum to the company total, every fct row's account is
its canonical account. With --diagnose, prints the gap and multiplied rows only.
"""
import sqlite3
import sys
from collections import defaultdict
from datetime import date, timedelta

import pandas as pd

DIAGNOSE = "--diagnose" in sys.argv
billing = sqlite3.connect("file:data/billing/billing.db?mode=ro", uri=True)
wh = sqlite3.connect("warehouse/analytics.db")

months = [r[0] for r in billing.execute(
    "SELECT period_month FROM accounting_periods WHERE status IN ('closed','closing') ORDER BY 1")]
fx = {(c, m): r for c, m, r in billing.execute("SELECT currency, rate_month, usd_per_unit FROM fx_rates")}
expected_keys, truth = set(), defaultdict(float)
for lid, cur, amt, ss, se in billing.execute("""
        SELECT l.invoice_line_id, i.currency, l.amount_minor, l.service_period_start, l.service_period_end
        FROM invoice_lines l JOIN invoices i USING (invoice_id)
        WHERE i.status = 'posted' AND l.line_type IN ('subscription','usage','onboarding','discount')"""):
    s, e = date.fromisoformat(ss), date.fromisoformat(se)
    total, m = (e - s).days + 1, s.replace(day=1)
    while m <= e:
        nxt = date(m.year + (m.month == 12), 1 if m.month == 12 else m.month + 1, 1)
        key = m.strftime("%Y-%m")
        if key in months:
            expected_keys.add(("invoice_line", lid, key))
            truth[key] += amt / 100 * ((min(e, nxt - timedelta(days=1)) - max(s, m)).days + 1) / total * fx[(cur, key)]
        m = nxt
for cid, cur, amt, issued in billing.execute("""
        SELECT c.credit_note_id, c.currency, c.amount_minor, c.issued_date FROM credit_notes c
        JOIN invoices i USING (invoice_id) WHERE c.status = 'issued' AND i.status = 'posted'"""):
    if issued[:7] in months:
        expected_keys.add(("credit_note", cid, issued[:7]))
        truth[issued[:7]] -= amt / 100 * fx[(cur, issued[:7])]

fct = pd.read_sql_query("SELECT * FROM fct_recognized_revenue", wh)
monthly = pd.read_sql_query("SELECT * FROM rpt_monthly_recognized_revenue", wh).set_index("revenue_month")
key = ["source_type", "source_id", "revenue_month"]
dup = fct[fct.duplicated(key, keep=False)]
print(f"{'month':8} {'billing':>14} {'pipeline':>14} {'diff':>12}")
for m in months:
    print(f"{m:8} {truth[m]:14,.2f} {monthly.loc[m, 'recognized_revenue_usd']:14,.2f} "
          f"{monthly.loc[m, 'recognized_revenue_usd'] - truth[m]:12,.2f}")
print(f"fct rows={len(fct)} expected={len(expected_keys)} multiplied source rows={dup[key].drop_duplicates().shape[0]}")
if DIAGNOSE:
    print(dup.groupby(["revenue_month", "billing_account_id"]).size().rename("rows").to_string())
    sys.exit(0)

problems = []
got_keys = set(map(tuple, fct[key].itertuples(index=False)))
if len(dup) or got_keys != expected_keys:
    problems.append("fct grain differs from billing source grain")
for m in months:
    if abs(monthly.loc[m, "recognized_revenue_usd"] - truth[m]) > 0.01:
        problems.append(f"{m} does not tie to billing")
seg = pd.read_sql_query("SELECT revenue_month, SUM(recognized_revenue_usd) v FROM rpt_segment_monthly_revenue GROUP BY 1", wh)
acc = pd.read_sql_query("SELECT revenue_month, SUM(recognized_revenue_usd) v FROM rpt_account_monthly_revenue GROUP BY 1", wh)
for df, name in ((seg, "segment"), (acc, "account")):
    for m, v in df.itertuples(index=False):
        if abs(v - monthly.loc[m, "recognized_revenue_usd"]) > 2.50:  # sum of cent-rounded rows
            problems.append(f"{name} report does not sum to company total in {m}")
reg = pd.read_csv("data/crm/account_migrations.csv", dtype=str, keep_default_na=False)
succ = dict(zip(reg.loc[reg.status != "scheduled", "legacy_account_id"], reg.loc[reg.status != "scheduled", "successor_account_id"]))
owner = dict(billing.execute("SELECT billing_account_id, crm_account_id FROM billing_accounts"))
def canon(a):
    seen = {a}
    while a in succ:
        a = succ[a]
        if a in seen:
            raise SystemExit(f"migration cycle at {a}")
        seen.add(a)
    return a
wrong = fct[fct["account_id"] != fct["billing_account_id"].map(lambda b: canon(owner[b]))]
if len(wrong):
    problems.append(f"{len(wrong)} fct rows not attributed to their canonical account")
if problems:
    print("VALIDATION FAILED:", *problems, sep="\n  ")
    sys.exit(1)
print("validation passed: grain preserved, all periods tie to billing, canonical attribution holds")
