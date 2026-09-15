"""Parameterised demand review for the G10 mutation suite (dev tool, never shipped to agents).

Reads only data/warehouse.sqlite. With VARIANT = {} it is a correct, independently written review (numpy NB likelihood
with traffic-weighted exposure offset and per-day posterior). VARIANT["method"] switches to a natural wrong estimator.
The mutation suite copies this file over `demandsci/cli.py` with VARIANT set.
"""
from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
from scipy.special import digamma, gammaln

VARIANT: dict = {}

CFG = {
    "method": "nb",          # nb | em | nb_common_alpha | nb_4week | sales | drop_censored | per_day_scale |
                             # uniform_time_scale | mean_rate_impute | poisson_offset | daily_censored_poisson |
                             # forecast_impute | profile_all_days | nb_no_promo | holdout_transfer |
                             # forecast_prior | v3_prior  (forecast as the day's prior mean + NB posterior, no model) |
                             # nb_plugin (NB rate x missing exposure, no posterior) | fe_profile (fixed-effects traffic
                             # profile) | nb_lognormal (Poisson-lognormal day shock; probe)
    "hardcoded_actions": None,
    "hardcoded_go_live": None,
    "hardcoded_holdout": None,
    "hardcoded_alpha": None,
    "hardcoded_profile": None,   # 3 x 24 traffic shares (weekday, saturday, sunday)
    "groups_kind": None,         # alternative correct covariate structures (see groups)
}


def load(db: Path) -> dict:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    q = lambda s: con.execute(s).fetchall()  # noqa: E731
    cal = {(s, d): (int(o[:2]), int(c[:2])) for s, d, st, o, c in q("SELECT * FROM store_calendar") if st == "open"}
    cat = dict(q("SELECT sku_id, category FROM skus"))
    arms = {s: a for s, _p, a, _g, _b in q("SELECT * FROM programme_assignment")}
    go_live = q("SELECT MIN(go_live_date) FROM programme_assignment")[0][0]
    inv = q("SELECT store_id, sku_id, date, on_hand_open FROM inventory_daily ORDER BY store_id, sku_id, date")
    idx = {}
    rows = []
    for s, k, d, oh in inv:
        if (s, d) not in cal:
            continue
        idx[(s, k, d)] = len(rows)
        rows.append((s, k, d, oh))
    n = len(rows)
    stores = sorted({r[0] for r in rows})
    skus = sorted({r[1] for r in rows})
    cats = sorted(set(cat.values()))
    si, ki, ci = ({v: i for i, v in enumerate(x)} for x in (stores, skus, cats))
    d0 = min(date.fromisoformat(r[2]) for r in rows)
    A = {k: np.zeros(n, int) for k in ("store", "sku", "cat", "week", "dow", "dt", "promo", "post", "lean")}
    open_h = np.zeros(n, int)
    close_h = np.zeros(n, int)
    on_hand = np.zeros(n)
    promo_days = set()
    for sku, a, b in q("SELECT sku_id, start_date, end_date FROM promotions"):
        da, db_ = date.fromisoformat(a), date.fromisoformat(b)
        for i in range((db_ - da).days + 1):
            promo_days.add((sku, date.fromordinal(da.toordinal() + i).isoformat()))
    for i, (s, k, d, oh) in enumerate(rows):
        dd = date.fromisoformat(d)
        A["store"][i], A["sku"][i], A["cat"][i] = si[s], ki[k], ci[cat[k]]
        A["week"][i] = (dd - d0).days // 7
        A["dow"][i] = dd.weekday()
        A["dt"][i] = 2 if dd.weekday() == 6 else 1 if dd.weekday() == 5 else 0
        A["promo"][i] = (k, d) in promo_days
        A["post"][i] = d >= (CFG["hardcoded_go_live"] or go_live)
        hold = CFG["hardcoded_holdout"]
        A["lean"][i] = (arms[s] == "lean26") if hold is None else (s not in hold)
        open_h[i], close_h[i] = cal[(s, d)]
        on_hand[i] = oh
    hourly = np.zeros((n, 24))
    for s, k, d, h, u in q("SELECT store_id, sku_id, date, hour, units FROM sales_hourly"):
        j = idx.get((s, k, d))
        if j is not None:
            hourly[j, h] += u
    trading = np.zeros((n, 24))
    for i in range(n):
        trading[i, open_h[i]:close_h[i]] = 1.0
    # in-stock fraction per clock hour from the opening state and the day's events
    ev = defaultdict(list)
    for s, k, t, e in q("SELECT store_id, sku_id, event_time, event_type FROM availability_events"):
        d, hms = t.split(" ")
        hh, mm, ss = (int(x) for x in hms.split(":"))
        ev[(s, k, d)].append((hh + mm / 60 + ss / 3600, e))
    instock = np.zeros((n, 24))
    for i, (s, k, d, oh) in enumerate(rows):
        state = oh > 0
        t0 = open_h[i]
        ivs = []
        for t, e in sorted(ev.get((s, k, d), [])):
            if t < open_h[i]:
                state = e == "back_in_stock"
                continue
            if t >= close_h[i]:
                break
            if e == "out_of_stock" and state:
                ivs.append((t0, t))
                state = False
            elif e == "back_in_stock" and not state:
                t0, state = t, True
        if state:
            ivs.append((t0, close_h[i]))
        for a, b in ivs:
            h = int(a)
            while h < b and h < 24:
                lo, hi = max(a, h), min(b, h + 1)
                if hi > lo:
                    instock[i, h] += hi - lo
                h += 1
    fc = defaultdict(dict)
    for m, s, k, d, f in q("SELECT * FROM forecasts"):
        j = idx.get((s, k, d))
        if j is not None:
            fc[m][j] = f
    v3 = np.array([fc["v3"].get(i, np.nan) for i in range(n)])
    v4 = np.array([fc["v4"].get(i, np.nan) for i in range(n)])
    prod = np.zeros(n)
    for s, k, d, m, f, _mult, _t in q("SELECT * FROM replenishment_orders"):
        j = idx.get((s, k, d))
        if j is not None:
            prod[j] = f
    con.close()
    return dict(rows=rows, n=n, A=A, hourly=hourly, instock=instock, trading=trading, sales=hourly.sum(1), cats=cats,
                v3=v3, v4=v4, prod=prod, go_live=CFG["hardcoded_go_live"] or go_live, stores=stores)


def profiles(X, clean_only=True, uniform=False):
    if CFG["hardcoded_profile"] is not None and not uniform:
        return np.array(CFG["hardcoded_profile"], float)
    A, hourly, instock, trading = X["A"], X["hourly"], X["instock"], X["trading"]
    full = np.isclose(instock.sum(1), trading.sum(1))
    prof = np.zeros((3, 24))
    for dt in range(3):
        m = A["dt"] == dt
        if clean_only:
            m = m & full
        std = trading[m].sum(0) > 0.5 * max(m.sum(), 1)
        p = std.astype(float) if uniform else hourly[m].sum(0) * std
        prof[dt] = p / p.sum()
    return prof


def exposure(X, prof):
    P = prof[X["A"]["dt"]]
    return (P * X["instock"]).sum(1), (P * X["trading"]).sum(1)


def groups(X, promo=True, season="week"):
    A = X["A"]
    kind = CFG.get("groups_kind")
    if kind:
        promo_cat = np.where(A["promo"] == 1, A["cat"] + 1, 0)
        gs = {
            "store_week": [A["store"] * 1000 + A["week"], A["sku"], A["dow"], A["cat"] * 1000 + A["week"], promo_cat],
            "sep_cat": [A["cat"] * 100 + A["store"] * 10 + A["post"], A["sku"], A["cat"] * 10 + A["dow"],
                        A["cat"] * 1000 + A["week"], promo_cat],
            "cat_period_only": [A["store"] * 10 + A["post"], A["sku"], A["dow"], A["cat"] * 10 + A["post"], promo_cat],
            "promo_common": [A["store"] * 10 + A["post"], A["sku"], A["dow"], A["cat"] * 1000 + A["week"], A["promo"]],
            "store_only": [A["store"], A["sku"], A["dow"], A["cat"] * 1000 + A["week"], promo_cat],
        }[kind]
        out = []
        for g in gs:
            u, inv = np.unique(g, return_inverse=True)
            out.append((inv, len(u)))
        return out
    season_idx = A["cat"] * 1000 + (A["week"] if season == "week" else A["week"] // 4)
    gs = [A["store"] * 10 + A["post"], A["sku"], A["dow"], season_idx]
    if promo:
        gs.append(np.where(A["promo"] == 1, A["cat"] + 1, 0))
    out = []
    for g in gs:
        u, inv = np.unique(g, return_inverse=True)
        out.append((inv, len(u)))
    return out


def fit(X, N, E, dist="nb", alpha_by_cat=True, promo=True, season="week", mask=None, iters=50):
    n = X["n"]
    mask = np.ones(n, bool) if mask is None else mask
    cat = X["A"]["cat"]
    nc = len(X["cats"])
    gs = groups(X, promo, season)
    logr = np.full(n, np.log(max(N[mask].sum(), 1) / max(E[mask].sum(), 1e-9)))
    alpha = np.full(nc if alpha_by_cat else 1, 3.0)
    if CFG["hardcoded_alpha"] is not None:
        alpha[:] = CFG["hardcoded_alpha"]
    grid = np.exp(np.linspace(np.log(0.3), np.log(60), 50))
    for it in range(iters):
        arow = alpha[cat] if alpha_by_cat else np.full(n, alpha[0])
        for inv, k in gs:
            mu = np.exp(logr) * E
            w = arow / (arow + mu) if dist == "nb" else np.ones(n)
            num = np.bincount(inv[mask], weights=(w * N)[mask], minlength=k)
            den = np.bincount(inv[mask], weights=(w * mu)[mask], minlength=k)
            upd = np.where((num > 0) & (den > 0), np.log(np.maximum(num, 1e-12) / np.maximum(den, 1e-12)), 0.0)
            logr = logr + np.clip(upd, -3, 3)[inv]
        if dist == "nb" and CFG["hardcoded_alpha"] is None and (it % 5 == 4):
            mu = np.exp(logr) * E
            for c in (range(nc) if alpha_by_cat else [None]):
                sel = mask & ((cat == c) if c is not None else True)
                Nc, mc = N[sel], np.maximum(mu[sel], 1e-12)
                ll = [np.sum(gammaln(Nc + a) - gammaln(a) + a * np.log(a / (a + mc)) + Nc * np.log(mc / (a + mc))) for a in grid]
                alpha[c if c is not None else 0] = grid[int(np.argmax(ll))]
    arow = alpha[cat] if alpha_by_cat else np.full(n, alpha[0])
    return np.exp(logr), arow


def fit_em(X, N, Ein, iters=60):
    n = X["n"]
    cat = X["A"]["cat"]
    nc = len(X["cats"])
    gs = groups(X)
    logr = np.full(n, np.log(N.sum() / Ein.sum()))
    alpha = np.full(nc, 3.0)
    for it in range(iters):
        a = alpha[cat]
        El = (a + N) / (a / np.exp(logr) + Ein)
        Elog = digamma(a + N) - np.log(a / np.exp(logr) + Ein)
        for inv, k in gs:
            num = np.bincount(inv, weights=a * El, minlength=k)
            den = np.bincount(inv, weights=a * np.exp(logr), minlength=k)
            logr = logr + np.clip(np.log(np.maximum(num, 1e-12) / np.maximum(den, 1e-12)), -3, 3)[inv]
        r = np.exp(logr)
        for c in range(nc):
            sel = cat == c
            s = np.mean(Elog[sel] - np.log(r[sel]) - El[sel] / r[sel])
            lo, hi = 0.05, 200.0
            for _ in range(50):
                mid = np.sqrt(lo * hi)
                if np.log(mid) - digamma(mid) + 1 + s > 0:
                    lo = mid
                else:
                    hi = mid
            alpha[c] = np.sqrt(lo * hi)
    return np.exp(logr), alpha[cat]


def posterior(N, rate, alpha, Ein, Efull):
    post = (alpha + N) / (alpha / rate + Ein)
    return np.where(np.isclose(Ein, Efull), N, N + post * (Efull - Ein))


def profile_conditional(X, iters=200):
    """Traffic shape by conditional multinomial likelihood with a free level per day (fixed-effects profile)."""
    A, hourly, instock, trading = X["A"], X["hourly"], X["instock"], X["trading"]
    prof = np.zeros((3, 24))
    for dt in range(3):
        m = A["dt"] == dt
        std = trading[m].sum(0) > 0.5 * m.sum()
        m = m & (hourly.sum(1) > 0)
        H, I = hourly[m][:, std], instock[m][:, std]
        g = np.full(std.sum(), 1.0 / std.sum())
        n = H.sum(1)
        for _ in range(iters):
            den = (I * g).sum(1)
            g = H.sum(0) / (I * (n / np.maximum(den, 1e-12))[:, None]).sum(0)
            g /= g.sum()
        prof[dt, std] = g
    return prof


def posterior_lognormal(N, rate, Ein, Efull, grp, ng):
    """Poisson-lognormal day shock (mean 1), sigma by ML per category (Gauss-Hermite), posterior imputation."""
    x, wq = np.polynomial.hermite_e.hermegauss(40)
    wq = wq / wq.sum()
    grid = np.linspace(0.15, 1.0, 35)
    out = N.astype(float).copy()
    cens = ~np.isclose(Ein, Efull)
    for c in range(ng):
        sel = (grp == c) & (Ein > 1e-9)
        Nc, mc = N[sel], rate[sel] * Ein[sel]
        best, bs = -np.inf, None
        for sg in grid:
            lam = mc[:, None] * np.exp(sg * x - sg * sg / 2)[None, :]
            ll = Nc[:, None] * np.log(lam) - lam - gammaln(Nc + 1)[:, None]
            mx = ll.max(1, keepdims=True)
            L = (mx[:, 0] + np.log((np.exp(ll - mx) * wq).sum(1))).sum()
            if L > best:
                best, bs = L, sg
        selc = (grp == c) & cens
        lam = rate[selc][:, None] * np.exp(bs * x - bs * bs / 2)[None, :]
        ll = N[selc][:, None] * np.log(np.maximum(lam, 1e-300)) - lam * Ein[selc][:, None]
        mx = ll.max(1, keepdims=True)
        wpost = np.exp(ll - mx) * wq
        out[selc] = N[selc] + (wpost * lam).sum(1) / wpost.sum(1) * (Efull[selc] - Ein[selc])
    return out


def estimate(X) -> np.ndarray:
    m = CFG["method"]
    N = X["sales"]
    prof = profiles(X)
    Ein, Efull = exposure(X, prof)
    cens = ~np.isclose(Ein, Efull)
    if m in ("nb", "nb_common_alpha", "nb_4week", "nb_no_promo"):
        rate, alpha = fit(X, N, Ein, "nb", alpha_by_cat=(m != "nb_common_alpha"), promo=(m != "nb_no_promo"),
                          season="4week" if m == "nb_4week" else "week")
        return posterior(N, rate, alpha, Ein, Efull)
    if m in ("store_week", "sep_cat", "cat_period_only", "promo_common", "store_only"):
        CFG["groups_kind"] = m
        try:
            rate, alpha = fit(X, N, Ein, "nb")
        finally:
            CFG["groups_kind"] = None
        return posterior(N, rate, alpha, Ein, Efull)
    if m == "alpha_sku":
        rate, _alpha = fit(X, N, Ein, "nb")
        sku = X["A"]["sku"]
        grid = np.exp(np.linspace(np.log(0.3), np.log(60), 60))
        mu = rate * Ein
        alpha = np.zeros(X["n"])
        for c in range(sku.max() + 1):
            sel = (sku == c) & (Ein > 1e-9)
            Nc, mc = N[sel], np.maximum(mu[sel], 1e-12)
            ll = [np.sum(gammaln(Nc + a) - gammaln(a) + a * np.log(a / (a + mc)) + Nc * np.log(mc / (a + mc))) for a in grid]
            alpha[sku == c] = grid[int(np.argmax(ll))]
        return posterior(N, rate, alpha, Ein, Efull)
    if m in ("nb_plugin", "nb_lognormal"):
        rate, alpha = fit(X, N, Ein, "nb")
        if m == "nb_plugin":
            return np.where(cens, N + rate * (Efull - Ein), N)
        return posterior_lognormal(N, rate, Ein, Efull, X["A"]["cat"], len(X["cats"]))
    if m == "fe_profile":
        cin, cfull = exposure(X, profile_conditional(X))
        rate, alpha = fit(X, N, cin, "nb")
        return posterior(N, rate, alpha, cin, cfull)
    if m == "em":
        rate, alpha = fit_em(X, N, Ein)
        return posterior(N, rate, alpha, Ein, Efull)
    if m in ("forecast_prior", "v3_prior"):
        fc = np.nan_to_num(X["prod"] if m == "forecast_prior" else X["v3"], nan=0.0)
        rate = np.maximum(fc, 1e-6) / np.maximum(Efull, 1e-9)
        cat = X["A"]["cat"]
        alpha = np.zeros(X["n"])
        grid = np.exp(np.linspace(np.log(0.3), np.log(60), 50))
        mu = rate * Ein
        for c in range(len(X["cats"])):
            sel = (cat == c) & (Ein > 1e-9)
            Nc, mc = N[sel], np.maximum(mu[sel], 1e-12)
            ll = [np.sum(gammaln(Nc + a) - gammaln(a) + a * np.log(a / (a + mc)) + Nc * np.log(mc / (a + mc))) for a in grid]
            alpha[cat == c] = grid[int(np.argmax(ll))]
        return posterior(N, rate, alpha, Ein, Efull)
    if m in ("sales", "holdout_transfer"):
        return N.copy()
    rate_b, _ = fit(X, N, Efull, "poisson", mask=~cens)
    if m == "drop_censored":
        return np.where(cens, np.maximum(N, rate_b * Efull), N)
    if m == "per_day_scale":
        share = np.where(Efull > 0, Ein / Efull, 1)
        return np.where(cens, np.where(share >= 0.1, N / np.maximum(share, 1e-9), np.maximum(N, rate_b * Efull)), N)
    if m == "uniform_time_scale":
        eu_in, eu_full = exposure(X, profiles(X, uniform=True))
        share = np.where(eu_full > 0, eu_in / eu_full, 1)
        return np.where(cens, np.where(share >= 0.1, N / np.maximum(share, 1e-9), np.maximum(N, rate_b * Efull)), N)
    if m == "mean_rate_impute":
        return np.where(cens, N + rate_b * (Efull - Ein), N)
    if m == "poisson_offset":
        rate_p, _ = fit(X, N, Ein, "poisson")
        return np.where(cens, N + rate_p * (Efull - Ein), N)
    if m == "forecast_impute":
        return np.where(cens, np.maximum(N, X["prod"]), N)
    if m == "profile_all_days":
        hin, hfull = exposure(X, profiles(X, clean_only=False))
        rate, alpha = fit(X, N, hin, "nb")
        cens_h = ~np.isclose(Ein, Efull)
        return np.where(cens_h, posterior(N, rate, alpha, hin, hfull), N)
    if m == "daily_censored_poisson":
        from scipy.stats import poisson
        rate_t = rate_b.copy()
        ed = N.copy()
        for _ in range(20):
            mu_t = rate_t * Efull
            sf = poisson.sf(N - 1, mu_t)
            sf1 = poisson.sf(N - 2, mu_t)
            ed = np.where(cens, np.maximum(mu_t * np.where(sf > 1e-12, sf1 / np.maximum(sf, 1e-12), 1.0), N), N)
            rate_t, _ = fit(X, ed, Efull, "poisson", iters=6)
        return ed
    raise ValueError(m)


def write(X, ED, out: Path) -> None:
    A = X["A"]
    out.mkdir(parents=True, exist_ok=True)
    N = X["sales"]
    with open(out / "demand_history.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["store_id", "sku_id", "date", "units_sold", "expected_demand", "lost_units"])
        for i, (s, k, d, _oh) in enumerate(X["rows"]):
            e = float(ED[i])
            w.writerow([s, k, d, int(N[i]), repr(e), repr(e - float(N[i]))])
    # category baselines from the history
    base = {}
    for p in (0, 1):
        msk = (A["post"] == p) & (A["promo"] == 0)
        sid = A["store"] * 10000 + A["sku"]
        u, inv = np.unique(sid[msk], return_inverse=True)
        means = np.bincount(inv, weights=ED[msk]) / np.bincount(inv)
        cat_of = np.zeros(len(u), int)
        cat_of[inv] = A["cat"][msk]
        base[p] = np.bincount(cat_of, weights=means, minlength=len(X["cats"]))
    with open(out / "category_trends.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "baseline_pre", "baseline_post", "baseline_change_pct", "action"])
        for c, name in enumerate(X["cats"]):
            pre, post = float(base[0][c]), float(base[1][c])
            ch = 100 * (post / pre - 1)
            if CFG["method"] == "holdout_transfer":
                hm = A["lean"] == 0
                vals = []
                for p in (0, 1):
                    mm = hm & (A["post"] == p) & (A["promo"] == 0) & (A["cat"] == c)
                    vals.append(N[mm].mean())
                ch_act = 100 * (vals[1] / vals[0] - 1)
            else:
                ch_act = ch
            act = "reduce" if ch_act <= -5 else "increase" if ch_act >= 5 else "maintain"
            if CFG["hardcoded_actions"]:
                act = CFG["hardcoded_actions"].get(name, act)
            w.writerow([name, repr(pre), repr(post), repr(ch), act])
    lost_u, lost_s = {}, {}
    for p, pn in ((0, "pre"), (1, "post")):
        lost_u[pn], lost_s[pn] = {}, {}
        for a, an in ((1, "lean26"), (0, "holdout")):
            msk = (A["post"] == p) & (A["lean"] == a)
            lu = float((ED[msk] - N[msk]).sum())
            lost_u[pn][an] = lu
            lost_s[pn][an] = lu / float(ED[msk].sum())
    pre = A["post"] == 0
    post_lean = (A["post"] == 1) & (A["lean"] == 1)
    bias = {"v3_pre_all_stores": float(100 * (X["v3"][pre].sum() - ED[pre].sum()) / ED[pre].sum()),
            "v4_post_lean26": float(100 * (X["v4"][post_lean].sum() - ED[post_lean].sum()) / ED[post_lean].sum())}
    (out / "programme_impact.json").write_text(json.dumps({"go_live_date": X["go_live"], "lost_units": lost_u,
                                                           "lost_share": lost_s, "forecast_bias_pct": bias}, indent=2) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="demandsci")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("review")
    r.add_argument("--db", default="data/warehouse.sqlite")
    r.add_argument("--out", default="out/review")
    a = ap.parse_args(argv)
    CFG.update(VARIANT)
    X = load(Path(a.db))
    write(X, estimate(X), Path(a.out))


if __name__ == "__main__":
    main()
