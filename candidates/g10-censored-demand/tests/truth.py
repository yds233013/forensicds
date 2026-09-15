"""Generator truth for the G10 verifier (standard library). All graded aggregates use realised demand."""
from __future__ import annotations

from collections import defaultdict

import world


def expected(w) -> dict:
    rows = [r for r in w.rows if not r["closed"]]
    golive = w.golive
    keys = {}
    meta = {}
    cat_of = {}
    full = set()
    totals = defaultdict(float)
    lost = defaultdict(float)
    dem_pa = defaultdict(float)
    series = defaultdict(lambda: [0.0, 0])      # (cat, period, store, sku) -> [sum D non-promo, n]
    bias = {"v3_pre_all_stores": [0.0, 0.0], "v4_post_lean26": [0.0, 0.0]}
    for r in rows:
        k = (r["store"], r["sku"], r["date"].isoformat())
        keys[k] = r["sales"]
        cat_of[r["sku"]] = r["category"]
        if world.full_in_stock(r):
            full.add(k)
        post = "post" if r["date"] >= golive else "pre"
        arm = r["arm"]
        promo = "promo" if r["promo"] else "nonpromo"
        meta[k] = (post, arm, promo)
        D, S = r["demand"], r["sales"]
        totals[(post, arm, promo)] += D
        lost[(post, arm)] += D - S
        lost[(post, promo)] += D - S
        dem_pa[(post, arm)] += D
        if not r["promo"]:
            acc = series[(r["category"], post, r["store"], r["sku"])]
            acc[0] += D
            acc[1] += 1
        if post == "pre":
            bias["v3_pre_all_stores"][0] += round(r["v3"], 3) - D
            bias["v3_pre_all_stores"][1] += D
        elif arm == "lean26":
            bias["v4_post_lean26"][0] += round(r["v4"], 3) - D
            bias["v4_post_lean26"][1] += D
    base = defaultdict(float)
    for (cat, post, _s, _k), (sm, n) in series.items():
        base[(cat, post)] += sm / n
    cats = sorted({r["category"] for r in rows})
    change = {c: 100 * (base[(c, "post")] / base[(c, "pre")] - 1) for c in cats}
    return {
        "keys": keys, "meta": meta, "cat_of": cat_of, "full_in_stock": full, "totals": dict(totals), "lost": dict(lost),
        "lost_share": {(p, a): lost[(p, a)] / dem_pa[(p, a)] for (p, a) in dem_pa},
        "category_change": change, "bias": {k: 100 * v[0] / v[1] for k, v in bias.items()},
        "go_live_date": golive.isoformat(),
    }
