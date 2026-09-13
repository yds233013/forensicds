#!/usr/bin/env python3
"""Build-time only: Finance close artifacts for the incident snapshot.

Writes Billing's "Recognized Revenue by Currency" exports for the last two
reportable periods and the Controllership tie-out note (comparing them with the
dashboard extract produced by the scheduled close run), and stamps the close-run
log with the scheduler's timestamps. Deleted from the image after the build.
"""
import csv
import re
import sqlite3
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

root = Path(sys.argv[1])
con = sqlite3.connect(root / "data/billing/billing.db")
months = [r[0] for r in con.execute(
    "SELECT period_month FROM accounting_periods WHERE status IN ('closed','closing') ORDER BY 1")][-2:]
fx = {(c, m): r for c, m, r in con.execute("SELECT currency, rate_month, usd_per_unit FROM fx_rates")}


def month_iter(s, e):
    m = s.replace(day=1)
    while m <= e:
        nxt = date(m.year + (m.month == 12), 1 if m.month == 12 else m.month + 1, 1)
        yield m, nxt - timedelta(days=1)
        m = nxt


gross = defaultdict(float)
credit = defaultdict(float)
for cur, amt, ss, se in con.execute("""
        SELECT i.currency, l.amount_minor, l.service_period_start, l.service_period_end
        FROM invoice_lines l JOIN invoices i USING (invoice_id)
        WHERE i.status = 'posted' AND l.line_type IN ('subscription','usage','onboarding','discount')"""):
    s, e = date.fromisoformat(ss), date.fromisoformat(se)
    total = (e - s).days + 1
    for m0, m1 in month_iter(s, e):
        key = f"{m0.year:04d}-{m0.month:02d}"
        if key in months:
            gross[(key, cur)] += amt / 100 * ((min(e, m1) - max(s, m0)).days + 1) / total
for cur, amt, issued in con.execute("""
        SELECT c.currency, c.amount_minor, c.issued_date FROM credit_notes c JOIN invoices i USING (invoice_id)
        WHERE c.status = 'issued' AND i.status = 'posted'"""):
    if issued[:7] in months:
        credit[(issued[:7], cur)] -= amt / 100

out = root / "reports/finance"
out.mkdir(parents=True, exist_ok=True)
totals = {}
for m in months:
    rows, tot = [], 0.0
    for cur in sorted({c for (mm, c) in list(gross) + list(credit) if mm == m}):
        g, c = gross[(m, cur)], credit[(m, cur)]
        usd = (g + c) * fx[(cur, m)]
        tot += usd
        rows.append([m, cur, f"{g:.2f}", f"{c:.2f}", f"{g + c:.2f}", f"{fx[(cur, m)]:.6f}", f"{usd:.2f}"])
    rows.append([m, "ALL", "", "", "", "", f"{tot:.2f}"])
    totals[m] = round(tot, 2)
    with open(out / f"billing_recognized_revenue_{m}.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["period_month", "currency", "recognized_invoice_lines_local", "credit_notes_local",
                    "recognized_revenue_local", "fx_usd_per_unit", "recognized_revenue_usd"])
        w.writerows(rows)

dash = {r["revenue_month"]: float(r["recognized_revenue_usd"])
        for r in csv.DictReader(open(root / "reports/exec_dashboard/recognized_revenue_by_month.csv"))}
prev, cur = months
lines = []
for m in months:
    var = dash[m] - totals[m]
    status = "Tied" if abs(var) < 0.01 else "NOT TIED"
    lines.append(f"| {m} | {totals[m]:,.2f} | {dash[m]:,.2f} | {var:,.2f} | {100 * var / totals[m]:.2f}% | {status} |")
(out / f"close_tieout_{cur}.md").write_text(f"""# Revenue tie-out - {cur} close

Prepared by: Finance Controllership (revenue close). Status: **dashboard held**.

Billing source: `billing_recognized_revenue_{prev}.csv`, `billing_recognized_revenue_{cur}.csv`
(Billing > Reports > Recognized Revenue by Currency, exported BD3).
Dashboard source: `reports/exec_dashboard/recognized_revenue_by_month.csv` from the
close run (scheduler run 10352).

| Period | Billing recognized revenue (USD) | Dashboard (USD) | Variance (USD) | Variance % | Status |
|--------|---------------------------------:|----------------:|---------------:|-----------:|--------|
{chr(10).join(lines)}

Notes
- {prev} tied to the cent at the {prev} close and still ties on this run.
- {cur}: the dashboard is above billing. We have not identified the cause. Billing
  is the source of truth; please do not ask Billing Ops to adjust invoices.
- Revenue Analytics to investigate and confirm corrected figures before the
  dashboard is released to the executive team.
""")

# Stamp the close-run log with the scheduler's wall-clock times (build runs later than the close).
log = root / "logs/pipeline/revrec_2026-09-03T06-10-44.log"
if log.exists():
    base = datetime(2026, 9, 3, 6, 10, 44)
    stamps = re.findall(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})", log.read_text(), flags=re.M)
    if stamps:
        t0 = datetime.strptime(stamps[0][0], "%Y-%m-%d %H:%M:%S")

        def restamp(mo):
            t = datetime.strptime(mo.group(1), "%Y-%m-%d %H:%M:%S")
            return (base + (t - t0)).strftime("%Y-%m-%d %H:%M:%S") + "," + mo.group(2)

        text = re.sub(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d{3})", restamp, log.read_text(), flags=re.M)
        text = re.sub(r"root=\S+\)", "root=/workspace)", text)
        log.write_text(text)
