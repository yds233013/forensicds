#!/usr/bin/env python3
"""Deterministic synthetic enterprise world for ForensicDS Task 01.

Generates the authoritative source extracts a B2B SaaS revenue pipeline reads:

  data/billing/billing.db            SQLite billing system extract (authoritative)
  data/crm/crm_accounts_export.csv   CRM account export (one row per account
                                     record version x billing-account link)
  data/crm/account_migrations.csv    Billing Ops migration register (one row per
                                     legacy -> successor relation)

Standard library only, fully determined by the spec dict (seeded RNG, sorted
iteration everywhere, no set/dict-order or hash-seed dependence), so the hidden
verifier can regenerate byte-identical pristine data and novel hidden fixtures.

This file is NOT shipped to the agent: the Docker build runs it and deletes it.
A byte-identical copy lives in tests/ for the verifier.
"""
from __future__ import annotations

import calendar
import csv
import hashlib
import json
import random
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

# --------------------------------------------------------------------------- #
# Calendar helpers
# --------------------------------------------------------------------------- #


def d(s: str) -> date:
    return date.fromisoformat(s)


def month_start(x: date) -> date:
    return x.replace(day=1)


def month_end(x: date) -> date:
    return x.replace(day=calendar.monthrange(x.year, x.month)[1])


def add_months(x: date, n: int) -> date:
    """First day of the month n months after x's month."""
    y, m = divmod(x.month - 1 + n, 12)
    return date(x.year + y, m + 1, 1)


def add_years_minus_day(x: date, years: int = 1) -> date:
    try:
        return x.replace(year=x.year + years) - timedelta(days=1)
    except ValueError:  # Feb 29
        return x.replace(year=x.year + years, day=28)


def ym(x: date) -> str:
    return f"{x.year:04d}-{x.month:02d}"


def iso(x: date | None) -> str:
    return x.isoformat() if x else ""


# --------------------------------------------------------------------------- #
# Static vocabularies (fictional)
# --------------------------------------------------------------------------- #

NAME_A = [
    "Kestrel", "Northgate", "Bluefin", "Harbor", "Summit", "Ironwood", "Cobalt", "Meridian",
    "Juniper", "Granite", "Larkspur", "Silverline", "Redwood", "Aster", "Beacon", "Copperleaf",
    "Driftwood", "Evergreen", "Falcon", "Glacier", "Halden", "Indigo", "Kinsale", "Lumen",
    "Marlow", "Nimbus", "Oakridge", "Pinecrest", "Quarry", "Riverton", "Sable", "Tamarack",
    "Umber", "Vantage", "Westfield", "Yarrow", "Zephyr", "Alder", "Brightwater", "Cedarline",
    "Dunmore", "Emberly", "Foxglove", "Greystone", "Hollis", "Ivory", "Jasper", "Keystone",
    "Lindell", "Moorland", "Norcross", "Orchard", "Pembrook", "Quill", "Rosemont", "Stratus",
    "Thornbury", "Upland", "Verity", "Wexford",
]
NAME_B = [
    "Logistics", "Health", "Analytics", "Foods", "Energy", "Robotics", "Capital", "Retail",
    "Biosciences", "Media", "Insurance", "Manufacturing", "Telecom", "Hospitality", "Learning",
    "Mobility", "Payments", "Security", "Labs", "Software", "Freight", "Pharma", "Materials",
    "Networks", "Outdoor", "Apparel", "Dental", "Travel", "Aerospace", "Ventures",
]
SUFFIX = {"US": "Inc.", "CA": "Ltd.", "GB": "Ltd", "DE": "GmbH", "FR": "SAS", "NL": "B.V.",
          "IE": "Ltd", "SG": "Pte. Ltd.", "AU": "Pty Ltd", "JP": "K.K."}
OWNERS = {
    "NA": ["Dana Whitfield", "Marcus Oyelaran", "Priya Raman", "Tom Castellano", "Renee Park",
           "Jordan Ellis", "Keisha Lambert", "Victor Nguyen", "Alyssa Brandt", "Omar Haddad"],
    "EMEA": ["Sophie Laurent", "Henrik Dahl", "Aoife Byrne", "Matteo Russo", "Katrin Vogel",
             "Liam Fairbanks", "Noor El-Amin"],
    "APAC": ["Mei Tanaka", "Arjun Mehta", "Chloe Watts", "Daniel Koh"],
}
REGION_COUNTRIES = {
    "NA": [("US", "USD", 0.85), ("CA", "USD", 0.15)],
    "EMEA": [("GB", "GBP", 0.35), ("DE", "EUR", 0.25), ("FR", "EUR", 0.15), ("NL", "EUR", 0.1),
             ("IE", "USD", 0.15)],
    "APAC": [("SG", "USD", 0.45), ("AU", "USD", 0.35), ("JP", "USD", 0.2)],
}

# plan_code -> (name, interval, list unit price minor (USD), kind)
PLANS = {
    "STARTER_M": ("Starter (monthly, per seat)", "month", 4900, "seats"),
    "GROWTH_M": ("Growth (monthly, per seat)", "month", 4500, "seats"),
    "BUSINESS_A": ("Business (annual, per seat)", "year", 60000, "seats"),
    "ENTERPRISE_A": ("Enterprise (annual, per seat)", "year", 72000, "seats"),
    "PREMIUM_SUPPORT_A": ("Premium Support (annual)", "year", 0, "support"),
    "ANALYTICS_ADDON_M": ("Analytics add-on (monthly, per seat)", "month", 1200, "seats"),
    "SUCCESS_PLUS_M": ("Customer Success Plus (monthly)", "month", 0, "support"),
    "API_USAGE": ("API usage (metered, billed in arrears)", "usage", 0, "usage"),
}

REVENUE_LINE_TYPES = ("subscription", "usage", "onboarding", "discount")

# --------------------------------------------------------------------------- #
# Default (public workspace) world spec
# --------------------------------------------------------------------------- #

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 73019,
    "go_live": "2025-09-01",
    "close_month": "2026-08",
    "extract_date": "2026-09-03",
    "segments": {"Enterprise": 40, "Mid-Market": 110, "SMB": 190},
    "new_customer_share": 0.22,
    "id_base": {"account": 100000, "billing": 230000},
    "fx": {
        "EUR": {"base": 1.086, "walk": 0.006, "shocks": {"2026-08": 0.021}},
        "GBP": {"base": 1.268, "walk": 0.005, "shocks": {"2026-08": 0.012}},
    },
    "price_changes": [{"plan_code": "GROWTH_M", "effective": "2026-08-01", "unit_price_minor": 4900}],
    "realignments": [{"date": "2026-08-01", "share": 0.30}, {"date": "2026-03-16", "share": 0.04}],
    "incidents": [{"date": "2026-08-14", "n_accounts": 34, "credit_pct": 0.10,
                   "issue_after_days": [6, 13], "force_migrated_legacy": 2}],
    "similar_ids": 0,
    "migrations": [
        # Q1/Q2 program: immediate cutover, legacy CRM record closed on the effective date,
        # CRM migration tool did not yet carry billing links to successors.
        {"kind": "single", "style": "closed", "effective": "2026-02-01", "copy_links": False,
         "select": {"segment": "Mid-Market", "billing": "monthly_only"}},
        {"kind": "single", "style": "closed", "effective": "2026-04-01", "copy_links": False,
         "select": {"segment": "SMB", "billing": "monthly_only"}},
        # Account moved twice: closed cutover in March, then staged in the August wave.
        {"kind": "chain", "select": {"segment": "Mid-Market", "billing": "monthly_only"},
         "hops": [{"style": "closed", "effective": "2026-03-01", "copy_links": False},
                  {"style": "staged", "effective": "2026-08-12", "cutover_closed": None,
                   "copy_links": True}]},
        # August Enterprise Contract Migration wave 1: staged cutovers.
        {"kind": "single", "style": "staged", "effective": "2026-08-03", "cutover_closed": None,
         "copy_links": True, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 3}},
        {"kind": "single", "style": "staged", "effective": "2026-08-05", "cutover_closed": None,
         "copy_links": True, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 11}},
        {"kind": "single", "style": "staged", "effective": "2026-08-06", "cutover_closed": "2026-08-28",
         "copy_links": True, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 5}},
        {"kind": "single", "style": "staged", "effective": "2026-08-10", "cutover_closed": None,
         "copy_links": True, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 14}},
        {"kind": "single", "style": "staged", "effective": "2026-08-19", "cutover_closed": None,
         "copy_links": True, "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 20}},
        {"kind": "consolidation", "n_sources": 2, "style": "staged", "effective": "2026-08-17",
         "cutover_closed": None, "copy_links": True,
         "select": {"segment": "Enterprise", "region": "EMEA", "billing": "has_annual", "size_rank": 30}},
        # Wave 2: planned, not yet effective.
        {"kind": "scheduled", "effective": "2026-09-14",
         "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 12}},
        {"kind": "scheduled", "effective": "2026-09-21",
         "select": {"segment": "Enterprise", "billing": "has_annual", "size_rank": 25}},
    ],
}


# --------------------------------------------------------------------------- #
# Generator
# --------------------------------------------------------------------------- #


class World:
    def __init__(self, spec: dict):
        self.spec = spec
        self.rng = random.Random(spec["seed"])
        self.go_live = d(spec["go_live"])
        self.close_month = d(spec["close_month"] + "-01")
        self.open_month = add_months(self.close_month, 1)
        self.extract = d(spec["extract_date"])
        self.accounts: dict[str, dict] = {}
        self.bas: dict[str, dict] = {}
        self.subs: list[dict] = []
        self.register: list[dict] = []
        self.used_names: set[str] = set()
        self.used_acc_ids: set[int] = set()
        self.next_ba = spec["id_base"]["billing"] + 1
        self.next_sub = 1
        self.migrated: set[str] = set()  # accounts touched by any migration (legacy or successor)

    # ---------------- ids & names ----------------
    def new_account_id(self) -> str:
        base = self.spec["id_base"]["account"]
        while True:
            n = self.rng.randint(base + 1000, base + 899999)
            if n not in self.used_acc_ids:
                self.used_acc_ids.add(n)
                return f"ACC-{n:06d}"

    def new_ba_id(self) -> str:
        n = self.next_ba
        self.next_ba += 1
        return f"BA-{n:06d}"

    def new_name(self) -> str:
        while True:
            name = f"{self.rng.choice(NAME_A)} {self.rng.choice(NAME_B)}"
            if name not in self.used_names:
                self.used_names.add(name)
                return name

    def pick_weighted(self, options):
        r = self.rng.random()
        acc = 0.0
        for *vals, w in options:
            acc += w
            if r <= acc:
                return vals
        return options[-1][:-1]

    # ---------------- plans & prices ----------------
    def plan_rows(self) -> list[dict]:
        rows = []
        changes = {c["plan_code"]: c for c in self.spec.get("price_changes", [])}
        for code in sorted(PLANS):
            name, interval, price, _kind = PLANS[code]
            if code in changes:
                eff = d(changes[code]["effective"])
                rows.append(dict(plan_code=code, plan_version=1, plan_name=name, billing_interval=interval,
                                 list_unit_price_minor=price, currency="USD", effective_from="2024-01-01",
                                 effective_to=iso(eff - timedelta(days=1))))
                rows.append(dict(plan_code=code, plan_version=2, plan_name=name, billing_interval=interval,
                                 list_unit_price_minor=changes[code]["unit_price_minor"], currency="USD",
                                 effective_from=iso(eff), effective_to=""))
            else:
                rows.append(dict(plan_code=code, plan_version=1, plan_name=name, billing_interval=interval,
                                 list_unit_price_minor=price, currency="USD", effective_from="2024-01-01",
                                 effective_to=""))
        return rows

    def list_price(self, code: str, on: date) -> int:
        price = PLANS[code][2]
        for c in self.spec.get("price_changes", []):
            if c["plan_code"] == code and on >= d(c["effective"]):
                price = c["unit_price_minor"]
        return price

    def fx_rates(self) -> list[dict]:
        rows = []
        months = []
        m = month_start(self.go_live)
        while m <= month_start(self.extract):
            months.append(m)
            m = add_months(m, 1)
        frng = random.Random(f"fx:{self.spec['seed']}")
        for cur in sorted(self.spec["fx"]):
            cfg = self.spec["fx"][cur]
            rate = cfg["base"]
            for m in months:
                rate = rate * (1 + frng.uniform(-cfg["walk"], cfg["walk"]))
                rate = rate * (1 + cfg.get("shocks", {}).get(ym(m), 0.0))
                rows.append(dict(currency=cur, rate_month=ym(m), usd_per_unit=round(rate, 6),
                                 rate_type="monthly_average", source="treasury_feed"))
        for m in months:
            rows.append(dict(currency="USD", rate_month=ym(m), usd_per_unit=1.0,
                             rate_type="monthly_average", source="treasury_feed"))
        return rows

    # ---------------- customers ----------------
    def build_customers(self):
        segs = self.spec["segments"]
        region_w = {"Enterprise": [("NA", .55), ("EMEA", .35), ("APAC", .10)],
                    "Mid-Market": [("NA", .60), ("EMEA", .28), ("APAC", .12)],
                    "SMB": [("NA", .62), ("EMEA", .26), ("APAC", .12)]}
        for seg in ["Enterprise", "Mid-Market", "SMB"]:
            for _ in range(segs[seg]):
                (region,) = self.pick_weighted(region_w[seg])
                country, currency = self.pick_weighted(REGION_COUNTRIES[region])
                is_new = self.rng.random() < self.spec["new_customer_share"]
                if is_new:
                    span = (month_end(self.close_month) - self.go_live).days
                    created = self.go_live + timedelta(days=self.rng.randint(20, span - 5))
                    start = created
                else:
                    created = date(2018, 1, 1) + timedelta(days=self.rng.randint(0, 2700))
                    if created > self.go_live - timedelta(days=30):
                        # pre-existing customers always predate billing go-live
                        created = self.go_live - timedelta(days=30 + (created - date(2018, 1, 1)).days % 900)
                    start = self.go_live
                acc = self.make_account(self.new_name(), seg, region, country, currency, created,
                                        owner=self.rng.choice(OWNERS[region]))
                acc["is_new"] = is_new
                ba = self.make_ba(acc, country, currency, created if is_new else date(2025, 8, 18))
                self.base_subscriptions(acc, ba, start, is_new)
                # A few Enterprise customers run a second billing account for another entity.
                if seg == "Enterprise" and not is_new and self.rng.random() < 0.12:
                    c2, cur2 = ("GB", "GBP") if region == "NA" else ("US", "USD")
                    ba2 = self.make_ba(acc, c2, cur2, date(2025, 8, 18), entity_suffix=True)
                    self.add_sub(ba2, "ENTERPRISE_A", self.rng.randint(80, 300) * 1,
                                 self.rng.randint(420, 640) * 100, start, pricing="contract",
                                 stub_end=self.stub_end(start))
        self.apply_churn_and_blocks()

    def make_account(self, name, seg, region, country, currency, created, owner) -> dict:
        acc = dict(id=self.new_account_id(), name=name, segment=seg, region=region, country=country,
                   currency=currency, created=created, owner=owner, owner_changes=[], status_events=[],
                   legacy_links=[], is_new=False)
        self.accounts[acc["id"]] = acc
        return acc

    def make_ba(self, acc, country, currency, created, entity_suffix=False, name=None) -> dict:
        base = name or acc["name"]
        legal = f"{base} {SUFFIX[country]}"
        if entity_suffix:
            legal = f"{base} ({country}) {SUFFIX[country]}"
        ba = dict(id=self.new_ba_id(), crm_account_id=acc["id"], legal_entity_name=legal,
                  billing_country=country, currency=currency, status="active", created=created, closed=None,
                  tax_rate=self.tax_rate(country))
        self.bas[ba["id"]] = ba
        return ba

    def tax_rate(self, country) -> float:
        if country in ("GB", "DE", "FR", "NL", "IE"):
            return 0.20
        if country == "US":
            return 0.0725 if self.rng.random() < 0.4 else 0.0
        if country == "AU":
            return 0.10
        return 0.0

    def stub_end(self, start: date) -> date | None:
        anniv = self.rng.randint(1, 12)
        if anniv == start.month:
            return None
        first = date(start.year if anniv > start.month else start.year + 1, anniv, 1)
        return first - timedelta(days=1)

    def add_sub(self, ba, code, qty, unit_price, start, pricing="list", end=None, stub_end=None,
                discount=0.0, usage_base=0, block=False) -> dict:
        s = dict(id=f"SUB-{self.next_sub:06d}", ba=ba["id"], plan=code, interval=PLANS[code][1],
                 kind=PLANS[code][3], qty=qty, unit_price=unit_price, pricing=pricing, start=start,
                 end=end, stub_end=stub_end, discount=discount, usage_base=usage_base, block=block,
                 onboarding=0)
        self.next_sub += 1
        self.subs.append(s)
        return s

    def base_subscriptions(self, acc, ba, start, is_new):
        seg = acc["segment"]
        r = self.rng
        if seg == "SMB":
            code = "STARTER_M" if r.random() < 0.45 else "GROWTH_M"
            self.add_sub(ba, code, r.randint(5, 40), self.list_price(code, start), start)
        elif seg == "Mid-Market":
            if r.random() < 0.55:
                disc = r.choice([0.0, 0.0, 0.05, 0.10])
                self.add_sub(ba, "GROWTH_M", r.randint(40, 250), self.list_price("GROWTH_M", start), start,
                             discount=disc)
            else:
                self.add_sub(ba, "BUSINESS_A", r.randint(50, 300), r.randint(480, 600) * 100, start,
                             pricing="contract", stub_end=None if is_new else self.stub_end(start),
                             discount=r.choice([0.0, 0.05]))
            if r.random() < 0.30:
                self.add_sub(ba, "ANALYTICS_ADDON_M", r.randint(20, 120), self.list_price("ANALYTICS_ADDON_M", start),
                             start)
            if r.random() < 0.25:
                self.add_sub(ba, "API_USAGE", 1, 0, start, pricing="metered", usage_base=r.randint(800, 4000) * 100)
            if is_new:
                self.subs[-1]["onboarding"] = 0  # placeholder, set on first sub below
                first = next(s for s in self.subs if s["ba"] == ba["id"])
                first["onboarding"] = r.randint(4, 12) * 100000
        else:
            stub = None if is_new else self.stub_end(start)
            seats = r.randint(600, 3500)
            main = self.add_sub(ba, "ENTERPRISE_A", seats, r.randint(380, 650) * 100, start, pricing="contract",
                                stub_end=stub, discount=r.choice([0.0, 0.0, 0.08, 0.12]))
            if r.random() < 0.7:
                self.add_sub(ba, "PREMIUM_SUPPORT_A", 1, r.randint(30, 150) * 100000, start, pricing="contract",
                             stub_end=stub)
            if r.random() < 0.8:
                self.add_sub(ba, "API_USAGE", 1, 0, start, pricing="metered", usage_base=r.randint(4000, 35000) * 100)
            if is_new:
                main["onboarding"] = r.randint(25, 60) * 100000

    def apply_churn_and_blocks(self):
        r = self.rng
        for acc_id in sorted(self.accounts):
            acc = self.accounts[acc_id]
            if acc["segment"] == "Enterprise":
                continue
            ba_ids = [b for b in sorted(self.bas) if self.bas[b]["crm_account_id"] == acc_id]
            subs = [s for s in self.subs if s["ba"] in ba_ids]
            monthly_only = all(s["interval"] != "year" for s in subs)
            u = r.random()
            if monthly_only and u < 0.06:
                first = max(s["start"] for s in subs)
                lo = add_months(max(first, self.go_live), 2)
                if lo < self.close_month:
                    months = (self.close_month.year - lo.year) * 12 + self.close_month.month - lo.month
                    end = month_end(add_months(lo, r.randint(0, max(months - 1, 0))))
                    for s in subs:
                        s["end"] = end
                    acc["churned"] = end
                    for b in ba_ids:
                        self.bas[b]["status"] = "closed"
                        self.bas[b]["closed"] = end
            elif u < 0.22:
                # Additional seat block on the same plan and terms: identical invoice lines.
                seat_subs = [s for s in subs if s["kind"] == "seats" and s["interval"] == "month"]
                if seat_subs:
                    s0 = seat_subs[0]
                    lo = max(s0["start"], self.go_live) + timedelta(days=15)
                    span = (month_end(self.close_month) - lo).days
                    if span > 40:
                        bstart = lo + timedelta(days=r.randint(0, span - 20))
                        if r.random() < 0.5:
                            bstart = month_start(add_months(bstart, 1))
                        self.add_sub(self.bas[s0["ba"]], s0["plan"], s0["qty"], s0["unit_price"], bstart,
                                     pricing=s0["pricing"], discount=s0["discount"], block=True)

    # ---------------- ARR & selection ----------------
    def arr(self, acc_id) -> float:
        tot = 0.0
        for s in self.subs:
            if self.bas[s["ba"]]["crm_account_id"] != acc_id:
                continue
            if s["interval"] == "year":
                tot += s["qty"] * s["unit_price"]
            elif s["interval"] == "month":
                tot += 12 * s["qty"] * s["unit_price"]
            else:
                tot += 12 * s["usage_base"]
        return tot

    def select(self, sel: dict, effective: date, n: int = 1) -> list[str]:
        cands = []
        for acc_id in sorted(self.accounts):
            acc = self.accounts[acc_id]
            if acc_id in self.migrated or acc.get("churned") or acc.get("scheduled"):
                continue
            if acc["segment"] != sel["segment"]:
                continue
            if sel.get("region") and acc["region"] != sel["region"]:
                continue
            if acc["created"] > effective - timedelta(days=90):
                continue
            ba_ids = [b for b in self.bas if self.bas[b]["crm_account_id"] == acc_id]
            if len(ba_ids) != 1:
                continue
            subs = [s for s in self.subs if s["ba"] == ba_ids[0]]
            has_annual = any(s["interval"] == "year" for s in subs)
            if sel.get("billing") == "monthly_only" and (has_annual or any(s["block"] for s in subs)):
                continue
            if sel.get("billing") == "has_annual" and not has_annual:
                continue
            if sel.get("currency") and acc["currency"] != sel["currency"]:
                continue
            cands.append(acc_id)
        if len(cands) < n:
            raise RuntimeError(f"not enough candidates for {sel}")
        if "size_rank" in sel:
            cands.sort(key=lambda a: (-self.arr(a), a))
            k = min(sel["size_rank"], len(cands) - n)
            return cands[k:k + n]
        return self.rng.sample(cands, n)

    # ---------------- migrations ----------------
    def build_migrations(self):
        counter = 0
        for prog in self.spec["migrations"]:
            kind = prog["kind"]
            if kind == "scheduled":
                (legacy,) = self.select(prog["select"], d(prog["effective"]))
                self.accounts[legacy]["scheduled"] = True
                counter += 1
                ba = self.single_ba(legacy)
                self.register.append(dict(
                    legacy_account_id=legacy, successor_account_id=self.reserve_successor_id(),
                    legacy_billing_account_id=ba, successor_billing_account_id="",
                    migration_type="entity_transfer", cutover_mode="staged", effective_date=prog["effective"],
                    cutover_closed_date="", status="scheduled"))
                continue
            if kind == "single":
                (legacy,) = self.select(prog["select"], d(prog["effective"]))
                self.migrate([legacy], prog)
            elif kind == "consolidation":
                legacies = self.select(prog["select"], d(prog["effective"]), n=prog["n_sources"])
                self.migrate(legacies, prog, consolidation=True)
            elif kind == "chain":
                first_eff = d(prog["hops"][0]["effective"])
                (cur,) = self.select(prog["select"], first_eff)
                for hop in prog["hops"]:
                    cur = self.migrate([cur], hop)
        # stable register ids by effective date
        self.register.sort(key=lambda r: (r["effective_date"], r["legacy_account_id"]))
        tick = 4100
        for i, row in enumerate(self.register, 1):
            row["migration_id"] = f"MIG-{row['effective_date'][:4]}-{i:04d}"
            row["change_ticket"] = f"BOPS-{tick + 17 * i}"

    def reserve_successor_id(self) -> str:
        return self.new_account_id()

    def single_ba(self, acc_id) -> str:
        (ba,) = [b for b in sorted(self.bas) if self.bas[b]["crm_account_id"] == acc_id]
        return ba

    def migrate(self, legacies: list[str], hop: dict, consolidation: bool = False) -> str:
        E = d(hop["effective"])
        style = hop["style"]
        if style == "closed" and E.day != 1:
            raise ValueError("closed-style migrations take effect on the 1st")
        closed_on = d(hop["cutover_closed"]) if hop.get("cutover_closed") else None
        la = self.accounts[legacies[0]]
        if consolidation:
            name = f"{la['name'].split()[0]} Group"
            if name in self.used_names:
                name = f"{la['name'].split()[0]} Holdings"
            self.used_names.add(name)
        else:
            name = la["name"] if self.rng.random() < 0.5 else f"{la['name']} Global"
        country, currency = la["country"], la["currency"]
        succ = self.make_account(name, la["segment"], la["region"], country, currency, E, owner=la["owner"])
        # owner at E is the legacy's owner as of E
        succ["owner"] = self.owner_at(la, E)
        new_ba = self.make_ba(succ, country, currency, E, name=name)
        self.migrated.add(succ["id"])
        for legacy in legacies:
            acc = self.accounts[legacy]
            self.migrated.add(legacy)
            ba_id = self.single_ba(legacy)
            if hop.get("copy_links", True):
                links = [ba_id] + list(acc["legacy_links"])
                for b in links:
                    if b not in succ["legacy_links"]:
                        succ["legacy_links"].append(b)
            end_crm = E if style == "closed" else closed_on
            acc["status_events"].append(dict(date=E, status="Migrated", successor=succ["id"], valid_to=end_crm))
            self.transform_subscriptions(ba_id, new_ba, E, style)
            if style == "closed":
                self.bas[ba_id]["status"] = "closed"
                self.bas[ba_id]["closed"] = E - timedelta(days=1)
            status = "completed" if (style == "closed" or closed_on is not None) else "cutover_in_progress"
            self.register.append(dict(
                legacy_account_id=legacy, successor_account_id=succ["id"], legacy_billing_account_id=ba_id,
                successor_billing_account_id=new_ba["id"],
                migration_type="entity_consolidation" if consolidation else "entity_transfer",
                cutover_mode="immediate" if style == "closed" else "staged", effective_date=iso(E),
                cutover_closed_date=iso(E if style == "closed" else closed_on), status=status))
        if style == "staged" and succ["segment"] == "Enterprise":
            self.add_sub(new_ba, "SUCCESS_PLUS_M", 1, self.rng.randint(30, 120) * 10000, E, pricing="contract")
        return succ["id"]

    def owner_at(self, acc, on: date) -> str:
        owner = acc["owner"]
        for ch_date, ch_owner in sorted(acc["owner_changes"]):
            if ch_date <= on:
                owner = ch_owner
        return owner

    def annual_term_containing(self, s, on: date) -> tuple[date, date]:
        for t_start, t_end, _bill, _amt in self.annual_terms(s, horizon=date(2100, 1, 1), stop_after=on):
            if t_start <= on <= t_end:
                return t_start, t_end
        raise RuntimeError("no term")

    def transform_subscriptions(self, old_ba_id, new_ba, E: date, style: str):
        for s in [s for s in self.subs if s["ba"] == old_ba_id]:
            if s["start"] > E or (s["end"] is not None and s["end"] < E):
                continue
            if s["kind"] == "usage":
                s["end"] = E - timedelta(days=1)
                self.add_sub(new_ba, s["plan"], 1, 0, E, pricing="metered", usage_base=s["usage_base"])
            elif s["interval"] == "month":
                if style == "closed":
                    s["end"] = E - timedelta(days=1)
                    nstart = E
                else:
                    s["end"] = month_end(E)
                    nstart = add_months(E, 1)
                self.add_sub(new_ba, s["plan"], s["qty"], s["unit_price"], nstart, pricing=s["pricing"],
                             discount=s["discount"], block=s["block"])
            else:
                if style == "closed":
                    raise ValueError("closed-style migration of annual contracts is not modelled")
                _t0, t_end = self.annual_term_containing(s, E)
                s["end"] = t_end
                self.add_sub(new_ba, s["plan"], s["qty"], s["unit_price"], t_end + timedelta(days=1),
                             pricing=s["pricing"], discount=s["discount"])

    # ---------------- owner realignments & similar ids ----------------
    def build_realignments(self):
        for re_ in self.spec.get("realignments", []):
            on = d(re_["date"])
            for acc_id in sorted(self.accounts):
                acc = self.accounts[acc_id]
                if acc["created"] >= on or acc.get("churned") and acc["churned"] < on:
                    continue
                if any(ev["date"] <= on + timedelta(days=45) for ev in acc["status_events"]):
                    continue
                if acc_id in self.migrated and acc["created"] >= on - timedelta(days=45):
                    continue
                if self.rng.random() < re_["share"]:
                    cur = self.owner_at(acc, on)
                    choices = [o for o in OWNERS[acc["region"]] if o != cur]
                    acc["owner_changes"].append((on, self.rng.choice(choices)))

    def apply_similar_ids(self):
        n = self.spec.get("similar_ids", 0)
        if not n:
            return
        legacy_ids = sorted({r["legacy_account_id"] for r in self.register if r["status"] != "scheduled"})
        plain = [a for a in sorted(self.accounts) if a not in self.migrated]
        for i in range(min(n, len(legacy_ids))):
            src = legacy_ids[i]
            digits = src[4:]
            new = f"ACC-{digits[:-2]}{digits[-1]}{digits[-2]}"
            if new == src or new in self.accounts:
                new = f"ACC-{digits}"[:-1] + str((int(digits[-1]) + 1) % 10)
            if new in self.accounts:
                continue
            victim = plain[(i * 7 + 3) % len(plain)]
            acc = self.accounts.pop(victim)
            acc["id"] = new
            self.accounts[new] = acc
            for b in self.bas.values():
                if b["crm_account_id"] == victim:
                    b["crm_account_id"] = new

    def renumber_billing_accounts(self):
        """Billing assigns account numbers sequentially by creation date."""
        order = sorted(self.bas.values(), key=lambda b: (b["created"], b["id"]))
        base = self.spec["id_base"]["billing"]
        remap = {b["id"]: f"BA-{base + i:06d}" for i, b in enumerate(order, 1)}
        self.bas = {remap[b["id"]]: dict(b, id=remap[b["id"]]) for b in order}
        for s in self.subs:
            s["ba"] = remap[s["ba"]]
        for acc in self.accounts.values():
            acc["legacy_links"] = [remap[b] for b in acc["legacy_links"]]
        for row in self.register:
            for k in ("legacy_billing_account_id", "successor_billing_account_id"):
                if row[k]:
                    row[k] = remap[row[k]]

    # ---------------- billing documents ----------------
    def annual_terms(self, s, horizon: date, stop_after: date | None = None):
        """Yield (service_start, service_end, bill_date, amount_minor) for an annual subscription."""
        out = []
        t = s["start"]
        if s["stub_end"] and s["stub_end"] > t:
            days = (s["stub_end"] - t).days + 1
            out.append((t, s["stub_end"], t, round(s["qty"] * s["unit_price"] * days / 365)))
            t = s["stub_end"] + timedelta(days=1)
        while t <= horizon and (s["end"] is None or t <= s["end"]):
            te = add_years_minus_day(t)
            out.append((t, te, t, s["qty"] * s["unit_price"]))
            if stop_after and te >= stop_after:
                break
            t = te + timedelta(days=1)
        return out

    def sub_terms(self, s) -> list[dict]:
        horizon = self.extract
        terms = []
        if s["kind"] == "usage":
            m = month_start(s["start"])
            last = s["end"] or month_end(self.extract)
            while m <= last:
                ss = max(s["start"], m)
                se = min(last, month_end(m))
                bill = add_months(m, 1)
                if bill > horizon or ss > se:
                    break
                days_frac = ((se - ss).days + 1) / ((month_end(m) - m).days + 1)
                urng = random.Random(f"usage:{self.spec['seed']}:{s['id']}:{ym(m)}")
                amt = round(s["usage_base"] * urng.uniform(0.6, 1.5) * days_frac)
                if amt > 0:
                    terms.append(dict(bill=bill, ss=ss, se=se, amount=amt, qty=1, unit=amt, line_type="usage",
                                      desc=f"API usage {ym(m)}"))
                m = add_months(m, 1)
            return terms
        if s["interval"] == "year":
            for ss, se, bill, amt in self.annual_terms(s, horizon):
                if bill > horizon:
                    break
                terms.append(dict(bill=bill, ss=ss, se=se, amount=amt, qty=s["qty"], unit=s["unit_price"],
                                  line_type="subscription", desc=PLANS[s["plan"]][0]))
        else:
            t = s["start"]
            while t <= horizon and (s["end"] is None or t <= s["end"]):
                me = month_end(t)
                if s["end"] is not None:
                    me = min(me, s["end"])
                price = self.list_price(s["plan"], t) if s["pricing"] == "list" else s["unit_price"]
                full = s["qty"] * price
                dim = calendar.monthrange(t.year, t.month)[1]
                days = (me - t).days + 1
                amt = full if days == dim else round(full * days / dim)
                terms.append(dict(bill=t, ss=t, se=me, amount=amt, qty=s["qty"], unit=price,
                                  line_type="subscription", desc=PLANS[s["plan"]][0]
                                  + ("" if days == dim else " (prorated)")))
                t = me + timedelta(days=1)
        if s["discount"]:
            for tm in list(terms):
                terms.append(dict(bill=tm["bill"], ss=tm["ss"], se=tm["se"], amount=-round(tm["amount"] * s["discount"]),
                                  qty=1, unit=-round(tm["amount"] * s["discount"]), line_type="discount",
                                  desc=f"Contract discount {int(round(s['discount'] * 100))}% - {s['plan']}"))
        if s["onboarding"] and s["start"] <= horizon:
            terms.append(dict(bill=s["start"], ss=s["start"], se=s["start"], amount=s["onboarding"], qty=1,
                              unit=s["onboarding"], line_type="onboarding", desc="Onboarding & implementation services"))
        return terms

    def build_billing(self):
        order = {"subscription": 0, "discount": 1, "usage": 2, "onboarding": 3}
        raw = []
        for s in self.subs:
            for t in self.sub_terms(s):
                raw.append((t["bill"], s["ba"], order[t["line_type"]], s["id"], t))
        raw.sort(key=lambda x: (x[0], x[1], x[2], x[3], x[4]["ss"]))
        invoices: list[dict] = []
        by_key: dict[tuple, dict] = {}
        for bill, ba, _o, sub_id, t in raw:
            key = (bill, ba)
            if key not in by_key:
                inv = dict(ba=ba, date=bill, lines=[], status="posted", replaces="")
                by_key[key] = inv
                invoices.append(inv)
            by_key[key]["lines"].append(dict(sub=sub_id, **t))
        # tax, status, ids
        vrng = random.Random(f"docs:{self.spec['seed']}")
        final = []
        for inv in invoices:
            ba = self.bas[inv["ba"]]
            sub = sum(l["amount"] for l in inv["lines"])
            if ba["tax_rate"] > 0 and sub > 0:
                tax = round(sub * ba["tax_rate"])
                inv["lines"].append(dict(sub="", bill=inv["date"], ss=inv["date"], se=inv["date"], amount=tax, qty=1,
                                         unit=tax, line_type="tax", desc=f"Tax {ba['tax_rate'] * 100:g}%"))
            if inv["date"] >= self.open_month:
                inv["status"] = "draft" if vrng.random() < 0.3 else "posted"
            final.append(inv)
            if inv["status"] == "posted" and inv["date"] < self.open_month and vrng.random() < 0.006:
                inv["status"] = "void"
                repl = dict(ba=inv["ba"], date=inv["date"], lines=[dict(l) for l in inv["lines"]],
                            status="posted", replaces=inv)
                final.append(repl)
        n_inv, n_line = 0, 0
        for inv in final:
            n_inv += 1
            inv["id"] = f"INV-{n_inv + 500000:07d}"
            for i, l in enumerate(inv["lines"], 1):
                n_line += 1
                l["id"] = f"IL-{n_line + 2000000:08d}"
                l["no"] = i
        for inv in final:
            if inv["replaces"]:
                inv["replaces"] = inv["replaces"]["id"]
        self.invoices = final

    def build_credit_notes(self):
        crng = random.Random(f"credits:{self.spec['seed']}")
        credits = []
        posted = [i for i in self.invoices if i["status"] == "posted"]
        for inv in posted:
            for l in inv["lines"]:
                if l["line_type"] != "subscription" or inv["date"] >= self.open_month:
                    continue
                if crng.random() < 0.012:
                    issued = inv["date"] + timedelta(days=crng.randint(3, 40))
                    if issued > self.extract:
                        continue
                    amt = round(l["amount"] * crng.uniform(0.05, 0.30))
                    credits.append(dict(inv=inv, line=l, issued=issued, amount=amt, reason="billing_correction",
                                        memo="Seat count correction"))
        for inc in self.spec.get("incidents", []):
            on = d(inc["date"])
            m0 = month_start(on)
            elig = {}
            for inv in posted:
                for l in inv["lines"]:
                    if l["line_type"] == "subscription" and l["ss"] <= m0 <= l["se"] and "prorated" not in l["desc"]:
                        ba = inv["ba"]
                        if ba not in elig or l["amount"] > elig[ba][1]["amount"]:
                            elig[ba] = (inv, l)
            keys = sorted(elig)
            legacy_bas = sorted({r["legacy_billing_account_id"] for r in self.register
                                 if r["status"] == "cutover_in_progress" and ym(d(r["effective_date"])) == ym(on)})
            forced = [b for b in legacy_bas if b in elig][: inc.get("force_migrated_legacy", 0)]
            others = [k for k in keys if k not in forced]
            chosen = forced + crng.sample(others, min(inc["n_accounts"] - len(forced), len(others)))
            for ba in sorted(chosen):
                inv, l = elig[ba]
                monthly = l["amount"] if (l["se"] - l["ss"]).days < 31 else l["amount"] / 12
                issued = on + timedelta(days=crng.randint(*inc["issue_after_days"]))
                if issued > self.extract:
                    continue
                credits.append(dict(inv=inv, line=l, issued=issued, amount=round(monthly * inc["credit_pct"]),
                                    reason="sla_credit", memo=f"SLA credit - incident {inc['date']}"))
        credits.sort(key=lambda c: (c["issued"], c["line"]["id"]))
        for i, c in enumerate(credits, 1):
            c["id"] = f"CN-{i + 70000:06d}"
        self.credits = credits

    # ---------------- CRM export ----------------
    def crm_rows(self) -> list[dict]:
        rows = []
        for acc_id in sorted(self.accounts):
            acc = self.accounts[acc_id]
            events = []
            for on, owner in acc["owner_changes"]:
                events.append((on, 0, dict(owner=owner)))
            for ev in acc["status_events"]:
                events.append((ev["date"], 1, dict(status=ev["status"], successor=ev["successor"],
                                                   valid_to=ev["valid_to"])))
            if acc.get("churned"):
                events.append((acc["churned"] + timedelta(days=1), 1, dict(status="Churned")))
            events.sort(key=lambda e: (e[0], e[1]))
            versions = []
            cur = dict(valid_from=acc["created"], owner=acc["owner"], status="Active", successor="", valid_to=None)
            for on, _p, ch in events:
                if on == cur["valid_from"]:
                    cur.update({k: v for k, v in ch.items() if k != "valid_to"})
                else:
                    prev = dict(cur)
                    prev["valid_to"] = on - timedelta(days=1)
                    versions.append(prev)
                    cur = dict(cur)
                    cur.pop("forced_end", None)
                    cur["valid_from"] = on
                    cur.update({k: v for k, v in ch.items() if k != "valid_to"})
                if "valid_to" in ch:
                    cur["forced_end"] = ch["valid_to"]
            cur["valid_to"] = cur.pop("forced_end", None)
            versions.append(cur)
            for v in versions:
                v.pop("forced_end", None)
            primaries = [b for b in sorted(self.bas) if self.bas[b]["crm_account_id"] == acc_id]
            for n, v in enumerate(versions, 1):
                links = [(b, "primary") for b in primaries] + [(b, "legacy") for b in sorted(acc["legacy_links"])]
                for b, lt in links:
                    rows.append(dict(
                        account_id=acc_id, record_version=n, valid_from=iso(v["valid_from"]),
                        valid_to=iso(v["valid_to"]), is_current="true" if n == len(versions) else "false",
                        account_name=acc["name"], segment=acc["segment"], region=acc["region"],
                        billing_country=acc["country"], account_owner=v["owner"], lifecycle_status=v["status"],
                        successor_account_id=v["successor"], billing_account_id=b, billing_link_type=lt))
        return rows

    # ---------------- output ----------------
    def generate(self):
        self.build_customers()
        self.build_migrations()
        self.build_realignments()
        self.apply_similar_ids()
        self.renumber_billing_accounts()
        self.build_billing()
        self.build_credit_notes()
        return self

    def write(self, root: Path):
        root = Path(root)
        (root / "data/billing").mkdir(parents=True, exist_ok=True)
        (root / "data/crm").mkdir(parents=True, exist_ok=True)
        db_path = root / "data/billing/billing.db"
        if db_path.exists():
            db_path.unlink()
        con = sqlite3.connect(db_path)
        con.executescript(DDL)
        con.executemany("INSERT INTO billing_accounts VALUES (?,?,?,?,?,?,?,?)", [
            (b["id"], b["crm_account_id"], b["legal_entity_name"], b["billing_country"], b["currency"], b["status"],
             iso(b["created"]), iso(b["closed"]) or None) for b in (self.bas[k] for k in sorted(self.bas))])
        con.executemany("INSERT INTO plans VALUES (?,?,?,?,?,?,?,?)", [
            (p["plan_code"], p["plan_version"], p["plan_name"], p["billing_interval"], p["list_unit_price_minor"],
             p["currency"], p["effective_from"], p["effective_to"] or None) for p in self.plan_rows()])
        con.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            (s["id"], s["ba"], s["plan"], s["interval"], s["qty"], s["unit_price"] if s["kind"] != "usage" else None,
             self.bas[s["ba"]]["currency"], s["discount"], iso(s["start"]), iso(s["end"]) or None,
             self.sub_status(s)) for s in self.subs])
        con.executemany("INSERT INTO invoices VALUES (?,?,?,?,?,?,?,?,?)", [
            (i["id"], i["ba"], iso(i["date"]), self.bas[i["ba"]]["currency"], i["status"],
             sum(l["amount"] for l in i["lines"] if l["line_type"] != "tax"),
             sum(l["amount"] for l in i["lines"] if l["line_type"] == "tax"),
             sum(l["amount"] for l in i["lines"]), i["replaces"] or None) for i in self.invoices])
        con.executemany("INSERT INTO invoice_lines VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
            (l["id"], i["id"], l["no"], l["sub"] or None, l["line_type"], l["desc"], l["qty"], l["unit"], l["amount"],
             iso(l["ss"]), iso(l["se"])) for i in self.invoices for l in i["lines"]])
        con.executemany("INSERT INTO credit_notes VALUES (?,?,?,?,?,?,?,?,?)", [
            (c["id"], c["inv"]["id"], c["line"]["id"], iso(c["issued"]), c["amount"], self.bas[c["inv"]["ba"]]["currency"],
             c["reason"], c["memo"], "issued") for c in self.credits])
        con.executemany("INSERT INTO fx_rates VALUES (?,?,?,?,?)", [
            (r["currency"], r["rate_month"], r["usd_per_unit"], r["rate_type"], r["source"]) for r in self.fx_rates()])
        periods = []
        m = month_start(self.go_live)
        while m <= self.open_month:
            if m < self.close_month:
                periods.append((ym(m), "closed", iso(add_months(m, 1) + timedelta(days=4))))
            elif m == self.close_month:
                periods.append((ym(m), "closing", None))
            else:
                periods.append((ym(m), "open", None))
            m = add_months(m, 1)
        con.executemany("INSERT INTO accounting_periods VALUES (?,?,?)", periods)
        con.commit()
        con.execute("VACUUM")
        con.close()

        crm = self.crm_rows()
        write_csv(root / "data/crm/crm_accounts_export.csv", crm, CRM_COLUMNS)
        reg_cols = ["migration_id", "legacy_account_id", "successor_account_id", "legacy_billing_account_id",
                    "successor_billing_account_id", "migration_type", "cutover_mode", "effective_date",
                    "cutover_closed_date", "status", "change_ticket"]
        write_csv(root / "data/crm/account_migrations.csv", self.register, reg_cols)

    def sub_status(self, s) -> str:
        if s["start"] > self.extract:
            return "pending"
        if s["end"] is not None and s["end"] < self.extract:
            return "ended"
        return "active"


CRM_COLUMNS = ["account_id", "record_version", "valid_from", "valid_to", "is_current", "account_name", "segment",
               "region", "billing_country", "account_owner", "lifecycle_status", "successor_account_id",
               "billing_account_id", "billing_link_type"]

DDL = """
CREATE TABLE billing_accounts (
  billing_account_id TEXT PRIMARY KEY,
  crm_account_id     TEXT NOT NULL,
  legal_entity_name  TEXT NOT NULL,
  billing_country    TEXT NOT NULL,
  currency           TEXT NOT NULL,
  status             TEXT NOT NULL,
  created_date       TEXT NOT NULL,
  closed_date        TEXT
);
CREATE TABLE plans (
  plan_code             TEXT NOT NULL,
  plan_version          INTEGER NOT NULL,
  plan_name             TEXT NOT NULL,
  billing_interval      TEXT NOT NULL,
  list_unit_price_minor INTEGER NOT NULL,
  currency              TEXT NOT NULL,
  effective_from        TEXT NOT NULL,
  effective_to          TEXT,
  PRIMARY KEY (plan_code, plan_version)
);
CREATE TABLE subscriptions (
  subscription_id    TEXT PRIMARY KEY,
  billing_account_id TEXT NOT NULL REFERENCES billing_accounts(billing_account_id),
  plan_code          TEXT NOT NULL,
  billing_interval   TEXT NOT NULL,
  quantity           INTEGER NOT NULL,
  unit_price_minor   INTEGER,
  currency           TEXT NOT NULL,
  discount_pct       REAL NOT NULL,
  start_date         TEXT NOT NULL,
  end_date           TEXT,
  status             TEXT NOT NULL
);
CREATE TABLE invoices (
  invoice_id         TEXT PRIMARY KEY,
  billing_account_id TEXT NOT NULL REFERENCES billing_accounts(billing_account_id),
  invoice_date       TEXT NOT NULL,
  currency           TEXT NOT NULL,
  status             TEXT NOT NULL,
  subtotal_minor     INTEGER NOT NULL,
  tax_minor          INTEGER NOT NULL,
  total_minor        INTEGER NOT NULL,
  replaces_invoice_id TEXT
);
CREATE TABLE invoice_lines (
  invoice_line_id      TEXT PRIMARY KEY,
  invoice_id           TEXT NOT NULL REFERENCES invoices(invoice_id),
  line_number          INTEGER NOT NULL,
  subscription_id      TEXT REFERENCES subscriptions(subscription_id),
  line_type            TEXT NOT NULL,
  description          TEXT NOT NULL,
  quantity             INTEGER NOT NULL,
  unit_price_minor     INTEGER NOT NULL,
  amount_minor         INTEGER NOT NULL,
  service_period_start TEXT NOT NULL,
  service_period_end   TEXT NOT NULL
);
CREATE TABLE credit_notes (
  credit_note_id  TEXT PRIMARY KEY,
  invoice_id      TEXT NOT NULL REFERENCES invoices(invoice_id),
  invoice_line_id TEXT NOT NULL REFERENCES invoice_lines(invoice_line_id),
  issued_date     TEXT NOT NULL,
  amount_minor    INTEGER NOT NULL,
  currency        TEXT NOT NULL,
  reason_code     TEXT NOT NULL,
  memo            TEXT,
  status          TEXT NOT NULL
);
CREATE TABLE fx_rates (
  currency     TEXT NOT NULL,
  rate_month   TEXT NOT NULL,
  usd_per_unit REAL NOT NULL,
  rate_type    TEXT NOT NULL,
  source       TEXT NOT NULL,
  PRIMARY KEY (currency, rate_month)
);
CREATE TABLE accounting_periods (
  period_month TEXT PRIMARY KEY,
  status       TEXT NOT NULL,
  closed_at    TEXT
);
CREATE INDEX ix_invoice_lines_invoice ON invoice_lines(invoice_id);
CREATE INDEX ix_invoices_account ON invoices(billing_account_id);
"""


def write_csv(path: Path, rows: list[dict], columns: list[str]):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})


# --------------------------------------------------------------------------- #
# Integrity digests (used by the verifier)
# --------------------------------------------------------------------------- #


def sqlite_logical_digest(db_path: Path) -> str:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    h = hashlib.sha256()
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    for t in tables:
        h.update(f"#table:{t}\n".encode())
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        h.update(("|".join(cols) + "\n").encode())
        order = ",".join(f'"{c}"' for c in cols)
        for row in con.execute(f'SELECT * FROM "{t}" ORDER BY {order}'):
            h.update((json.dumps(row, default=str) + "\n").encode())
    con.close()
    return h.hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_digests(root: Path) -> dict:
    root = Path(root)
    return {
        "data/billing/billing.db": sqlite_logical_digest(root / "data/billing/billing.db"),
        "data/crm/crm_accounts_export.csv": file_digest(root / "data/crm/crm_accounts_export.csv"),
        "data/crm/account_migrations.csv": file_digest(root / "data/crm/account_migrations.csv"),
    }


def build(spec: dict, root: Path) -> World:
    w = World(spec).generate()
    w.write(root)
    return w


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    build(VISIBLE_SPEC, out)
    print(json.dumps(source_digests(out), indent=2))
