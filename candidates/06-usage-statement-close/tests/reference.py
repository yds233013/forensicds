"""Independent reference for Task 06 (pure Python; shares no code with the workspace pipeline or the generator).

Semantics (contract §4, billing schedule, vendor delivery documentation, data catalog):
- a record is (event_id, rev); repeated deliveries of a record are one record; the highest rev of an event is current;
  quantity "0.000" voids the window;
- usage belongs to the UTC calendar month of window_start (windows are aligned and never straddle months);
- the statement for month S reflects records received before its close (00:00 UTC on the 4th of S+1): a usage line for
  S rated with S's rate card, and for each earlier month M an adjustment line when usage known at close differs from
  the quantity billed on issued statements for M; its amount is the charge for the known quantity under M's rate card
  minus the amount already billed for M;
- the usage mart holds every customer x meter x month with a known record, as currently known (all deliveries).
"""
from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ZERO = Decimal(0)


def _close(month: str) -> str:
    y, m = map(int, month.split("-"))
    y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return f"{y:04d}-{m:02d}-04T00:00:00Z"


def _read_records(root: Path):
    for part in sorted((Path(root) / "raw/landing").glob("received_date=*/*.jsonl.gz")):
        with gzip.open(part, "rt", encoding="utf-8") as fh:
            for line in fh:
                d = json.loads(line)
                yield d["received_at"], d["record"]


def _current(records, received_before: str | None) -> dict:
    """(customer, meter, month) -> quantity from the highest revision of each event received before the cutoff."""
    best: dict[str, tuple[int, str, str, str, Decimal]] = {}
    for received_at, r in records:
        if received_before is not None and received_at >= received_before:
            continue
        cur = best.get(r["event_id"])
        if cur is None or r["rev"] > cur[0]:
            best[r["event_id"]] = (r["rev"], r["customer_id"], r["meter"], r["window_start"][:7], Decimal(r["quantity"]))
    usage: dict[tuple, Decimal] = defaultdict(lambda: ZERO)
    for _rev, cid, meter, month, q in best.values():
        usage[(cid, meter, month)] += q
    return usage


def _rate_cards(root: Path) -> dict:
    cards = defaultdict(list)
    with open(Path(root) / "config/rate_cards.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            cards[(r["customer_id"], r["meter"])].append(
                (r["effective_month"], Decimal(r["included_units"]), Decimal(r["tier1_units"]),
                 Decimal(r["tier1_rate"]), Decimal(r["tier2_rate"])))
    return cards


def _charge(cards: dict, cid: str, meter: str, month: str, q: Decimal) -> Decimal:
    eff = [c for c in cards[(cid, meter)] if c[0] <= month]
    _m, included, t1_units, r1, r2 = max(eff, key=lambda c: c[0])
    over = max(ZERO, q - included)
    t1 = min(over, t1_units)
    return (t1 * r1 + (over - t1) * r2).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def usage_mart(root: Path) -> dict:
    return dict(_current(_read_records(root), None))


def statement(root: Path, month: str) -> dict:
    records = list(_read_records(root))
    known = _current(records, _close(month))
    cards = _rate_cards(root)
    billed_q: dict[tuple, Decimal] = defaultdict(lambda: ZERO)
    billed_a: dict[tuple, Decimal] = defaultdict(lambda: ZERO)
    for f in sorted((Path(root) / "ledger/issued").glob("statement_*.csv")):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh):
                if r["statement_month"] >= month:
                    continue
                k = (r["customer_id"], r["meter"], r["service_month"])
                billed_q[k] += Decimal(r["quantity"])
                billed_a[k] += Decimal(r["amount"])
    lines = {}
    keys = {k for k in known if k[2] <= month} | {k for k in billed_q if k[2] < month}
    for cid, meter, m in sorted(keys):
        q = known.get((cid, meter, m), ZERO)
        if m == month:
            if q > 0:
                lines[(cid, meter, "usage", m)] = (q, _charge(cards, cid, meter, m, q))
            continue
        bq = billed_q.get((cid, meter, m), ZERO)
        if q != bq:
            lines[(cid, meter, "adjustment", m)] = (q - bq, _charge(cards, cid, meter, m, q) - billed_a.get((cid, meter, m), ZERO))
    summary = defaultdict(lambda: [ZERO, ZERO])
    for (cid, _meter, kind, _m), (_q, amount) in lines.items():
        summary[cid][0 if kind == "usage" else 1] += amount
    return {"lines": lines, "summary": {c: (u, a, u + a) for c, (u, a) in summary.items()}, "close_at": _close(month)}
