"""G05 v2 Phase-0 estimator panel: accepted causal estimators and natural wrong analyses (research only).

Every method returns aggregate(...) output: wave, kit, pooled, gate (log net sales run-rate effects unless stated).
"""
from __future__ import annotations

import numpy as np

import g05_sim as S


# ---------------------------------------------------------------- helpers
def _fe_fit(y, M, group, store_trend, iters):
    """Alternating projections for y = a_s + b_{group(s),t} (+ c_s t) on mask M. Returns fitted array."""
    Sn, T = y.shape
    ng = int(group.max()) + 1
    Mf = M.astype(float)
    tt = np.broadcast_to(np.arange(T, dtype=float), (Sn, T))
    a = np.zeros(Sn); b = np.zeros((ng, T)); c = np.zeros(Sn)
    cnt_s = np.maximum(Mf.sum(1), 1)
    for _ in range(iters):
        trend = c[:, None] * tt if store_trend else 0.0
        a = (Mf * (y - b[group] - trend)).sum(1) / cnt_s
        r = y - a[:, None] - trend
        num = np.zeros((ng, T)); den = np.zeros((ng, T))
        np.add.at(num, group, Mf * r); np.add.at(den, group, Mf)
        b = num / np.maximum(den, 1e-9)
        if store_trend:
            r2 = y - b[group]
            tbar = (Mf * tt).sum(1) / cnt_s
            rbar = (Mf * r2).sum(1) / cnt_s
            tc = tt - tbar[:, None]
            c = (Mf * (r2 - rbar[:, None]) * tc).sum(1) / np.maximum((Mf * tc * tc).sum(1), 1e-9)
    trend = c[:, None] * tt if store_trend else 0.0
    return a[:, None] + b[group] + trend


def fe_impute(w, y, fit_mask, group, extra=None, store_trend=False, iters=60):
    """Untreated-outcome model fitted on fit_mask; with `extra`, partial it out (Frisch-Waugh) and keep gamma * extra."""
    if extra is None:
        return _fe_fit(y, fit_mask, group, store_trend, iters)
    ry = y - _fe_fit(y, fit_mask, group, store_trend, iters)
    rx = extra - _fe_fit(extra, fit_mask, group, store_trend, iters)
    M = fit_mask
    gam = float((ry[M] * rx[M]).sum() / (rx[M] * rx[M]).sum())
    return _fe_fit(y - gam * extra, fit_mask, group, store_trend, iters) + gam * extra


def untreated_mask(w, G=None, comparable=True):
    G = w["G"] if G is None else G
    m = np.arange(w["T"])[None, :] < G[:, None]
    return m & w["comparable"] if comparable else m


def imputation(w, y=None, group="format", G=None, comparable=True, window=None, gate_mode="kit",
               store_trend=False, extra=None, window_comparable=None):
    y = w["y_s"] if y is None else y
    G = w["G"] if G is None else G
    grp = {"format": w["fmt"], "none": np.zeros(w["S"], int), "kit": w["kit"], "format_kit": w["fmt"] * 2 + w["kit"]}[group]
    fit = untreated_mask(w, G, comparable)
    yhat = fe_impute(w, y, fit, grp, extra=extra, store_trend=store_trend)
    lo, hi = window or w["spec"]["rr_window"]
    wc = comparable if window_comparable is None else window_comparable
    mask = S.window_mask(w, G=G, lo=lo, hi=hi, use_comparable=wc)
    return S.aggregate(w, y - yhat, mask, gate_mode=gate_mode)


def cs_store_did(w, y=None, conditional=True, base="clean", controls="notyet", comparable=True, gate_mode="kit",
                 window=None, cond_on="fmt"):
    """Store-level DiD: treated store vs same-format (or all) not-yet-treated controls, per run-rate week."""
    y = w["y_s"] if y is None else y
    T = w["T"]; G = w["G"]; C = w["comparable"] if comparable else np.ones_like(w["comparable"])
    lo, hi = window or w["spec"]["rr_window"]
    tau_hat = np.zeros((w["S"], T))
    mask = S.window_mask(w, lo=lo, hi=hi, use_comparable=comparable)
    inst = np.where(w["wave"] < 4)[0]
    cv = w[cond_on]
    keys = {(int(G[s]), int(cv[s]) if conditional else 0) for s in inst}
    for g, f in keys:
        tr = inst[(G[inst] == g) & ((cv[inst] == f) if conditional else True)]
        pool = np.arange(w["S"])
        if conditional:
            pool = pool[cv == f]
        if base == "clean":
            bw = np.arange(max(g - 10, 0), g - 2)          # e = -10 .. -3
        elif base == "e43":
            bw = np.arange(g - 4, g - 2)                    # e = -4 .. -3
        elif base == "last":
            bw = np.arange(g - 8, g - 2)                    # latest comparable week in e = -8 .. -3
        else:
            bw = np.array([g - 1])                          # g-1, whatever it holds
        def base_mean(units):
            if base == "last":
                Cb = C[np.ix_(units, bw)]
                Yb = y[np.ix_(units, bw)]
                has = Cb.any(1)
                last = len(bw) - 1 - np.argmax(Cb[:, ::-1], axis=1)
                return np.where(has, Yb[np.arange(len(units)), last], np.nan)
            Cb = C[np.ix_(units, bw)] if base != "gm1" else np.ones((len(units), len(bw)), bool)
            v = np.where(Cb, y[np.ix_(units, bw)], 0).sum(1)
            n = Cb.sum(1)
            return np.where(n > 0, v / np.maximum(n, 1), np.nan)
        btr = base_mean(tr)
        for k in range(lo, hi + 1):
            tk = g + k
            if tk >= T:
                continue
            if controls == "notyet":
                ctrl = pool[G[pool] > tk]
            else:
                ctrl = pool[~np.isfinite(G[pool])]
            ok = C[ctrl, tk] if comparable else np.ones(len(ctrl), bool)
            ctrl = ctrl[ok]
            bc = base_mean(ctrl)
            good = ~np.isnan(bc)
            cdiff = np.mean(y[ctrl[good], tk] - bc[good])
            tau_hat[tr, tk] = (y[tr, tk] - btr) - cdiff
    return S.aggregate(w, tau_hat, mask, gate_mode=gate_mode)


def twfe_static(w, y, G, comparable):
    Sn, T = y.shape
    D = (np.arange(T)[None, :] >= G[:, None]).astype(float)
    M = w["comparable"] if comparable else np.ones((Sn, T), bool)
    Mf = M.astype(float)
    def dm(v):
        v = v * Mf
        for _ in range(80):
            v = v - Mf * ((v.sum(1) / np.maximum(Mf.sum(1), 1))[:, None])
            v = v - Mf * ((v.sum(0) / np.maximum(Mf.sum(0), 1))[None, :])
        return v
    Dt, Yt = dm(D), dm(y)
    beta = float((Dt * Yt).sum() / (Dt * Dt).sum())
    return beta


def const(w, beta):
    return {"wave": {f"W{i + 1}": beta for i in range(4)}, "kit": {"full": beta, "compact": beta}, "pooled": beta,
            "gate": beta}


def twfe_event(w, lo=-12, hi=25, ref=-1):
    """TWFE with binned event-time dummies on all stores and all weeks, reference e=-1; run-rate = mean of 12..25."""
    y = w["y_s"]; Sn, T = y.shape
    e = np.arange(T)[None, :] - w["G"][:, None]
    ev = np.clip(np.where(np.isfinite(e), e, lo - 1), lo - 1, hi + 1)   # lo-1 bin = far pre and never
    ks = [k for k in range(lo, hi + 2) if k != ref]
    X = np.stack([(ev == k).astype(float) for k in ks], -1)             # S x T x K
    def dm(v):
        for _ in range(60):
            v = v - v.mean(1, keepdims=True)
            v = v - v.mean(0, keepdims=True)
        return v
    Xd = dm(X.copy()); Yd = dm(y.copy())
    Xf = Xd.reshape(-1, len(ks)); Yf = Yd.reshape(-1)
    coef = np.linalg.lstsq(Xf, Yf, rcond=None)[0]
    rr = np.mean([coef[ks.index(k)] for k in range(12, 26)])
    return const(w, float(rr))


# ---------------------------------------------------------------- accepted
def a_imp_format_week(w):      return imputation(w, group="format")
def a_cs_format_notyet(w):     return cs_store_did(w, conditional=True, base="clean", controls="notyet")
def a_cs_format_never(w):      return cs_store_did(w, conditional=True, base="clean", controls="never")
def a_imp_store_trend(w):      return imputation(w, group="none", store_trend=True)
def a_cs_base_last(w):         return cs_store_did(w, conditional=True, base="last", controls="notyet")
def a_cs_base_e43(w):          return cs_store_did(w, conditional=True, base="e43", controls="notyet")


# ---------------------------------------------------------------- wrong / near-miss
def w_before_after(w):
    y = w["y_s"]; T = w["T"]; G = w["G"]; C = w["comparable"]
    e = np.arange(T)[None, :] - G[:, None]
    pre = C & (e >= -26) & (e <= -3)
    b = np.where(pre, y, 0).sum(1) / np.maximum(pre.sum(1), 1)
    return S.aggregate(w, y - b[:, None], S.window_mask(w))

def w_house_twfe_basket(w):    return const(w, twfe_static(w, w["y_b"], w["planned"], comparable=False))
def w_twfe_static_sales(w):    return const(w, twfe_static(w, w["y_s"], w["G"], comparable=True))
def w_twfe_event_ref_m1(w):    return twfe_event(w)
def w_cs_gm1_pooled(w):        return cs_store_did(w, conditional=False, base="gm1", comparable=False)
def w_imp_unconditional(w):    return imputation(w, group="none")
def w_cs_unconditional(w):     return cs_store_did(w, conditional=False, base="clean")
def w_outcome_basket(w):       return imputation(w, y=w["y_b"], group="format")
def w_gate_pooled(w):          return imputation(w, group="format", gate_mode="pooled")
def w_window_0_25(w):          return imputation(w, group="format", window=(0, 25))
def w_planned_timing(w):       return imputation(w, group="format", G=w["planned"])
def w_mediator_control(w):     return imputation(w, group="format", extra=w["y_n"])
def w_all_weeks_comparable(w): return imputation(w, group="format", comparable=False)
def n_gate_sqft_linear(w):     return imputation(w, group="format", gate_mode="sqft")
def n_kit_week_fe(w):          return imputation(w, group="kit")
def n_gate_by_format(w):       return imputation(w, group="format", gate_mode="format")
def a_imp_format_kit_week(w):  return imputation(w, group="format_kit")

ACCEPTED = {"imp_format_week": a_imp_format_week, "cs_format_notyet": a_cs_format_notyet,
            "cs_format_never": a_cs_format_never, "imp_store_trend": a_imp_store_trend,
            "imp_format_kit_week": a_imp_format_kit_week, "cs_base_last": a_cs_base_last,
            "cs_base_e43": a_cs_base_e43}
WRONG = {"before_after": w_before_after, "house_twfe_basket": w_house_twfe_basket,
         "twfe_static_sales": w_twfe_static_sales, "twfe_event_ref_m1": w_twfe_event_ref_m1,
         "cs_gm1_pooled": w_cs_gm1_pooled, "imp_unconditional": w_imp_unconditional,
         "cs_unconditional": w_cs_unconditional, "outcome_basket": w_outcome_basket,
         "gate_pooled_installed": w_gate_pooled, "window_0_25": w_window_0_25,
         "planned_timing": w_planned_timing, "mediator_control": w_mediator_control,
         "all_weeks_comparable": w_all_weeks_comparable}
def x_window_0_25_trend(w):   return imputation(w, group="none", store_trend=True, window=(0, 25))
def x_window_0_25_cs(w):      return cs_store_did(w, window=(0, 25))
def x_kit_conditioning_cs(w): return cs_store_did(w, cond_on="kit")
def x_closures_in_window(w):  return imputation(w, group="format", window_comparable=False)
def x_gate_pooled_cs(w):      return cs_store_did(w, gate_mode="pooled")

VARIANTS_OF_WRONG = {"window_0_25_trend": x_window_0_25_trend, "window_0_25_cs": x_window_0_25_cs,
                     "kit_conditioning_cs": x_kit_conditioning_cs, "closures_in_window_only": x_closures_in_window,
                     "gate_pooled_cs": x_gate_pooled_cs}
UNDECIDED = {"gate_sqft_linear": n_gate_sqft_linear, "kit_week_fe": n_kit_week_fe, "gate_by_format": n_gate_by_format}
