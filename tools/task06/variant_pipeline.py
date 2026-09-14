"""Configurable plain-Python close job used by the Task 06 mutation suite (installed as jobs/close_month.py).

VARIANT (set below by shortcuts.py) selects one semantic choice per stage; the default is the correct close. This file
also serves as the independent plain-Python implementation (no pandas) when VARIANT is empty.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

VARIANT: dict = {}
ROOT = Path(__file__).resolve().parents[1]
ZERO = Decimal(0)


def opt(name, default):
    return VARIANT.get(name, default)


def ts(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def close_of(month: str) -> datetime:
    y, m = map(int, month.split("-"))
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    hard = opt("hardcoded_closes", None)
    if hard is not None:
        return ts(hard[month]) if month in hard else datetime(y, m, 1, tzinfo=timezone.utc)
    return datetime(y, m, 4, tzinfo=timezone.utc)


def prev_month(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y - (m == 1):04d}-{12 if m == 1 else m - 1:02d}"


def load_deliveries():
    out = []
    for part in sorted((ROOT / "raw/landing").glob("received_date=*/*.jsonl.gz")):
        with gzip.open(part, "rt") as fh:
            for line in fh:
                d = json.loads(line)
                out.append((ts(d["received_at"]), d["delivery_id"], d["collector"], d["record"]))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def dedupe(deliveries):
    mode = opt("dedupe", "record")
    if mode == "none":
        return deliveries
    seen, last_seen, out = set(), {}, []
    for t, did, coll, r in deliveries:
        if mode == "record":
            k = (r["event_id"], r["rev"])
            if k in seen:
                continue
            seen.add(k)
        elif mode == "record_last":
            last_seen[(r["event_id"], r["rev"])] = (t, did, coll, r)
            continue
        elif mode == "event_first":
            if r["event_id"] in seen:
                continue
            seen.add(r["event_id"])
        elif mode == "ttl":
            prev = last_seen.get(r["event_id"])
            last_seen[r["event_id"]] = t
            if prev is not None and t - prev <= timedelta(hours=24):
                continue
        elif mode == "hardcoded_outage":
            k = (r["event_id"], r["rev"])
            prev = last_seen.get(k)
            if k not in last_seen:
                last_seen[k] = t
            elif (t - prev <= timedelta(hours=1)) or (coll == "eu-west-1" and ts("2026-09-02T09:00:00Z") <= t < ts("2026-09-02T12:00:00Z")):
                continue
        out.append((t, did, coll, r))
    if mode == "record_last":
        out = sorted(last_seen.values(), key=lambda x: (x[0], x[1]))
    return out


def attribution_month(t, r) -> str:
    mode = opt("attribution", "window_start")
    if mode == "window_end":
        return r["window_end"][:7]
    if mode == "received":
        return t.strftime("%Y-%m")
    return r["window_start"][:7]


def current_usage(records, before=None):
    mode = opt("current", "max_rev")
    per_event = defaultdict(list)
    for t, did, coll, r in records:
        if before is not None and (t > before if opt("close_inclusive", False) else t >= before):
            continue
        per_event[r["event_id"]].append((t, r))
    usage = defaultdict(lambda: ZERO)
    for items in per_event.values():
        if mode == "max_rev":
            chosen = [max(items, key=lambda x: x[1]["rev"])]
        elif mode == "last_received":
            chosen = [max(items, key=lambda x: x[0])]
        elif mode == "first_rev":
            chosen = [min(items, key=lambda x: (x[1]["rev"], x[0]))]
        elif mode == "sum_all":
            chosen = items
        for t, r in chosen:
            usage[(r["customer_id"], r["meter"], attribution_month(t, r))] += Decimal(r["quantity"])
    return usage


def rate_cards():
    cards = defaultdict(list)
    with open(ROOT / "config/rate_cards.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            cards[(r["customer_id"], r["meter"])].append(r)
    return cards


def charge(cards, cid, meter, month, q):
    rows = [r for r in cards[(cid, meter)] if r["effective_month"] <= month]
    allowed = opt("hardcoded_rate_periods", None)
    if allowed is not None:
        rows = [r for r in rows if r["effective_month"] in allowed] or [min(cards[(cid, meter)], key=lambda r: r["effective_month"])]
    r = max(rows, key=lambda r: r["effective_month"])
    over = max(ZERO, q - Decimal(r["included_units"]))
    t1 = min(over, Decimal(r["tier1_units"]))
    return (t1 * Decimal(r["tier1_rate"]) + (over - t1) * Decimal(r["tier2_rate"])).quantize(Decimal("0.01"), ROUND_HALF_UP)


def tier1_rate(cards, cid, meter, month):
    rows = [r for r in cards[(cid, meter)] if r["effective_month"] <= month]
    return Decimal(max(rows, key=lambda r: r["effective_month"])["tier1_rate"])


def billed_to_date(month):
    bq, ba = defaultdict(lambda: ZERO), defaultdict(lambda: ZERO)
    for f in sorted((ROOT / "ledger/issued").glob("statement_*.csv")):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh):
                if r["statement_month"] >= month:
                    continue
                if opt("billed", "all_lines") == "usage_lines_only" and r["line_type"] != "usage":
                    continue
                k = (r["customer_id"], r["meter"], r["service_month"])
                bq[k] += Decimal(r["quantity"])
                ba[k] += Decimal(r["amount"])
    return bq, ba


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", required=True)
    month = ap.parse_args().month
    cards = rate_cards()
    records = dedupe(load_deliveries())
    out = ROOT / "out"

    mart = current_usage(records)
    if opt("mart", "current") == "received":
        saved = dict(VARIANT)
        VARIANT["attribution"] = "received"
        mart = current_usage(records)
        VARIANT.clear()
        VARIANT.update(saved)
    (out / "usage_mart").mkdir(parents=True, exist_ok=True)
    with open(out / "usage_mart/usage_by_service_month.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["customer_id", "meter", "service_month", "quantity"])
        for (c, m, s), q in sorted(mart.items()):
            w.writerow([c, m, s, f"{q:.3f}"])

    close = close_of(month)
    cutoff = opt("cutoff", "close")
    lines = []
    if cutoff == "receipt_window":
        opens = close_of(prev_month(month))
        totals = defaultdict(lambda: ZERO)
        window = [x for x in records if opens <= x[0] < close]
        for (c, m, _s), q in current_usage(window).items():
            totals[(c, m)] += q
        for (c, m), q in sorted(totals.items()):
            if q > 0:
                lines.append((c, m, "usage", month, q, charge(cards, c, m, month, q)))
    else:
        known = current_usage(records, None if cutoff == "extract" else close)
        adj_known = current_usage(records, None) if opt("adjust_knowledge", "close") == "extract" else known
        bq, ba = billed_to_date(month)
        for (c, m, s), q in sorted(known.items()):
            if s == month and q > 0:
                lines.append((c, m, "usage", month, q, charge(cards, c, m, month, q)))
        mode = opt("adjustments", "correct")
        if mode == "reissue":
            for (c, m, s), q in sorted(adj_known.items()):
                if s < month and s >= "2026-07" and q != bq.get((c, m, s), ZERO):
                    lines.append((c, m, "usage", s, q, charge(cards, c, m, s, q)))
        elif mode != "none":
            keys = {k for k in adj_known if k[2] < month} | {k for k in bq if k[2] < month}
            for c, m, s in sorted(keys):
                q = adj_known.get((c, m, s), ZERO)
                if q == bq.get((c, m, s), ZERO):
                    continue
                dq = q - bq.get((c, m, s), ZERO)
                if mode == "statement_rates":
                    amt = charge(cards, c, m, month, q) - charge(cards, c, m, month, bq.get((c, m, s), ZERO))
                elif mode == "linear":
                    amt = (dq * tier1_rate(cards, c, m, s)).quantize(Decimal("0.01"), ROUND_HALF_UP)
                else:
                    amt = charge(cards, c, m, s, q) - ba.get((c, m, s), ZERO)
                lines.append((c, m, "adjustment", s, dq, amt))
    for extra in opt("extra_lines", []):
        lines.append(tuple(extra[:4]) + (Decimal(extra[4]), Decimal(extra[5])))
    st = out / "statements" / month
    st.mkdir(parents=True, exist_ok=True)
    with open(st / "statement_lines.csv", "w", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["statement_month", "customer_id", "meter", "line_type", "service_month", "quantity", "amount"])
        for c, m, k, s, q, a in sorted(lines, key=lambda l: (l[0], l[1], l[2], l[3])):
            w.writerow([month, c, m, k, s, f"{q:.3f}", f"{a:.2f}"])
    summ = defaultdict(lambda: [ZERO, ZERO])
    for c, m, k, s, q, a in lines:
        summ[c][0 if k == "usage" else 1] += a
    (st / "summary.json").write_text(json.dumps({
        "statement_month": month, "close_at": close.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "customers": [{"customer_id": c, "usage_amount": f"{u:.2f}", "adjustment_amount": f"{a:.2f}",
                       "total_amount": f"{u + a:.2f}"} for c, (u, a) in sorted(summ.items())]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
