"""G35 world generator: a randomised-saturation dispatch-priority experiment.

Standard library only, on purpose: the verifier imports this module inside an isolated virtualenv
that contains pytest and nothing else, so it cannot depend on numpy or pandas.

The mechanism, in one sentence: couriers are a fixed pool inside a (city, day) dispatch block and are
rationed in proportion to each merchant's demand times its dispatch weight, so priority handed to one
merchant is priority taken from another, and when every merchant carries the same weight the
allocation is identical to nobody carrying priority.
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

SATURATIONS = (0.0, 0.25, 0.5, 0.75, 1.0)

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 3510774,
    "n_cities": 60,
    "n_days": 28,
    "start_date": "2026-04-06",
    "merchants_per_city": 45,      # upper bound; actual city size is lognormal below this
    "city_size_sigma": 0.55,
    "demand_mu": 2.6,              # mean-log of a merchant's daily order volume
    "demand_sigma": 0.55,
    "capacity_ratio": 0.78,        # courier capacity / expected demand  (< 1 => rationing)
    "cap_city_sigma": 0.06,
    "cap_day_sigma": 0.04,
    "cap_idio_sigma": 0.03,
    "priority_weight": 2.6,        # dispatch weight multiplier while priority is active
    "delta": 0.060,                # genuine routing efficiency of the new dispatcher
    "adoption": 0.80,
    "adopt_size_tilt": 0.55,
    "gate": 0.015,                 # launch iff the full-rollout effect >= +1.5 fulfilment points
}

CITY_PREFIX = ("Ashford", "Brightwater", "Calderon", "Dunmore", "Eastvale", "Fairholm", "Glenmoor",
               "Harborne", "Ivyridge", "Junction", "Kingsley", "Lakemont", "Marlow", "Northgate",
               "Oakhurst", "Pinebrook", "Quarry", "Redstone", "Stonebridge", "Thornwood",
               "Uplands", "Verity", "Westmere", "Yarrow")
CITY_SUFFIX = ("", " North", " South", " East", " West", " Central", " Heights", " Park")


# --------------------------------------------------------------------------- small stdlib samplers
def _poisson(rng, lam):
    if lam > 30:
        return max(0, int(rng.gauss(lam, math.sqrt(lam)) + 0.5))
    el, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= el:
            return k
        k += 1


def _binom(rng, n, p):
    if n <= 0:
        return 0
    if n > 40:
        v = rng.gauss(n * p, math.sqrt(max(n * p * (1 - p), 1e-9)))
        return max(0, min(n, int(v + 0.5)))
    return sum(1 for _ in range(n) if rng.random() < p)


# ------------------------------------------------------------------------------------ the world
def _blocks(sp, rng):
    """Merchant demand and courier capacity per block; identical across every counterfactual."""
    n_cities, n_days, cap_n = sp["n_cities"], sp["n_days"], sp["merchants_per_city"]
    sizes, base = [], []
    for c in range(n_cities):
        k = int(round(cap_n * math.exp(rng.gauss(0, sp["city_size_sigma"]))))
        k = max(8, min(cap_n, k))
        sizes.append(k)
        base.append([math.exp(rng.gauss(sp["demand_mu"], sp["demand_sigma"])) for _ in range(k)])

    f_city = [math.exp(rng.gauss(0, sp["cap_city_sigma"])) for _ in range(n_cities)]
    f_day = [math.exp(rng.gauss(0, sp["cap_day_sigma"])) for _ in range(n_days)]

    blocks = []
    for c in range(n_cities):
        for d in range(n_days):
            dem = [float(max(_poisson(rng, b), 1)) for b in base[c]]
            tot = sum(dem)
            cap = (tot * sp["capacity_ratio"] * f_city[c] * f_day[d]
                   * math.exp(rng.gauss(0, sp["cap_idio_sigma"])))
            blocks.append({"city": c, "day": d, "dem": dem, "cap": cap})
    return blocks, sizes


def _adopt_prob(dem_i, sp, mean_log, sd_log):
    """Adoption rises with merchant size; assignment stays random, so the ITT estimand is intact."""
    z = (math.log(max(dem_i, 1.0)) - mean_log) / (sd_log + 1e-9)
    return min(0.99, max(0.05, sp["adoption"] * (1.0 + sp["adopt_size_tilt"] * z * 0.5)))


def _serve(dem, cap, active, sp):
    """Expected fulfilment rate per merchant under weighted proportional courier rationing.

    `active[i]` is True when merchant i is running the new dispatcher. Returns expected rates; the
    caller adds sampling noise where a realised count is required.
    """
    tot_dem = sum(dem)
    if tot_dem <= 0:
        return [0.0] * len(dem)
    dem_active = sum(d for d, a in zip(dem, active) if a)
    supply = cap * (1.0 + sp["delta"] * (dem_active / tot_dem))

    w = sp["priority_weight"]
    claim = [d * (w if a else 1.0) for d, a in zip(dem, active)]
    served = [0.0] * len(dem)
    live = [d > 0 for d in dem]
    remaining = supply
    for _ in range(4):
        tot_claim = sum(c for c, l in zip(claim, live) if l)
        if tot_claim <= 0 or remaining <= 1e-9:
            break
        spill = 0.0
        for i in range(len(dem)):
            if not live[i]:
                continue
            want = dem[i] - served[i]
            give = min(claim[i] / tot_claim * remaining, want)
            served[i] += give
            spill += give
            if dem[i] - served[i] <= 1e-9:
                live[i] = False
        remaining = max(remaining - spill, 0.0)
        if not any(live):
            break
    return [min(1.0, served[i] / dem[i]) if dem[i] > 0 else 0.0 for i in range(len(dem))]


def build(spec):
    """Run the experiment: randomised saturation per block, complete randomisation within block."""
    sp = dict(spec)
    rng = random.Random(sp["seed"])
    blocks, sizes = _blocks(sp, rng)

    all_dem = [d for b in blocks for d in b["dem"]]
    mean_log = sum(math.log(max(d, 1.0)) for d in all_dem) / len(all_dem)
    var = sum((math.log(max(d, 1.0)) - mean_log) ** 2 for d in all_dem) / len(all_dem)
    sd_log = math.sqrt(var)
    sp["_mean_log"], sp["_sd_log"] = mean_log, sd_log

    arng = random.Random(sp["seed"] + 101)
    for b in blocks:
        n = len(b["dem"])
        pi = arng.choice(SATURATIONS)
        k = int(round(pi * n))
        idx = list(range(n))
        arng.shuffle(idx)
        assigned = [False] * n
        for j in idx[:k]:
            assigned[j] = True
        active = [assigned[i] and arng.random() < _adopt_prob(b["dem"][i], sp, mean_log, sd_log)
                  for i in range(n)]
        rate = _serve(b["dem"], b["cap"], active, sp)
        b["pi"] = pi
        b["assigned"] = assigned
        b["active"] = active
        b["delivered"] = [_binom(arng, int(b["dem"][i]), rate[i]) for i in range(n)]
    return {"spec": sp, "blocks": blocks, "sizes": sizes}


# ------------------------------------------------------------------------------------ latent truth
def truth(world_obj, n_mc=3):
    """Exact population quantities by counterfactual replay on the same demand and capacity draw.

    Expected rates are used rather than sampled counts, so these are population values and carry no
    Monte-Carlo noise beyond the adoption draw, which is averaged over `n_mc` replays.
    """
    sp = world_obj["spec"]
    blocks = world_obj["blocks"]
    ml, sl = sp["_mean_log"], sp["_sd_log"]
    rng = random.Random(sp["seed"] + 5150)

    tot_dem = sum(sum(b["dem"]) for b in blocks)
    acc = {"full": 0.0, "none": 0.0, "half_t": 0.0, "half_c": 0.0,
           "half_tw": 0.0, "half_cw": 0.0, "none_cw": 0.0, "none_c": 0.0}
    for _ in range(n_mc):
        for b in blocks:
            dem, n = b["dem"], len(b["dem"])
            on_full = [rng.random() < _adopt_prob(dem[i], sp, ml, sl) for i in range(n)]
            r_full = _serve(dem, b["cap"], on_full, sp)
            r_none = _serve(dem, b["cap"], [False] * n, sp)
            acc["full"] += sum(r_full[i] * dem[i] for i in range(n))
            acc["none"] += sum(r_none[i] * dem[i] for i in range(n))

            idx = list(range(n))
            rng.shuffle(idx)
            half = [False] * n
            for j in idx[: n // 2]:
                half[j] = True
            on_half = [half[i] and rng.random() < _adopt_prob(dem[i], sp, ml, sl) for i in range(n)]
            r_half = _serve(dem, b["cap"], on_half, sp)
            for i in range(n):
                if half[i]:
                    acc["half_t"] += r_half[i] * dem[i]
                    acc["half_tw"] += dem[i]
                else:
                    acc["half_c"] += r_half[i] * dem[i]
                    acc["half_cw"] += dem[i]
                    acc["none_c"] += r_none[i] * dem[i]
                    acc["none_cw"] += dem[i]

    policy = (acc["full"] - acc["none"]) / (tot_dem * n_mc)
    direct = acc["half_t"] / acc["half_tw"] - acc["half_c"] / acc["half_cw"]
    spill = acc["half_c"] / acc["half_cw"] - acc["none_c"] / acc["none_cw"]
    return {
        "policy_effect_full": policy,
        "direct_effect_50": direct,
        "spillover_50": spill,
        "fulfilment_none": acc["none"] / (tot_dem * n_mc),
        "fulfilment_full": acc["full"] / (tot_dem * n_mc),
        "decision": "launch" if policy >= sp["gate"] else "hold",
    }


# ------------------------------------------------------------------------------------- warehouse
def write_sqlite(world_obj, out_dir):
    sp, blocks = world_obj["spec"], world_obj["blocks"]
    db = os.path.join(out_dir, "warehouse.sqlite")
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    c = con.cursor()
    c.execute("CREATE TABLE merchants (merchant_id TEXT PRIMARY KEY, city_id TEXT, "
              "merchant_name TEXT, cuisine TEXT)")
    c.execute("CREATE TABLE block_assignment (block_id TEXT PRIMARY KEY, city_id TEXT, "
              "service_date TEXT, assigned_saturation REAL, assigned_at TEXT)")
    c.execute("CREATE TABLE merchant_assignment (block_id TEXT, merchant_id TEXT, "
              "assigned_priority INTEGER)")
    c.execute("CREATE TABLE priority_activation (block_id TEXT, merchant_id TEXT, "
              "activated INTEGER)")
    c.execute("CREATE TABLE merchant_day_orders (block_id TEXT, merchant_id TEXT, "
              "orders_requested INTEGER, orders_delivered INTEGER)")
    c.execute("CREATE TABLE extract_meta (key TEXT, value TEXT)")

    p = random.Random(sp["seed"] + 991)
    start = date.fromisoformat(sp["start_date"])
    names = []
    for i in range(sp["n_cities"]):
        names.append("%s%s" % (CITY_PREFIX[i % len(CITY_PREFIX)],
                               CITY_SUFFIX[(i // len(CITY_PREFIX)) % len(CITY_SUFFIX)]))
    city_ids = ["CTY-%04d" % (7000 + i) for i in range(sp["n_cities"])]
    p.shuffle(city_ids)

    merch_ids = {}
    merch_rows = []
    for ci, k in enumerate(world_obj["sizes"]):
        for j in range(k):
            mid = "MER-%06d" % (100000 + ci * 1000 + j)
            merch_ids[(ci, j)] = mid
            merch_rows.append((mid, city_ids[ci], "%s Kitchen %d" % (names[ci], j + 1),
                               p.choice(("pizza", "burgers", "sushi", "thai", "bakery", "grill"))))

    ba, ma, pa, mdo = [], [], [], []
    for b in blocks:
        bid = "BLK-%s-%s" % (city_ids[b["city"]][4:], (start + timedelta(days=b["day"])).isoformat())
        sd = (start + timedelta(days=b["day"])).isoformat()
        ba.append((bid, city_ids[b["city"]], sd, b["pi"], sd + "T04:00:00Z"))
        for i in range(len(b["dem"])):
            mid = merch_ids[(b["city"], i)]
            ma.append((bid, mid, 1 if b["assigned"][i] else 0))
            if b["assigned"][i]:
                pa.append((bid, mid, 1 if b["active"][i] else 0))
            mdo.append((bid, mid, int(b["dem"][i]), int(b["delivered"][i])))

    p.shuffle(merch_rows); p.shuffle(ba); p.shuffle(ma); p.shuffle(pa); p.shuffle(mdo)
    c.executemany("INSERT INTO merchants VALUES (?,?,?,?)", merch_rows)
    c.executemany("INSERT INTO block_assignment VALUES (?,?,?,?,?)", ba)
    c.executemany("INSERT INTO merchant_assignment VALUES (?,?,?)", ma)
    c.executemany("INSERT INTO priority_activation VALUES (?,?,?)", pa)
    c.executemany("INSERT INTO merchant_day_orders VALUES (?,?,?,?)", mdo)
    c.executemany("INSERT INTO extract_meta VALUES (?,?)", [
        ("experiment_name", "priority-dispatch-pilot"),
        ("dispatch_pool", "city and service date"),
        ("randomisation", "two stage: saturation per dispatch pool, then merchants within pool"),
        ("window_start", start.isoformat()),
        ("window_end", (start + timedelta(days=sp["n_days"] - 1)).isoformat()),
        ("outcome", "orders_delivered / orders_requested"),
    ])
    con.commit()
    con.close()
    return db


def db_digest(db_path):
    con = sqlite3.connect(db_path)
    h = hashlib.sha256()
    for t in ("merchants", "block_assignment", "merchant_assignment", "priority_activation",
              "merchant_day_orders", "extract_meta"):
        for row in con.execute("SELECT * FROM %s ORDER BY 1,2" % t):
            h.update(repr(row).encode())
    con.close()
    return h.hexdigest()[:16]


def main(argv):
    out = argv[1]
    data = os.path.join(out, "data")
    os.makedirs(data, exist_ok=True)
    w = build(VISIBLE_SPEC)
    db = write_sqlite(w, data)
    sys.stderr.write("wrote %s digest=%s\n" % (db, db_digest(db)))


if __name__ == "__main__":
    main(sys.argv)
