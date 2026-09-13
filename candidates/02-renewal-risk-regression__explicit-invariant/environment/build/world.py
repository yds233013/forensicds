#!/usr/bin/env python3
"""Deterministic synthetic warehouse for ForensicDS Task 02 (renewal-risk model).

Produces `data/warehouse.db`, a SQLite extract of the analytics warehouse:

  accounts                          one row per customer account (static firmographics)
  contracts                         one row per contract term
  renewal_outcomes                  one row per decided renewal (label source)
  usage_weekly                      one row per account per ISO week (loaded after the week closes)
  support_tickets                   one row per ticket (current state)
  crm_opportunities                 one row per CRM opportunity (CURRENT state, overwritten on update)
  crm_opportunity_field_history     one row per tracked-field change (append-only audit trail)
  cs_account_health                 one row per account (CURRENT state, overwritten on update)
  cs_account_health_history         one row per tracked-field change (append-only audit trail)
  warehouse_sync_log                one row per connector incident (outage and replay)

Every row carries `synced_at`, the time it landed in the warehouse replica. Business timestamps
(`changed_at`, `opened_at`, ...) can precede `synced_at` by minutes (CRM streaming), a night
(CS health batch), a week (partner-channel deals) or longer (replication outages).

Standard library only; fully determined by the spec (seeded RNGs, sorted iteration).
Not shipped to the agent: the Docker build runs it and deletes it; tests/ holds a byte-identical copy.
"""
from __future__ import annotations

import hashlib
import json
import math
import random
import sqlite3
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

TS = "%Y-%m-%d %H:%M:%S"

STAGES_OPEN = ["Qualification", "Discovery", "Proposal", "Negotiation", "Verbal"]
COMPETITORS = ["Brightwell", "Norvana", "Quantiq", "Stackline", "Veritrail"]
INDUSTRIES = ["Software", "Financial Services", "Healthcare", "Retail", "Manufacturing", "Media", "Logistics",
              "Education", "Energy", "Telecom"]
REGIONS = [("NA", 0.55), ("EMEA", 0.30), ("APAC", 0.15)]
SEGMENTS = [("Enterprise", 0.15), ("Mid-Market", 0.35), ("SMB", 0.50)]
OWNERS = ["d.whitfield", "m.oyelaran", "p.raman", "t.castellano", "r.park", "s.laurent", "h.dahl", "a.byrne",
          "m.tanaka", "a.mehta", "k.lambert", "v.nguyen"]
CSMS = ["csm.ellis", "csm.brandt", "csm.haddad", "csm.vogel", "csm.russo", "csm.koh", "csm.watts"]

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 90417,
    "extract_date": "2026-08-15",
    "first_account_date": "2021-03-01",
    "n_accounts": 1400,
    "horizon_days": 90,
    "churn_intercept": -1.9,
    "churn_slope": 1.3,
    "pre_cutoff_changes": [0, 3],
    "late_opp_share": 0.18,
    "crm": {
        "sync_minutes": [1, 14],
        "outages": [{"start": "2025-11-03 00:00:00", "end": "2025-11-18 00:00:00", "replay": "2025-11-18 03:10:00"}],
        "partner_share": 0.08,
        "partner_sync_weekday": 6,          # Sunday
        "partner_sync_time": "22:00:00",
        "rep_update_prob_churn": 0.4,
        "rep_update_prob_renew": 0.45,
        "competitor_on_loss": 0.45,
        "renewer_amount_change": 0.6,
        "stale_close_prob": 0.2,
    },
    "health": {
        "sync_time": "01:30:00",
        "sync_day_lag": 1,
        "sync_jitter_minutes": 25,
        "churn_decline": 0.4,
        "renewer_improve": 0.25,
        "renewer_decline": 0.2,
        "sentiment_escalation": 0.5,
    },
    "expansion_rate_per_year": 0.45,
}


def d(s: str) -> date:
    return date.fromisoformat(s)


def dt(s: str) -> datetime:
    return datetime.strptime(s, TS)


def fmt(x: datetime | None) -> str | None:
    return x.strftime(TS) if x else None


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def clip(x, lo, hi):
    return max(lo, min(hi, x))


def off_midnight(x: datetime) -> datetime:
    """Load timestamps never fall exactly on a day boundary (keeps 'loaded before 00:00' unambiguous)."""
    return x + timedelta(seconds=1) if x.time() == time(0, 0) else x


def monday_on_or_after(x: date) -> date:
    return x + timedelta(days=(7 - x.weekday()) % 7)


class World:
    def __init__(self, spec: dict):
        self.spec = spec
        self.seed = spec["seed"]
        self.extract = datetime.combine(d(spec["extract_date"]), time(0, 0))
        self.accounts: list[dict] = []
        self.contracts: list[dict] = []
        self.outcomes: list[dict] = []
        self.usage: list[tuple] = []
        self.tickets: list[dict] = []
        self.opps: list[dict] = []
        self.opp_hist: list[dict] = []
        self.health_hist: list[dict] = []
        self.sync_log: list[dict] = []
        self._replay_counter = 0

    def rng(self, *parts) -> random.Random:
        return random.Random(":".join(str(p) for p in (self.seed,) + parts))

    # ------------------------------------------------------------------ sync semantics
    def crm_synced(self, changed: datetime, source: str, lag_s: int) -> datetime:
        """Replication time of a CRM change. Monotone in `changed` for a given record (constant lag)."""
        c = self.spec["crm"]
        s = changed + timedelta(seconds=lag_s)
        if source == "partner":
            days = (c["partner_sync_weekday"] - changed.weekday()) % 7
            batch = datetime.combine(changed.date() + timedelta(days=days), time.fromisoformat(c["partner_sync_time"]))
            if batch <= changed:
                batch += timedelta(days=7)
            s = max(s, batch + timedelta(seconds=lag_s % 900))
        for o in c["outages"]:
            if dt(o["start"]) <= changed < dt(o["replay"]) or dt(o["start"]) <= s < dt(o["replay"]):
                self._replay_counter += 1
                s = max(s, dt(o["replay"]) + timedelta(seconds=self._replay_counter))
        return off_midnight(s)

    def health_synced(self, changed: datetime, account_id: str) -> datetime:
        """Nightly batch load; all changes of one account made on the same day land in the same batch."""
        h = self.spec["health"]
        batch = datetime.combine(changed.date() + timedelta(days=h["sync_day_lag"]), time.fromisoformat(h["sync_time"]))
        if batch <= changed:
            batch += timedelta(days=1)
        j = int(hashlib.sha256(f"{self.seed}:{account_id}:{batch.date()}".encode()).hexdigest()[:6], 16)
        return batch + timedelta(seconds=(j % (h["sync_jitter_minutes"] * 60)) + 1)

    # ------------------------------------------------------------------ accounts & contracts
    def pick(self, r, options):
        x, acc = r.random(), 0.0
        for v, w in options:
            acc += w
            if x <= acc:
                return v
        return options[-1][0]

    def build_accounts(self):
        r = self.rng("accounts")
        first = d(self.spec["first_account_date"])
        last = self.extract.date() - timedelta(days=380)
        span = (last - first).days
        ids = r.sample(range(10000, 99999), self.spec["n_accounts"])
        for i in range(self.spec["n_accounts"]):
            seg = self.pick(r, SEGMENTS)
            created = first + timedelta(days=r.randint(0, span))
            self.accounts.append(dict(
                account_id=f"A-{ids[i]:05d}", segment=seg, region=self.pick(r, REGIONS),
                industry=r.choice(INDUSTRIES), created_date=created, owner=r.choice(OWNERS), csm=r.choice(CSMS),
                a0=r.gauss(0, 0.75), terms=[]))
        self.accounts.sort(key=lambda a: a["account_id"])

    def build_contracts(self):
        cid = 0
        for acc in self.accounts:
            r = self.rng("terms", acc["account_id"])
            seats = {"Enterprise": r.randint(400, 3000), "Mid-Market": r.randint(60, 400), "SMB": r.randint(8, 60)}[acc["segment"]]
            price = {"Enterprise": r.uniform(420, 620), "Mid-Market": r.uniform(360, 480), "SMB": r.uniform(300, 400)}[acc["segment"]]
            plan = "Enterprise" if acc["segment"] == "Enterprise" or r.random() < 0.15 else r.choice(["Growth", "Team"])
            start = acc["created_date"]
            u_prev = acc["a0"]
            while datetime.combine(start, time()) < self.extract:
                renewal = start + timedelta(days=365)
                u = 0.55 * u_prev + 0.45 * acc["a0"] + r.gauss(0, 0.75)
                churn = r.random() < sigmoid(self.spec["churn_intercept"] + self.spec["churn_slope"] * u)
                decided = datetime.combine(renewal - timedelta(days=r.randint(0, 25)), time(r.randint(9, 17), r.randint(0, 59)))
                cid += 1
                term = dict(contract_id=f"C-{cid:06d}", account_id=acc["account_id"], start_date=start, renewal_date=renewal,
                            seats=seats, arr_usd=round(seats * price, 2), plan=plan, u=u, churn=churn, decided=decided,
                            T=datetime.combine(renewal - timedelta(days=self.spec["horizon_days"]), time()))
                acc["terms"].append(term)
                self.contracts.append(term)
                if decided < self.extract:
                    sync = decided + timedelta(minutes=r.randint(2, 14))
                    self.outcomes.append(dict(contract_id=term["contract_id"], account_id=acc["account_id"],
                                              renewal_date=renewal, outcome="churned" if churn else "renewed",
                                              decided_at=decided, synced_at=sync))
                if churn or decided >= self.extract:
                    break
                seats = max(5, int(round(seats * (1 + r.gauss(0.04, 0.12) - 0.05 * max(0.0, u)))))
                start = renewal
                u_prev = u

    def term_at(self, acc, day: date):
        for t in acc["terms"]:
            if t["start_date"] <= day < t["renewal_date"]:
                return t
        return None

    # ------------------------------------------------------------------ usage & support
    def build_usage_and_support(self):
        tid = 0
        for acc in self.accounts:
            r = self.rng("usage", acc["account_id"])
            wk = monday_on_or_after(acc["created_date"])
            while True:
                synced = datetime.combine(wk + timedelta(days=7), time(2, 0)) + timedelta(minutes=r.randint(0, 40))
                if synced >= self.extract:
                    break
                t = self.term_at(acc, wk)
                if t is None:
                    break
                phase = (wk - t["start_date"]).days / 365.0
                u = t["u"]
                ratio = 0.70 - 0.09 * u - 0.10 * u * phase + r.gauss(0, 0.07)
                if t["churn"] and phase > 0.75:
                    ratio -= 0.25 * (phase - 0.75)
                ratio = clip(ratio, 0.02, 1.0)
                active = int(round(ratio * t["seats"]))
                api = int(round(active * r.uniform(15, 45) * (1 - 0.08 * u)))
                logins = int(round(active * r.uniform(2, 6)))
                self.usage.append((acc["account_id"], wk.isoformat(), active, max(api, 0), logins, fmt(synced)))
                # support tickets opened during this week
                lam = 0.10 * (t["seats"] / 50.0) ** 0.35 * math.exp(0.35 * u)
                n, p, L = 0, 1.0, math.exp(-lam)
                while True:
                    p *= r.random()
                    if p <= L:
                        break
                    n += 1
                for _ in range(n):
                    opened = datetime.combine(wk + timedelta(days=r.randint(0, 6)), time(r.randint(1, 21), r.randint(0, 59), r.randint(0, 59)))
                    if opened >= self.extract:
                        continue
                    sev1_p = min(0.3, 0.05 * math.exp(0.45 * u))
                    x = r.random()
                    sev = "sev1" if x < sev1_p else "sev2" if x < sev1_p + 0.3 else "sev3"
                    closed = opened + timedelta(hours=r.expovariate(1 / 60.0))
                    if closed.time() >= time(23, 40):
                        closed -= timedelta(minutes=45)
                    closed = closed if closed < self.extract - timedelta(minutes=20) else None
                    tid += 1
                    last_event = closed or opened
                    self.tickets.append(dict(ticket_id=f"T-{tid:07d}", account_id=acc["account_id"], opened_at=opened,
                                             severity=sev, category=r.choice(["billing", "bug", "how-to", "integration", "outage"]),
                                             closed_at=closed, synced_at=last_event + timedelta(minutes=r.randint(3, 12))))
                wk += timedelta(days=7)

    # ------------------------------------------------------------------ CRM opportunities
    def add_opp(self, acc, opp_type, contract, created: datetime, initial: dict, changes: list, source: str, r):
        oid = f"OPP-{len(self.opps) + 1:07d}"
        state = dict(initial)
        events = [(created, f, "", v) for f, v in initial.items()]
        last_at: dict[str, datetime] = {}
        for when, field, value in sorted(changes, key=lambda c: (c[0], c[1])):
            when = max(when, created + timedelta(hours=1), last_at.get(field, created) + timedelta(minutes=30))
            if when >= self.extract or state[field] == value:
                continue
            events.append((when, field, state[field], value))
            state[field] = value
            last_at[field] = when
        lag = r.randint(60, 840)
        creation_sync = self.crm_synced(created, source, lag)
        hist = []
        n_creation = len(initial)
        prev_sync = creation_sync
        for idx, (when, field, old, new) in enumerate(events):
            # rows of one record replicate in commit order: strictly increasing synced_at after creation
            if idx < n_creation:
                s = creation_sync
            else:
                s = off_midnight(max(self.crm_synced(when, source, lag) + timedelta(seconds=idx), prev_sync + timedelta(seconds=1)))
                prev_sync = s
            hist.append(dict(opportunity_id=oid, field=field, old_value=old, new_value=new, changed_at=when, synced_at=s,
                             changed_by=acc["owner"] if source == "direct" else "partner-integration"))
        visible = [h for h in hist if h["synced_at"] < self.extract]
        if not any(h["changed_at"] == created for h in visible):
            return  # creation not yet replicated at extract time
        cur = {}
        for h in sorted(visible, key=lambda h: (h["synced_at"], h["changed_at"])):
            cur[h["field"]] = h["new_value"]
        self.opp_hist.extend(visible)
        self.opps.append(dict(opportunity_id=oid, account_id=acc["account_id"],
                              contract_id=contract["contract_id"] if contract else None, opportunity_type=opp_type,
                              lead_source=source, owner=acc["owner"], created_at=created,
                              stage=cur["stage"], forecast_category=cur["forecast_category"], amount_usd=cur["amount_usd"],
                              close_date=cur["close_date"], competitor=cur["competitor"],
                              last_modified_at=max(h["changed_at"] for h in visible),
                              synced_at=max(h["synced_at"] for h in visible)))

    def forecast_draw(self, r, u):
        logits = {"Commit": -0.3 - 1.1 * u, "Best Case": 0.2 - 0.2 * u, "Pipeline": 0.4, "Omitted": -2.6 + 1.2 * u}
        z = sum(math.exp(v) for v in logits.values())
        x, acc = r.random() * z, 0.0
        for k in ["Commit", "Best Case", "Pipeline", "Omitted"]:
            acc += math.exp(logits[k])
            if x <= acc:
                return k
        return "Pipeline"

    def build_crm(self):
        c = self.spec["crm"]
        for acc in self.accounts:
            for t in acc["terms"]:
                r = self.rng("renewal-opp", t["contract_id"])
                T, R, u = t["T"], t["renewal_date"], t["u"]
                source = "partner" if r.random() < c["partner_share"] else "direct"
                if r.random() < self.spec["late_opp_share"]:
                    created = T + timedelta(days=r.randint(1, 60), hours=r.randint(8, 18), minutes=r.randint(0, 59))
                else:
                    created = datetime.combine(R - timedelta(days=r.randint(95, 170)), time(r.randint(8, 18), r.randint(0, 59), r.randint(0, 59)))
                if created >= self.extract or created >= t["decided"]:
                    continue
                amount = t["arr_usd"]
                initial = dict(stage="Qualification", forecast_category="Pipeline", amount_usd=f"{amount:.2f}",
                               close_date=R.isoformat(), competitor="")
                changes = []
                stage_i = 0
                # --- changes before the prediction point (information legitimately known at scoring time)
                lo, hi = self.spec["pre_cutoff_changes"]
                if created < T - timedelta(days=2):
                    n = r.randint(lo, hi)
                    span = (T - created).total_seconds() - 3600
                    for when in sorted(created + timedelta(seconds=r.uniform(60, span)) for _ in range(n)):
                        kind = self.pick(r, [("stage", 0.35), ("forecast_category", 0.3), ("amount_usd", 0.15),
                                             ("close_date", 0.1), ("competitor", 0.1)])
                        if kind == "stage" and stage_i < 3:
                            stage_i += 1
                            changes.append((when, "stage", STAGES_OPEN[stage_i]))
                        elif kind == "forecast_category":
                            changes.append((when, "forecast_category", self.forecast_draw(r, u)))
                        elif kind == "amount_usd":
                            amount = amount * (1.12 if u < -0.4 else 0.9 if u > 0.9 else r.uniform(0.97, 1.05))
                            changes.append((when, "amount_usd", f"{amount:.2f}"))
                        elif kind == "close_date":
                            changes.append((when, "close_date", (R + timedelta(days=r.randint(-20, 20))).isoformat()))
                        elif kind == "competitor" and u > 0.3 and r.random() < 0.6:
                            changes.append((when, "competitor", r.choice(COMPETITORS)))
                # --- changes after the prediction point (the renewal plays out)
                dec = t["decided"]
                after = max(T, created) + timedelta(hours=1)
                if t["churn"]:
                    if r.random() < c["rep_update_prob_churn"] and dec > after:
                        w = max(after, dec - timedelta(days=r.randint(5, 45)))
                        changes.append((w, "forecast_category", "Omitted"))
                        if r.random() < 0.4:
                            changes.append((w + timedelta(hours=2), "stage", "Negotiation"))
                        changes.append((dec, "stage", "Closed Lost"))
                        changes.append((dec + timedelta(minutes=1), "amount_usd", "0.00"))
                        changes.append((dec + timedelta(minutes=2), "close_date", dec.date().isoformat()))
                        if r.random() < c["competitor_on_loss"]:
                            changes.append((dec + timedelta(minutes=3), "competitor", r.choice(COMPETITORS)))
                    elif r.random() < c["stale_close_prob"]:
                        changes.append((dec + timedelta(days=r.randint(10, 40)), "stage", "Closed Lost"))
                else:
                    if r.random() < c["rep_update_prob_renew"] and dec > after:
                        if r.random() < 0.15:
                            changes.append((after + timedelta(days=r.randint(0, 20)), "forecast_category", "Best Case"))
                        if r.random() < 0.7:
                            changes.append((max(after, dec - timedelta(days=r.randint(10, 60))), "forecast_category", "Commit"))
                        changes.append((max(after, dec - timedelta(days=r.randint(3, 30))), "stage", "Negotiation"))
                        changes.append((max(after, dec - timedelta(days=r.randint(0, 2))), "stage", "Verbal"))
                        changes.append((dec, "stage", "Closed Won"))
                        changes.append((dec + timedelta(minutes=1), "forecast_category", "Closed"))
                        if r.random() < c["renewer_amount_change"]:
                            changes.append((dec + timedelta(minutes=2), "amount_usd", f"{amount * r.uniform(0.9, 1.3):.2f}"))
                        changes.append((dec + timedelta(minutes=3), "close_date", dec.date().isoformat()))
                    elif r.random() < c["stale_close_prob"]:
                        changes.append((dec + timedelta(days=r.randint(5, 30)), "stage", "Closed Won"))
                self.add_opp(acc, "renewal", t, created, initial, changes, source, r)
            # expansion opportunities over the account's lifetime
            r = self.rng("expansion", acc["account_id"])
            end = min(self.extract, max(t["decided"] for t in acc["terms"]))
            life_days = (end - datetime.combine(acc["created_date"], time())).days
            n = sum(1 for _ in range(max(1, life_days // 30)) if r.random() < self.spec["expansion_rate_per_year"] / 12)
            for _ in range(n):
                created = datetime.combine(acc["created_date"] + timedelta(days=r.randint(30, max(31, life_days - 1))),
                                           time(r.randint(8, 18), r.randint(0, 59), r.randint(0, 59)))
                t = self.term_at(acc, created.date()) or acc["terms"][-1]
                source = "partner" if r.random() < c["partner_share"] else "direct"
                amt = t["arr_usd"] * r.uniform(0.05, 0.3)
                initial = dict(stage="Qualification", forecast_category="Pipeline", amount_usd=f"{amt:.2f}",
                               close_date=(created.date() + timedelta(days=60)).isoformat(), competitor="")
                p1 = created + timedelta(days=r.randint(5, 30), hours=r.randint(0, 6))
                closed = p1 + timedelta(days=r.randint(10, 90), hours=r.randint(0, 6))
                won = r.random() < sigmoid(0.3 - 0.8 * t["u"])
                changes = [(p1, "stage", "Proposal"), (p1 + timedelta(minutes=5), "forecast_category", "Best Case"),
                           (closed, "stage", "Closed Won" if won else "Closed Lost"),
                           (closed + timedelta(minutes=1), "forecast_category", "Closed" if won else "Omitted")]
                self.add_opp(acc, "expansion", None, created, initial, changes, source, r)

    # ------------------------------------------------------------------ CS health
    def build_health(self):
        h = self.spec["health"]
        for acc in self.accounts:
            r = self.rng("health", acc["account_id"])
            created = datetime.combine(acc["created_date"], time(9, r.randint(0, 59)))
            state = dict(health_score="70", health_color="Green", nps_last="", csm_sentiment="Neutral")
            events = [(created, f, "", v) for f, v in state.items()]
            proposals = []
            # monthly health score recalculation
            m = date(acc["created_date"].year, acc["created_date"].month, 1)
            while True:
                m = date(m.year + (m.month == 12), 1 if m.month == 12 else m.month + 1, 1)
                when = datetime.combine(m, time(10, 0)) + timedelta(minutes=r.randint(0, 420))
                if when >= self.extract:
                    break
                t = self.term_at(acc, m)
                if t is None:
                    break
                score = 72 - 13 * t["u"] + r.gauss(0, 9)
                if when >= t["T"]:
                    frac = min(1.0, (when - t["T"]).days / 90.0)
                    if t["churn"]:
                        score -= h["churn_decline"] * frac * r.uniform(0, 40)
                    elif r.random() < h["renewer_decline"]:
                        score -= frac * r.uniform(0, 25)
                    elif r.random() < h["renewer_improve"]:
                        score += r.uniform(0, 12)
                score = int(round(clip(score, 0, 100)))
                color = "Green" if score >= 70 else "Yellow" if score >= 50 else "Red"
                proposals.append((when, "health_score", str(score)))
                proposals.append((when + timedelta(seconds=1), "health_color", color))
            # quarterly NPS survey and QBR sentiment
            q = acc["created_date"] + timedelta(days=r.randint(20, 80))
            while datetime.combine(q, time()) < self.extract:
                t = self.term_at(acc, q)
                if t is None:
                    break
                when = datetime.combine(q, time(r.randint(8, 20), r.randint(0, 59)))
                nps = 22 - 20 * t["u"] + r.gauss(0, 22)
                if t["churn"] and when >= t["T"]:
                    nps -= 30 * h["churn_decline"]
                proposals.append((when, "nps_last", str(int(round(clip(nps, -100, 100))))))
                x = r.random()
                if x < sigmoid(-1.8 + 1.2 * t["u"]):
                    sent = "Negative"
                elif x < sigmoid(-1.8 + 1.2 * t["u"]) + sigmoid(-0.4 - 1.0 * t["u"]) * 0.7:
                    sent = "Positive"
                else:
                    sent = "Neutral"
                proposals.append((when + timedelta(hours=3), "csm_sentiment", sent))
                if t["churn"] and when >= t["T"] and r.random() < h["sentiment_escalation"]:
                    proposals.append((when + timedelta(days=r.randint(1, 20)), "csm_sentiment", "Negative"))
                q += timedelta(days=r.randint(80, 100))
            last_at: dict[str, datetime] = {}
            for when, field, value in sorted(proposals):
                if field in last_at and when.date() <= last_at[field].date():
                    continue  # at most one change per field per day (one nightly batch per day)
                if when >= self.extract or state[field] == value:
                    continue
                events.append((when, field, state[field], value))
                state[field] = value
                last_at[field] = when
            hist = []
            for when, field, old, new in events:
                hist.append(dict(account_id=acc["account_id"], field=field, old_value=old, new_value=new, changed_at=when,
                                 synced_at=self.health_synced(when, acc["account_id"]), changed_by=acc["csm"] if field != "health_score" and field != "health_color" else "health-model"))
            self.health_hist.extend(x for x in hist if x["synced_at"] < self.extract)

    def build_sync_log(self):
        for o in self.spec["crm"]["outages"]:
            self.sync_log.append(dict(source="crm", event="replication_outage", started_at=o["start"], ended_at=o["end"],
                                      note=f"CRM change stream paused; backlog replayed at {o['replay']}"))

    # ------------------------------------------------------------------ output
    def generate(self):
        self.build_accounts()
        self.build_contracts()
        self.build_usage_and_support()
        self.build_crm()
        self.build_health()
        self.build_sync_log()
        return self

    def write(self, root: Path):
        root = Path(root)
        (root / "data").mkdir(parents=True, exist_ok=True)
        path = root / "data/warehouse.db"
        if path.exists():
            path.unlink()
        con = sqlite3.connect(path)
        con.executescript(DDL)
        con.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?)", [
            (a["account_id"], a["segment"], a["region"], a["industry"], a["created_date"].isoformat(),
             fmt(datetime.combine(a["created_date"], time(5, 0)))) for a in self.accounts])
        con.executemany("INSERT INTO contracts VALUES (?,?,?,?,?,?,?,?)", [
            (t["contract_id"], t["account_id"], t["start_date"].isoformat(), t["renewal_date"].isoformat(), t["seats"],
             t["arr_usd"], t["plan"], fmt(datetime.combine(t["start_date"], time(6, 0)))) for t in self.contracts])
        con.executemany("INSERT INTO renewal_outcomes VALUES (?,?,?,?,?,?)", [
            (o["contract_id"], o["account_id"], o["renewal_date"].isoformat(), o["outcome"], fmt(o["decided_at"]),
             fmt(o["synced_at"])) for o in self.outcomes])
        con.executemany("INSERT INTO usage_weekly VALUES (?,?,?,?,?,?)", self.usage)
        con.executemany("INSERT INTO support_tickets VALUES (?,?,?,?,?,?,?)", [
            (x["ticket_id"], x["account_id"], fmt(x["opened_at"]), x["severity"], x["category"], fmt(x["closed_at"]),
             fmt(x["synced_at"])) for x in self.tickets])
        con.executemany("INSERT INTO crm_opportunities VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
            (o["opportunity_id"], o["account_id"], o["contract_id"], o["opportunity_type"], o["lead_source"], o["owner"],
             fmt(o["created_at"]), o["stage"], o["forecast_category"], float(o["amount_usd"]), o["close_date"],
             o["competitor"] or None, fmt(o["last_modified_at"]), fmt(o["synced_at"])) for o in self.opps])
        hist = sorted(self.opp_hist, key=lambda h: (h["synced_at"], h["opportunity_id"], h["changed_at"], h["field"]))
        con.executemany("INSERT INTO crm_opportunity_field_history VALUES (?,?,?,?,?,?,?,?)", [
            (f"OFH-{i:08d}", h["opportunity_id"], h["field"], h["old_value"], h["new_value"], fmt(h["changed_at"]),
             fmt(h["synced_at"]), h["changed_by"]) for i, h in enumerate(hist, 1)])
        cur_health = {}
        for h in sorted(self.health_hist, key=lambda h: (h["synced_at"], h["changed_at"])):
            rec = cur_health.setdefault(h["account_id"], {"last_changed": h["changed_at"], "synced": h["synced_at"]})
            rec[h["field"]] = h["new_value"]
            rec["last_changed"] = max(rec["last_changed"], h["changed_at"])
            rec["synced"] = max(rec["synced"], h["synced_at"])
        con.executemany("INSERT INTO cs_account_health VALUES (?,?,?,?,?,?,?)", [
            (a, int(v["health_score"]), v["health_color"], int(v["nps_last"]) if v["nps_last"] else None,
             v["csm_sentiment"], fmt(v["last_changed"]), fmt(v["synced"])) for a, v in sorted(cur_health.items())])
        hh = sorted(self.health_hist, key=lambda h: (h["synced_at"], h["account_id"], h["changed_at"], h["field"]))
        con.executemany("INSERT INTO cs_account_health_history VALUES (?,?,?,?,?,?,?,?)", [
            (f"HFH-{i:08d}", h["account_id"], h["field"], h["old_value"], h["new_value"], fmt(h["changed_at"]),
             fmt(h["synced_at"]), h["changed_by"]) for i, h in enumerate(hh, 1)])
        con.executemany("INSERT INTO warehouse_sync_log VALUES (?,?,?,?,?)", [
            (x["source"], x["event"], x["started_at"], x["ended_at"], x["note"]) for x in self.sync_log])
        con.commit()
        con.execute("VACUUM")
        con.close()


DDL = """
CREATE TABLE accounts (account_id TEXT PRIMARY KEY, segment TEXT NOT NULL, region TEXT NOT NULL, industry TEXT NOT NULL,
  created_date TEXT NOT NULL, synced_at TEXT NOT NULL);
CREATE TABLE contracts (contract_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, start_date TEXT NOT NULL,
  renewal_date TEXT NOT NULL, seats INTEGER NOT NULL, arr_usd REAL NOT NULL, plan TEXT NOT NULL, synced_at TEXT NOT NULL);
CREATE TABLE renewal_outcomes (contract_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, renewal_date TEXT NOT NULL,
  outcome TEXT NOT NULL, decided_at TEXT NOT NULL, synced_at TEXT NOT NULL);
CREATE TABLE usage_weekly (account_id TEXT NOT NULL, week_start TEXT NOT NULL, active_users INTEGER NOT NULL,
  api_calls INTEGER NOT NULL, logins INTEGER NOT NULL, synced_at TEXT NOT NULL, PRIMARY KEY (account_id, week_start));
CREATE TABLE support_tickets (ticket_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, opened_at TEXT NOT NULL,
  severity TEXT NOT NULL, category TEXT NOT NULL, closed_at TEXT, synced_at TEXT NOT NULL);
CREATE TABLE crm_opportunities (opportunity_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, contract_id TEXT,
  opportunity_type TEXT NOT NULL, lead_source TEXT NOT NULL, owner TEXT NOT NULL, created_at TEXT NOT NULL,
  stage TEXT NOT NULL, forecast_category TEXT NOT NULL, amount_usd REAL NOT NULL, close_date TEXT NOT NULL,
  competitor TEXT, last_modified_at TEXT NOT NULL, synced_at TEXT NOT NULL);
CREATE TABLE crm_opportunity_field_history (history_id TEXT PRIMARY KEY, opportunity_id TEXT NOT NULL, field TEXT NOT NULL,
  old_value TEXT, new_value TEXT, changed_at TEXT NOT NULL, synced_at TEXT NOT NULL, changed_by TEXT NOT NULL);
CREATE TABLE cs_account_health (account_id TEXT PRIMARY KEY, health_score INTEGER NOT NULL, health_color TEXT NOT NULL,
  nps_last INTEGER, csm_sentiment TEXT NOT NULL, last_changed_at TEXT NOT NULL, synced_at TEXT NOT NULL);
CREATE TABLE cs_account_health_history (history_id TEXT PRIMARY KEY, account_id TEXT NOT NULL, field TEXT NOT NULL,
  old_value TEXT, new_value TEXT, changed_at TEXT NOT NULL, synced_at TEXT NOT NULL, changed_by TEXT NOT NULL);
CREATE TABLE warehouse_sync_log (source TEXT NOT NULL, event TEXT NOT NULL, started_at TEXT NOT NULL, ended_at TEXT,
  note TEXT);
CREATE INDEX ix_usage_account ON usage_weekly(account_id, week_start);
CREATE INDEX ix_tickets_account ON support_tickets(account_id, opened_at);
CREATE INDEX ix_opp_account ON crm_opportunities(account_id);
CREATE INDEX ix_ofh_opp ON crm_opportunity_field_history(opportunity_id, synced_at);
CREATE INDEX ix_hfh_account ON cs_account_health_history(account_id, synced_at);
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
    w = World(spec).generate()
    w.write(root)
    return w


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    build(VISIBLE_SPEC, out)
    print(sqlite_logical_digest(out / "data/warehouse.db"))
