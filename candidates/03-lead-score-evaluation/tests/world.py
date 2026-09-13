#!/usr/bin/env python3
"""Deterministic synthetic RevOps warehouse for ForensicDS Task 03 (lead-score evaluation).

Produces `data/revops.db` (SQLite):

  leads               one row per inbound lead (intake record)
  lead_scores         one row per (lead, model_version) score, logged when the lead is scored
  routing_events      one row per routing decision (initial routing at intake, later re-routes)
  sdr_activities      one row per SDR touch (call / email / meeting)
  conversions         one row per closed-won opportunity sourced from a lead (sales-led or self-serve)
  lead_lifecycle      one row per accepted lead: RevOps lifecycle v2 rollup (derived, rebuilt nightly)
  router_config_log   one row per router configuration version

Mechanism: the champion lead-score model routes leads. Leads scoring at or above the router threshold go to
the SDR queue; a random exploration holdout goes to the SDR queue regardless of score; the rest go to nurture,
from which reps occasionally claim leads. Being worked by an SDR strongly raises the chance of converting.
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
from datetime import date, datetime, time, timedelta
from pathlib import Path

TS = "%Y-%m-%d %H:%M:%S"
SOURCES = ["web_form", "demo_request", "content_download", "webinar", "partner_referral"]
SIZES = ["1-50", "51-200", "201-1000", "1000+"]
COUNTRIES = [("US", .52), ("GB", .12), ("DE", .09), ("CA", .07), ("FR", .06), ("AU", .05), ("NL", .04), ("IN", .05)]
REPS = ["sdr.alvarez", "sdr.bishop", "sdr.chen", "sdr.dube", "sdr.eriksen", "sdr.farouk", "sdr.garcia", "sdr.hale"]

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 44021,
    "start_date": "2025-04-01",
    "extract_date": "2026-09-05",
    "leads_per_day": 58,
    "reject_rate": 0.06,
    "holdout_pct": 10,
    "holdout_pauses": [],
    "thresholds": [{"from": "2025-01-01", "threshold": 0.30, "version": "router-2025.11"},
                   {"from": "2026-06-15", "threshold": 0.22, "version": "router-2026.06"}],
    "source_mix": {"web_form": .34, "demo_request": .14, "content_download": .28, "webinar": .12, "partner_referral": .12},
    "campaigns": [{"source": "webinar", "from": "2026-06-01", "to": "2026-06-30", "extra_per_day": 18, "intent_shift": -0.7}],
    "model_noise": 0.95,
    "worked_conv_intercept": -2.35,
    "worked_conv_slope": 1.05,
    "unworked_conv_intercept": -5.4,
    "unworked_conv_slope": 0.8,
    "sla_breach_rate": 0.05,
    "claim_base": 0.03,
    "claim_demo_request": 0.22,
    "claim_intent_slope": 0.5,
    "reassign_rate_routed": 0.05,
    "reassign_rate_holdout": 0.0,
    "challenger_from": "2026-06-01",
    "late_close_share": 0.12,
}

SOURCE_INTENT = {"web_form": 0.1, "demo_request": 0.8, "content_download": -0.4, "webinar": -0.2, "partner_referral": 0.5}


def dtp(s: str) -> datetime:
    return datetime.strptime(s, TS)


def fmt(x: datetime | None) -> str | None:
    return x.strftime(TS) if x else None


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def pick(r: random.Random, weights: dict | list):
    items = list(weights.items()) if isinstance(weights, dict) else weights
    x, acc = r.random(), 0.0
    for v, w in items:
        acc += w
        if x <= acc:
            return v
    return items[-1][0]


class World:
    def __init__(self, spec: dict):
        self.spec = spec
        self.seed = spec["seed"]
        self.leads, self.scores, self.routing, self.activities, self.conversions = [], [], [], [], []
        self.lifecycle = []
        self.extract = datetime.combine(date.fromisoformat(spec["extract_date"]), time())

    def rng(self, *parts):
        return random.Random(":".join(str(p) for p in (self.seed,) + parts))

    def threshold_at(self, t: datetime):
        cur = None
        for th in self.spec["thresholds"]:
            if t >= datetime.combine(date.fromisoformat(th["from"]), time()):
                cur = th
        return cur

    def in_pause(self, t: datetime) -> bool:
        return any(dtp(p["start"]) <= t < dtp(p["end"]) for p in self.spec["holdout_pauses"])

    def generate(self):
        s = self.spec
        r = self.rng("leads")
        day = date.fromisoformat(s["start_date"])
        n = 0
        while datetime.combine(day, time()) < self.extract - timedelta(days=1):
            weekday = day.weekday()
            base = s["leads_per_day"] * (0.45 if weekday >= 5 else 1.0)
            k = max(0, int(round(r.gauss(base, math.sqrt(base)))))
            extra = []
            for c in s["campaigns"]:
                if date.fromisoformat(c["from"]) <= day <= date.fromisoformat(c["to"]):
                    extra += [c] * max(0, int(round(r.gauss(c["extra_per_day"], 2))))
            for i in range(k + len(extra)):
                camp = extra[i - k] if i >= k else None
                n += 1
                self.make_lead(n, day, camp)
            day += timedelta(days=1)
        return self

    def make_lead(self, n: int, day: date, camp):
        s = self.spec
        lid = f"L-{(n * 2654435761 + self.seed * 7919) % 4294967291:010d}"  # bijective in n: ids never collide
        r = self.rng("lead", lid)
        created = datetime.combine(day, time(r.randint(0, 23), r.randint(0, 59), r.randint(0, 59)))
        source = camp["source"] if camp else pick(r, s["source_mix"])
        size = pick(r, [("1-50", .42), ("51-200", .30), ("201-1000", .18), ("1000+", .10)])
        u = r.gauss(0, 1) + SOURCE_INTENT[source] + {"1-50": -0.2, "51-200": 0, "201-1000": 0.15, "1000+": 0.3}[size]
        if camp:
            u += camp["intent_shift"]
        rejected = r.random() < s["reject_rate"]
        lead = dict(lead_id=lid, created_at=created, source=source, company_size=size, country=pick(r, COUNTRIES),
                    intake_status=("rejected_spam" if r.random() < .6 else "rejected_duplicate") if rejected else "accepted",
                    campaign=f"{camp['source']}-{camp['from'][:7]}" if camp else None)
        self.leads.append(lead)
        if rejected:
            return
        # champion score at intake (model cannot see u exactly)
        score = sigmoid(-1.6 + 0.95 * (u + r.gauss(0, s["model_noise"])))
        scored_at = created + timedelta(seconds=r.randint(20, 240))
        self.scores.append((lid, "lsm-3.2", fmt(scored_at), round(score, 6)))
        if created >= datetime.combine(date.fromisoformat(s["challenger_from"]), time()):
            ch = sigmoid(-1.55 + 0.95 * (u + r.gauss(0, s["model_noise"] * 0.9)))
            self.scores.append((lid, "lsm-3.3-shadow", fmt(scored_at + timedelta(seconds=5)), round(ch, 6)))
        # initial routing
        routed_at = scored_at + timedelta(seconds=r.randint(5, 90))
        th = self.threshold_at(created)
        bucket = int(hashlib.sha256(f"router:{lid}".encode()).hexdigest()[:8], 16) % 100
        if bucket < s["holdout_pct"] and not self.in_pause(created):
            policy, queue = "exploration_holdout", "sdr_inbound"
        elif score >= th["threshold"]:
            policy, queue = "score_threshold", "sdr_inbound"
        else:
            policy, queue = "below_threshold_nurture", "nurture"
        self.routing.append(dict(lead_id=lid, routed_at=routed_at, policy=policy, queue=queue,
                                 router_version=th["version"], threshold=th["threshold"], score_at_routing=round(score, 6)))
        # who gets worked
        worked_at = None
        current_queue = queue
        if queue == "sdr_inbound":
            if r.random() >= s["sla_breach_rate"]:
                worked_at = routed_at + timedelta(minutes=r.randint(8, 60 * 30))
            reassign = s["reassign_rate_holdout"] if policy == "exploration_holdout" else s["reassign_rate_routed"]
            if r.random() < reassign:
                t = routed_at + timedelta(days=r.randint(2, 20), minutes=r.randint(0, 600))
                self.routing.append(dict(lead_id=lid, routed_at=t, policy="territory_reassign", queue="sdr_inbound",
                                         router_version=self.threshold_at(t)["version"], threshold=None, score_at_routing=None))
        else:
            p_claim = s["claim_base"] + (s["claim_demo_request"] if source == "demo_request" else 0)
            p_claim *= math.exp(s["claim_intent_slope"] * min(u, 2.5))
            if r.random() < min(0.9, p_claim):
                t = routed_at + timedelta(days=r.randint(1, 14), minutes=r.randint(0, 600))
                self.routing.append(dict(lead_id=lid, routed_at=t, policy="manual_rep_claim", queue="sdr_inbound",
                                         router_version=self.threshold_at(t)["version"], threshold=None, score_at_routing=None))
                worked_at = t + timedelta(minutes=r.randint(5, 600))
                current_queue = "sdr_inbound"
        if worked_at is not None and worked_at < self.extract:
            rep = r.choice(REPS)
            k = r.randint(1, 6)
            t = worked_at
            for j in range(k):
                if t >= self.extract:
                    break
                self.activities.append((lid, fmt(t), r.choice(["call", "email", "email", "call", "meeting"]), rep))
                t += timedelta(hours=r.randint(4, 120))
        # outcome
        if worked_at is not None:
            p = sigmoid(s["worked_conv_intercept"] + s["worked_conv_slope"] * u)
            channel = "sales_led"
        else:
            p = sigmoid(s["unworked_conv_intercept"] + s["unworked_conv_slope"] * u)
            channel = "self_serve"
        converted_at = None
        if r.random() < p:
            start = worked_at or created
            days = r.uniform(7, 58) if r.random() > s["late_close_share"] else r.uniform(58, 140)
            converted_at = start + timedelta(days=days)
            if converted_at < self.extract:
                self.conversions.append((f"OPP-{lid[2:]}", lid, fmt(converted_at), channel,
                                         round(r.uniform(6, 60) * 1000 * (3 if size == "1000+" else 1), 2)))
            else:
                converted_at = None
        qualified = worked_at is not None and (converted_at is not None or r.random() < 0.18 + 0.1 * max(u, 0))
        first_worked = worked_at if worked_at is not None and worked_at < self.extract else None
        c60 = converted_at is not None and converted_at - created <= timedelta(days=60)
        self.lifecycle.append((lid, fmt(created), current_queue,
                               fmt(first_worked), int(qualified), fmt(converted_at), int(c60),
                               "customer" if converted_at else ("sql" if qualified else ("working" if first_worked else "nurture"))))

    def write(self, root: Path):
        root = Path(root)
        (root / "data").mkdir(parents=True, exist_ok=True)
        path = root / "data/revops.db"
        if path.exists():
            path.unlink()
        con = sqlite3.connect(path)
        con.executescript(DDL)
        con.executemany("INSERT INTO leads VALUES (?,?,?,?,?,?,?)", [
            (l["lead_id"], fmt(l["created_at"]), l["source"], l["company_size"], l["country"], l["intake_status"], l["campaign"])
            for l in sorted(self.leads, key=lambda l: (l["created_at"], l["lead_id"]))])
        con.executemany("INSERT INTO lead_scores VALUES (?,?,?,?)", sorted(self.scores, key=lambda x: (x[2], x[0], x[1])))
        ev = sorted(self.routing, key=lambda e: (e["routed_at"], e["lead_id"]))
        con.executemany("INSERT INTO routing_events VALUES (?,?,?,?,?,?,?,?)", [
            (f"RT-{i:07d}", e["lead_id"], fmt(e["routed_at"]), e["policy"], e["queue"], e["router_version"], e["threshold"],
             e["score_at_routing"]) for i, e in enumerate(ev, 1) if e["routed_at"] < self.extract])
        act = sorted(self.activities, key=lambda a: (a[1], a[0]))
        con.executemany("INSERT INTO sdr_activities VALUES (?,?,?,?,?)", [(f"ACT-{i:08d}",) + a for i, a in enumerate(act, 1)])
        con.executemany("INSERT INTO conversions VALUES (?,?,?,?,?)", sorted(self.conversions, key=lambda c: (c[2], c[1])))
        con.executemany("INSERT INTO lead_lifecycle VALUES (?,?,?,?,?,?,?,?)", sorted(self.lifecycle, key=lambda x: (x[1], x[0])))
        versions = []
        for th in self.spec["thresholds"]:
            versions.append((th["version"], th["from"], th["threshold"], self.spec["holdout_pct"], "lsm-3.2"))
        con.executemany("INSERT INTO router_config_log VALUES (?,?,?,?,?)", versions)
        con.commit()
        con.execute("VACUUM")
        con.close()


DDL = """
CREATE TABLE leads (lead_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, source TEXT NOT NULL, company_size TEXT NOT NULL,
  country TEXT NOT NULL, intake_status TEXT NOT NULL, campaign TEXT);
CREATE TABLE lead_scores (lead_id TEXT NOT NULL, model_version TEXT NOT NULL, scored_at TEXT NOT NULL, score REAL NOT NULL,
  PRIMARY KEY (lead_id, model_version));
CREATE TABLE routing_events (routing_event_id TEXT PRIMARY KEY, lead_id TEXT NOT NULL, routed_at TEXT NOT NULL,
  policy TEXT NOT NULL, queue TEXT NOT NULL, router_version TEXT NOT NULL, threshold REAL, score_at_routing REAL);
CREATE TABLE sdr_activities (activity_id TEXT PRIMARY KEY, lead_id TEXT NOT NULL, activity_at TEXT NOT NULL,
  activity_type TEXT NOT NULL, rep TEXT NOT NULL);
CREATE TABLE conversions (opportunity_id TEXT PRIMARY KEY, lead_id TEXT NOT NULL, closed_won_at TEXT NOT NULL,
  channel TEXT NOT NULL, first_year_arr_usd REAL NOT NULL);
CREATE TABLE lead_lifecycle (lead_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, current_queue TEXT NOT NULL,
  first_worked_at TEXT, qualified INTEGER NOT NULL, converted_at TEXT, converted_60d INTEGER NOT NULL, lifecycle_stage TEXT NOT NULL);
CREATE TABLE router_config_log (router_version TEXT PRIMARY KEY, effective_from TEXT NOT NULL, threshold REAL NOT NULL,
  exploration_holdout_pct INTEGER NOT NULL, champion_model TEXT NOT NULL);
CREATE INDEX ix_scores_lead ON lead_scores(lead_id);
CREATE INDEX ix_routing_lead ON routing_events(lead_id, routed_at);
CREATE INDEX ix_act_lead ON sdr_activities(lead_id, activity_at);
CREATE INDEX ix_conv_lead ON conversions(lead_id);
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
    print(sqlite_logical_digest(out / "data/revops.db"))
