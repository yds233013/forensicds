#!/usr/bin/env python3
"""Deterministic synthetic product warehouse for ForensicDS Task 05 (onboarding experiment readout).

Produces `data/product.db` (SQLite):

  workspaces        one row per workspace (tenant): plan, signup channel, size band, internal flag
  users             one row per user
  memberships       one row per (user, workspace) membership
  experiments       experiment registry (id, unit type, dates)
  xp_assignments    assignment log (one row per assignment decision, incl. SDK retries and re-bucketing incidents)
  exposure_events   client-side exposure logs (user, workspace context, variant as rendered by the SDK)
  product_events    product analytics events (user, workspace context)

Mechanism: XP-231 randomizes new workspaces at onboarding start into an onboarding checklist (treatment) or the
standard dashboard (control). The checklist slightly raises the chance that members perform a core action. Exposure
logging differs by arm: control logs when the dashboard loads, treatment logs when the checklist component finishes
mounting, which low-intent users often leave before. The web SDK caches a user's variant, so users who belong to
several workspaces see (and log) the variant of the first workspace they were bucketed in.
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
REGIONS = [("NA", .46), ("EMEA", .34), ("APAC", .20)]
NOISE_EVENTS = ["page_view", "project_created", "invite_sent", "integration_viewed", "settings_opened"]

VISIBLE_SPEC: dict = {
    "name": "visible",
    "seed": 5153,
    "xp_id": "XP-231",
    "xp_start": "2026-07-06",
    "extract_date": "2026-09-02",
    "analysis_date": "2026-09-01",
    "workspaces_per_day": 105,
    "self_serve_share": 0.80,
    "internal_share": 0.015,
    "self_serve_plans": {"free": 0.60, "team": 0.40},
    "sales_plans": {"business": 0.70, "enterprise_trial": 0.30},
    "plan_intent": {"free": -0.25, "team": 0.25, "starter": 0.0, "business": 0.3, "enterprise_trial": 0.2},
    "size_mix": {"1-10": 0.56, "11-50": 0.30, "51-200": 0.10, "201+": 0.04},
    "extra_members": {"1-10": 2.2, "11-50": 4.5, "51-200": 7.0, "201+": 9.0},
    "stratify": "plan_size",
    "onboarding_lag_long_share": 0.15,
    "onboarding_lag_long_days": [1, 10],
    "agency_share": 0.05,
    "sdk_retry_share": 0.02,
    "rebucket_incidents": [{"at": "2026-07-29 14:00:00", "share": 0.06, "lookback_days": 20}],
    "treatment_share": 0.5,
    "open_intercept": 1.3,
    "open_slope": 0.7,
    "control_log_rate": 0.985,
    "mount_intercept": 0.3,
    "mount_intercept_after_fix": 0.9,
    "mount_slope": 1.4,
    "perf_fix_at": "2026-07-21 09:00:00",
    "core_intercept": -0.55,
    "core_slope": 1.0,
    "core_lift": 0.07,
    "core_delay_days": [0.0, 19.0],
    "api_core_rate": 0.03,
    "pre_assignment_activity_share": 0.4,
    "campaigns": [{"from": "2026-08-03", "to": "2026-08-14", "extra_per_day": 35, "intent_shift": -0.6}],
    "concurrent_user_xp": {"id": "XP-240", "from": "2026-07-20", "visit_rate": 0.2},
}


def fmt(x: datetime | None) -> str | None:
    return None if x is None else x.strftime(TS)


def dtp(s: str) -> datetime:
    return datetime.strptime(s, TS)


def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def pick(r: random.Random, weights: dict):
    x, acc = r.random() * sum(weights.values()), 0.0
    for k, w in weights.items():
        acc += w
        if x < acc:
            return k
    return k


def bucket(salt: str, unit: str) -> float:
    return int(hashlib.sha256(f"{salt}:{unit}".encode()).hexdigest()[:8], 16) / 0x100000000


class World:
    def __init__(self, spec: dict):
        self.spec = spec
        self.seed = spec["seed"]
        self.extract = datetime.combine(date.fromisoformat(spec["extract_date"]), time())
        self.workspaces, self.users, self.members, self.assign, self.expo, self.events = [], [], [], [], [], []
        self.agency_pool: list[dict] = []
        self.n_users = 0

    def rng(self, *parts):
        return random.Random(":".join(str(p) for p in (self.seed,) + parts))

    def new_user(self, created: datetime, r, agency=False) -> dict:
        self.n_users += 1
        u = dict(user_id=f"u_{(self.n_users * 2654435761 + self.seed * 97) % 4294967291:010d}", created_at=created,
                 base=r.gauss(0, 0.8), agency=agency, cached={}, xp240=None)
        self.users.append(u)
        return u

    def stratum(self, plan: str, size: str, region: str) -> str:
        by = self.spec["stratify"]
        small = size in ("1-10", "11-50")
        if by == "plan_size":
            return f"{plan}|{'small' if small else 'large'}"
        if by == "plan_region":
            return f"{plan}|{region}"
        raise ValueError(by)

    def generate(self):
        s = self.spec
        start = date.fromisoformat(s["xp_start"])
        day = start - timedelta(days=12)
        n = 0
        while datetime.combine(day, time()) < self.extract:
            r = self.rng("day", day.isoformat())
            k = max(0, int(round(r.gauss(s["workspaces_per_day"] * (0.5 if day.weekday() >= 5 else 1), 6))))
            camp = [c for c in s["campaigns"] if date.fromisoformat(c["from"]) <= day <= date.fromisoformat(c["to"])]
            extra = sum(c["extra_per_day"] for c in camp)
            for i in range(k + extra):
                n += 1
                self.make_workspace(n, day, camp[0]["intent_shift"] if (camp and i >= k) else 0.0)
            day += timedelta(days=1)
        self.concurrent_experiment()
        return self

    def make_workspace(self, n: int, day: date, shift: float):
        s = self.spec
        wid = f"ws_{(n * 2246822519 + self.seed * 31) % 4294967291:010d}"
        r = self.rng("ws", wid)
        created = datetime.combine(day, time(r.randint(0, 23), r.randint(0, 59), r.randint(0, 59)))
        channel = "self_serve" if r.random() < s["self_serve_share"] else "sales_assisted"
        plan = pick(r, s["self_serve_plans"] if channel == "self_serve" else s["sales_plans"])
        size = pick(r, s["size_mix"])
        region = pick(r, dict(REGIONS))
        internal = int(r.random() < s["internal_share"])
        u_w = r.gauss(0, 1) + s["plan_intent"][plan] + shift
        ws = dict(workspace_id=wid, created_at=created, plan=plan, signup_channel=channel, size=size, region=region,
                  is_internal=internal)
        self.workspaces.append(ws)
        # onboarding start = assignment time
        if r.random() < s["onboarding_lag_long_share"]:
            lag = timedelta(days=r.uniform(*s["onboarding_lag_long_days"]))
        else:
            lag = timedelta(minutes=r.uniform(1, 180))
        assigned = created + lag
        xp_start = datetime.combine(date.fromisoformat(s["xp_start"]), time())
        in_xp = xp_start <= assigned < self.extract
        variant = None
        if in_xp:
            variant = "treatment" if bucket(s["xp_id"], wid) < s["treatment_share"] else "control"
            stratum = self.stratum(plan, size, region)
            self.assign.append([s["xp_id"], "workspace", wid, variant, stratum, assigned])
            if r.random() < s["sdk_retry_share"]:
                self.assign.append([s["xp_id"], "workspace", wid, variant, stratum, assigned + timedelta(seconds=r.randint(1, 40))])
            for inc in s["rebucket_incidents"]:
                t = dtp(inc["at"])
                if t - timedelta(days=inc["lookback_days"]) <= assigned < t and t < self.extract and r.random() < inc["share"]:
                    v2 = "treatment" if bucket(s["xp_id"] + ":flush:" + inc["at"], wid) < s["treatment_share"] else "control"
                    self.assign.append([s["xp_id"], "workspace", wid, v2, stratum, t + timedelta(seconds=r.randint(0, 3600))])
        # members
        owner = self.new_user(created, r)
        roster = [(owner, created)]
        extra = int(min(60, max(0, round(r.expovariate(1 / s["extra_members"][size])))))
        for j in range(extra):
            joined = assigned + timedelta(days=r.expovariate(1 / 3.0))
            if joined >= self.extract:
                continue
            u = None
            if self.agency_pool and r.random() < s["agency_share"]:
                u = r.choice(self.agency_pool)
                if u["created_at"] > joined:  # an agency user can only join after their account exists
                    u = None
            if u is None:
                u = self.new_user(joined, r, agency=r.random() < s["agency_share"])
                if u["agency"]:
                    self.agency_pool.append(u)
            if any(m[0] is u for m in roster):
                continue
            roster.append((u, joined))
        # teammates of workspaces whose owner starts onboarding late sometimes set things up before assignment
        ps = self.rng("pre", wid)
        if assigned - created >= timedelta(days=1) and ps.random() < s["pre_assignment_activity_share"]:
            for idx in range(min(len(roster), ps.randint(2, 4))):
                u, joined = roster[idx]
                if idx:
                    joined = created + (assigned - created) * ps.uniform(0.0, 0.5)
                    if u["created_at"] > joined:
                        continue
                    roster[idx] = (u, joined)
                self.events.append([u["user_id"], wid, "core_action", joined + (assigned - joined) * ps.uniform(0.1, 0.95)])
        for u, joined in roster:
            self.members.append((u["user_id"], wid, fmt(joined), "owner" if u is owner else "member"))
            self.member_behaviour(ws, u, joined, assigned, variant, u_w, r)

    def member_behaviour(self, ws, u, joined, assigned, variant, u_w, r):
        s = self.spec
        wid = ws["workspace_id"]
        u_i = u_w + 0.5 * u["base"] + r.gauss(0, 0.6)
        ref = max(joined, assigned)
        # the SDK caches the first variant a user was bucketed into for this experiment
        shown = None
        if variant is not None:
            shown = u["cached"].setdefault(s["xp_id"], variant)
        checklist = shown == "treatment" and ws["signup_channel"] == "self_serve"
        opened_at = None
        if r.random() < sigmoid(s["open_intercept"] + s["open_slope"] * u_i):
            opened_at = ref + timedelta(minutes=r.expovariate(1 / (60 * 20.0)))
            if opened_at >= self.extract:
                opened_at = None
        if opened_at is not None and variant is not None:
            if shown == "control" and r.random() < s["control_log_rate"]:
                self.expo.append([s["xp_id"], u["user_id"], wid, "control", opened_at + timedelta(seconds=r.randint(1, 5))])
            elif shown == "treatment":
                mi = s["mount_intercept_after_fix"] if opened_at >= dtp(s["perf_fix_at"]) else s["mount_intercept"]
                if ws["signup_channel"] == "self_serve" and r.random() < sigmoid(mi + s["mount_slope"] * u_i):
                    self.expo.append([s["xp_id"], u["user_id"], wid, "treatment", opened_at + timedelta(seconds=r.randint(3, 25))])
        # core actions
        if opened_at is not None:
            p = sigmoid(s["core_intercept"] + s["core_slope"] * u_i + (s["core_lift"] if checklist else 0.0))
            if r.random() < p:
                t = opened_at + timedelta(days=r.uniform(*s["core_delay_days"]))
                for _ in range(1 + (r.random() < 0.5)):
                    if t < self.extract:
                        self.events.append([u["user_id"], wid, "core_action", t])
                    t += timedelta(days=r.expovariate(1 / 4.0))
            for _ in range(r.randint(1, 4)):
                t = opened_at + timedelta(minutes=r.uniform(0, 60 * 24 * 20))
                if t < self.extract:
                    self.events.append([u["user_id"], wid, r.choice(NOISE_EVENTS), t])
        elif r.random() < s["api_core_rate"]:
            t = ref + timedelta(days=r.uniform(0, 25))
            if t < self.extract:
                self.events.append([u["user_id"], wid, "core_action", t])

    def concurrent_experiment(self):
        cx = self.spec.get("concurrent_user_xp")
        if not cx:
            return
        start = datetime.combine(date.fromisoformat(cx["from"]), time())
        for u in self.users:
            if not (start <= u["created_at"] < self.extract):
                continue
            r = self.rng("xp240", u["user_id"])
            v = "treatment" if bucket(cx["id"], u["user_id"]) < 0.5 else "control"
            self.assign.append([cx["id"], "user", u["user_id"], v, "all", u["created_at"] + timedelta(seconds=r.randint(5, 600))])
            if r.random() < cx["visit_rate"]:
                t = u["created_at"] + timedelta(days=r.uniform(0, 12))
                if t < self.extract:
                    self.expo.append([cx["id"], u["user_id"], None, v, t])

    def write(self, root: Path):
        root = Path(root)
        (root / "data").mkdir(parents=True, exist_ok=True)
        path = root / "data/product.db"
        if path.exists():
            path.unlink()
        con = sqlite3.connect(path)
        con.executescript(DDL)
        con.executemany("INSERT INTO workspaces VALUES (?,?,?,?,?,?,?)", [
            (w["workspace_id"], fmt(w["created_at"]), w["plan"], w["signup_channel"], w["size"], w["region"], w["is_internal"])
            for w in sorted(self.workspaces, key=lambda w: (w["created_at"], w["workspace_id"])) if w["created_at"] < self.extract])
        con.executemany("INSERT INTO users VALUES (?,?)", sorted((u["user_id"], fmt(u["created_at"])) for u in self.users))
        con.executemany("INSERT INTO memberships VALUES (?,?,?,?)", sorted(self.members, key=lambda m: (m[2], m[0], m[1])))
        s = self.spec
        con.executemany("INSERT INTO experiments VALUES (?,?,?,?,?)", [
            (s["xp_id"], "Onboarding checklist for new workspaces", "workspace", s["xp_start"], "running")]
            + ([(s["concurrent_user_xp"]["id"], "Annual-plan emphasis on pricing page", "user", s["concurrent_user_xp"]["from"], "running")]
               if s.get("concurrent_user_xp") else []))
        rows = sorted((a for a in self.assign if a[5] < self.extract), key=lambda a: (a[5], a[2], a[0]))
        con.executemany("INSERT INTO xp_assignments VALUES (?,?,?,?,?,?,?)",
                        [(f"as_{i:08d}", a[0], a[1], a[2], a[3], a[4], fmt(a[5])) for i, a in enumerate(rows, 1)])
        ex = sorted((e for e in self.expo if e[4] < self.extract), key=lambda e: (e[4], e[1], e[0]))
        con.executemany("INSERT INTO exposure_events VALUES (?,?,?,?,?,?)",
                        [(f"ex_{i:08d}", e[0], e[1], e[2], e[3], fmt(e[4])) for i, e in enumerate(ex, 1)])
        ev = sorted(self.events, key=lambda e: (e[3], e[0], e[1], e[2]))
        con.executemany("INSERT INTO product_events VALUES (?,?,?,?,?)",
                        [(f"pe_{i:09d}", e[0], e[1], e[2], fmt(e[3])) for i, e in enumerate(ev, 1)])
        con.commit()
        con.execute("VACUUM")
        con.close()


DDL = """
CREATE TABLE workspaces (workspace_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, plan TEXT NOT NULL,
  signup_channel TEXT NOT NULL, size_band TEXT NOT NULL, region TEXT NOT NULL, is_internal INTEGER NOT NULL);
CREATE TABLE users (user_id TEXT PRIMARY KEY, created_at TEXT NOT NULL);
CREATE TABLE memberships (user_id TEXT NOT NULL, workspace_id TEXT NOT NULL, joined_at TEXT NOT NULL, role TEXT NOT NULL,
  PRIMARY KEY (user_id, workspace_id));
CREATE TABLE experiments (experiment_id TEXT PRIMARY KEY, name TEXT NOT NULL, unit_type TEXT NOT NULL, started_on TEXT NOT NULL,
  status TEXT NOT NULL);
CREATE TABLE xp_assignments (assignment_id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, unit_type TEXT NOT NULL,
  unit_id TEXT NOT NULL, variant TEXT NOT NULL, stratum TEXT NOT NULL, assigned_at TEXT NOT NULL);
CREATE TABLE exposure_events (exposure_id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, user_id TEXT NOT NULL,
  workspace_id TEXT, variant TEXT NOT NULL, exposed_at TEXT NOT NULL);
CREATE TABLE product_events (event_id TEXT PRIMARY KEY, user_id TEXT NOT NULL, workspace_id TEXT NOT NULL,
  event_type TEXT NOT NULL, event_at TEXT NOT NULL);
CREATE INDEX ix_assign ON xp_assignments(experiment_id, unit_id, assigned_at);
CREATE INDEX ix_expo ON exposure_events(experiment_id, user_id, exposed_at);
CREATE INDEX ix_events ON product_events(workspace_id, event_type, event_at);
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
    print(sqlite_logical_digest(out / "data/product.db"))
