"""Independent correct review for G10 (dev tool, never shipped to agents): Bayesian data augmentation.

Written without reference to variant_review.py or the reference solution's code. Differences in structure:
  - loader: plain sqlite3 + dicts; in-stock exposure by integrating a cumulative traffic curve over in-stock intervals;
  - traffic shape: estimated from holdout-store days on shelf all day with the day type's standard hours;
  - inference: Gibbs sampler over latent day multipliers eps_d ~ Gamma(alpha, alpha), multiplicative Gamma-conjugate
    factor updates (store x period, SKU, weekday, category x week, category x promotion) and a grid-Gibbs step for the
    per-category alpha; Rao-Blackwellised posterior mean of the day intensity averaged over retained sweeps.
usage: alt_gibbs_review.py review --db DB --out DIR   (also importable: main(argv))
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
from scipy.special import gammaln

VARIANT: dict = {}
SWEEPS, BURN, SEED = 400, 200, 20260914


def daytype(d: date) -> int:
    return 2 if d.weekday() == 6 else 1 if d.weekday() == 5 else 0


def hours_of(t: str) -> float:
    hh, mm, ss = t.split(":")
    return int(hh) + int(mm) / 60 + int(ss) / 3600


def read(db: Path) -> dict:
    con = sqlite3.connect(f"file:{Path(db).resolve()}?mode=ro", uri=True)
    cal = {}
    for s, d, status, o, c in con.execute("SELECT store_id, date, status, open_time, close_time FROM store_calendar"):
        if status == "open":
            cal[(s, d)] = (hours_of(o + ":00" if len(o) == 5 else o), hours_of(c + ":00" if len(c) == 5 else c))
    category = dict(con.execute("SELECT sku_id, category FROM skus"))
    arm, go_live = {}, None
    for s, a, g in con.execute("SELECT store_id, arm, go_live_date FROM programme_assignment"):
        arm[s], go_live = a, g if go_live is None else min(go_live, g)
    promos = defaultdict(list)
    for k, a, b in con.execute("SELECT sku_id, start_date, end_date FROM promotions"):
        promos[k].append((a, b))
    keys, open_stock = [], []
    for s, k, d, oh in con.execute("SELECT store_id, sku_id, date, on_hand_open FROM inventory_daily"):
        if (s, d) in cal:
            keys.append((s, k, d))
            open_stock.append(oh)
    order = sorted(range(len(keys)), key=lambda i: keys[i])
    keys = [keys[i] for i in order]
    open_stock = [open_stock[i] for i in order]
    pos = {key: i for i, key in enumerate(keys)}
    n = len(keys)
    hourly = np.zeros((n, 24))
    for s, k, d, h, u in con.execute("SELECT store_id, sku_id, date, hour, units FROM sales_hourly"):
        i = pos.get((s, k, d))
        if i is not None:
            hourly[i, h] += u
    events = defaultdict(list)
    for s, k, t, e in con.execute("SELECT store_id, sku_id, event_time, event_type FROM availability_events"):
        d, clock = t.split(" ")
        events[(s, k, d)].append((hours_of(clock), e))
    forecasts = {"v3": np.full(n, np.nan), "v4": np.full(n, np.nan)}
    for m, s, k, d, f in con.execute("SELECT model, store_id, sku_id, date, forecast_units FROM forecasts"):
        i = pos.get((s, k, d))
        if i is not None and m in forecasts:
            forecasts[m][i] = f
    con.close()

    intervals, full = [], np.zeros(n, bool)
    for i, (s, k, d) in enumerate(keys):
        o, c = cal[(s, d)]
        on = open_stock[i] > 0
        start, iv = o, []
        for t, e in sorted(events.get((s, k, d), [])):
            if not (o <= t < c):
                continue
            if e == "out_of_stock" and on:
                iv.append((start, t))
                on = False
            elif e == "back_in_stock" and not on:
                start, on = t, True
        if on:
            iv.append((start, c))
        intervals.append(iv)
        full[i] = len(iv) == 1 and iv[0] == (o, c)
    dates = [date.fromisoformat(d) for _s, _k, d in keys]
    first = min(dates)
    return dict(keys=keys, n=n, cal=cal, category=category, arm=arm, go_live=go_live, promos=promos, hourly=hourly,
                intervals=intervals, full=full, dates=dates, first=first, forecasts=forecasts)


def exposures(W: dict) -> tuple[np.ndarray, np.ndarray]:
    n, keys, cal = W["n"], W["keys"], W["cal"]
    dt = np.array([daytype(d) for d in W["dates"]])
    hold = np.array([W["arm"][s] == "holdout" for s, _k, _d in keys])
    cum = []
    for t in range(3):
        hours = [cal[(s, d)] for i, (s, _k, d) in enumerate(keys) if dt[i] == t]
        std = max(set(hours), key=hours.count)
        sel = (dt == t) & hold & W["full"] & np.array([cal[(s, d)] == std for s, _k, d in keys])
        shape = W["hourly"][sel].sum(0)
        shape = shape / shape.sum()
        cum.append(np.concatenate([[0.0], np.cumsum(shape)]))

    def curve(t_type, x):
        h = min(int(x), 23)
        return cum[t_type][h] + (x - h) * (cum[t_type][h + 1] - cum[t_type][h])

    e_in, e_full = np.zeros(n), np.zeros(n)
    for i, (s, _k, d) in enumerate(keys):
        o, c = cal[(s, d)]
        e_full[i] = curve(dt[i], c) - curve(dt[i], o)
        e_in[i] = sum(curve(dt[i], b) - curve(dt[i], a) for a, b in W["intervals"][i])
    e_in[W["full"]] = e_full[W["full"]]
    return e_in, e_full


def factor_codes(W: dict) -> tuple[list[tuple[np.ndarray, int, np.ndarray]], np.ndarray, np.ndarray, np.ndarray, list[str]]:
    keys, cat = W["keys"], W["category"]
    cats = sorted(set(cat.values()))
    post = np.array([d >= W["go_live"] for _s, _k, d in keys])
    promo = np.array([any(a <= d <= b for a, b in W["promos"][k]) for _s, k, d in keys])
    lab = {
        "store_period": [f"{s}|{p}" for (s, _k, _d), p in zip(keys, post)],
        "sku": [k for _s, k, _d in keys],
        "weekday": [str(d.weekday()) for d in W["dates"]],
        "cat_week": [f"{cat[k]}|{(dd - W['first']).days // 7}" for (_s, k, _d), dd in zip(keys, W["dates"])],
        "cat_promo": [cat[k] if p else "-" for (_s, k, _d), p in zip(keys, promo)],
    }
    out = []
    for name, labels in lab.items():
        levels = sorted(set(labels))
        idx = {v: j for j, v in enumerate(levels)}
        codes = np.array([idx[v] for v in labels])
        fixed = np.array([v == "-" for v in levels]) if name == "cat_promo" else np.zeros(len(levels), bool)
        out.append((codes, len(levels), fixed))
    cat_code = np.array([cats.index(cat[k]) for _s, k, _d in keys])
    return out, post, promo, cat_code, cats


def gibbs(N, e_in, factors, cat_code, n_cats):
    rng = np.random.default_rng(SEED)
    n = len(N)
    vals = [np.ones(k) for _c, k, _f in factors]
    scale = N.sum() / e_in.sum()
    alpha = np.full(n_cats, 3.0)
    grid = np.exp(np.linspace(np.log(0.2), np.log(80), 120))
    a0, b0 = 0.01, 0.01
    acc = np.zeros(n)
    kept = 0
    eps = np.ones(n)
    for sweep in range(SWEEPS):
        r = scale * np.prod([v[c] for v, (c, _k, _f) in zip(vals, factors)], axis=0)
        a = alpha[cat_code]
        eps = rng.gamma(a + N, 1.0 / (a + r * e_in))
        for j, (codes, k, fixed) in enumerate(factors):
            r_minus = r / vals[j][codes]
            shape = a0 + np.bincount(codes, weights=N, minlength=k)
            rate = b0 + np.bincount(codes, weights=r_minus * eps * e_in, minlength=k)
            new = rng.gamma(shape, 1.0 / rate)
            if fixed.any():
                new[fixed] = 1.0
            else:                                   # move the level of the factor into the scale (r unchanged)
                g = np.exp(np.mean(np.log(new)))
                new /= g
                scale *= g
                r_minus = r_minus * g
            vals[j] = new
            r = r_minus * new[codes]
        base_r = r / scale
        scale = rng.gamma(a0 + N.sum(), 1.0 / (b0 + (base_r * eps * e_in).sum()))
        r = base_r * scale
        slog = np.bincount(cat_code, weights=np.log(eps), minlength=n_cats)
        ssum = np.bincount(cat_code, weights=eps, minlength=n_cats)
        cnt = np.bincount(cat_code, minlength=n_cats)
        for c in range(n_cats):
            lp = cnt[c] * (grid * np.log(grid) - gammaln(grid)) + (grid - 1) * slog[c] - grid * ssum[c] - np.log(grid)
            p = np.exp(lp - lp.max())
            alpha[c] = rng.choice(grid, p=p / p.sum())
        if sweep >= BURN:
            a = alpha[cat_code]
            acc += (a + N) / (a / r + e_in)
            kept += 1
    return acc / kept


def main(argv=None):
    ap = argparse.ArgumentParser(prog="demandsci")
    sub = ap.add_subparsers(dest="cmd", required=True)
    rv = sub.add_parser("review")
    rv.add_argument("--db", default="data/warehouse.sqlite")
    rv.add_argument("--out", default="out/review")
    args = ap.parse_args(argv)
    W = read(Path(args.db))
    e_in, e_full = exposures(W)
    factors, post, promo, cat_code, cats = factor_codes(W)
    N = W["hourly"].sum(1)
    lam = gibbs(N, e_in, factors, cat_code, len(cats))
    ed = np.where(W["full"], N, N + lam * np.maximum(e_full - e_in, 0.0))

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "demand_history.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["store_id", "sku_id", "date", "units_sold", "expected_demand", "lost_units"])
        for i, (s, k, d) in enumerate(W["keys"]):
            w.writerow([s, k, d, int(N[i]), repr(float(ed[i])), repr(float(ed[i] - N[i]))])
    series = defaultdict(lambda: [0.0, 0])
    for i, (s, k, _d) in enumerate(W["keys"]):
        if not promo[i]:
            acc = series[(cats[cat_code[i]], bool(post[i]), s, k)]
            acc[0] += ed[i]
            acc[1] += 1
    base = defaultdict(float)
    for (c, p, _s, _k), (tot, cnt) in series.items():
        base[(c, p)] += tot / cnt
    with open(out / "category_trends.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "baseline_pre", "baseline_post", "baseline_change_pct", "action"])
        for c in cats:
            pre, pst = float(base[(c, False)]), float(base[(c, True)])
            ch = 100 * (pst / pre - 1)
            w.writerow([c, repr(pre), repr(pst), repr(ch), "reduce" if ch <= -5 else "increase" if ch >= 5 else "maintain"])
    lean = np.array([W["arm"][s] == "lean26" for s, _k, _d in W["keys"]])
    lu, ls = {}, {}
    for pn, pm in (("pre", ~post), ("post", post)):
        lu[pn], ls[pn] = {}, {}
        for an, am in (("lean26", lean), ("holdout", ~lean)):
            m = pm & am
            lu[pn][an] = float((ed[m] - N[m]).sum())
            ls[pn][an] = lu[pn][an] / float(ed[m].sum())
    f = W["forecasts"]
    pl = post & lean
    bias = {"v3_pre_all_stores": float(100 * (np.nansum(f["v3"][~post]) - ed[~post].sum()) / ed[~post].sum()),
            "v4_post_lean26": float(100 * (np.nansum(f["v4"][pl]) - ed[pl].sum()) / ed[pl].sum())}
    (out / "programme_impact.json").write_text(json.dumps({"go_live_date": W["go_live"], "lost_units": lu,
                                                           "lost_share": ls, "forecast_bias_pct": bias}, indent=2) + "\n")


if __name__ == "__main__":
    main()
