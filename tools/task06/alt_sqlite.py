"""Independent correct close job built on SQLite (installed as jobs/close_month.py by the mutation suite).

Deliveries and issued statements are loaded into an in-memory database; record identity, current revisions, the close
cutoff, service-month attribution and billed-to-date totals are SQL; rating uses Python Decimal.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import sqlite3
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    month = ap.parse_args().month
    y, m = map(int, month.split("-"))
    close = f"{y + (m == 12):04d}-{1 if m == 12 else m + 1:02d}-04T00:00:00Z"

    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE d (received_at TEXT, event_id TEXT, rev INT, customer_id TEXT, meter TEXT, window_start TEXT, qty TEXT)")
    rows = []
    for part in sorted((ROOT / "raw/landing").glob("received_date=*/*.jsonl.gz")):
        with gzip.open(part, "rt") as fh:
            for line in fh:
                o = json.loads(line)
                r = o["record"]
                rows.append((o["received_at"], r["event_id"], r["rev"], r["customer_id"], r["meter"], r["window_start"], r["quantity"]))
    db.executemany("INSERT INTO d VALUES (?,?,?,?,?,?,?)", rows)
    db.execute("CREATE TABLE issued (statement_month TEXT, customer_id TEXT, meter TEXT, line_type TEXT, service_month TEXT, quantity TEXT, amount TEXT)")
    for f in sorted((ROOT / "ledger/issued").glob("statement_*.csv")):
        with open(f, newline="") as fh:
            db.executemany("INSERT INTO issued VALUES (?,?,?,?,?,?,?)",
                           [(r["statement_month"], r["customer_id"], r["meter"], r["line_type"], r["service_month"],
                             r["quantity"], r["amount"]) for r in csv.DictReader(fh)])
    cards = {}
    with open(ROOT / "config/rate_cards.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            cards.setdefault((r["customer_id"], r["meter"]), []).append(r)

    def charge(cid, meter, mo, q):
        r = max((c for c in cards[(cid, meter)] if c["effective_month"] <= mo), key=lambda c: c["effective_month"])
        over = max(Decimal(0), q - Decimal(r["included_units"]))
        t1 = min(over, Decimal(r["tier1_units"]))
        return (t1 * Decimal(r["tier1_rate"]) + (over - t1) * Decimal(r["tier2_rate"])).quantize(Decimal("0.01"), ROUND_HALF_UP)

    current_sql = """
      WITH rec AS (SELECT event_id, rev, customer_id, meter, substr(window_start, 1, 7) AS mo, qty
                   FROM d {where} GROUP BY event_id, rev),
           cur AS (SELECT *, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY rev DESC) AS rn FROM rec)
      SELECT customer_id, meter, mo, qty FROM cur WHERE rn = 1 ORDER BY customer_id, meter, mo"""

    def usage(where, params=()):
        tot = {}
        for cid, meter, mo, q in db.execute(current_sql.format(where=where), params):
            tot[(cid, meter, mo)] = tot.get((cid, meter, mo), Decimal(0)) + Decimal(q)
        return tot

    out = ROOT / "out"
    (out / "usage_mart").mkdir(parents=True, exist_ok=True)
    with open(out / "usage_mart/usage_by_service_month.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["customer_id", "meter", "service_month", "quantity"])
        for (cid, meter, mo), q in sorted(usage("").items()):
            w.writerow([cid, meter, mo, f"{q:.3f}"])

    known = usage("WHERE received_at < ?", (close,))
    billed = {}
    for cid, meter, sm, q, a in db.execute("SELECT customer_id, meter, service_month, quantity, amount FROM issued WHERE statement_month < ?", (month,)):
        b = billed.setdefault((cid, meter, sm), [Decimal(0), Decimal(0)])
        b[0] += Decimal(q)
        b[1] += Decimal(a)
    lines = []
    for key in sorted({k for k in known if k[2] <= month} | {k for k in billed if k[2] < month}):
        cid, meter, sm = key
        q = known.get(key, Decimal(0))
        if sm == month:
            if q > 0:
                lines.append((cid, meter, "usage", sm, q, charge(cid, meter, sm, q)))
        else:
            bq, ba = billed.get(key, (Decimal(0), Decimal(0)))
            if q != bq:
                lines.append((cid, meter, "adjustment", sm, q - bq, charge(cid, meter, sm, q) - ba))
    st = out / "statements" / month
    st.mkdir(parents=True, exist_ok=True)
    with open(st / "statement_lines.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["statement_month", "customer_id", "meter", "line_type", "service_month", "quantity", "amount"])
        for cid, meter, k, sm, q, a in lines:
            w.writerow([month, cid, meter, k, sm, f"{q:.3f}", f"{a:.2f}"])
    summary = {}
    for cid, _m, k, _s, _q, a in lines:
        s = summary.setdefault(cid, [Decimal(0), Decimal(0)])
        s[0 if k == "usage" else 1] += a
    (st / "summary.json").write_text(json.dumps({"statement_month": month, "close_at": close, "customers": [
        {"customer_id": c, "usage_amount": f"{u:.2f}", "adjustment_amount": f"{a:.2f}", "total_amount": f"{u + a:.2f}"}
        for c, (u, a) in sorted(summary.items())]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
