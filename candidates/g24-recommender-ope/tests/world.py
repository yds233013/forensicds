#!/usr/bin/env python3
"""Deterministic synthetic home-row recommendation logs for ForensicDS G24 (off-policy evaluation).

Standard library only; fully determined by the spec. Deleted from the image after the build; tests/ holds a copy.

Per home request:
    retrieval  -> pool of K titles for the user
    ranking    -> production: eligible titles by v6 score;  exploration: uniform shuffle of the pool
    business rules -> ineligible titles (already watched, licence window) drop out of the ordered list
    serving    -> the first five survivors are the slate; the response is cached per (session, surface) for the TTL
    clients    -> renders; a reload inside the TTL re-serves the stored slate under a new serve_id
    clicks     -> position based: P(click at slot k) = examination(device, k) * relevance(user, title)

The propensity the ranker logs is the ordered-slate probability over the PRE-filter pool of size K.  The served
ordering is uniform over orderings of the m eligible titles, so the item-in-slot marginal is 1/m.

A session that comes back after the TTL gets a NEW decision (fresh retrieval and, in the exploration stream, a fresh
shuffle); for production the pool is unchanged, so its slate is usually identical to the earlier one.
"""
from __future__ import annotations

import hashlib
import math
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

SLOTS = 5
DEVICES = ("web", "mobile", "tv")
GENRES = ("Drama", "Comedy", "Documentary", "Thriller", "Kids", "Sport")

THETA = {
    "web": [1.00, 0.70, 0.54, 0.43, 0.35],
    "mobile": [1.00, 0.62, 0.45, 0.33, 0.26],
    "tv": [1.00, 0.52, 0.33, 0.22, 0.15],
}

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 20260901,
    "start": "2026-06-01",
    "days": 92,
    "n_users": 42000,
    "n_items": 4000,
    "n_decisions": 130_000,
    "explore_share": 0.45,
    "ab_share": 0.50,          # share of non-exploration traffic in the v7 arm during the A/B window
    "ab_window": (46, 67),
    "device_mix": (0.45, 0.30, 0.25),
    "theta": THETA,
    "pool_k": (8, 14),             # fallback when pool_k_device is not set
    "pool_k_device": {"web": (12, 18), "mobile": (9, 14), "tv": (6, 9)},   # retrieval budget per device
    "filter_rate": (0.0, 0.30),
    "filter_taste_coupling": 0.0,  # suppression intensity vs member taste (0: independent)
    "suppress_relevance": 0.0,     # 0: which titles are suppressed does not depend on their relevance
    "taste_sd": 0.9,
    "pool_taste": 9.0,             # retrieval pool grows with member engagement (titles per unit of taste)
    "min_eligible": 6,
    "r_scale": 0.30,
    "v6_pop_weight": 0.90, "v6_noise": 0.120,
    "v7_mode": "v6_rerank",       # v6_rerank: keeps v6's strong titles, swaps its weakest for a novel one
    "v7_order_novelty": 0.35,   # novelty tilt in v7's ordering of its row (in relevance units)
    "v7_noise": 0.012,
    "v7pd_noise": 0.015,
    "ttl_seconds": 600,
    "reload_lambda": {"web": 0.15, "mobile": 0.25, "tv": 0.55},
    "reload_quality": 1.2,
    "return_after_ttl": 0.18,       # chance the session returns after the TTL: a new decision, often the same slate
    "candidate_log_share_prod": 0.04,
    "trading_hours": (7, 24),
}


class World:
    pass


def _sig(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _poisson(rng: random.Random, lam: float, cap: int = 6) -> int:
    lam = max(lam, 0.01)
    p, cum, x, k = math.exp(-lam), math.exp(-lam), rng.random(), 0
    while x > cum and k < cap:
        k += 1
        p *= lam / k
        cum += p
    return k


def generate(spec: dict) -> World:
    rng = random.Random(spec["seed"])
    w = World()
    w.spec = spec
    start = date.fromisoformat(spec["start"])
    w.start = start

    items = []
    for i in range(spec["n_items"]):
        q = rng.gauss(0, 1)
        items.append({"item_id": f"T{100000 + i}", "q": q, "pop": 0.35 * q + rng.gauss(0, 1),
                      "nov": rng.gauss(0, 1), "genre": GENRES[i % len(GENRES)], "year": 1975 + (i * 7) % 51})
    w.items = items

    theta = {d: spec["theta"][d] for d in DEVICES}
    k_lo, k_hi = spec["pool_k"]
    f_lo, f_hi = spec["filter_rate"]
    ab_lo, ab_hi = spec["ab_window"]
    dev_cum, acc = [], 0.0
    for d, p in zip(DEVICES, spec["device_mix"]):
        acc += p
        dev_cum.append((acc, d))

    decisions, serves, events, cand_rows = [], [], [], []   # events: click rows only
    session_no = 0

    while len(decisions) < spec["n_decisions"]:
        # ---- session context
        user = rng.randrange(spec["n_users"])
        x = rng.random()
        device = next(d for c, d in dev_cum if x <= c)
        day = rng.randrange(spec["days"])
        t = datetime.combine(start + timedelta(days=day), datetime.min.time()) + timedelta(
            hours=rng.randrange(*spec["trading_hours"]), minutes=rng.randrange(60), seconds=rng.randrange(60))
        in_ab_window = ab_lo <= day <= ab_hi
        x = rng.random()
        if x < spec["explore_share"]:
            stream, ab_arm = "explore_shuffle", "none"
        elif in_ab_window:                            # A/B arm is a property of the member
            member_draw = random.Random(f"{spec['seed']}|ab|{user}").random()
            stream, ab_arm = "prod_rank", ("v7" if member_draw < spec["ab_share"] else "control")
        else:
            stream, ab_arm = "prod_rank", "none"
        session_id = f"S{session_no:08d}"
        session_no += 1

        # ---- retrieval pool and per-user relevance (stable within the session)
        u_taste = rng.gauss(0, spec["taste_sd"])
        k_lo_d, k_hi_d = spec["pool_k_device"][device] if spec.get("pool_k_device") else (k_lo, k_hi)
        # members with richer histories get larger retrieval pools (they are also the more engaged members)
        K = rng.randint(k_lo_d, k_hi_d) + int(round(spec["pool_taste"] * u_taste))
        K = max(spec["min_eligible"] + 1, min(K, 30))
        pool = rng.sample(range(spec["n_items"]), K)
        r, s6, s7sel, s7pd, nov = [], [], [], [], []
        for j in pool:
            it = items[j]
            rel = spec["r_scale"] * _sig(it["q"] + u_taste + rng.gauss(0, 0.9) - 0.9)
            r.append(rel)
            s6.append(rel + spec["v6_pop_weight"] * 0.1 * it["pop"] + rng.gauss(0, spec["v6_noise"]))
            s7sel.append(rel + rng.gauss(0, spec["v7_noise"]))
            s7pd.append(rel + rng.gauss(0, spec["v7pd_noise"]))
            nov.append(it["nov"])

        for vec in (s6, s7sel, s7pd):                 # keep scores distinct within a request (no ranking ties)
            seen = {}
            for j, v in enumerate(vec):
                key = round(v, 9)
                while key in seen:
                    v += 1e-7
                    key = round(v, 9)
                seen[key] = j
                vec[j] = v

        taste_rank = _sig(spec["filter_taste_coupling"] * u_taste + rng.gauss(0, 0.5))
        share = f_lo + (f_hi - f_lo) * taste_rank
        m = max(spec["min_eligible"], K - int(share * K))
        supp = [rng.random() + spec["suppress_relevance"] * (r[j] / spec["r_scale"]) for j in range(K)]
        order_supp = sorted(range(K), key=lambda j: supp[j])
        eligible = set(order_supp[:m])
        reasons = {j: ("already_watched" if rng.random() < 0.7 else "licence_window") for j in order_supp[m:]}

        # v7 was trained on the production ranker's own logs: it keeps most of what v6 shows, drops v6's weakest
        # slot for a novel title, and re-orders the row by novelty
        if spec["v7_mode"] == "v6_rerank":
            v6_rank = sorted([j for j in range(K) if j in eligible], key=lambda j: -s6[j])
            outsiders = [j for j in v6_rank[SLOTS:]]
            novel = max(outsiders, key=lambda j: nov[j]) if outsiders else v6_rank[SLOTS - 1]
            top_set = v6_rank[: SLOTS - 1] + [novel]
            s7 = [(10.0 + r[j] + spec["v7_order_novelty"] * spec["r_scale"] * nov[j])
                  if j in top_set else s7sel[j] for j in range(K)]
        else:                                          # "relevance": a genuinely better ranker
            s7 = list(s7sel)

        def slate_by(score):
            return sorted([j for j in range(K) if j in eligible], key=lambda j: -score[j])[:SLOTS]

        target = {"v6": slate_by(s6), "v7": slate_by(s7), "v7_pd": slate_by(s7pd)}
        th = theta[device]
        value = {p: sum(th[k] * r[j] for k, j in enumerate(sl)) for p, sl in target.items()}

        # ---- one or more decisions in this session (a return after the TTL is a new decision)
        n_dec = 1 + (1 if rng.random() < spec["return_after_ttl"] else 0)
        for d_i in range(n_dec):
            if len(decisions) >= spec["n_decisions"]:
                break
            if d_i:
                t = t + timedelta(seconds=spec["ttl_seconds"] + rng.randrange(20, 5400))
            if stream == "explore_shuffle":
                shuffled = list(range(K))
                rng.shuffle(shuffled)
                served = [j for j in shuffled if j in eligible][:SLOTS]
            elif ab_arm == "v7":
                served = target["v7"]
            else:
                served = target["v6"]

            clicks = [1 if rng.random() < th[k] * r[j] else 0 for k, j in enumerate(served)]
            slate_value = sum(th[k] * r[j] for k, j in enumerate(served))
            lam = spec["reload_lambda"][device] * (
                1.0 + spec["reload_quality"] * (spec["r_scale"] - slate_value) / spec["r_scale"])
            extra = _poisson(rng, lam)

            decision_id = f"D{len(decisions):08d}"
            serve_times = sorted([t] + [t + timedelta(seconds=rng.randrange(25, spec["ttl_seconds"] - 20))
                                        for _ in range(extra)])
            propensity = 1.0 if stream == "prod_rank" else math.exp(-sum(math.log(K - q) for q in range(SLOTS)))
            serve_ids = []
            for st in serve_times:
                serve_id = f"R{len(serves):09d}"
                serve_ids.append(serve_id)
                serves.append((serve_id, session_id, f"U{user:06d}", device, "home",
                               st.strftime("%Y-%m-%d %H:%M:%S"), stream, ab_arm,
                               *[items[pool[j]]["item_id"] for j in served], round(propensity, 12), K))
            for k, c in enumerate(clicks):
                if c:
                    s_i = rng.randrange(len(serve_ids))
                    ts = serve_times[s_i] + timedelta(seconds=rng.randrange(3, 120))
                    events.append((f"C{len(events):09d}", serve_ids[s_i], ts.strftime("%Y-%m-%d %H:%M:%S"),
                                   k + 1, items[pool[served[k]]]["item_id"]))

            log_candidates = stream == "explore_shuffle" or rng.random() < spec["candidate_log_share_prod"]
            if log_candidates:
                for j in range(K):
                    cand_rows.append((serve_ids[0], items[pool[j]]["item_id"], round(s6[j], 9), round(s7[j], 9),
                                      round(s7pd[j], 9), reasons.get(j)))

            decisions.append({
                "decision_id": decision_id, "serve_id": serve_ids[0], "serve_ids": serve_ids,
                "session_id": session_id, "user": user, "device": device, "stream": stream, "ab_arm": ab_arm,
                "decided_at": t, "K": K, "m": m, "pool": pool, "eligible": eligible, "served": served,
                "clicks": clicks, "target": target, "value": value, "r": r, "n_serves": len(serve_ids),
                "logged_candidates": log_candidates,
            })

    w.decisions = decisions
    w.serves = serves
    w.events = events
    w.cand_rows = cand_rows
    w.theta = theta
    return w


def truth(w: World) -> dict:
    """Exact policy values over all decisions in the extract (expectations, not click draws)."""
    n = len(w.decisions)
    return {p: sum(d["value"][p] for d in w.decisions) / n for p in ("v6", "v7", "v7_pd")}


# ------------------------------------------------------------------------------------------------ warehouse

SCHEMA = """
CREATE TABLE items (item_id TEXT PRIMARY KEY, title TEXT, genre TEXT, release_year INTEGER);
CREATE TABLE rec_serves (
  serve_id TEXT PRIMARY KEY, session_id TEXT, user_id TEXT, device TEXT, surface TEXT, served_at TEXT,
  stream TEXT, ab_arm TEXT, slot_1 TEXT, slot_2 TEXT, slot_3 TEXT, slot_4 TEXT, slot_5 TEXT,
  propensity REAL, candidate_count INTEGER);
CREATE TABLE rec_candidates (
  serve_id TEXT, item_id TEXT, score_v6 REAL, score_v7 REAL, score_v7_pd REAL, filter_reason TEXT);
CREATE TABLE click_events (
  click_id TEXT PRIMARY KEY, serve_id TEXT, click_time TEXT, position INTEGER, item_id TEXT);
CREATE INDEX ix_serves_session ON rec_serves(session_id, served_at);
"""

DIGEST_TABLES = ("items", "rec_serves", "rec_candidates", "click_events")


def write_db(w: World, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO items VALUES (?,?,?,?)",
                    [(it["item_id"], f"{it['genre']} {it['item_id'][1:]}", it["genre"], it["year"])
                     for it in w.items])
    con.executemany("INSERT INTO rec_serves VALUES (" + ",".join("?" * 15) + ")", w.serves)
    con.executemany("INSERT INTO rec_candidates VALUES (?,?,?,?,?,?)", w.cand_rows)
    con.executemany("INSERT INTO click_events VALUES (?,?,?,?,?)", w.events)
    con.commit()
    con.execute("VACUUM")
    con.close()


def db_digest(path: Path) -> str:
    hh = hashlib.sha256()
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        for t in DIGEST_TABLES:
            hh.update(t.encode())
            try:
                rows = sorted(con.execute(f"SELECT * FROM {t}").fetchall(), key=repr)
            except sqlite3.Error:
                hh.update(b"<missing>")
                continue
            for row in rows:
                hh.update(repr(row).encode())
        hh.update(repr(con.execute("SELECT name, sql FROM sqlite_master ORDER BY name").fetchall()).encode())
    finally:
        con.close()
    return hh.hexdigest()


def build(spec: dict, root: Path) -> World:
    root = Path(root)
    w = generate(spec)
    write_db(w, root / "data/logs.sqlite")
    return w


if __name__ == "__main__":
    import copy
    import time

    t0 = time.time()
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    w = build(copy.deepcopy(VISIBLE_SPEC), target)
    t = truth(w)
    print(f"decisions={len(w.decisions)} serves={len(w.serves)} "
          f"clicks={len(w.events)} candidates={len(w.cand_rows)} truth={ {k: round(v, 4) for k, v in t.items()} } "
          f"in {time.time() - t0:.1f}s")
