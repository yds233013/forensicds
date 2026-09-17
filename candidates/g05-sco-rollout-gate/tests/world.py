"""Deterministic generator for the SCO 2.0 rollout warehouse (stdlib only).

usage: python world.py OUT_DIR [SPEC_NAME]      writes OUT_DIR/data/warehouse.sqlite

The same module is used by the verifier to generate hidden warehouses and exact truth. Design draws (stores, layout,
waves, slips, closures, effect multipliers) and outcome noise use separate random streams, so the noise can be redrawn
with the design held fixed.
"""
from __future__ import annotations

import copy
import hashlib
import math
import os
import random
import sqlite3
import sys
from datetime import date, timedelta

FORMATS = ("Supercentre", "Market", "Neighbourhood")
KITS = ("full", "compact")
REGIONS = ("North", "Coast", "Valley", "Metro", "Lakes", "Uplands")
CLOSURE_TYPES = ("weather", "refrigeration", "power", "flooring")

VISIBLE_SPEC = {
    "name": "visible",
    "seed": 20240517,
    "noise_seed": None,                 # None: derived from seed
    "start": "2023-09-04",              # Monday
    "T": 156,
    "n_stores": 900,
    "format_share": (0.20, 0.35, 0.45),
    "sqft_range": {"Supercentre": (60, 110), "Market": (25, 50), "Neighbourhood": (10, 30)},
    "full_kit_prob": {"Supercentre": 1.00, "Market": 0.75, "Neighbourhood": 0.25},
    "wave_probs": {"Supercentre|full": (0.33, 0.22, 0.15, 0.10, 0.20),
                   "Market|full": (0.20, 0.25, 0.20, 0.15, 0.20),
                   "Market|compact": (0.05, 0.10, 0.15, 0.25, 0.45),
                   "Neighbourhood|full": (0.10, 0.15, 0.20, 0.20, 0.35),
                   "Neighbourhood|compact": (0.02, 0.04, 0.08, 0.16, 0.70)},
    "planned_week": (76, 86, 96, 106),
    "remaining_weeks": (170, 182),      # planned go-live of waves 5 and 6 (after the extract)
    "slip_rate": 0.20, "slip_max": 4,
    "trend_per_year": {"Supercentre": 0.060, "Market": 0.010, "Neighbourhood": -0.010},
    "season_amp": 0.06,
    "basket_effect": {"full": 0.070, "compact": 0.012},
    "txn_effect": {"full": -0.020, "compact": -0.015},
    "effect_sd": 0.25,
    "ramp_scale": 10.0,
    "sd_txn": 0.014, "sd_basket": 0.010, "ar": 0.5,
    "install_week_probs": (0.70, 0.20, 0.10),
    "install_hours": (14, 28),
    "other_closure_rate": 0.03, "other_hours": (7, 28),
    "trading_hours_day": 14.0,
    "gate": 0.025,
    "rr_window": (12, 25),
    "pharmacy_share": {"Supercentre": 1.0, "Market": 0.6, "Neighbourhood": 0.0},
}


def _rng(seed, tag):
    h = hashlib.sha256(f"{seed}|{tag}".encode()).digest()
    return random.Random(int.from_bytes(h[:8], "big"))


def week_start(spec, t):
    return date.fromisoformat(spec["start"]) + timedelta(days=7 * t)


def _choice(r, probs):
    u, acc = r.random(), 0.0
    for i, p in enumerate(probs):
        acc += p
        if u < acc:
            return i
    return len(probs) - 1


def build_world(spec):
    """Return the full world (design, potential outcomes, observed tables) as plain Python structures."""
    spec = copy.deepcopy(spec)
    seed = spec["seed"]
    nseed = spec["noise_seed"] if spec["noise_seed"] is not None else seed + 1
    rd = _rng(seed, "design")
    T = spec["T"]
    stores = []
    for i in range(spec["n_stores"]):
        f = FORMATS[_choice(rd, spec["format_share"])]
        lo, hi = spec["sqft_range"][f]
        sqft = round(rd.uniform(lo, hi) * 1000, -2)
        kit = "full" if rd.random() < spec["full_kit_prob"][f] else "compact"
        wave = _choice(rd, spec["wave_probs"][f"{f}|{kit}"]) + 1          # 1..4 installed, 5 remaining
        region = REGIONS[rd.randrange(len(REGIONS))]
        if wave <= 4:
            planned = spec["planned_week"][wave - 1]
            slip = rd.randint(1, spec["slip_max"]) if rd.random() < spec["slip_rate"] else 0
            G = planned + slip
        else:
            wave = 5 if rd.random() < 0.5 else 6
            planned = spec["remaining_weeks"][wave - 5]
            slip, G = 0, None
        m = math.exp(rd.gauss(-spec["effect_sd"] ** 2 / 2, spec["effect_sd"]))
        opened = date(1998, 1, 1) + timedelta(days=rd.randrange(9000))
        u = rd.random()
        p1, p2, _ = spec["install_week_probs"]
        install_weeks = [] if G is None else ([G - 1] if u < p1 else ([G - 2] if u < p1 + p2 else [G - 2, G - 1]))
        pharmacy = rd.random() < spec["pharmacy_share"][f]
        stores.append(dict(store_id=f"S{i + 1:04d}", format=f, region=region, sqft=sqft, kit=kit, wave=wave,
                           planned=planned, slip=slip, G=G, m=m, opened_on=opened.isoformat(),
                           install_weeks=install_weeks, pharmacy=pharmacy,
                           bay_survey_day=rd.randrange(20)))

    # closures (design stream): per store-week list of (weekday, hours, type)
    closures = {}
    for s in stores:
        for w in s["install_weeks"]:
            total = rd.uniform(*spec["install_hours"])
            days = [total] if total <= spec["trading_hours_day"] else [spec["trading_hours_day"], total - spec["trading_hours_day"]]
            d0 = rd.choice((1, 2))            # Tuesday or Wednesday start
            closures.setdefault((s["store_id"], w), []).extend(
                (d0 + j, max(0.5, round(h, 1)), "install") for j, h in enumerate(days))
        for t in range(T):
            if rd.random() < spec["other_closure_rate"]:
                total = rd.uniform(*spec["other_hours"])
                ctype = CLOSURE_TYPES[rd.randrange(len(CLOSURE_TYPES))]
                days = []
                while total > 1e-9:
                    h = min(total, spec["trading_hours_day"])
                    days.append(h)
                    total -= h
                d0 = rd.randrange(0, 7 - len(days) + 1)
                closures.setdefault((s["store_id"], t), []).extend(
                    (d0 + j, max(0.5, round(h, 1)), ctype) for j, h in enumerate(days))

    # outcomes (noise stream)
    rn = _rng(nseed, "noise")
    trows, truth_rows = [], []
    for s in stores:
        f, k = s["format"], s["kit"]
        a_n = math.log((9000, 5000, 2600)[FORMATS.index(f)] * math.exp(rn.gauss(0, 0.15)))
        a_b = math.log((48, 38, 22)[FORMATS.index(f)] * math.exp(rn.gauss(0, 0.08)))
        a_p = math.log((52000, 30000, 1)[FORMATS.index(f)] * math.exp(rn.gauss(0, 0.20)))
        sco0 = min(0.45, max(0.05, rn.gauss(0.24, 0.05)))
        phi = spec["ar"]
        en = rn.gauss(0, spec["sd_txn"]); eb = rn.gauss(0, spec["sd_basket"]); ep = rn.gauss(0, 0.03)
        for t in range(T):
            if t:
                en = phi * en + rn.gauss(0, spec["sd_txn"] * math.sqrt(1 - phi ** 2))
                eb = phi * eb + rn.gauss(0, spec["sd_basket"] * math.sqrt(1 - phi ** 2))
                ep = phi * ep + rn.gauss(0, 0.03 * math.sqrt(1 - phi ** 2))
            trend = spec["trend_per_year"][f] * t / 52.0
            season = spec["season_amp"] * math.sin(2 * math.pi * t / 52.0) + (0.03 if t % 52 in (15, 16) else 0.0)
            cl = closures.get((s["store_id"], t), [])
            hours = sum(h for _, h, _ in cl)
            open_frac = 1 - hours / (7 * spec["trading_hours_day"])
            e = None if s["G"] is None else t - s["G"]
            ramp = 0.0 if e is None or e < 0 else 1 - math.exp(-(e + 1) / spec["ramp_scale"])
            tau_b = spec["basket_effect"][k] * s["m"] * ramp
            tau_n = spec["txn_effect"][k] * s["m"] * ramp
            y_n = a_n + trend + season + math.log(open_frac) + en + tau_n
            y_b = a_b + 0.5 * trend + 0.3 * season + (-0.02 if hours > 0 else 0.0) + eb + tau_b
            txns = max(1, int(round(math.exp(y_n))))
            net_sales = round(math.exp(y_n + y_b), 2)
            sco = sco0 + rn.gauss(0, 0.012) + (0.0 if ramp == 0 else (0.22 if k == "full" else 0.14) * min(1.0, 0.6 + ramp))
            pharm = round(math.exp(a_p + trend + 0.5 * season + math.log(open_frac) + ep), 2) if s["pharmacy"] else None
            trows.append((s["store_id"], week_start(spec, t).isoformat(), net_sales, txns, round(min(0.95, sco), 4),
                          pharm))
            truth_rows.append((s["store_id"], t, tau_b + tau_n, hours == 0))
    return dict(spec=spec, stores=stores, closures=closures, kpi=trows, tau=truth_rows)


def write_warehouse(world, path):
    spec = world["spec"]
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    c = con.cursor()
    c.executescript("""
    CREATE TABLE stores (store_id TEXT PRIMARY KEY, format TEXT, region TEXT, sqft INTEGER, opened_on TEXT);
    CREATE TABLE layout_survey (store_id TEXT, surveyed_on TEXT, rear_bagging_bay INTEGER, surveyor_note TEXT);
    CREATE TABLE rollout_plan (store_id TEXT, wave INTEGER, planned_go_live TEXT, planned_kit TEXT, plan_version TEXT);
    CREATE TABLE install_log (work_order TEXT, store_id TEXT, event TEXT, event_date TEXT, kit TEXT);
    CREATE TABLE store_closures (store_id TEXT, closure_date TEXT, closure_type TEXT, hours_closed REAL);
    CREATE TABLE kpi_store_week (store_id TEXT, week_start TEXT, net_sales REAL, customer_txns INTEGER,
                                 sco_txn_share REAL, pharmacy_sales REAL);
    """)
    for s in world["stores"]:
        c.execute("INSERT INTO stores VALUES (?,?,?,?,?)", (s["store_id"], s["format"], s["region"], int(s["sqft"]),
                                                             s["opened_on"]))
        bay = 1 if s["kit"] == "full" else 0
        note = ("bay usable for bagging lane" if bay else
                ("no rear bay" if s["format"] != "Supercentre" else "bay blocked"))
        c.execute("INSERT INTO layout_survey VALUES (?,?,?,?)",
                  (s["store_id"], (date(2024, 6, 3) + timedelta(days=s["bay_survey_day"])).isoformat(), bay, note))
        c.execute("INSERT INTO rollout_plan VALUES (?,?,?,?,?)",
                  (s["store_id"], s["wave"], week_start(spec, s["planned"]).isoformat(), s["kit"], "2024-11"))
    wo = 0
    for s in sorted(world["stores"], key=lambda s: (s["G"] or 10 ** 9, s["store_id"])):
        if s["G"] is None:
            continue
        wo += 1
        g = week_start(spec, s["G"])
        inst = sorted(d for (sid, w), cl in world["closures"].items() if sid == s["store_id"] and w in s["install_weeks"]
                      for d in [week_start(spec, w) + timedelta(days=cl[0][0])])
        prewire = week_start(spec, s["G"] - 3) + timedelta(days=3)
        for ev, d in (("prewire", prewire), ("install", inst[0]), ("go_live", g)):
            c.execute("INSERT INTO install_log VALUES (?,?,?,?,?)", (f"WO-{24000 + wo}", s["store_id"], ev,
                                                                     d.isoformat(), s["kit"]))
    for (sid, t), cl in sorted(world["closures"].items()):
        for day, h, ctype in cl:
            c.execute("INSERT INTO store_closures VALUES (?,?,?,?)",
                      (sid, (week_start(spec, t) + timedelta(days=day)).isoformat(), ctype, h))
    c.executemany("INSERT INTO kpi_store_week VALUES (?,?,?,?,?,?)", world["kpi"])
    con.commit()
    c.execute("VACUUM")
    con.close()


def truth(world):
    """Exact estimands from potential outcomes (log net sales, run-rate window, comparable weeks, store-weighted)."""
    spec = world["spec"]
    lo, hi = spec["rr_window"]
    by_store = {s["store_id"]: s for s in world["stores"]}
    acc = {}
    for sid, t, tau, comparable in world["tau"]:
        s = by_store[sid]
        if s["G"] is None or not comparable:
            continue
        if lo <= t - s["G"] <= hi:
            a = acc.setdefault(sid, [0.0, 0])
            a[0] += tau
            a[1] += 1
    theta = {sid: v[0] / v[1] for sid, v in acc.items() if v[1] > 0}
    def mean(xs):
        xs = list(xs)
        return sum(xs) / len(xs)
    waves = {str(w): mean(theta[s["store_id"]] for s in world["stores"] if s["wave"] == w and s["store_id"] in theta)
             for w in (1, 2, 3, 4)}
    kits = {k: mean(theta[s["store_id"]] for s in world["stores"] if s["kit"] == k and s["store_id"] in theta)
            for k in KITS}
    rem = [s for s in world["stores"] if s["G"] is None]
    pi_full = sum(s["kit"] == "full" for s in rem) / len(rem)
    gate = pi_full * kits["full"] + (1 - pi_full) * kits["compact"]
    return {"effect_by_wave": waves, "effect_by_kit": kits,
            "pooled_installed": mean(theta.values()), "gate_effect": gate,
            "decision": "continue" if gate >= spec["gate"] else "stop",
            "n_installed": len(theta), "n_remaining": len(rem), "remaining_full_share": pi_full}


def db_digest(path):
    """Content digest of the warehouse (tables in fixed order, rows sorted)."""
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    h = hashlib.sha256()
    try:
        for table in ("stores", "layout_survey", "rollout_plan", "install_log", "store_closures", "kpi_store_week"):
            cols = [r[1] for r in con.execute(f"PRAGMA table_info({table})")]
            h.update(f"{table}|{cols}".encode())
            for row in con.execute(f"SELECT * FROM {table} ORDER BY {', '.join(cols)}"):
                h.update(repr(row).encode())
            names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view','index','trigger')")}
        h.update(repr(sorted(names)).encode())
    finally:
        con.close()
    return h.hexdigest()


def expected_panel(world):
    """Exact analysis_panel rows keyed by (store_id, week_start)."""
    spec = world["spec"]
    T = spec["T"]
    out = {}
    for i, (sid, wk, sales, txns, sco, ph) in enumerate(world["kpi"]):
        s = world["stores"][i // T]
        t = i % T
        cl = world["closures"].get((sid, t))
        live = s["G"] is not None
        out[(sid, wk)] = (s["wave"], week_start(spec, s["G"]).isoformat() if live else "",
                          (t - s["G"]) if live else None, 0 if cl else 1, math.log(sales))
    return out


def main(out_dir, name="visible"):
    spec = VISIBLE_SPEC
    if name != "visible":
        from scenarios import HIDDEN_SPECS
        spec = next(s for s in HIDDEN_SPECS if s["name"] == name)
    w = build_world(spec)
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)
    write_warehouse(w, os.path.join(out_dir, "data", "warehouse.sqlite"))
    return w


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "visible")
