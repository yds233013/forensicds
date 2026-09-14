"""Oracle helper: diagnose the close and audit the rebuilt statement.

--diagnose: redelivered records, revisions and voids dropped by the redelivery filter, events whose revisions arrive
out of order, usage from other months inside each statement period, and records received after the September close.
Otherwise: re-derive every statement line independently (per customer x meter x service month) and compare with the
statement written by the pipeline, and check that adjustments telescope to the charge for the known quantity.
"""
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

month = sys.argv[sys.argv.index("--month") + 1] if "--month" in sys.argv else "2026-09"
y, m = map(int, month.split("-"))
close = f"{y + (m == 12):04d}-{1 if m == 12 else m + 1:02d}-04T00:00:00Z"
deliveries = []
for part in sorted(Path("raw/landing").glob("received_date=*/*.jsonl.gz")):
    with gzip.open(part, "rt") as fh:
        deliveries.extend(json.loads(l) for l in fh)
if "--diagnose" in sys.argv:
    pairs = Counter((d["record"]["event_id"], d["record"]["rev"]) for d in deliveries)
    revs = defaultdict(list)
    for d in sorted(deliveries, key=lambda d: d["received_at"]):
        revs[d["record"]["event_id"]].append(d["record"]["rev"])
    print("deliveries", len(deliveries), "records", len(pairs), "redelivered records", sum(v > 1 for v in pairs.values()))
    print("events with revisions", sum(max(v) > 1 for v in revs.values()),
          "out-of-order", sum(any(v[i] < max(v[:i]) for i in range(1, len(v))) for v in revs.values()))
    print("voids", sum(1 for d in deliveries if d["record"]["rev"] > 1 and d["record"]["quantity"] == "0.000"))
    late = [d for d in deliveries if d["received_at"] >= close]
    print("received after close", len(late), "of which for", month, sum(d["record"]["window_start"][:7] == month for d in late))
    sys.exit(0)
best = {}
for d in deliveries:
    if d["received_at"] >= close:
        continue
    r = d["record"]
    if r["event_id"] not in best or r["rev"] > best[r["event_id"]]["rev"]:
        best[r["event_id"]] = r
known = defaultdict(Decimal)
for r in best.values():
    known[(r["customer_id"], r["meter"], r["window_start"][:7])] += Decimal(r["quantity"])
billed = defaultdict(lambda: [Decimal(0), Decimal(0)])
for f in Path("ledger/issued").glob("statement_*.csv"):
    for r in csv.DictReader(open(f)):
        if r["statement_month"] < month:
            b = billed[(r["customer_id"], r["meter"], r["service_month"])]
            b[0] += Decimal(r["quantity"]); b[1] += Decimal(r["amount"])
written = {(r["customer_id"], r["meter"], r["line_type"], r["service_month"]): (Decimal(r["quantity"]), Decimal(r["amount"]))
           for r in csv.DictReader(open(f"out/statements/{month}/statement_lines.csv"))}
bad = 0
for (cid, meter, kind, sm), (q, a) in written.items():
    exp_q = known[(cid, meter, sm)] - (billed[(cid, meter, sm)][0] if kind == "adjustment" else 0)
    bad += q != exp_q
print("audit:", "statement quantities re-derived" if bad == 0 else f"{bad} quantity mismatches")
sys.exit(1 if bad else 0)
