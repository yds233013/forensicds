"""G10 tolerance / identifiability pilot: estimators on generator output (numpy).

Every estimator sees only observable quantities (hourly sales, availability events, opening on-hand, trading hours,
calendar, promo flags, forecasts, store/SKU attributes). Truth (mu, lambda, demand) is used only for scoring.
"""
from __future__ import annotations

import numpy as np
from scipy.special import digamma, gammaln

import g10_world as G


# ------------------------------------------------------------------------------------------------ observable arrays


def arrays(w):
    spec = w.spec
    rows = [r for r in w.rows if not r["closed"]]
    n = len(rows)
    st = {s["store_id"]: i for i, s in enumerate(w.stores)}
    sk = {k["sku_id"]: i for i, k in enumerate(w.skus)}
    cats = list(spec["categories"])
    ci = {c: i for i, c in enumerate(cats)}
    day0 = w.days[0]
    A = {k: np.zeros(n, dtype=int) for k in ("store", "sku", "cat", "day", "week", "dow", "promo", "lean", "post",
                                               "comp", "afternoon", "dt")}
    F = {k: np.zeros(n) for k in ("sales", "demand", "mu", "v3", "v4", "prod_fc")}
    hourly = np.zeros((n, 24))
    instock = np.zeros((n, 24))        # fraction of each clock hour in stock, within trading hours
    trading = np.zeros((n, 24))        # fraction of each clock hour open
    # opening in-stock state: on_hand at open (observable: daily open on-hand snapshot)
    for i, r in enumerate(rows):
        A["store"][i] = st[r["store"]]
        A["sku"][i] = sk[r["sku"]]
        A["cat"][i] = ci[r["category"]]
        dd = (r["date"] - day0).days
        A["day"][i] = dd
        A["week"][i] = dd // 7
        A["dow"][i] = r["date"].weekday()
        A["dt"][i] = 2 if r["date"].weekday() == 6 else 1 if r["date"].weekday() == 5 else 0
        A["promo"][i] = r["promo"]
        A["post"][i] = r["date"] >= w.golive
        A["lean"][i] = r["arm"] == "lean26"
        A["comp"][i] = r["competitor_active"]
        A["afternoon"][i] = r["slot"] == "afternoon"
        F["sales"][i] = r["sales"]
        F["demand"][i] = r["demand"]
        F["mu"][i] = r["mu"]
        F["v3"][i] = r["v3"]
        F["v4"][i] = r["v4"] if r["v4"] is not None else np.nan
        F["prod_fc"][i] = r["v4"] if (r["v4"] is not None and r["arm"] == "lean26") else r["v3"]
        hourly[i, :] = r["hourly"]
        oh, ch = r["open_h"], r["close_h"]
        trading[i, oh:ch] = 1.0
        for a, b in G.in_stock_intervals(r, r["on_hand_open"]):
            h0 = int(a)
            while h0 < b and h0 < 24:
                lo, hi = max(a, h0), min(b, h0 + 1)
                if hi > lo:
                    instock[i, h0] += hi - lo
                h0 += 1
    return {"A": A, "F": F, "hourly": hourly, "instock": instock, "trading": trading, "n": n, "cats": cats,
            "spec": spec}


# ------------------------------------------------------------------------------------------------ profiles / exposure


def estimate_profiles(X, clean_only=True, uniform=False):
    """Intraday shape per day type from hourly sales; returns (n,24) weights normalised per standard day."""
    A, hourly, instock, trading = X["A"], X["hourly"], X["instock"], X["trading"]
    full = np.isclose(instock.sum(1), trading.sum(1))
    prof = np.zeros((3, 24))
    for dt in range(3):
        m = A["dt"] == dt
        if clean_only:
            m &= full
        std_hours = trading[m].sum(0) > 0.5 * m.sum()     # standard open hours for the day type
        if uniform:
            p = std_hours.astype(float)
        else:
            p = hourly[m].sum(0) * std_hours
        prof[dt] = p / p.sum()
    return prof


def exposures(X, prof):
    P = prof[X["A"]["dt"]]
    lam_in = (P * X["instock"]).sum(1)
    lam_full = (P * X["trading"]).sum(1)
    return lam_in, lam_full


# ------------------------------------------------------------------------------------------------ multiplicative models


def factor_groups(X, promo=True, comp=True, season="week"):
    A = X["A"]
    season_idx = A["cat"] * 100 + (A["week"] if season == "week" else (A["week"] // 4))
    groups = [("store", A["store"], 16), ("sku", A["sku"], A["sku"].max() + 1), ("dow", A["dow"], 7),
              ("catseason", season_idx, None)]
    if promo:
        groups.append(("promo_cat", np.where(A["promo"] == 1, A["cat"] + 1, 0), None))
    if comp:
        groups.append(("comp", A["comp"], 2))
    out = []
    for name, idx, k in groups:
        u, inv = np.unique(idx, return_inverse=True)
        out.append((name, inv, len(u), u))
    return out


def fit_rate(X, N, E, dist="nb", alpha_by_cat=True, promo=True, comp=True, mask=None, iters=60, season="week"):
    """Fit rate r_i = prod factors (per unit exposure) with counts N and exposure E. NB via weighted IPF + alpha
    profile likelihood; Poisson via plain IPF. Returns (rate, alpha per row)."""
    A = X["A"]
    n = X["n"]
    if mask is None:
        mask = np.ones(n, bool)
    groups = factor_groups(X, promo, comp, season)
    logr = np.full(n, np.log(max(N[mask].sum(), 1) / max(E[mask].sum(), 1e-9)))
    facs = [np.zeros(k) for _, _, k, _ in groups]
    cat = A["cat"]
    alpha = np.full(8, 3.0) if alpha_by_cat else np.array([3.0])
    for it in range(iters):
        r = np.exp(logr)
        mu = r * E
        a_row = alpha[cat] if alpha_by_cat else np.full(n, alpha[0])
        wgt = (a_row / (a_row + mu)) if dist == "nb" else np.ones(n)
        for gi, (name, inv, k, _) in enumerate(groups):
            num = np.bincount(inv[mask], weights=(wgt * N)[mask], minlength=k)
            den = np.bincount(inv[mask], weights=(wgt * mu)[mask], minlength=k)
            upd = np.where((num > 0) & (den > 0), np.log(np.maximum(num, 1e-12) / np.maximum(den, 1e-12)), 0.0)
            upd = np.clip(upd, -3, 3)
            facs[gi] += upd
            logr = logr + upd[inv]
            r = np.exp(logr)
            mu = r * E
            wgt = (a_row / (a_row + mu)) if dist == "nb" else np.ones(n)
        if dist == "nb" and it % 5 == 4:
            for c in (range(8) if alpha_by_cat else [None]):
                sel = mask & ((cat == c) if c is not None else True)
                Nc, muc = N[sel], mu[sel]
                grid = np.exp(np.linspace(np.log(0.3), np.log(60), 60))
                ll = [np.sum(gammaln(Nc + a) - gammaln(a) + a * np.log(a / (a + muc)) + Nc * np.log(np.maximum(muc, 1e-12) / (a + muc))) for a in grid]
                best = grid[int(np.argmax(ll))]
                fine = np.exp(np.linspace(np.log(best) - 0.15, np.log(best) + 0.15, 21))
                llf = [np.sum(gammaln(Nc + a) - gammaln(a) + a * np.log(a / (a + muc)) + Nc * np.log(np.maximum(muc, 1e-12) / (a + muc))) for a in fine]
                if c is None:
                    alpha[0] = fine[int(np.argmax(llf))]
                else:
                    alpha[c] = fine[int(np.argmax(llf))]
            a_row = alpha[cat] if alpha_by_cat else np.full(n, alpha[0])
    return np.exp(logr), (alpha[cat] if alpha_by_cat else np.full(n, alpha[0]))


def fit_em_gamma(X, N, Ein, Efull, iters=80):
    """Independent EM over latent day intensities (Gamma-Poisson): E-step posterior of lambda_d; M-step IPF of
    prior means on E[lambda] with unit exposure; alpha per category from the digamma equation."""
    A = X["A"]
    n = X["n"]
    groups = factor_groups(X)
    logr = np.full(n, np.log(N.sum() / Ein.sum()))
    cat = A["cat"]
    alpha = np.full(8, 3.0)
    for it in range(iters):
        r = np.exp(logr)
        a = alpha[cat]
        post_shape = a + N
        post_rate = a / r + Ein
        El = post_shape / post_rate
        Elog = digamma(post_shape) - np.log(post_rate)
        for gi, (name, inv, k, _) in enumerate(groups):
            # complete-data score for log factor: sum a*(E[lambda]/r - 1) = 0  (weights a)
            num = np.bincount(inv, weights=a * El, minlength=k)
            den = np.bincount(inv, weights=a * np.exp(logr), minlength=k)
            upd = np.clip(np.log(np.maximum(num, 1e-12) / np.maximum(den, 1e-12)), -3, 3)
            logr = logr + upd[inv]
        r = np.exp(logr)
        for c in range(8):
            sel = cat == c
            s = np.mean(Elog[sel] - np.log(r[sel]) - El[sel] / r[sel])
            # solve log(a) - digamma(a) + 1 + s = 0
            lo, hi = 0.05, 200.0
            for _ in range(60):
                mid = np.sqrt(lo * hi)
                val = np.log(mid) - digamma(mid) + 1 + s
                if val > 0:
                    lo = mid
                else:
                    hi = mid
            alpha[c] = np.sqrt(lo * hi)
    return np.exp(logr), alpha[cat]


# ------------------------------------------------------------------------------------------------ estimators


def expected_demand_posterior(N, rate, alpha, Ein, Efull):
    post = (alpha + N) / (alpha / rate + Ein)
    return np.where(np.isclose(Ein, Efull), N, N + post * (Efull - Ein))


def run_all(X):
    A, Fv = X["A"], X["F"]
    N = Fv["sales"]
    prof = estimate_profiles(X, clean_only=True)
    Ein, Efull = exposures(X, prof)
    cens = ~np.isclose(Ein, Efull)
    out = {}

    rate, alpha = fit_rate(X, N, Ein, "nb", alpha_by_cat=True)
    out["C1_nb_offset_posterior"] = expected_demand_posterior(N, rate, alpha, Ein, Efull)
    rate_c, alpha_c = fit_rate(X, N, Ein, "nb", alpha_by_cat=False)
    out["C2_nb_common_alpha"] = expected_demand_posterior(N, rate_c, alpha_c, Ein, Efull)
    rate_em, alpha_em = fit_em_gamma(X, N, Ein, Efull)
    out["C3_em_gamma_poisson"] = expected_demand_posterior(N, rate_em, alpha_em, Ein, Efull)
    rate_4, alpha_4 = fit_rate(X, N, Ein, "nb", season="4week")
    out["C4_nb_4week_season"] = expected_demand_posterior(N, rate_4, alpha_4, Ein, Efull)

    out["W_A_sales"] = N.copy()
    # B: drop censored days; rate from uncensored days; censored days replaced by max(sales, fitted mean)
    rate_b, _ = fit_rate(X, N, Efull, "poisson", mask=~cens)
    out["W_B_drop_censored"] = np.where(cens, np.maximum(N, rate_b * Efull), N)
    # C: per-day traffic-share scaling (fallback to B when almost no exposure)
    share = np.where(Efull > 0, Ein / Efull, 1)
    out["W_C_per_day_scale"] = np.where(cens, np.where(share >= 0.1, N / np.maximum(share, 1e-9), rate_b * Efull), N)
    # C2: uniform time scaling
    profu = estimate_profiles(X, uniform=True)
    Eu_in, Eu_full = exposures(X, profu)
    shu = np.where(Eu_full > 0, Eu_in / Eu_full, 1)
    out["W_C2_uniform_time_scale"] = np.where(cens, np.where(shu >= 0.1, N / np.maximum(shu, 1e-9), rate_b * Efull), N)
    # D: lost = uncensored-day mean rate x out-of-stock exposure
    out["W_D_mean_rate_impute"] = np.where(cens, N + rate_b * (Efull - Ein), N)
    # F: Poisson exposure-offset model, lost = fitted rate x out-of-stock exposure
    rate_p, _ = fit_rate(X, N, Ein, "poisson")
    out["W_F_poisson_offset"] = np.where(cens, N + rate_p * (Efull - Ein), N)
    # G: forecast imputation (production forecast)
    out["W_G_forecast_impute"] = np.where(cens, np.maximum(N, Fv["prod_fc"]), N)
    # H: profile from all days, otherwise C1
    prof_all = estimate_profiles(X, clean_only=False)
    Ha_in, Ha_full = exposures(X, prof_all)
    rate_h, alpha_h = fit_rate(X, N, Ha_in, "nb")
    out["W_H_profile_all_days"] = expected_demand_posterior(N, rate_h, alpha_h, Ha_in, Ha_full)
    # I: NB without promo covariate
    rate_i, alpha_i = fit_rate(X, N, Ein, "nb", promo=False)
    out["W_I_nb_no_promo"] = expected_demand_posterior(N, rate_i, alpha_i, Ein, Efull)
    # T: daily censored Poisson (Tobit-like EM: censored days have D >= sales)
    rate_t = rate_b.copy()
    from scipy.stats import poisson
    for _ in range(25):
        mu_t = rate_t * Efull
        # E[D | D >= N] for Poisson
        sf = poisson.sf(N - 1, mu_t)
        sf1 = poisson.sf(N - 2, mu_t)
        ed = np.where(cens, mu_t * np.where(sf > 1e-12, sf1 / np.maximum(sf, 1e-12), 1.0), N)
        ed = np.where(cens, np.maximum(ed, N), N)
        rate_t, _ = fit_rate(X, ed, Efull, "poisson", iters=8)
    out["W_T_daily_censored_poisson"] = ed
    return out, {"cens": cens, "prof": prof, "alpha_c1": alpha}


# ------------------------------------------------------------------------------------------------ graded quantities


def series_baseline(X, V, period):
    """Category baseline: sum over store-SKU series of the mean of V over that series' non-promotional trading days."""
    A = X["A"]
    m = (A["post"] == period) & (A["promo"] == 0)
    sid = A["store"] * 1000 + A["sku"]
    u, inv = np.unique(sid[m], return_inverse=True)
    sums = np.bincount(inv, weights=V[m])
    cnt = np.bincount(inv)
    cat_of = np.zeros(len(u), int)
    cat_of[inv] = A["cat"][m]
    return np.bincount(cat_of, weights=sums / cnt, minlength=8)


def graded(X, ED, mu_for_baseline=None):
    A, Fv = X["A"], X["F"]
    res = {}
    V = ED if mu_for_baseline is None else mu_for_baseline
    b0, b1 = series_baseline(X, V, 0), series_baseline(X, V, 1)
    for c, name in enumerate(X["cats"]):
        res[f"cat_change::{name}"] = 100 * (b1[c] / b0[c] - 1)
    for p in (0, 1):
        for arm in (0, 1):
            for pr in (0, 1):
                m = (A["post"] == p) & (A["lean"] == arm) & (A["promo"] == pr)
                res[f"total::post{p}_lean{arm}_promo{pr}"] = ED[m].sum()
            m = (A["post"] == p) & (A["lean"] == arm)
            res[f"lost::post{p}_lean{arm}"] = (ED[m] - Fv["sales"][m]).sum()
        for pr in (0, 1):
            m = (A["post"] == p) & (A["promo"] == pr)
            res[f"lost::post{p}_promo{pr}"] = (ED[m] - Fv["sales"][m]).sum()
    m3 = A["post"] == 0
    res["bias::v3_pre"] = 100 * (Fv["v3"][m3].sum() - ED[m3].sum()) / ED[m3].sum()
    m4 = (A["post"] == 1) & (A["lean"] == 1)
    res["bias::v4_post_lean"] = 100 * (Fv["v4"][m4].sum() - ED[m4].sum()) / ED[m4].sum()
    return res


def truth(X):
    Fv = X["F"]
    return graded(X, Fv["demand"])
