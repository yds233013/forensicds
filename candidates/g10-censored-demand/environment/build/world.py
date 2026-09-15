#!/usr/bin/env python3
"""Deterministic synthetic grocery warehouse for ForensicDS G10 (unconstrained demand under stockout censoring).

Standard library only; fully determined by the spec. Deleted from the image after the build; tests/ holds a copy.

Latent demand -> forecast-driven inventory -> in-store arrivals -> sales / stockouts -> observed logs.

Per store x SKU x trading day:
  mu_d   = base_sku * scale_store * dow * season_cat(week) * promo_lift_cat^promo * competitor_store(date) * hours_share
  lambda = mu_d * eps,  eps ~ Gamma(alpha_cat, 1/alpha_cat)                      (day-level shock, mean 1)
  arrivals: Poisson process on trading hours with intensity lambda * g_daytype(hour) (piecewise constant per hour)
  inventory: delivered once a day at the store's slot, up to ceil(m * forecast) capped by shelf capacity;
             leftover carries over; each arrival buys one unit if on-hand > 0, otherwise it is lost.
Forecasts use past observed sales only (no latent quantity):
  v3: trailing 28-day mean of non-promotional sales per calendar/hours unit x the model's own weekday / promo factors;
  v4 (from LEAN-26 go-live): level trained on the last 8 weeks of pre-go-live stockout-free non-promotional days, then
      frozen, x the model's own season trend (noisy), weekday and promo factors (promo under-reaction).
  An 8-week burn-in before the extract window gives the forecasts history; it is not written to the warehouse.
"""
from __future__ import annotations

import bisect
import copy
import math
import random
from collections import deque
from datetime import date, timedelta

WEEKDAY_PROFILE = [2, 3, 4, 5, 5, 5, 5, 5, 6, 8, 11, 13, 10, 6]          # 08..22 (14 h), Mon-Fri
SATURDAY_PROFILE = [3, 5, 7, 9, 10, 10, 9, 8, 7, 7, 7, 7, 6, 5]         # 08..22
SUNDAY_PROFILE = [6, 9, 12, 13, 13, 12, 11, 10]                          # 10..18

CATEGORIES = {
    # name: (alpha, season change over the window (last week vs first week), promo lift)
    "Soups & broths": (3.0, -0.26, 2.0),
    "Hot beverages": (4.0, -0.22, 1.9),
    "Ice cream & frozen desserts": (3.5, +0.30, 2.4),
    "Breakfast cereals": (5.0, 0.0, 1.8),
    "Snacks & crisps": (2.5, 0.0, 2.6),
    "Pasta & sauces": (4.5, 0.0, 2.0),
    "Soft drinks": (3.0, 0.0, 2.2),
    "Household cleaning": (6.0, 0.0, 1.7),
}

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 101013,
    "start": "2026-04-06",
    "weeks": 24,
    "golive_week": 12,                     # LEAN-26 + v4 from the start of week index 12 (2026-06-29)
    "n_stores": 16,
    "afternoon_slot_stores": 6,
    "holdout_stores": 4,
    "skus_per_category": 8,
    "categories": CATEGORIES,
    "sku_base_median": 4.0, "sku_base_sigma": 0.7,
    "store_scale": [0.7, 1.3],
    "dow": [0.92, 0.90, 0.93, 0.98, 1.10, 1.25, 0.92],
    "promo_share_pre": 0.12, "promo_share_post": 0.06,
    "alpha_scale": 1.0,
    "profiles": {"weekday": WEEKDAY_PROFILE, "saturday": SATURDAY_PROFILE, "sunday": SUNDAY_PROFILE},
    "hours": {"weekday": (8, 22), "saturday": (8, 22), "sunday": (10, 18)},
    "m_pre": 1.8, "m_lean": 1.25, "m_holdout": 1.8,
    "shelf_cap_mult": 2.6,
    "forecast_sigma_v3": 0.12, "forecast_sigma_v4": 0.10, "forecast_param_sigma": 0.06, "v4_season_sigma": 0.10,
    "v4_promo_under": 0.85, "burn_weeks": 8,
    "competitor": {"stores": 2, "week": 15, "effect": 0.90},
    "short_hours": [("2026-07-04", 8, 16)],
    "closures": [(11, "2026-05-12")],
}


def daytype(d: date) -> str:
    return "sunday" if d.weekday() == 6 else "saturday" if d.weekday() == 5 else "weekday"


def trading_hours(spec, d: date):
    """(open_hour, close_hour) of the chain calendar for a date (store closures are handled separately)."""
    for ds, o, c in spec["short_hours"]:
        if d.isoformat() == ds:
            return o, c
    return tuple(spec["hours"][daytype(d)])


def profile_for(spec, d: date):
    dt = daytype(d)
    p = spec["profiles"][dt]
    start = spec["hours"][dt][0]
    assert len(p) == spec["hours"][dt][1] - start, "profile length must match standard trading hours"
    tot = float(sum(p))
    return start, [x / tot for x in p]


class World:
    pass


def generate(spec: dict) -> World:
    rng = random.Random(spec["seed"])
    w = World()
    w.spec = spec
    start = date.fromisoformat(spec["start"])
    days = [start + timedelta(days=i) for i in range(7 * spec["weeks"])]
    w.days = days
    cats = list(spec["categories"])
    n_st = spec["n_stores"]
    stores = []
    idx = list(range(n_st))
    rng.shuffle(idx)
    afternoon = set(idx[: spec["afternoon_slot_stores"]])
    # holdout: randomized, balanced across slots
    morning_ids = [i for i in range(n_st) if i not in afternoon]
    aft_ids = [i for i in range(n_st) if i in afternoon]
    rng.shuffle(morning_ids)
    rng.shuffle(aft_ids)
    h = spec["holdout_stores"]
    holdout = set(morning_ids[: h - h // 2] + aft_ids[: h // 2])
    lean_ids = [i for i in range(n_st) if i not in holdout]
    rng.shuffle(lean_ids)
    comp = set(lean_ids[: spec["competitor"]["stores"]]) if spec["competitor"] else set()
    for i in range(n_st):
        stores.append({"store_id": f"S{i + 1:02d}", "i": i, "slot": "afternoon" if i in afternoon else "morning",
                       "arm": "holdout" if i in holdout else "lean26", "scale": rng.uniform(*spec["store_scale"]),
                       "competitor": i in comp})
    w.stores = stores
    skus = []
    for ci, c in enumerate(cats):
        for j in range(spec["skus_per_category"]):
            base = spec["sku_base_median"] * math.exp(rng.gauss(0, spec["sku_base_sigma"]))
            skus.append({"sku_id": f"K{ci + 1}{j + 1:02d}", "category": c, "base": base})
    w.skus = skus
    golive = start + timedelta(days=7 * spec["golive_week"])
    w.golive = golive
    comp_date = start + timedelta(days=7 * spec["competitor"]["week"]) if spec["competitor"] else None
    closures = {(f"S{s:02d}", d) for s, d in spec["closures"]}

    burn = spec.get("burn_weeks", 8)                           # simulated history before the extract window
    sim_days = [start + timedelta(days=i) for i in range(-7 * burn, 7 * spec["weeks"])]

    # promotions: chain-wide SKU-weeks (Wed..Tue)
    promo = set()
    for k in skus:
        for wk in range(-burn, spec["weeks"] + 1):
            wstart = start + timedelta(days=7 * wk - 5)             # Wednesday before week wk's Monday
            share = spec["promo_share_pre"] if wstart + timedelta(days=3) < golive else spec["promo_share_post"]
            if rng.random() < share:
                for dd in range(7):
                    promo.add((k["sku_id"], wstart + timedelta(days=dd)))
    w.promo = promo

    # forecasting models' own (estimated) calendar and promotion factors; neither knows the competitor
    fsig = spec["forecast_param_sigma"]
    dow3 = [x * math.exp(rng.gauss(0, fsig)) for x in spec["dow"]]
    dow4 = [x * math.exp(rng.gauss(0, fsig)) for x in spec["dow"]]
    lift3 = {c: v[2] * math.exp(rng.gauss(0, fsig)) for c, v in spec["categories"].items()}
    lift4 = {c: v[2] * math.exp(rng.gauss(0, fsig)) * spec["v4_promo_under"] for c, v in spec["categories"].items()}
    season4 = {c: v[1] + rng.gauss(0, spec["v4_season_sigma"]) for c, v in spec["categories"].items()}

    def season_at(change, di):
        return 1 + change * (di // 7 - (spec["weeks"] - 1) / 2) / (spec["weeks"] - 1)

    def hours_factor(d, oh, ch):
        so, sc = spec["hours"][daytype(d)]
        return (ch - oh) / (sc - so)

    rows = []   # one per store x sku x trading day in the extract window
    for s in stores:
        for k in skus:
            cat = k["category"]
            alpha, season_change, lift = spec["categories"][cat]
            alpha *= spec["alpha_scale"]
            cap = max(4, math.ceil(spec["shelf_cap_mult"] * k["base"] * s["scale"] * 1.25))
            on_hand = cap // 2
            srng = random.Random(f"{spec['seed']}|{s['store_id']}|{k['sku_id']}")
            # v3: trailing 28-day mean of non-promotional sales per unit of calendar/hours factor (all days)
            last3 = k["base"] * s["scale"] * season_at(season_change, -7 * burn)     # level carried in from before the burn-in
            hist3 = deque((sim_days[0] - timedelta(days=28 - i), last3) for i in range(28))
            sum3 = last3 * 28
            hist4 = []          # (date, normalised sales, clean) for v4 training before go-live
            level4 = None
            for di_sim, d in enumerate(sim_days):
                di = di_sim - 7 * burn
                in_window = di >= 0
                closed = in_window and (s["store_id"], d.isoformat()) in closures
                season = season_at(season_change, di)
                is_promo = (k["sku_id"], d) in promo
                oh, ch = trading_hours(spec, d) if in_window else tuple(spec["hours"][daytype(d)])
                pstart, prof = profile_for(spec, d)
                share = sum(prof[hh - pstart] for hh in range(oh, ch) if 0 <= hh - pstart < len(prof))
                hf = hours_factor(d, oh, ch)
                compf = spec["competitor"]["effect"] if (s["competitor"] and comp_date and d >= comp_date) else 1.0
                mu_full = k["base"] * s["scale"] * spec["dow"][d.weekday()] * season * (lift if is_promo else 1.0)
                mu = mu_full * compf * share         # expected arrivals over the trading hours
                # forecasts from past observed sales only
                while hist3 and (d - hist3[0][0]).days > 28:
                    sum3 -= hist3.popleft()[1]
                level3 = sum3 / len(hist3) if hist3 else last3
                v3 = level3 * dow3[d.weekday()] * (lift3[cat] if is_promo else 1.0) * hf * math.exp(srng.gauss(0, spec["forecast_sigma_v3"]))
                v4 = None
                if d >= golive:
                    if level4 is None:
                        train = [(dd, v, c) for dd, v, c in hist4 if (golive - dd).days <= 56]
                        clean = [v for _dd, v, c in train if c]
                        use = clean if len(clean) >= 4 else [v for _dd, v, _c in train]
                        level4 = sum(use) / len(use) if use else level3
                    v4 = level4 * season_at(season4[cat], di) * dow4[d.weekday()] * (lift4[cat] if is_promo else 1.0) * hf \
                        * math.exp(srng.gauss(0, spec["forecast_sigma_v4"]))
                lean = d >= golive and s["arm"] == "lean26"
                prod_fc = v4 if lean else v3
                m = spec["m_lean"] if lean else (spec["m_holdout"] if d >= golive else spec["m_pre"])
                target = min(cap, math.ceil(m * prod_fc))
                eps = srng.gammavariate(alpha, 1 / alpha)
                lam = mu * eps
                row = {"store": s["store_id"], "sku": k["sku_id"], "category": cat, "date": d, "promo": is_promo,
                       "closed": closed, "open_h": oh, "close_h": ch, "mu": mu, "lam": lam, "v3": v3, "v4": v4,
                       "target": target, "slot": s["slot"], "arm": s["arm"], "competitor_active": compf < 1,
                       "cap": cap, "multiplier": m, "prod_model": "v4" if lean else "v3", "prod_fc": prod_fc}
                if closed:
                    row.update(demand=0, sales=0, hourly=[], events=[], on_hand_open=on_hand, delivered=0,
                               delivery_time=None, on_hand_close=on_hand)
                    rows.append(row)
                    continue
                # arrivals: cumulative-intensity exponential gaps over the trading hours
                hours = [hh for hh in range(oh, ch)]
                rates = [lam / share * prof[hh - pstart] for hh in hours]
                cum = [0.0]
                for r in rates:
                    cum.append(cum[-1] + r)
                arrivals = []
                x = srng.expovariate(1.0) if cum[-1] > 0 else float("inf")
                while x < cum[-1]:
                    j = bisect.bisect_right(cum, x) - 1
                    t = hours[j] + (x - cum[j]) / rates[j]
                    arrivals.append(t)
                    x += srng.expovariate(1.0)
                on_open = on_hand
                events = []
                delivered = 0
                deliv_t = 6.0 if s["slot"] == "morning" else 14.0
                if s["slot"] == "morning":
                    if target > on_hand:
                        delivered = target - on_hand
                        if on_hand == 0:
                            events.append((deliv_t, "back_in_stock"))
                        on_hand = target
                    on_open = on_hand
                sales_times = []
                delivered_done = s["slot"] == "morning"
                for t in arrivals:
                    if not delivered_done and t >= deliv_t:
                        if target > on_hand:
                            delivered = target - on_hand
                            if on_hand == 0:
                                events.append((deliv_t, "back_in_stock"))
                            on_hand = target
                        delivered_done = True
                    if on_hand > 0:
                        on_hand -= 1
                        sales_times.append(t)
                        if on_hand == 0:
                            events.append((t, "out_of_stock"))
                if not delivered_done:
                    if target > on_hand:
                        delivered = target - on_hand
                        if on_hand == 0:
                            events.append((deliv_t, "back_in_stock"))
                        on_hand = target
                hourly = [0] * 24
                for t in sales_times:
                    hourly[int(t)] += 1
                row.update(demand=len(arrivals), sales=len(sales_times), hourly=hourly, events=events,
                           on_hand_open=on_open, delivered=delivered, delivery_time=deliv_t, on_hand_close=on_hand,
                           arrivals=arrivals)
                # history the forecasting systems see (observable: sales, calendar, stock records)
                if not is_promo:
                    norm = len(sales_times) / (dow3[d.weekday()] * hf)
                    hist3.append((d, norm))
                    sum3 += norm
                    last3 = norm
                    if d < golive:
                        clean = on_open > 0 and not any(e == "out_of_stock" and oh <= t < ch for t, e in events)
                        hist4.append((d, len(sales_times) / (dow4[d.weekday()] * hf * season_at(season4[cat], di)), clean))
                if in_window:
                    rows.append(row)
    w.rows = rows
    return w


def in_stock_intervals(row, on_hand_open_for_day):
    """Trading-hour in-stock intervals reconstructed from the day's opening on-hand and events (observable)."""
    oh, ch = row["open_h"], row["close_h"]
    state = on_hand_open_for_day > 0
    t0 = oh
    iv = []
    for t, ev in sorted(row["events"]):
        if t < oh:
            state = ev == "back_in_stock"
            continue
        if t >= ch:
            break
        if ev == "out_of_stock" and state:
            iv.append((t0, t))
            state = False
        elif ev == "back_in_stock" and not state:
            t0 = t
            state = True
    if state:
        iv.append((t0, ch))
    return iv


# ------------------------------------------------------------------------------------------------ warehouse

import hashlib
import sqlite3
import sys
from pathlib import Path

SCHEMA = """
CREATE TABLE stores (store_id TEXT PRIMARY KEY, store_name TEXT NOT NULL, delivery_slot TEXT NOT NULL,
  delivery_time TEXT NOT NULL);
CREATE TABLE store_calendar (store_id TEXT NOT NULL, date TEXT NOT NULL, status TEXT NOT NULL, open_time TEXT,
  close_time TEXT, PRIMARY KEY (store_id, date));
CREATE TABLE skus (sku_id TEXT PRIMARY KEY, category TEXT NOT NULL, description TEXT NOT NULL);
CREATE TABLE planogram (store_id TEXT NOT NULL, sku_id TEXT NOT NULL, shelf_capacity INTEGER NOT NULL,
  PRIMARY KEY (store_id, sku_id));
CREATE TABLE promotions (sku_id TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL, mechanic TEXT NOT NULL);
CREATE TABLE sales_hourly (store_id TEXT NOT NULL, sku_id TEXT NOT NULL, date TEXT NOT NULL, hour INTEGER NOT NULL,
  units INTEGER NOT NULL);
CREATE TABLE availability_events (store_id TEXT NOT NULL, sku_id TEXT NOT NULL, event_time TEXT NOT NULL,
  event_type TEXT NOT NULL);
CREATE TABLE inventory_daily (store_id TEXT NOT NULL, sku_id TEXT NOT NULL, date TEXT NOT NULL,
  on_hand_open INTEGER NOT NULL, delivered_units INTEGER NOT NULL, delivered_at TEXT NOT NULL,
  on_hand_close INTEGER NOT NULL, PRIMARY KEY (store_id, sku_id, date));
CREATE TABLE replenishment_orders (store_id TEXT NOT NULL, sku_id TEXT NOT NULL, date TEXT NOT NULL,
  forecast_model TEXT NOT NULL, forecast_units REAL NOT NULL, multiplier REAL NOT NULL, order_up_to INTEGER NOT NULL,
  PRIMARY KEY (store_id, sku_id, date));
CREATE TABLE forecasts (model TEXT NOT NULL, store_id TEXT NOT NULL, sku_id TEXT NOT NULL, date TEXT NOT NULL,
  forecast_units REAL NOT NULL, PRIMARY KEY (model, store_id, sku_id, date));
CREATE TABLE programme_assignment (store_id TEXT PRIMARY KEY, programme TEXT NOT NULL, arm TEXT NOT NULL,
  go_live_date TEXT NOT NULL, randomisation_block TEXT NOT NULL);
CREATE INDEX ix_sales_key ON sales_hourly (store_id, sku_id, date);
CREATE INDEX ix_events_key ON availability_events (store_id, sku_id, event_time);
"""

SKU_WORDS = {
    "Soups & broths": ["tomato soup", "chicken broth", "minestrone", "lentil soup", "vegetable stock", "pea & ham soup",
                       "miso broth", "mushroom soup"],
    "Hot beverages": ["ground coffee", "instant coffee", "black tea", "green tea", "hot chocolate", "herbal tea",
                      "coffee pods", "chai latte mix"],
    "Ice cream & frozen desserts": ["vanilla tub", "choc ices", "sorbet", "ice lollies", "cookie dough tub",
                                    "frozen yogurt", "cones 4pk", "mango sorbet"],
    "Breakfast cereals": ["corn flakes", "granola", "porridge oats", "muesli", "bran flakes", "rice pops",
                          "wheat biscuits", "choco hoops"],
    "Snacks & crisps": ["ready salted crisps", "tortilla chips", "popcorn", "pretzels", "salt & vinegar crisps",
                        "nut mix", "rice cakes", "cheese puffs"],
    "Pasta & sauces": ["spaghetti", "penne", "tomato sauce", "pesto", "fusilli", "lasagne sheets", "arrabbiata",
                       "carbonara sauce"],
    "Soft drinks": ["cola 2l", "lemonade", "orange juice", "sparkling water", "diet cola 2l", "iced tea", "energy drink",
                    "apple juice"],
    "Household cleaning": ["washing-up liquid", "surface spray", "bleach", "dishwasher tabs", "laundry pods",
                           "glass cleaner", "floor cleaner", "sponges 5pk"],
}


def hhmm(h: float) -> str:
    secs = int(round(h * 3600))
    return f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}"


def ts(d: date, h: float) -> str:
    secs = int(h * 3600)                  # truncate: an event just before closing stays before closing
    dd = d + timedelta(days=secs // 86400)
    secs %= 86400
    return f"{dd.isoformat()} {secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"


def full_in_stock(row) -> bool:
    iv = in_stock_intervals(row, row["on_hand_open"])
    return len(iv) == 1 and abs(iv[0][0] - row["open_h"]) < 1e-9 and abs(iv[0][1] - row["close_h"]) < 1e-9


def write_db(w: World, path: Path) -> None:
    spec = w.spec
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO stores VALUES (?,?,?,?)",
                    [(s["store_id"], f"Harvest Lane {s['store_id']}", s["slot"], "06:00" if s["slot"] == "morning" else "14:00")
                     for s in w.stores])
    cal = []
    closures = {(f"S{i:02d}", d) for i, d in spec["closures"]}
    for s in w.stores:
        for d in w.days:
            if (s["store_id"], d.isoformat()) in closures:
                cal.append((s["store_id"], d.isoformat(), "closed", None, None))
            else:
                oh, ch = trading_hours(spec, d)
                cal.append((s["store_id"], d.isoformat(), "open", f"{oh:02d}:00", f"{ch:02d}:00"))
    con.executemany("INSERT INTO store_calendar VALUES (?,?,?,?,?)", cal)
    words = {}
    for k in w.skus:
        lst = SKU_WORDS.get(k["category"], [])
        j = int(k["sku_id"][2:]) - 1
        words[k["sku_id"]] = lst[j] if j < len(lst) else f"{k['category'].lower()} item {j + 1}"
    con.executemany("INSERT INTO skus VALUES (?,?,?)", [(k["sku_id"], k["category"], words[k["sku_id"]]) for k in w.skus])
    caps = {}
    for r in w.rows:
        caps[(r["store"], r["sku"])] = r["cap"]
    con.executemany("INSERT INTO planogram VALUES (?,?,?)", [(a, b, c) for (a, b), c in sorted(caps.items())])
    # promotions as Wed..Tue ranges
    by_sku = {}
    for sku, d in w.promo:
        by_sku.setdefault(sku, []).append(d)
    promos = []
    for sku, ds in by_sku.items():
        ds.sort()
        i = 0
        while i < len(ds):
            j = i
            while j + 1 < len(ds) and ds[j + 1] == ds[j] + timedelta(days=1):
                j += 1
            promos.append((sku, ds[i].isoformat(), ds[j].isoformat(), "multibuy" if (hash_int(sku + ds[i].isoformat()) % 3) else "price cut"))
            i = j + 1
    promos.sort()
    con.executemany("INSERT INTO promotions VALUES (?,?,?,?)", promos)
    sales, events, inv, orders, fcs = [], [], [], [], []
    for r in w.rows:
        if r["closed"]:
            continue
        d = r["date"]
        ds = d.isoformat()
        for hh, u in enumerate(r["hourly"]):
            if u:
                sales.append((r["store"], r["sku"], ds, hh, u))
        for t, ev in r["events"]:
            events.append((r["store"], r["sku"], ts(d, t), ev))
        inv.append((r["store"], r["sku"], ds, r["on_hand_open"], r["delivered"], hhmm(r["delivery_time"]), r["on_hand_close"]))
        orders.append((r["store"], r["sku"], ds, r["prod_model"], round(r["prod_fc"], 3), r["multiplier"], r["target"]))
        fcs.append(("v3", r["store"], r["sku"], ds, round(r["v3"], 3)))
        if r["v4"] is not None:
            fcs.append(("v4", r["store"], r["sku"], ds, round(r["v4"], 3)))
    sales.sort()
    events.sort()
    con.executemany("INSERT INTO sales_hourly VALUES (?,?,?,?,?)", sales)
    con.executemany("INSERT INTO availability_events VALUES (?,?,?,?)", events)
    con.executemany("INSERT INTO inventory_daily VALUES (?,?,?,?,?,?,?)", inv)
    con.executemany("INSERT INTO replenishment_orders VALUES (?,?,?,?,?,?,?)", orders)
    con.executemany("INSERT INTO forecasts VALUES (?,?,?,?,?)", fcs)
    blocks = {}
    con.executemany("INSERT INTO programme_assignment VALUES (?,?,?,?,?)",
                    [(s["store_id"], "LEAN-26", s["arm"], w.golive.isoformat(), f"slot:{s['slot']}") for s in w.stores])
    con.commit()
    con.execute("VACUUM")
    con.close()


def hash_int(x: str) -> int:
    return int(hashlib.sha256(x.encode()).hexdigest()[:8], 16)


DIGEST_TABLES = ["stores", "store_calendar", "skus", "planogram", "promotions", "sales_hourly", "availability_events",
                 "inventory_daily", "replenishment_orders", "forecasts", "programme_assignment"]


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
    write_db(w, root / "data/warehouse.sqlite")
    return w


def write_field_note(w: World, root: Path) -> None:
    """Store operations field note about the competitor opening (visible workspace only)."""
    spec = w.spec
    if not spec["competitor"]:
        return
    d = date.fromisoformat(spec["start"]) + timedelta(days=7 * spec["competitor"]["week"])
    names = [f"{s['store_id']}" for s in w.stores if s["competitor"]]
    text = f"""# Field note: competitor opening

From: Store operations, south region.

A discount grocer opened on {d.strftime('%A %d %B %Y')} within walking distance of {' and '.join(names)}. Store managers
report lower footfall since the opening. No change to trading hours or ranges at our stores.
No other openings or closures near our stores this year.
"""
    notes = root / "notes"
    notes.mkdir(parents=True, exist_ok=True)
    (notes / f"{(d + timedelta(days=16)).isoformat()}_competitor_opening.md").write_text(text)


if __name__ == "__main__":
    import time
    t0 = time.time()
    target = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    w = build(copy.deepcopy(VISIBLE_SPEC), target)
    write_field_note(w, target)
    rows = [r for r in w.rows if not r["closed"]]
    dem = sum(r["demand"] for r in rows)
    sal = sum(r["sales"] for r in rows)
    print(f"rows={len(rows)} demand={dem} sales={sal} lost_share={1 - sal / dem:.3f} in {time.time() - t0:.1f}s")
