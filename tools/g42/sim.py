"""G42 pre-build screen: comparable-store sales for a covenant test (research only, no model calls).

Generates whole retail estates, computes the covenant object exactly, and measures every labelled
wrong object against it. Gate (pre-registered in research/g42/concept.md):
  1. the covenant decision must not be constant across worlds;
  2. each wrong object must move the reported growth by more than the reporting precision (0.0001)
     in at least 3 of 4 sampled worlds, and flip the covenant decision in at least one world.

    python tools/g42/sim.py [n_worlds]
"""
from __future__ import annotations

import hashlib
import random
import sys
from datetime import date, timedelta

WEEKS = 13                      # a fiscal quarter
PEAK_WEEK = 8                   # the trading peak sits inside the quarter
FLOOR = -0.015                  # covenant: cash sweep if comp growth < -1.5 %
N_STORES = 140
REGIONS, DISTRICTS = 4, 16


def rng(seed, tag):
    return random.Random(int(hashlib.sha256(f"{seed}:{tag}".encode()).hexdigest()[:16], 16))


def build(seed):
    """A retail estate with a 52/53-week calendar, plus this quarter and the prior-year quarter."""
    d = rng(seed, "design")
    fy_start = date(2025, 2, 2)                     # prior-year fiscal year start (Sunday)
    prior_start = fy_start + timedelta(weeks=26)
    cur_start = prior_start + timedelta(weeks=52 + (1 if d.random() < 0.3 else 0))   # 53-week year
    prior = (prior_start, prior_start + timedelta(weeks=WEEKS) - timedelta(days=1))
    cur = (cur_start, cur_start + timedelta(weeks=WEEKS) - timedelta(days=1))

    chain_trend = d.choice([-0.055, -0.03, -0.012, 0.004, 0.02])
    stores = []
    for i in range(N_STORES):
        opened = fy_start - timedelta(days=d.randint(200, 3000)) if d.random() < 0.85 \
            else prior_start + timedelta(days=d.randint(-20, 200))
        closed = None
        if d.random() < 0.06:
            closed = cur_start + timedelta(days=d.randint(-120, 80))
        stores.append({"id": f"S{1000+i}", "district": f"D{i % DISTRICTS:02d}", "region": f"R{i % REGIONS}",
                       "opened": opened, "closed": closed, "base": d.lognormvariate(9.6, 0.95),
                       "trend": d.gauss(chain_trend, 0.045), "ownership": "OWNED",
                       "relocated_from": None, "converted_on": None, "remodel": None, "dark": False})
    # relocations: a successor store inherits one predecessor's trading history
    for s in d.sample(stores, 6):
        succ = dict(s)
        succ["id"] = s["id"] + "R"
        succ["relocated_from"] = s["id"]
        succ["opened"] = cur_start - timedelta(days=d.randint(10, 300))
        s["closed"] = succ["opened"] - timedelta(days=1)
        succ["closed"] = None
        stores.append(succ)
    for s in d.sample([x for x in stores if x["relocated_from"] is None], 10):
        st = cur_start + timedelta(days=d.randint(-40, 60))
        s["remodel"] = (st, st + timedelta(days=d.randint(8, 30)))          # closed >= 7 days
    for s in d.sample([x for x in stores if x["relocated_from"] is None], 5):
        s["converted_on"] = cur_start + timedelta(days=d.randint(-30, 50))
    for s in d.sample(stores, 3):
        s["dark"] = True
    return {"seed": seed, "stores": stores, "prior": prior, "cur": cur, "cur_start": cur_start,
            "prior_start": prior_start}


def sales(w, s, period, channel_split=True):
    """Net sales for one store over one period, by channel."""
    d = rng(f"{w['seed']}:{s['id']}", period[0].isoformat())
    lo, hi = period
    out = {"IN_STORE": 0.0, "ONLINE_FULFILLED": 0.0, "WHOLESALE": 0.0}
    day = lo
    years = (lo - w["prior_start"]).days / 365.0
    while day <= hi:
        trading = s["opened"] <= day and (s["closed"] is None or day <= s["closed"])
        if s["remodel"] and s["remodel"][0] <= day <= s["remodel"][1]:
            trading = False
        if s["converted_on"] and day >= s["converted_on"]:
            trading = False                                  # franchise: no longer our sales
        if trading:
            wk = ((day - w["prior_start"]).days // 7) % 52
            season = 1.0 + 1.6 * max(0.0, 1.0 - abs(wk - PEAK_WEEK) / 2.0)
            base = s["base"] / 7.0 * (1 + s["trend"]) ** years * season * d.uniform(0.82, 1.18)
            out["IN_STORE"] += base
            if s["dark"]:
                out["ONLINE_FULFILLED"] += base * d.uniform(0.35, 0.9)
            elif d.random() < 0.5:
                out["ONLINE_FULFILLED"] += base * d.uniform(0.02, 0.08)
            if d.random() < 0.15:
                out["WHOLESALE"] += base * d.uniform(0.1, 0.6)
        day += timedelta(days=1)
    return out


def traded_whole(w, s, period, chain):
    """Did this trading identity trade for the whole period (following a relocation chain)?"""
    lo, hi = period
    ids = [s]
    src = s["relocated_from"]
    while src and src in chain:
        p = chain[src]
        ids.append(p)
        src = p["relocated_from"]
    day = lo
    while day <= hi:
        if not any(x["opened"] <= day and (x["closed"] is None or day <= x["closed"]) for x in ids):
            return False
        day += timedelta(days=7)
    return True


def basket(w, *, follow_relocation=True, end_only=False, include_remodel=False,
           include_converted=False, prior_only=False):
    chain = {s["id"]: s for s in w["stores"]}
    out = []
    for s in w["stores"]:
        if s["relocated_from"] and not follow_relocation:
            pass                                             # treated as a brand new store: excluded below
        if not include_remodel and s["remodel"]:
            continue
        if not include_converted and s["converted_on"]:
            continue
        ok_cur = traded_whole(w, s, w["cur"], chain if follow_relocation else {})
        ok_prior = traded_whole(w, s, w["prior"], chain if follow_relocation else {})
        if end_only:
            ok = s["opened"] <= w["cur"][1] and (s["closed"] is None or s["closed"] >= w["cur"][1])
        elif prior_only:
            ok = ok_prior
        else:
            ok = ok_cur and ok_prior
        if ok:
            out.append(s)
    return out


def comp_sales(w, s, period, *, include_wholesale=False, include_dark=False, follow_relocation=True):
    chain = {x["id"]: x for x in w["stores"]}
    parts = [s]
    src = s["relocated_from"]
    while src and follow_relocation:
        p = chain[src]
        parts.append(p)
        src = p["relocated_from"]
    tot = 0.0
    for x in parts:
        v = sales(w, x, period)
        tot += v["IN_STORE"]
        if include_wholesale:
            tot += v["WHOLESALE"]
        if include_dark or not x["dark"]:
            tot += v["ONLINE_FULFILLED"] if (include_dark or not x["dark"]) else 0.0
    return tot


def growth(cur, prior):
    return (cur - prior) / prior if prior else 0.0


def truth(w):
    b = basket(w)
    c = sum(comp_sales(w, s, w["cur"]) for s in b)
    p = sum(comp_sales(w, s, w["prior"]) for s in b)
    g = growth(c, p)
    return {"growth": round(g, 6), "n_basket": len(b), "decision": "cash_sweep" if g < FLOOR else "no_sweep"}


def wrongs(w):
    out = {}
    all_s = w["stores"]

    def agg(b, **kw):
        c = sum(comp_sales(w, s, kw.pop("cur_period", w["cur"]), **kw) for s in b)
        p = sum(comp_sales(w, s, kw.get("prior_period", w["prior"]), **kw) for s in b)
        return growth(c, p)

    out["W01_total_chain_growth"] = growth(
        sum(comp_sales(w, s, w["cur"], include_wholesale=True, include_dark=True) for s in all_s),
        sum(comp_sales(w, s, w["prior"], include_wholesale=True, include_dark=True) for s in all_s))
    out["W02_basket_open_at_period_end"] = agg(basket(w, end_only=True))
    # date-aligned prior period: 364 days back regardless of the 53-week year
    dp = (w["cur"][0] - timedelta(days=365), w["cur"][1] - timedelta(days=365))
    b = basket(w)
    out["W03_date_aligned_prior"] = growth(sum(comp_sales(w, s, w["cur"]) for s in b),
                                           sum(comp_sales(w, s, dp) for s in b))
    out["W04_remodels_included"] = agg(basket(w, include_remodel=True))
    out["W05_relocation_as_close_and_open"] = agg(basket(w, follow_relocation=False), follow_relocation=False)
    out["W06_franchise_conversions_included"] = agg(basket(w, include_converted=True))
    out["W07_wholesale_included"] = agg(b, include_wholesale=True)
    out["W08_dark_store_fulfilment_included"] = agg(b, include_dark=True)
    gs = [growth(comp_sales(w, s, w["cur"]), comp_sales(w, s, w["prior"])) for s in b
          if comp_sales(w, s, w["prior"]) > 0]
    out["W09_mean_of_store_growth_rates"] = sum(gs) / len(gs) if gs else 0.0
    out["W11_basket_from_prior_period_only"] = agg(basket(w, prior_only=True))
    return {k: round(v, 6) for k, v in out.items()}


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    seeds = [11_000_003 + 7919 * i for i in range(n)]
    rows = []
    for s in seeds:
        w = build(s)
        t = truth(w)
        rows.append((s, t, wrongs(w)))
        print(f"seed {s}: basket {t['n_basket']:3d}  growth {t['growth']:+.4f}  {t['decision']}")
    names = sorted(rows[0][2])
    print()
    print(f"{'wrong object':42s} " + "".join(f"{i:>10d}" for i in range(len(rows))) + "   sep  flips")
    for nm in names:
        seps = flips = 0
        cells = []
        for _, t, wr in rows:
            d = wr[nm] - t["growth"]
            if abs(d) > 1e-4:
                seps += 1
            if ("cash_sweep" if wr[nm] < FLOOR else "no_sweep") != t["decision"]:
                flips += 1
            cells.append(f"{d:+10.4f}")
        print(f"{nm:42s} " + "".join(cells) + f"  {seps:>4d}  {flips:>4d}")
    dec = {t["decision"] for _, t, _ in rows}
    print(f"\ndecisions across worlds: {sorted(dec)}  ({'VARIES' if len(dec) > 1 else 'CONSTANT - FAILS GATE 1'})")


if __name__ == "__main__":
    main()
