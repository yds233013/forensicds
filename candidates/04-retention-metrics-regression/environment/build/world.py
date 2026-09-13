#!/usr/bin/env python3
"""Deterministic synthetic subscription warehouse for ForensicDS Task 04 (retention metrics).

Produces `data/warehouse.db` (SQLite):

  crm_accounts         one row per CRM account (customers and prospects; created by Sales Ops, often before any contract)
  contracts            one row per signed contract document (CRM classification entered by Sales Ops)
  subscription_lines   one row per contract line (recurring lines carry ARR over [start_date, end_date))
  fx_rates             not used (USD only) - intentionally absent
  price_changes        one row per list-price program

Standard library only; fully determined by the spec. Deleted from the image after the build; tests/ holds a copy.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

INDUSTRIES = ["Software", "Financial Services", "Healthcare", "Retail", "Manufacturing", "Media", "Logistics", "Education"]
REGIONS = [("NA", .55), ("EMEA", .3), ("APAC", .15)]
PRODUCTS = {"core": 1.0, "analytics_addon": 0.25, "premium_support": 0.12}

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 60613,
    "start_date": "2021-01-01",
    "extract_date": "2026-08-05",
    "new_customers_per_month": 26,
    "abm": {"from": "2025-04-01", "prospects_per_month": 55, "convert_share": 0.28, "lead_months": [2, 11]},
    "outbound_precreate_share": 0.25,
    "outbound_lead_days": [20, 200],
    "inbound_lead_days": [1, 25],
    "never_convert_prospects_per_month": 20,
    "annual_churn_prob": 0.13,
    "reactivation_prob": 0.22,
    "reactivation_gap_days": [60, 420],
    "short_term_share": 0.05,
    "upsell_prob": 0.30,
    "downsell_prob": 0.10,
    "renewal_gap_prob": 0.05,
    "early_signing_days": [0, 75],
    "late_signing_share": 0.08,
    "late_signing_days": [5, 45],
    "very_late_signing_share": 0.03,
    "very_late_signing_days": [100, 240],
    "price_increase": {"from": "2025-07-01", "uplift": 0.07},
    "line_split_from": "2025-11-01",
    "contract_type_mislabel": 0.06,
    "big_deal": {"date": "2026-02-10", "arr": 1_150_000},
    "arr_scale": 1.0,
    "boundary_arr_accounts": None,
}


def d(s: str) -> date:
    return date.fromisoformat(s)


def add_months(x: date, n: int) -> date:
    y, m = divmod(x.month - 1 + n, 12)
    y += x.year
    m += 1
    day = min(x.day, [31, 29 if y % 4 == 0 and (y % 100 or y % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return date(y, m, day)


class World:
    def __init__(self, spec: dict):
        self.spec = spec
        self.seed = spec["seed"]
        self.extract = d(spec["extract_date"])
        self.accounts, self.contracts, self.lines = [], [], []
        self.n_acc = 0

    def rng(self, *p):
        return random.Random(":".join(map(str, (self.seed,) + p)))

    def new_account_id(self) -> str:
        self.n_acc += 1
        return f"0015{(self.n_acc * 2654435761 + self.seed) % 4294967291:010d}"

    def add_account(self, created: date, source: str, r) -> dict:
        a = dict(account_id=self.new_account_id(), created_at=created, source=source, industry=r.choice(INDUSTRIES),
                 region=[v for v, _ in REGIONS][min(2, int(r.random() * 2.2))], name=f"Account {self.n_acc:05d}")
        self.accounts.append(a)
        return a

    def price_factor(self, start: date) -> float:
        pi = self.spec.get("price_increase")
        return 1 + pi["uplift"] if pi and start >= d(pi["from"]) else 1.0

    def add_contract(self, acc, signed: date, start: date, months: int, arr: float, ctype: str, r, products=None):
        cid = f"CT-{len(self.contracts) + 1:07d}"
        mislabel = r.random() < self.spec["contract_type_mislabel"]
        crm_type = ctype
        if ctype == "reactivation":
            crm_type = "new_business" if r.random() < 0.7 else "renewal"
        elif mislabel and ctype == "renewal":
            crm_type = "new_business"
        self.contracts.append(dict(contract_id=cid, account_id=acc["account_id"], signed_at=signed, contract_type=crm_type))
        end = add_months(start, months)
        products = products or ["core"] + [p for p in ("analytics_addon", "premium_support") if r.random() < 0.35]
        split = start >= d(self.spec["line_split_from"])
        weights = {p: PRODUCTS[p] for p in products}
        tot = sum(weights.values())
        for p in products:
            share = arr * weights[p] / tot
            parts = [0.6, 0.4] if (split and p == "core") else [1.0]
            for part in parts:
                self.lines.append(dict(contract_id=cid, account_id=acc["account_id"], product=p, line_type="recurring",
                                       start_date=start, end_date=end, arr_usd=round(share * part, 2)))
        if ctype in ("new_business", "reactivation") and r.random() < 0.6:
            self.lines.append(dict(contract_id=cid, account_id=acc["account_id"], product="onboarding", line_type="one_time",
                                   start_date=start, end_date=start + timedelta(days=1), arr_usd=round(arr * 0.15, 2)))
        return end

    def amend(self, acc, signed: date, start: date, end: date, ctype: str, product: str, arr: float):
        cid = f"CT-{len(self.contracts) + 1:07d}"
        self.contracts.append(dict(contract_id=cid, account_id=acc["account_id"], signed_at=signed, contract_type=ctype))
        self.lines.append(dict(contract_id=cid, account_id=acc["account_id"], product=product, line_type="recurring",
                               start_date=start, end_date=end, arr_usd=arr))

    def customer_lifecycle(self, acc, first_start: date, arr0: float, r):
        s = self.spec
        start, arr, months = first_start, arr0, (r.choice([1, 3]) if r.random() < s["short_term_share"] else 12)
        signed = start - timedelta(days=r.randint(3, 30))
        ctype = "new_business"
        while start < self.extract:
            if signed >= self.extract:
                break
            end = self.add_contract(acc, signed, start, months, arr, ctype, r)
            # mid-term amendments (co-terminous with the current term)
            if months == 12 and r.random() < s["upsell_prob"]:
                ms = add_months(start, r.randint(2, 9))
                if ms < self.extract:
                    up = round(arr * r.uniform(0.1, 0.45), 2)
                    self.amend(acc, ms - timedelta(days=r.randint(0, 20)), ms, end, "upsell", "analytics_addon", up)
                    arr += up
            if months == 12 and r.random() < s["downsell_prob"]:
                ms = add_months(start, r.randint(3, 9))
                if ms < self.extract:
                    core = [ln for ln in self.lines if ln["account_id"] == acc["account_id"] and ln["product"] == "core"
                            and ln["start_date"] <= ms < ln["end_date"] and ln["end_date"] == end]
                    if core:
                        total = sum(ln["arr_usd"] for ln in core)
                        for ln in core:
                            ln["end_date"] = ms
                        cut = r.uniform(0.1, 0.35)
                        self.amend(acc, ms - timedelta(days=r.randint(0, 15)), ms, end, "downsell", "core", round(total * (1 - cut), 2))
                        arr -= total * cut
            # renewal decision
            churn_p = s["annual_churn_prob"] if months == 12 else 0.25
            if r.random() < churn_p:
                if r.random() < s["reactivation_prob"]:
                    gap = r.randint(*s["reactivation_gap_days"])
                    start = end + timedelta(days=gap)
                    arr = arr * r.uniform(0.6, 1.1) * self.price_factor(start) / self.price_factor(end)
                    signed = start - timedelta(days=r.randint(5, 40))
                    ctype, months = "reactivation", 12
                    continue
                break
            gap = r.randint(3, 40) if r.random() < s["renewal_gap_prob"] else 0
            new_start = end + timedelta(days=gap)
            arr = arr * r.uniform(0.95, 1.12) * self.price_factor(new_start) / self.price_factor(start)
            signed = new_start - timedelta(days=r.randint(*s["early_signing_days"]))
            if r.random() < s["late_signing_share"]:  # renewal paperwork signed after the term started, backdated
                signed = new_start + timedelta(days=r.randint(*s["late_signing_days"]))
            vl = self.rng("very_late", acc["account_id"], new_start.isoformat())
            if vl.random() < s["very_late_signing_share"]:  # evergreen renewals papered months after the term started
                signed = new_start + timedelta(days=vl.randint(*s["very_late_signing_days"]))
            start, ctype, months = new_start, "renewal", 12
        return acc

    def generate(self):
        s = self.spec
        month = d(s["start_date"])
        k = 0
        while month < self.extract:
            r = self.rng("month", month.isoformat())
            n = max(0, int(round(r.gauss(s["new_customers_per_month"], 4))))
            for i in range(n):
                k += 1
                rr = self.rng("cust", month.isoformat(), i)
                first_start = month + timedelta(days=rr.randint(0, 27))
                source = "inbound" if rr.random() > s["outbound_precreate_share"] else "outbound"
                lo, hi = s["inbound_lead_days" if source == "inbound" else "outbound_lead_days"]
                created = first_start - timedelta(days=rr.randint(lo, hi))
                acc = self.add_account(created, source, rr)
                size = rr.random()
                arr0 = math.exp(rr.gauss(math.log(18000), 0.9)) * s["arr_scale"] * self.price_factor(first_start)
                self.customer_lifecycle(acc, first_start, round(arr0, 2), rr)
            for i in range(s["never_convert_prospects_per_month"]):
                rr = self.rng("prospect", month.isoformat(), i)
                self.add_account(month + timedelta(days=rr.randint(0, 27)), rr.choice(["inbound", "outbound", "partner"]), rr)
            abm = s.get("abm")
            if abm and month >= d(abm["from"]):
                rr = self.rng("abm", month.isoformat())
                for i in range(abm["prospects_per_month"]):
                    created = month + timedelta(days=rr.randint(0, 4))
                    acc = self.add_account(created, "abm_target_list", rr)
                    if rr.random() < abm["convert_share"]:
                        first_start = add_months(created, rr.randint(*abm["lead_months"])) + timedelta(days=rr.randint(0, 25))
                        if first_start < self.extract:
                            arr0 = math.exp(rr.gauss(math.log(42000), 0.8)) * s["arr_scale"] * self.price_factor(first_start)
                            self.customer_lifecycle(acc, first_start, round(arr0, 2), rr)
            month = add_months(month, 1)
        bd = s.get("big_deal")
        if bd:
            rr = self.rng("bigdeal")
            big = max((a for a in self.accounts if a["source"] != "abm_target_list"),
                      key=lambda a: sum(ln["arr_usd"] for ln in self.lines if ln["account_id"] == a["account_id"]
                                        and ln["line_type"] == "recurring" and ln["start_date"] <= d(bd["date"]) < ln["end_date"]))
            cur_end = max((ln["end_date"] for ln in self.lines if ln["account_id"] == big["account_id"]
                           and ln["start_date"] <= d(bd["date"]) < ln["end_date"]), default=add_months(d(bd["date"]), 12))
            cid = f"CT-{len(self.contracts) + 1:07d}"
            self.contracts.append(dict(contract_id=cid, account_id=big["account_id"], signed_at=d(bd["date"]) - timedelta(days=9),
                                       contract_type="upsell"))
            self.lines.append(dict(contract_id=cid, account_id=big["account_id"], product="core", line_type="recurring",
                                   start_date=d(bd["date"]), end_date=cur_end, arr_usd=float(bd["arr"])))
        ba = s.get("boundary_arr_accounts")
        if ba:  # single-product customers whose contract ARR sits exactly on a segment threshold
            rr = self.rng("boundary")
            lo, hi = d(ba["from"]), d(ba["to"])
            for value in ba["values"]:
                for i in range(ba["per_value"]):
                    start = lo + timedelta(days=rr.randint(0, (hi - lo).days))
                    acc = self.add_account(start - timedelta(days=rr.randint(5, 60)), "inbound", rr)
                    self.amend(acc, start - timedelta(days=rr.randint(3, 20)), start, add_months(start, 12), "new_business",
                               "core", round(value, 2))
        return self

    def write(self, root: Path):
        root = Path(root)
        (root / "data").mkdir(parents=True, exist_ok=True)
        path = root / "data/warehouse.db"
        if path.exists():
            path.unlink()
        con = sqlite3.connect(path)
        con.executescript(DDL)
        con.executemany("INSERT INTO crm_accounts VALUES (?,?,?,?,?,?)", [
            (a["account_id"], a["name"], a["created_at"].isoformat() + " 09:00:00", a["source"], a["industry"], a["region"])
            for a in sorted(self.accounts, key=lambda a: a["account_id"]) if a["created_at"] < self.extract])
        valid = {c["contract_id"] for c in self.contracts if c["signed_at"] < self.extract}
        con.executemany("INSERT INTO contracts VALUES (?,?,?,?)", [
            (c["contract_id"], c["account_id"], c["signed_at"].isoformat(), c["contract_type"]) for c in self.contracts
            if c["contract_id"] in valid])
        rows = [ln for ln in self.lines if ln["contract_id"] in valid and ln["end_date"] > ln["start_date"] and ln["arr_usd"] > 0]
        rows.sort(key=lambda ln: (ln["start_date"], ln["account_id"], ln["contract_id"], ln["product"], ln["arr_usd"]))
        con.executemany("INSERT INTO subscription_lines VALUES (?,?,?,?,?,?,?,?)", [
            (f"SL-{i:08d}", ln["contract_id"], ln["account_id"], ln["product"], ln["line_type"], ln["start_date"].isoformat(),
             ln["end_date"].isoformat(), ln["arr_usd"]) for i, ln in enumerate(rows, 1)])
        pi = self.spec.get("price_increase")
        if pi:
            con.execute("INSERT INTO price_changes VALUES (?,?,?)", ("PRICE-2025", pi["from"], pi["uplift"]))
        con.commit()
        con.execute("VACUUM")
        con.close()


DDL = """
CREATE TABLE crm_accounts (account_id TEXT PRIMARY KEY, account_name TEXT NOT NULL, created_at TEXT NOT NULL, source TEXT NOT NULL,
  industry TEXT NOT NULL, region TEXT NOT NULL);
CREATE TABLE contracts (contract_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, signed_at TEXT NOT NULL, contract_type TEXT NOT NULL);
CREATE TABLE subscription_lines (line_id TEXT PRIMARY KEY, contract_id TEXT NOT NULL, account_id TEXT NOT NULL, product TEXT NOT NULL,
  line_type TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, arr_usd REAL NOT NULL);
CREATE TABLE price_changes (program_id TEXT PRIMARY KEY, effective_from TEXT NOT NULL, renewal_uplift REAL NOT NULL);
CREATE INDEX ix_lines_account ON subscription_lines(account_id, start_date);
CREATE INDEX ix_contracts_account ON contracts(account_id);
"""


def sqlite_logical_digest(db_path: Path) -> str:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    h = hashlib.sha256()
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        cols = [c[1] for c in con.execute(f'PRAGMA table_info("{t}")')]
        h.update(f"#{t}|{'|'.join(cols)}\n".encode())
        for row in con.execute(f'SELECT * FROM "{t}" ORDER BY {",".join(chr(34) + c + chr(34) for c in cols)}'):
            h.update((json.dumps(row) + "\n").encode())
    con.close()
    return h.hexdigest()


def build(spec: dict, root: Path) -> World:
    w = World(copy.deepcopy(spec)).generate()
    w.write(root)
    return w


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    build(VISIBLE_SPEC, out)
    print(sqlite_logical_digest(out / "data/warehouse.db"))
