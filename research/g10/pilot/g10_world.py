#!/usr/bin/env python3
"""G10 data-generating process (pilot version of the task generator; standard library only, deterministic).

Latent demand -> forecast-driven inventory -> in-store arrivals -> sales / stockouts -> observed logs.

Per store x SKU x trading day:
  mu_d   = base_sku * scale_store * dow * season_cat(week) * promo_lift_cat^promo * competitor_store(date) * hours_share
  lambda = mu_d * eps,  eps ~ Gamma(alpha_cat, 1/alpha_cat)                      (day-level shock, mean 1)
  arrivals: Poisson process on trading hours with intensity lambda * g_daytype(hour) (piecewise constant per hour)
  inventory: delivered once a day at the store's slot, up to ceil(m * forecast) capped by shelf capacity;
             leftover carries over; each arrival buys one unit if on-hand > 0, otherwise it is lost.
Forecasts: v3 ~ mu * LN(0, s); v4 (from LEAN-26 go-live) ~ mu * (1 - pre-period lost share of the series)
           * promo under-reaction * LN(0, s)  -- trained on censored sales.
"""
from __future__ import annotations

import bisect
import copy
import math
import random
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
    "seed": 101010,
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
    "m_pre": 1.6, "m_lean": 1.1, "m_holdout": 1.6,
    "shelf_cap_mult": 2.6,
    "forecast_sigma_v3": 0.15, "forecast_sigma_v4": 0.12, "v4_promo_under": 0.85, "v4_censor_learning": 1.0,
    "competitor": {"stores": 2, "week": 15, "effect": 0.90},
    "short_hours": [("2026-07-04", 8, 16)],
    "closures": [(11, "2026-05-12")],
}


def daytype(d: date) -> str:
    return "sunday" if d.weekday() == 6 else "saturday" if d.weekday() == 5 else "weekday"


def trading_hours(spec, d: date):
    """(open_hour, close_hour) or None if closed for all stores' standard calendar (store closures handled separately)."""
    for ds, o, c in spec["short_hours"]:
        if d.isoformat() == ds:
            return o, c
    return (10, 18) if d.weekday() == 6 else (8, 22)


def profile_for(spec, d: date):
    dt = daytype(d)
    p = spec["profiles"][dt]
    start = 10 if dt == "sunday" else 8
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

    # promotions: chain-wide SKU-weeks (Wed..Tue)
    promo = set()
    for k in skus:
        for wk in range(spec["weeks"] + 1):
            wstart = start + timedelta(days=7 * wk - 5)             # Wednesday before week wk's Monday
            share = spec["promo_share_pre"] if wstart + timedelta(days=3) < golive else spec["promo_share_post"]
            if rng.random() < share:
                for dd in range(7):
                    promo.add((k["sku_id"], wstart + timedelta(days=dd)))
    w.promo = promo

    rows = []   # one per store x sku x trading day
    for s in stores:
        for k in skus:
            cat = k["category"]
            alpha, season_change, lift = spec["categories"][cat]
            alpha *= spec["alpha_scale"]
            cap = max(4, math.ceil(spec["shelf_cap_mult"] * k["base"] * s["scale"] * 1.25))
            on_hand = cap // 2
            pre_arr = pre_sales = 0
            v4_factor = None
            srng = random.Random(f"{spec['seed']}|{s['store_id']}|{k['sku_id']}")
            for di, d in enumerate(days):
                closed = (s["store_id"], d.isoformat()) in closures
                week = di // 7
                season = 1 + season_change * (week - (spec["weeks"] - 1) / 2) / (spec["weeks"] - 1)
                is_promo = (k["sku_id"], d) in promo
                oh, ch = trading_hours(spec, d)
                pstart, prof = profile_for(spec, d)
                share = sum(prof[hh - pstart] for hh in range(oh, ch) if 0 <= hh - pstart < len(prof))
                compf = spec["competitor"]["effect"] if (s["competitor"] and comp_date and d >= comp_date) else 1.0
                mu_full = k["base"] * s["scale"] * spec["dow"][d.weekday()] * season * (lift if is_promo else 1.0)
                mu = mu_full * compf * share
                # forecasts (do not know the competitor effect)
                f_mu = mu_full * share
                v3 = f_mu * math.exp(srng.gauss(0, spec["forecast_sigma_v3"]))
                if d >= golive and v4_factor is None:
                    v4_factor = 1 - spec["v4_censor_learning"] * (1 - pre_sales / pre_arr if pre_arr else 0.0)
                v4 = None
                if d >= golive:
                    v4 = f_mu * v4_factor * (spec["v4_promo_under"] if is_promo else 1.0) * math.exp(srng.gauss(0, spec["forecast_sigma_v4"]))
                lean = d >= golive and s["arm"] == "lean26"
                prod_fc = v4 if lean else v3
                m = spec["m_lean"] if lean else (spec["m_holdout"] if d >= golive else spec["m_pre"])
                target = min(cap, math.ceil(m * prod_fc))
                eps = srng.gammavariate(alpha, 1 / alpha)
                lam = mu * eps
                row = {"store": s["store_id"], "sku": k["sku_id"], "category": cat, "date": d, "promo": is_promo,
                       "closed": closed, "open_h": oh, "close_h": ch, "mu": mu, "lam": lam, "v3": v3, "v4": v4,
                       "target": target, "slot": s["slot"], "arm": s["arm"], "competitor_active": compf < 1}
                if closed:
                    row.update(demand=0, sales=0, hourly=[], events=[], on_hand_open=on_hand, delivered=0,
                               delivery_time=None, on_hand_close=on_hand)
                    rows.append(row)
                    continue
                # arrivals: cumulative-intensity exponential gaps over the trading hours
                hours = [hh for hh in range(oh, ch)]
                rates = [lam * prof[hh - pstart] for hh in hours]
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
                elif on_hand == 0:
                    pass
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
                if d < golive:
                    pre_arr += len(arrivals)
                    pre_sales += len(sales_times)
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


if __name__ == "__main__":
    import time
    t = time.time()
    w = generate(copy.deepcopy(VISIBLE_SPEC))
    rows = [r for r in w.rows if not r["closed"]]
    dem = sum(r["demand"] for r in rows)
    sal = sum(r["sales"] for r in rows)
    cens = sum(1 for r in rows if r["sales"] < r["demand"] or any(e[1] == "out_of_stock" for e in r["events"]))
    print(f"rows={len(w.rows)} demand={dem} sales={sal} lost_share={1 - sal / dem:.3f} censored_days={cens / len(rows):.3f} in {time.time() - t:.1f}s")
