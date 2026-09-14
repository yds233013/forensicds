#!/usr/bin/env python3
"""Deterministic synthetic metering world for ForensicDS Task 06 (usage statement close).

Writes, under a workspace root:

  raw/landing/received_date=YYYY-MM-DD/part-0.jsonl.gz   collector deliveries (at-least-once), one JSON object per line
  config/customers.csv                                  customer registry
  config/rate_cards.csv                                 effective-dated rate cards (included units, overage tiers)
  ledger/issued/statement_YYYY-MM.csv                   statements issued by the billing system (immutable)

Mechanisms (all documented in the workspace): 4-hour usage windows per customer x meter; deliveries arrive shortly
after window end, sometimes hours to weeks late; the vendor re-emits corrected records with a higher `rev` (including
voids, quantity 0), occasionally before a delayed earlier revision arrives; collectors retry deliveries; a collector
outage buffers records and replays recently delivered ones on recovery.

Issued history is produced by simulating the billing process at each statement close: statements before the streaming
cutover follow the contract (batch era); statements after it are produced by the streaming consumer (v2). Standard
library only; fully determined by the spec. Deleted from the image after the build; tests/ holds a copy.
"""
from __future__ import annotations

import copy
import csv
import gzip
import hashlib
import io
import json
import math
import random
import sys
from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

UTC = timezone.utc
Q3 = Decimal("0.001")
C2 = Decimal("0.01")

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 60606,
    "world_start": "2026-03-01",
    "extract_at": "2026-10-06T06:00:00",
    "statement_month": "2026-09",
    "cutover": "2026-07-06T00:00:00",
    "late_runs": {"2026-05": "2026-06-05T09:12:00"},
    "n_customers": 28,
    "regions": {"us-east": 0.45, "eu-west": 0.35, "ap-south": 0.20},
    "meters": {
        "compute_credits": {"level": 38.0, "sigma": 0.55, "r1": "3.2000", "r2": "2.8000", "tier1_share": 0.25},
        "api_requests_k": {"level": 310.0, "sigma": 0.70, "r1": "0.1800", "r2": "0.1500", "tier1_share": 0.30},
    },
    "window_hours": 4,
    "rate_changes": {"2026-05": 1.05, "2026-09": 1.08},
    "included_ratio": [0.60, 0.95],
    "amendments": {"cus_northwind": "2026-06"},
    "prompt_minutes": 2.5,
    "late_share": 0.02,
    "late_hours": [2, 150],
    "very_late_share": 0.0015,
    "very_late_days": [8, 38],
    "retry_share": 0.004,
    "revision_share": 0.03,
    "revision_days": [0.5, 12.0],
    "second_revision_share": 0.25,
    "late_revision_share": 0.0015,
    "late_revision_days": [25, 45],
    "void_share": 0.003,
    "out_of_order_share": 0.12,
    "dedupe_ttl_hours": 24,
    "outages": [{"collector": "eu-west", "start": "2026-08-30T14:00:00", "end": "2026-09-02T09:00:00",
                 "replay_hours": 6, "flush_hours": 3}],
    "churn": {},
    "northwind_headroom": 1.04,
}


def dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=UTC)


def iso(t: datetime) -> str:
    return t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def month_of(t: datetime) -> str:
    return f"{t.year:04d}-{t.month:02d}"


def month_start(m: str) -> datetime:
    y, mo = map(int, m.split("-"))
    return datetime(y, mo, 1, tzinfo=UTC)


def next_month(m: str) -> str:
    y, mo = map(int, m.split("-"))
    return f"{y + (mo == 12):04d}-{1 if mo == 12 else mo + 1:02d}"


def months_between(a: str, b: str) -> list[str]:
    out, m = [], a
    while m <= b:
        out.append(m)
        m = next_month(m)
    return out


def close_of(m: str) -> datetime:
    return month_start(next_month(m)) + timedelta(hours=72)


def q3(x) -> Decimal:
    return Decimal(str(x)).quantize(Q3, rounding=ROUND_HALF_UP)


def cents(x: Decimal) -> Decimal:
    return x.quantize(C2, rounding=ROUND_HALF_UP)


def h(*parts) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def charge(terms: dict, q: Decimal) -> Decimal:
    over = max(Decimal(0), q - terms["included_units"])
    t1 = min(over, terms["tier1_units"])
    return cents(t1 * terms["tier1_rate"] + (over - t1) * terms["tier2_rate"])


class World:
    def __init__(self, spec: dict):
        self.s = spec
        self.seed = spec["seed"]
        self.extract = dt(spec["extract_at"])
        self.start = dt(spec["world_start"] + "T00:00:00")
        self.customers: list[dict] = []
        self.deliveries: list[dict] = []
        self.rate_cards: list[dict] = []
        self.issued: dict[str, list[dict]] = {}

    def rng(self, *parts) -> random.Random:
        return random.Random(h(self.seed, *parts))

    # ------------------------------------------------------------------------------------------ customers and usage
    def make_customers(self):
        s = self.s
        r = self.rng("customers")
        names = ["Northwind Logistics", "Acme Analytics", "Bluefin Health", "Cedar Retail", "Dunmore Freight",
                 "Elm Street Media", "Fjord Energy", "Granite Insurance", "Harbor Foods", "Iris Biotech",
                 "Juniper Travel", "Kestrel Games", "Lumen Robotics", "Maple Credit", "Nimbus Telecom",
                 "Orchid Fashion", "Pioneer Mining", "Quill Publishing", "Redwood Labs", "Summit Rail",
                 "Tidewater Ports", "Umbra Security", "Vista Realty", "Willow Clinics", "Xenon Chips",
                 "Yarrow Farms", "Zephyr Air", "Atlas Legal", "Beacon Schools", "Comet Payments", "Delta Water",
                 "Ember Studios", "Falcon Parts", "Gale Wind", "Helix Genomics"]
        for i in range(s["n_customers"]):
            name = names[i % len(names)] + ("" if i < len(names) else f" {i}")
            cid = "cus_northwind" if i == 0 else "cus_" + h(self.seed, "cust", i)[:10]
            region = "eu-west" if i == 0 else r.choices(list(s["regions"]), weights=list(s["regions"].values()))[0]
            meters = {}
            for m, cfg in s["meters"].items():
                if i == 0 or r.random() < 0.9:
                    meters[m] = math.exp(r.gauss(math.log(cfg["level"]), cfg["sigma"]))
            if not meters:
                m = list(s["meters"])[0]
                meters[m] = s["meters"][m]["level"]
            churn = s["churn"].get(str(i))
            self.customers.append(dict(customer_id=cid, name=name, region=region, levels=meters, ends=churn, index=i))

    def window_quantity(self, c: dict, meter: str, ws: datetime, r: random.Random) -> Decimal:
        lvl = c["levels"][meter]
        dow = 0.62 if ws.weekday() >= 5 else 1.0
        hour = [0.55, 0.7, 1.25, 1.35, 1.15, 0.8][ws.hour // 4]
        trend = 1 + 0.005 * ((ws - self.start).days / 30)
        q = lvl * dow * hour * trend * math.exp(r.gauss(0, 0.28))
        return q3(max(0.0, q))

    def generate(self):
        s = self.s
        self.make_customers()
        wh = timedelta(hours=s["window_hours"])
        for c in self.customers:
            ends = dt(c["ends"]) if c["ends"] else None
            for meter in sorted(c["levels"]):
                ws = self.start
                while ws + wh <= self.extract:
                    if ends is not None and ws >= ends:
                        break
                    self.emit_window(c, meter, ws, ws + wh)
                    ws += wh
        self.apply_outages()
        self.deliveries = [d for d in self.deliveries if d["received_at"] < self.extract]
        self.deliveries.sort(key=lambda d: (d["received_at"], d["delivery_id"]))
        return self

    def deliver(self, rec: dict, t: datetime, k: int, collector: str):
        did = "dlv_" + h(self.seed, rec["event_id"], rec["rev"], k)[:20]
        self.deliveries.append(dict(delivery_id=did, received_at=t.replace(microsecond=0), collector=collector,
                                    record=rec))

    def emit_window(self, c: dict, meter: str, ws: datetime, we: datetime):
        s = self.s
        eid = "evt_" + h(self.seed, c["customer_id"], meter, iso(ws))[:24]
        r = self.rng("win", eid)
        collector = c["region"]
        base = dict(event_id=eid, customer_id=c["customer_id"], meter=meter, window_start=iso(ws), window_end=iso(we))
        revs = [(1, self.window_quantity(c, meter, ws, r))]
        # first delivery time
        u = r.random()
        if u < s["very_late_share"]:
            t1 = we + timedelta(days=r.uniform(*s["very_late_days"]))
        elif u < s["very_late_share"] + s["late_share"]:
            t1 = we + timedelta(hours=r.uniform(*s["late_hours"]))
        else:
            t1 = we + timedelta(seconds=r.expovariate(1 / (60 * s["prompt_minutes"])))
        times = [t1]
        # vendor corrections
        v = r.random()
        if v < s["void_share"]:
            revs.append((2, Decimal("0.000")))
            times.append(we + timedelta(days=r.uniform(*s["revision_days"])))
        elif v < s["void_share"] + s["revision_share"]:
            revs.append((2, q3(float(revs[0][1]) * r.uniform(0.8, 1.2))))
            times.append(we + timedelta(days=r.uniform(*s["revision_days"])))
            if r.random() < s["second_revision_share"]:
                revs.append((3, q3(float(revs[1][1]) * r.uniform(0.9, 1.1))))
                times.append(times[-1] + timedelta(days=r.uniform(0.5, 6)))
        elif v < s["void_share"] + s["revision_share"] + s["late_revision_share"]:
            revs.append((2, q3(float(revs[0][1]) * r.uniform(0.7, 1.3))))
            times.append(we + timedelta(days=r.uniform(*s["late_revision_days"])))
        if len(revs) > 1 and r.random() < s["out_of_order_share"]:
            # the first revision sits in an edge buffer and arrives after the vendor correction
            times[0] = times[1] + timedelta(hours=r.uniform(1, 36))
        for i, ((rev, q), t) in enumerate(zip(revs, times)):
            rec = dict(base, rev=rev, quantity=f"{q:.3f}")
            self.deliver(rec, t, 0, collector)
            if r.random() < s["retry_share"]:
                self.deliver(rec, t + timedelta(seconds=r.uniform(20, 1800)), 1, collector)

    def apply_outages(self):
        for o in self.s["outages"]:
            start, end = dt(o["start"]), dt(o["end"])
            r = self.rng("outage", o["start"])
            flush = timedelta(hours=o["flush_hours"])
            at_end = o.get("flush_at_end_share", 0.0)
            replay_from = start - timedelta(hours=o["replay_hours"])
            extra = []
            for d in self.deliveries:
                if d["collector"] != o["collector"]:
                    continue
                if start <= d["received_at"] < end:
                    d["received_at"] = end if r.random() < at_end else (end + flush * r.random()).replace(microsecond=0)
                elif replay_from <= d["received_at"] < start:
                    rec = d["record"]
                    did = "dlv_" + h(self.seed, "replay", o["start"], d["delivery_id"])[:20]
                    extra.append(dict(delivery_id=did, received_at=(end + flush * r.random()).replace(microsecond=0),
                                      collector=d["collector"], record=rec))
            self.deliveries.extend(extra)

    # ------------------------------------------------------------------------------------------ billing simulation
    def true_usage(self, until: datetime | None = None) -> dict:
        """Quantity per (customer, meter, month) from the highest known revision per event."""
        best: dict[str, tuple[int, dict]] = {}
        for d in self.deliveries:
            if until is not None and d["received_at"] >= until:
                continue
            rec = d["record"]
            cur = best.get(rec["event_id"])
            if cur is None or rec["rev"] > cur[0]:
                best[rec["event_id"]] = (rec["rev"], rec)
        out = defaultdict(Decimal)
        for _rev, rec in best.values():
            out[(rec["customer_id"], rec["meter"], rec["window_start"][:7])] += Decimal(rec["quantity"])
        return out

    def make_rate_cards(self):
        s = self.s
        final = self.true_usage()
        months = months_between(s["world_start"][:7], s["statement_month"])
        change_months = sorted(s["rate_changes"])
        for c in self.customers:
            r = self.rng("rates", c["customer_id"])
            for meter in sorted(c["levels"]):
                cfg = s["meters"][meter]
                monthly = float(sum(v for (cid, m, mo), v in final.items() if cid == c["customer_id"] and m == meter
                                    and mo in months[:3])) / 3 or 1.0
                included = q3(round(monthly * r.uniform(*s["included_ratio"]), -1))
                nw_aug = final.get((c["customer_id"], meter, "2026-08"))
                if c["customer_id"] == "cus_northwind" and nw_aug is not None and s.get("northwind_headroom"):
                    included = q3(round(float(nw_aug) * 0.93, -1))
                tier1 = q3(round(monthly * cfg["tier1_share"], -1))
                eff = [s["world_start"][:7]] + change_months
                amend = s["amendments"].get(c["customer_id"]) or s["amendments"].get(f"#{c['index']}")
                if amend:
                    eff = sorted(set(eff + [amend]))
                mult = 1.0
                for e in eff:
                    if e in s["rate_changes"]:
                        mult *= s["rate_changes"][e]
                    inc = included
                    if amend and e >= amend:
                        aug = final.get((c["customer_id"], meter, "2026-08"))
                        if c["customer_id"] == "cus_northwind" and aug is not None and s.get("northwind_headroom"):
                            inc = q3(round(float(aug) * s["northwind_headroom"], -1))
                        else:
                            inc = q3(round(float(included) * 1.15, -1))
                    self.rate_cards.append(dict(customer_id=c["customer_id"], meter=meter, effective_month=e,
                                                included_units=inc, tier1_units=tier1,
                                                tier1_rate=(Decimal(cfg["r1"]) * Decimal(str(mult))).quantize(Decimal("0.0001")),
                                                tier2_rate=(Decimal(cfg["r2"]) * Decimal(str(mult))).quantize(Decimal("0.0001"))))

    def terms(self, cid: str, meter: str, month: str) -> dict:
        cands = [rc for rc in self.rate_cards if rc["customer_id"] == cid and rc["meter"] == meter
                 and rc["effective_month"] <= month]
        return max(cands, key=lambda rc: rc["effective_month"])

    def issue_history(self):
        s = self.s
        cutover = dt(s["cutover"])
        first = s["world_start"][:7]
        prev_close = self.start
        for m in months_between(first, s["statement_month"])[:-1]:
            close = close_of(m)
            issued_at = dt(s["late_runs"][m]) if m in s["late_runs"] else close + timedelta(hours=2, minutes=17)
            policy = s.get("policies", {}).get(m, "v2" if close > cutover else "batch")
            lines = self.batch_statement(m, close) if policy == "batch" else self.v2_statement(m, prev_close, close)
            self.issued[m] = [dict(l, issued_at=iso(issued_at)) for l in lines]
            prev_close = close

    def billed(self, before_month: str) -> dict:
        out = defaultdict(lambda: [Decimal(0), Decimal(0)])
        for m, lines in self.issued.items():
            if m >= before_month:
                continue
            for l in lines:
                k = (l["customer_id"], l["meter"], l["service_month"])
                out[k][0] += l["quantity"]
                out[k][1] += l["amount"]
        return out

    def batch_statement(self, m: str, close: datetime) -> list[dict]:
        known = self.true_usage(until=close)
        billed = self.billed(m)
        lines = []
        keys = sorted(set(k for k in known if k[2] <= m) | set(k for k in billed if k[2] < m))
        for cid, meter, mo in keys:
            q = known.get((cid, meter, mo), Decimal(0))
            if mo == m:
                if q > 0:
                    lines.append(dict(statement_month=m, customer_id=cid, meter=meter, line_type="usage",
                                      service_month=mo, quantity=q, amount=charge(self.terms(cid, meter, mo), q)))
                continue
            bq, ba = billed.get((cid, meter, mo), (Decimal(0), Decimal(0)))
            if q != bq:
                lines.append(dict(statement_month=m, customer_id=cid, meter=meter, line_type="adjustment",
                                  service_month=mo, quantity=q - bq,
                                  amount=charge(self.terms(cid, meter, mo), q) - ba))
        return lines

    def v2_statement(self, m: str, prev_close: datetime, close: datetime) -> list[dict]:
        ttl = timedelta(hours=self.s["dedupe_ttl_hours"])
        last_seen: dict[str, datetime] = {}
        total = defaultdict(Decimal)
        for d in self.deliveries:  # sorted by (received_at, delivery_id)
            if d["received_at"] >= close:
                break
            eid = d["record"]["event_id"]
            prev = last_seen.get(eid)
            last_seen[eid] = d["received_at"]
            if prev is not None and d["received_at"] - prev <= ttl:
                continue
            if d["received_at"] >= prev_close:
                total[(d["record"]["customer_id"], d["record"]["meter"])] += Decimal(d["record"]["quantity"])
        lines = []
        for (cid, meter), q in sorted(total.items()):
            if q > 0:
                lines.append(dict(statement_month=m, customer_id=cid, meter=meter, line_type="usage", service_month=m,
                                  quantity=q, amount=charge(self.terms(cid, meter, m), q)))
        return lines

    # ------------------------------------------------------------------------------------------ writing
    def write(self, root: Path):
        root = Path(root)
        land = root / "raw/landing"
        by_day = defaultdict(list)
        for d in self.deliveries:
            by_day[d["received_at"].date().isoformat()].append(d)
        for day, ds in sorted(by_day.items()):
            p = land / f"received_date={day}" / "part-0.jsonl.gz"
            p.parent.mkdir(parents=True, exist_ok=True)
            buf = io.BytesIO()
            with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
                for d in ds:
                    obj = {"delivery_id": d["delivery_id"], "received_at": iso(d["received_at"]),
                           "collector": d["collector"] + "-1", "record": d["record"]}
                    gz.write((json.dumps(obj, separators=(",", ":")) + "\n").encode())
            p.write_bytes(buf.getvalue())
        (root / "config").mkdir(parents=True, exist_ok=True)
        with open(root / "config/customers.csv", "w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["customer_id", "name", "region", "currency"])
            for c in sorted(self.customers, key=lambda c: c["customer_id"]):
                w.writerow([c["customer_id"], c["name"], c["region"], "USD"])
        with open(root / "config/rate_cards.csv", "w", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(["customer_id", "meter", "effective_month", "included_units", "tier1_units", "tier1_rate", "tier2_rate"])
            for rc in sorted(self.rate_cards, key=lambda x: (x["customer_id"], x["meter"], x["effective_month"])):
                w.writerow([rc["customer_id"], rc["meter"], rc["effective_month"], f"{rc['included_units']:.3f}",
                            f"{rc['tier1_units']:.3f}", f"{rc['tier1_rate']:.4f}", f"{rc['tier2_rate']:.4f}"])
        led = root / "ledger/issued"
        led.mkdir(parents=True, exist_ok=True)
        for m, lines in sorted(self.issued.items()):
            with open(led / f"statement_{m}.csv", "w", newline="") as fh:
                w = csv.writer(fh, lineterminator="\n")
                w.writerow(["statement_id", "statement_month", "customer_id", "meter", "line_type", "service_month",
                            "quantity", "amount", "issued_at"])
                for i, l in enumerate(sorted(lines, key=lambda l: (l["customer_id"], l["meter"], l["line_type"] != "usage",
                                                                    l["service_month"])), 1):
                    w.writerow([f"ST-{m.replace('-', '')}-{i:05d}", l["statement_month"], l["customer_id"], l["meter"],
                                l["line_type"], l["service_month"], f"{l['quantity']:.3f}", f"{l['amount']:.2f}",
                                l["issued_at"]])


def build(spec: dict, root: Path) -> World:
    w = World(copy.deepcopy(spec)).generate()
    w.make_rate_cards()
    w.issue_history()
    w.write(root)
    return w


def tree_digest(root: Path, rel_paths=("raw/landing", "config/customers.csv", "config/rate_cards.csv", "ledger/issued")) -> str:
    hh = hashlib.sha256()
    root = Path(root)
    for rel in rel_paths:
        p = root / rel
        files = sorted(x for x in p.rglob("*") if x.is_file()) if p.is_dir() else [p]
        for f in files:
            if not f.exists():
                continue
            data = f.read_bytes()
            if f.suffix == ".gz":
                data = gzip.decompress(data)
            hh.update(str(f.relative_to(root)).encode() + b"\0" + hashlib.sha256(data).digest())
    return hh.hexdigest()


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    build(VISIBLE_SPEC, out)
    print(tree_digest(out))
