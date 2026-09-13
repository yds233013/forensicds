#!/usr/bin/env python3
"""Build-time only: reproduce the retention reporting history inside the workspace.

- FP&A retention workbook figures published for 2024-Q1 .. 2025-Q4 (workbook logic re-implemented here from the
  handbook definitions, independently of the semantic-layer SQL). Each quarter was published from the billing data
  as known on its publication date (quarter end + 12 days): renewals signed later and backdated to the term start
  were not yet in billing, so published figures differ slightly from a restatement on today's extract.
- The current semantic-layer build (board extracts) for the default as-of date.
- Stakeholder notes and logs quoting those numbers.
Deleted from the image after the build.
"""
import csv
import sqlite3
import subprocess
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(sys.argv[1])
con = sqlite3.connect(ROOT / "data/warehouse.db")
lines = defaultdict(list)
for acc, s, e, arr, signed in con.execute("SELECT l.account_id, l.start_date, l.end_date, l.arr_usd, c.signed_at "
                                          "FROM subscription_lines l JOIN contracts c USING (contract_id) "
                                          "WHERE l.line_type='recurring' AND l.arr_usd > 0"):
    lines[acc].append((s, e, arr, signed))
KNOWN_BY = None


def arr(acc, day):
    return round(sum(a for s, e, a, signed in lines[acc] if s <= day < e and signed <= KNOWN_BY), 2)


def qbounds(y, q):
    s = date(y, 3 * q - 2, 1)
    e = date(y + 1, 1, 1) if q == 4 else date(y, 3 * q + 1, 1)
    return s.isoformat(), e.isoformat()


published = []
for y, q in [(2024, 1), (2024, 2), (2024, 3), (2024, 4), (2025, 1), (2025, 2), (2025, 3), (2025, 4)]:
    s, e = qbounds(y, q)
    KNOWN_BY = (date.fromisoformat(e) + timedelta(days=12)).isoformat()
    start = end = floor = n = churned = 0
    for acc in lines:
        a0 = arr(acc, s)
        if a0 <= 0:
            continue
        a1 = arr(acc, e)
        n += 1
        start += a0
        end += a1
        floor += min(a0, a1)
        churned += a1 <= 0
    published.append((f"{y}-Q{q}", n, round(start), round(end / start, 4), round(floor / start, 4), round(churned / n, 4)))
fin = ROOT / "reports/finance"
fin.mkdir(parents=True, exist_ok=True)
with open(fin / "retention_workbook_published.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["quarter", "cohort_customers", "starting_arr", "nrr", "grr", "logo_churn_rate", "published_in"])
    for row in published:
        w.writerow(list(row) + [f"FY{row[0][:4]} board pack"])

subprocess.run([sys.executable, "-m", "metrics_layer", "build", "--config", "config/metrics_layer.toml"], cwd=ROOT,
               env={"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin:/usr/local/bin"}, check=True, capture_output=True)
board = {r["quarter"]: r for r in csv.DictReader(open(ROOT / "reports/board/retention_quarterly.csv"))}
pub = {r[0]: r for r in published}
q4, q1, q2 = board["2025-Q4"], board["2026-Q1"], board["2026-Q2"]
(ROOT / "notes").mkdir(parents=True, exist_ok=True)
(ROOT / "notes/2026-07-28_cfo_retention_question.md").write_text(f"""# Q2 board pack - retention numbers

From: CFO. To: FP&A, Analytics Engineering. 2026-07-28.

The Q2 board pack draft (from the semantic layer) shows quarterly NRR of {float(q2['nrr']):.1%} for Q2, after
{float(q1['nrr']):.1%} for Q1, which was the first quarter we published from the new layer in April. The draft's
trend chart also restates last year: Q4 FY2025 now shows {float(q4['nrr']):.1%} NRR, but we published
{pub['2025-Q4'][3]:.1%} to the board in February (`reports/finance/retention_workbook_published.csv`).

Sales also reported record new-logo signings in Q1 and Q2, yet the ARR bridge shows new ARR of only
${float(q1['new_arr']) / 1e6:.2f}M in Q1 and ${float(q2['new_arr']) / 1e6:.2f}M in Q2.

Sales Ops points to the 2025 price increase and February's large enterprise expansion. Either way, I can't take a
restatement of published numbers to the board without understanding it. Please get to the bottom of this and fix the layer before
the board meeting on 2026-08-20.
""")
logs = ROOT / "logs"
logs.mkdir(exist_ok=True)
(logs / "deployments.csv").write_text("""deployed_at,service,version,summary,ticket
2025-03-31T09:00:00Z,crm,abm-import,ABM target account list imports enabled,SOPS-301
2025-07-01T00:00:00Z,billing,pricebook-2025,2025 price book on renewals (+7%),PRC-12
2025-09-01T10:15:00Z,metrics_layer,1.0.0,ARR dashboard models,AE-88
2025-11-01T06:00:00Z,billing,bill-77,Core platform lines split into platform and seat lines,BILL-77
2026-01-15T11:40:00Z,metrics_layer,1.3.0,Set-based arr_boundaries; cent rounding,AE-102
2026-02-10T08:30:00Z,sales,deal-desk,Enterprise expansion booked ($1.15M ARR),DD-2026-014
2026-03-01T09:00:00Z,sales-ops,reorg-2026,Renewal owner re-mapping after Sales reorg,SOPS-340
2026-04-06T16:05:00Z,metrics_layer,2.0.0,Retention metrics moved from FP&A workbook to semantic layer; history restated,FPA-201
2026-06-08T13:20:00Z,metrics_layer,2.1.0,retention_by_segment,FPA-219
""")
print(published[-1], q2["nrr"])
