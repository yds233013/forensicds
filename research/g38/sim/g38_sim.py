"""G38 simulation prototype: threshold-triggered Supplier Development Programme (SDP) + regression to the mean.

RESEARCH ONLY. No task, no candidate, no model.

DGP (monthly, t = 0..35; programme launch t = 24):
  alpha_i ~ N(mu, sa^2)                         persistent supplier defect propensity (log scale)
  u_it    = rho u_i,t-1 + eta_it                 transient supplier-specific shocks, stationary AR(1)
  s_t     = season * sin(2 pi t / 12)            fleet-wide seasonality
  lam0_it = exp(alpha_i + s_t + u_it)            latent untreated defect rate
  E_it    = E_i * exp(Enoise z)                  parts received;  E_i ~ logN(log Emed, Esd)
  D_it    ~ Poisson(E_it * lam_it),  lam = lam0 * (1 - delta_i) while enrolled
Trigger (operational policy, fixed): at the end of month t in 23..28, a not-yet-enrolled supplier whose rolling
3-month ppm exceeds 1,500 is enrolled from month t+1 (t0) for 6 months.
Truth (verifier only): Q1 = mean over enrollees of sum_{h<6} E (lam0 - lam1);  Q2 = sum E(lam0-lam1) / sum E lam0.

    python research/g38/sim/g38_sim.py [draws] [scale]
"""
from __future__ import annotations

import json, math, sys
from pathlib import Path

import numpy as np

T, LAUNCH, LAST_T0, HOR = 36, 24, 29, 6
TRIG, ROLLOUT = 1500e-6, 75.0
P_LAUNCH, P_LAST = 12, 17                  # pseudo-launch in the pre-programme era, 12 months earlier (same calendar)

BASE = dict(N=600, mu=math.log(600e-6), sa=0.55, rho=0.5, se=0.30, season=0.10,
            Emed=60000.0, Esd=1.0, Enoise=0.15, delta=0.25, dsd=0.08, L=3)
# regimes fixed BEFORE any method was scored (scientific axes, see fixtures.md)
FIX = {
    "visible":  dict(seed=11),
    "hidden_a": dict(seed=22, delta=0.00, se=0.40, rho=0.30),            # pure regression to the mean
    "hidden_b": dict(seed=33, delta=0.20, se=0.22, rho=0.80),            # persistent shocks
    "hidden_c": dict(seed=44, delta=0.30, sa=0.80, se=0.20),             # heterogeneity dominates, little RTM
    "hidden_d": dict(seed=55, delta=0.12, Emed=12000.0, Esd=1.3, season=0.20),  # small suppliers, strong season
}
SCALES = {  # top-design prototypes on the same simulator (top_designs.md)
    "R1_supplier": {},
    "R2_warehouse": dict(N=60, Emed=400000.0, Esd=0.5, mu=math.log(900e-6), sa=0.35),
    "R3_depot": dict(N=250, Emed=900000.0, Esd=0.4, mu=math.log(700e-6), sa=0.30),
}


def params(fx, scale="R1_supplier"):
    p = dict(BASE); p.update(SCALES[scale]); p.update(FIX[fx]); return p


# ------------------------------------------------------------------------------------------ generator
def draw(p, rng, exogenous=False):
    N, L = p["N"], p["L"]
    alpha = p["mu"] + p["sa"] * rng.standard_normal(N)
    vu = p["se"] ** 2 / (1 - p["rho"] ** 2)
    u = np.empty((N, T)); u[:, 0] = math.sqrt(vu) * rng.standard_normal(N)
    for t in range(1, T):
        u[:, t] = p["rho"] * u[:, t - 1] + p["se"] * rng.standard_normal(N)
    s = p["season"] * np.sin(2 * np.pi * np.arange(T) / 12)
    lam0 = np.exp(alpha[:, None] + s[None, :] + u)
    Ei = p["Emed"] * np.exp(p["Esd"] * rng.standard_normal(N))
    E = Ei[:, None] * np.exp(p["Enoise"] * rng.standard_normal((N, T)))
    D0 = rng.poisson(E * lam0)
    t0 = np.full(N, -1)
    if not exogenous:
        for t in range(LAUNCH - 1, LAST_T0):
            S = D0[:, t - L + 1:t + 1].sum(1) / E[:, t - L + 1:t + 1].sum(1)
            new = (t0 < 0) & (S > TRIG)
            t0[new] = t + 1
    else:  # ablation: same number of enrollees, timing and selection unrelated to outcomes
        n_enr = int(p.get("_n_enr", 60))
        who = rng.choice(N, n_enr, replace=False)
        t0[who] = rng.integers(LAUNCH, LAST_T0 + 1, n_enr)
    delta = np.clip(p["delta"] + p["dsd"] * rng.standard_normal(N), 0, 0.6) if p["delta"] > 0 else np.zeros(N)
    enrolled = np.zeros((N, T), bool)
    for i in np.where(t0 >= 0)[0]:
        enrolled[i, t0[i]:t0[i] + HOR] = True
    lam1 = np.where(enrolled, lam0 * (1 - delta[:, None]), lam0)
    D = np.where(enrolled, rng.poisson(E * lam1), D0)
    idx = np.where(t0 >= 0)[0]
    av = np.array([(E[i, t0[i]:t0[i] + HOR] * (lam0[i, t0[i]:t0[i] + HOR] - lam1[i, t0[i]:t0[i] + HOR])).sum() for i in idx])
    cf = np.array([(E[i, t0[i]:t0[i] + HOR] * lam0[i, t0[i]:t0[i] + HOR]).sum() for i in idx])
    truth = {"q1": float(av.mean()) if len(idx) else 0.0, "q2": float(av.sum() / cf.sum()) if len(idx) else 0.0,
             "n_enr": int(len(idx))}
    truth["decision"] = "expand" if truth["q1"] >= ROLLOUT else "hold"
    return dict(D=D, E=E, t0=t0, L=L), truth


# ------------------------------------------------------------------------------------------ helpers
def win(D, E, i, a, b):
    return D[i, a:b].sum(), E[i, a:b].sum()


def enr(X):
    return np.where(X["t0"] >= 0)[0]


def post(X):
    D, E, t0 = X["D"], X["E"], X["t0"]
    return np.array([D[i, t0[i]:t0[i] + HOR].sum() for i in enr(X)]), np.array([E[i, t0[i]:t0[i] + HOR].sum() for i in enr(X)])


def result(X, cf, dpost=None):
    dp = post(X)[0] if dpost is None else dpost
    av = cf - dp
    q1 = float(av.mean()); q2 = float(av.sum() / cf.sum())
    return {"q1": q1, "q2": q2, "decision": "expand" if q1 >= ROLLOUT else "hold"}


def season_index_totals(X, era=(0, LAUNCH)):
    D, E = X["D"][:, era[0]:era[1]], X["E"][:, era[0]:era[1]]
    tot = D.sum() / E.sum()
    return np.array([D[:, m::12].sum() / E[:, m::12].sum() / tot for m in range(12)])


def poisson_glm(Xm, y, off, iters=50):
    b = np.zeros(Xm.shape[1]); b[0] = math.log(max(y.sum(), 1) / np.exp(off).sum())
    for _ in range(iters):
        eta = Xm @ b + off; mu = np.exp(eta); W = mu
        z = eta - off + (y - mu) / mu
        A = Xm.T @ (W[:, None] * Xm); bn = np.linalg.solve(A + 1e-9 * np.eye(len(b)), Xm.T @ (W * z))
        if np.max(np.abs(bn - b)) < 1e-10:
            b = bn; break
        b = bn
    return b


# ------------------------------------------------------------------------------------------ V1: pseudo-episode calibration
def _episodes(X, t_lo, t_hi, first_only=True, idx_season=None):
    """Apply the SAME trigger rule inside [t_lo-1, t_hi-1]; return per-episode (S*, H*, post count, post expected offset)."""
    D, E, L = X["D"], X["E"], X["L"]; N = D.shape[0]; si = idx_season
    t0 = np.full(N, -1); rows = []
    for t in range(t_lo - 1, t_hi):
        S = D[:, t - L + 1:t + 1].sum(1) / E[:, t - L + 1:t + 1].sum(1)
        hit = (S > TRIG) & ((t0 < 0) if first_only else True)
        for i in np.where(hit)[0]:
            if first_only:
                t0[i] = t + 1
            rows.append((i, t + 1))
    return rows


def _feat(X, i, t0, si):
    D, E, L = X["D"], X["E"], X["L"]
    m = lambda a, b: (np.arange(a, b) % 12)
    Ss = D[i, t0 - L:t0].sum() / (E[i, t0 - L:t0] * si[m(t0 - L, t0)]).sum()
    Hs = (D[i, t0 - L - 6:t0 - L].sum() + 0.5) / (E[i, t0 - L - 6:t0 - L] * si[m(t0 - L - 6, t0 - L)]).sum()
    off = (E[i, t0:t0 + HOR] * si[m(t0, t0 + HOR)]).sum()
    return math.log(Ss), math.log(Hs), off


def V1_pseudo_episode(X, first_only=True, use_H=True, season=True):
    si = season_index_totals(X) if season else np.ones(12)
    rows = _episodes(X, P_LAUNCH, P_LAST, first_only)
    F = np.array([_feat(X, i, t0, si) for i, t0 in rows])
    y = np.array([X["D"][i, t0:t0 + HOR].sum() for i, t0 in rows], float)
    cols = [np.ones(len(F)), F[:, 0]] + ([F[:, 1]] if use_H else [])
    b = poisson_glm(np.column_stack(cols), y, np.log(F[:, 2]))
    Fr = np.array([_feat(X, i, X["t0"][i], si) for i in enr(X)])
    colr = [np.ones(len(Fr)), Fr[:, 0]] + ([Fr[:, 1]] if use_H else [])
    cf = Fr[:, 2] * np.exp(np.column_stack(colr) @ b)
    return result(X, cf)


# ------------------------------------------------------------------------------------------ V2: state-space / EB latent risk
def _hyper(X, era=(0, LAUNCH), rho_fixed=None, noise=True):
    D, E = X["D"][:, era[0]:era[1]].astype(float), X["E"][:, era[0]:era[1]]
    y = np.log((D + 0.5) / E); r = 1.0 / (D + 0.5) if noise else np.zeros_like(y)
    mu_m = np.array([y[:, m::12].mean() for m in range(12)])
    yc = y - mu_m[np.arange(era[0], era[1]) % 12][None, :]
    K = 6; C = [np.mean(yc * yc) - r.mean()] + [np.mean(yc[:, :-k] * yc[:, k:]) for k in range(1, K + 1)]
    best = None
    for rho in ([rho_fixed] if rho_fixed is not None else np.arange(0.0, 0.96, 0.01)):
        A = np.column_stack([np.ones(K + 1), rho ** np.arange(K + 1)]); A[0, 1] = 1.0
        if rho == 0:
            A[1:, 1] = 0.0
        v, *_ = np.linalg.lstsq(A, np.array(C), rcond=None); v = np.maximum(v, 1e-6)
        sse = float(np.sum((A @ v - C) ** 2))
        if best is None or sse < best[0]:
            best = (sse, rho, v[0], v[1])
    _, rho, va, vu = best
    return mu_m, rho, va, vu


def V2_state_space(X, rho_fixed=None, noise=True, season=True, hyper_era=(0, LAUNCH), include_post=False, h_shift=0):
    D, E, t0 = X["D"].astype(float), X["E"], X["t0"]
    mu_m, rho, va, vu = _hyper(X, hyper_era, rho_fixed, noise)
    if not season:
        mu_m = np.full(12, mu_m.mean())
    ve = vu * (1 - rho ** 2)
    ids = enr(X); cf = []
    for i in ids:
        m = np.zeros(2); P = np.diag([va, vu]); F = np.diag([1.0, rho]); Q = np.diag([0.0, ve])
        last = t0[i] + (HOR if include_post else 0)
        for t in range(0, last):
            if t > 0:
                m = F @ m; P = F @ P @ F.T + Q
            y = math.log((D[i, t] + 0.5) / E[i, t]) - mu_m[t % 12]
            r = 1.0 / (D[i, t] + 0.5) if noise else 1e-9
            Hv = np.array([1.0, 1.0]); S = Hv @ P @ Hv + r; Kg = P @ Hv / S
            m = m + Kg * (y - Hv @ m); P = P - np.outer(Kg, Hv @ P)
        c = 0.0
        for h in range(HOR):
            tt = t0[i] + h + h_shift
            k = max(tt - (last - 1), 0)
            a = np.array([1.0, rho ** k]); mean = a @ m + mu_m[tt % 12]
            var = a @ P @ a + ve * sum(rho ** (2 * j) for j in range(k))
            c += E[i, tt] * math.exp(mean + 0.5 * var)
        cf.append(c)
    cf = np.array(cf)
    if h_shift:
        dp = np.array([D[i, t0[i] + h_shift:t0[i] + h_shift + HOR].sum() for i in ids])
        return result(X, cf, dp)
    return result(X, cf)


# ------------------------------------------------------------------------------------------ legitimate variants
def L1_pseudo_S_only(X): return V1_pseudo_episode(X, use_H=False)
def L2_pseudo_all_crossings(X): return V1_pseudo_episode(X, first_only=False)


def L3_history_nn_match(X, k=5):
    """Nearest-neighbour matching (on log S*, log H*) against same-rule historical pseudo-episodes."""
    si = season_index_totals(X)
    rows = _episodes(X, P_LAUNCH, P_LAST, True)
    F = np.array([_feat(X, i, t0, si) for i, t0 in rows])
    rate = np.array([X["D"][i, t0:t0 + HOR].sum() for i, t0 in rows]) / F[:, 2]
    Fr = np.array([_feat(X, i, X["t0"][i], si) for i in enr(X)])
    sd = F[:, :2].std(0)
    cf = []
    for f in Fr:
        d = np.sqrt((((F[:, :2] - f[:2]) / sd) ** 2).sum(1)); nn = np.argsort(d)[:k]
        cf.append(f[2] * rate[nn].mean())
    return result(X, np.array(cf))


VALID = {"V1_pseudo_episode": V1_pseudo_episode, "V2_state_space": V2_state_space}
LEGIT = {"L1_pseudo_S_only": L1_pseudo_S_only, "L2_pseudo_all_crossings": L2_pseudo_all_crossings,
         "L3_history_nn_match": L3_history_nn_match}


# ------------------------------------------------------------------------------------------ wrong methods
def _rate_cf(X, a_fn, b_fn, season=False):
    D, E, t0 = X["D"], X["E"], X["t0"]; si = season_index_totals(X) if season else np.ones(12)
    out = []
    for i in enr(X):
        a, b = a_fn(t0[i]), b_fn(t0[i])
        r = D[i, a:b].sum() / (E[i, a:b] * si[np.arange(a, b) % 12]).sum()
        out.append(r * (E[i, t0[i]:t0[i] + HOR] * si[np.arange(t0[i], t0[i] + HOR) % 12]).sum())
    return np.array(out)


def _controls(X):
    return np.where(X["t0"] < 0)[0]


def W01_pre_post_trigger_window(X): return result(X, _rate_cf(X, lambda t: t - X["L"], lambda t: t))


def W02_dashboard_ppm_change(X):
    r = W01_pre_post_trigger_window(X)
    D, E, t0 = X["D"], X["E"], X["t0"]
    rel = [1 - (D[i, t0[i]:t0[i] + HOR].sum() / E[i, t0[i]:t0[i] + HOR].sum()) /
           (D[i, t0[i] - X["L"]:t0[i]].sum() / E[i, t0[i] - X["L"]:t0[i]].sum()) for i in enr(X)]
    r["q2"] = float(np.mean(rel)); return r


def W03_all_pre_mean(X): return result(X, _rate_cf(X, lambda t: 0, lambda t: t))
def W04_pre_mean_excluding_trigger(X): return result(X, _rate_cf(X, lambda t: 0, lambda t: t - X["L"]))
def W04b_pre_mean_excl_trigger_seasonal(X): return result(X, _rate_cf(X, lambda t: 0, lambda t: t - X["L"], season=True))


def _did(X, pre_a, pre_b):
    D, E, t0 = X["D"], X["E"], X["t0"]; c = _controls(X); out = []
    for i in enr(X):
        a, b = pre_a(t0[i]), pre_b(t0[i])
        ri = D[i, a:b].sum() / E[i, a:b].sum()
        rc_pre = D[c, a:b].sum() / E[c, a:b].sum(); rc_post = D[c, t0[i]:t0[i] + HOR].sum() / E[c, t0[i]:t0[i] + HOR].sum()
        out.append(ri * rc_post / rc_pre * E[i, t0[i]:t0[i] + HOR].sum())
    return result(X, np.array(out))


def W05_did_never_enrolled(X): return _did(X, lambda t: 0, lambda t: t)
def W06_event_study_ref_trigger_window(X): return _did(X, lambda t: t - X["L"], lambda t: t)
def W07_did_excluding_trigger_window(X): return _did(X, lambda t: 0, lambda t: t - X["L"])


def W08_match_trigger_value_contemporaneous(X, k=5):
    """Controls: never-enrolled suppliers whose rolling ppm at the same month is closest (necessarily below 1,500)."""
    D, E, t0, L = X["D"], X["E"], X["t0"], X["L"]; c = _controls(X); out = []
    for i in enr(X):
        a = t0[i] - L
        Sc = D[c, a:t0[i]].sum(1) / E[c, a:t0[i]].sum(1)
        nn = c[np.argsort(-Sc)[:k]]                     # highest-S untreated = closest to the treated
        ratio = (D[nn, t0[i]:t0[i] + HOR].sum() / E[nn, t0[i]:t0[i] + HOR].sum()) / (D[nn, a:t0[i]].sum() / E[nn, a:t0[i]].sum())
        Si = D[i, a:t0[i]].sum() / E[i, a:t0[i]].sum()
        out.append(Si * ratio * E[i, t0[i]:t0[i] + HOR].sum())
    return result(X, np.array(out))


def _hist_unit_months(X):
    """All pre-era supplier-months (not rule-selected) with full windows: (logS*, logH*, post rate, post offset). Cached."""
    if "_hum" in X:
        return X["_hum"]
    D, E, L = X["D"].astype(float), X["E"], X["L"]; si = season_index_totals(X); Es = E * si[np.arange(T) % 12][None, :]
    out = []
    for t0 in range(L + 6, LAUNCH - HOR + 1):
        S = D[:, t0 - L:t0].sum(1) / Es[:, t0 - L:t0].sum(1)
        Hh = (D[:, t0 - L - 6:t0 - L].sum(1) + 0.5) / Es[:, t0 - L - 6:t0 - L].sum(1)
        off = Es[:, t0:t0 + HOR].sum(1); pr = D[:, t0:t0 + HOR].sum(1) / off
        ok = S > 0
        out.append(np.column_stack([np.log(S[ok]), np.log(Hh[ok]), pr[ok], off[ok]]))
    X["_hum"] = np.vstack(out); return X["_hum"]


def W09_match_S_historical_any_month(X, k=10):
    H = _hist_unit_months(X); si = season_index_totals(X); out = []
    for i in enr(X):
        f = _feat(X, i, X["t0"][i], si); nn = np.argsort(np.abs(H[:, 0] - f[0]))[:k]
        out.append(f[2] * H[nn, 2].mean())
    return result(X, np.array(out))


def W10_match_H_only_historical(X, k=10):
    H = _hist_unit_months(X); si = season_index_totals(X); out = []
    for i in enr(X):
        f = _feat(X, i, X["t0"][i], si); nn = np.argsort(np.abs(H[:, 1] - f[1]))[:k]
        out.append(f[2] * H[nn, 2].mean())
    return result(X, np.array(out))


def W11_rd_extrapolation(X):
    """Regress log post rate on log S among never-enrolled suppliers at launch (all S < 1,500), extrapolate."""
    D, E, L = X["D"], X["E"], X["L"]; c = _controls(X); t = LAUNCH
    S = np.log((D[c, t - L:t].sum(1) + 0.5) / E[c, t - L:t].sum(1)); P = np.log((D[c, t:t + HOR].sum(1) + 0.5) / E[c, t:t + HOR].sum(1))
    b1, b0 = np.polyfit(S, P, 1); out = []
    for i in enr(X):
        ti = X["t0"][i]; Si = math.log(D[i, ti - L:ti].sum() / E[i, ti - L:ti].sum())
        out.append(math.exp(b0 + b1 * Si) * E[i, ti:ti + HOR].sum())
    return result(X, np.array(out))


def W12_raw_counts(X):
    D, t0 = X["D"], X["t0"]; return result(X, np.array([D[i, :t0[i]].mean() * HOR for i in enr(X)]))


def W13_q2_supplier_average(X):
    """Q2 as the unweighted mean of per-supplier relative reductions (contract pins a ratio of sums)."""
    cf = _v2_cf(X); r = result(X, cf); r["q2"] = float(np.mean(1 - post(X)[0] / cf)); return r


def _v2_cf(X):
    D, E, t0 = X["D"].astype(float), X["E"], X["t0"]; mu_m, rho, va, vu = _hyper(X); ve = vu * (1 - rho ** 2); out = []
    for i in enr(X):
        m = np.zeros(2); P = np.diag([va, vu]); F = np.diag([1.0, rho]); Q = np.diag([0.0, ve])
        for t in range(t0[i]):
            if t > 0:
                m = F @ m; P = F @ P @ F.T + Q
            y = math.log((D[i, t] + 0.5) / E[i, t]) - mu_m[t % 12]; r = 1 / (D[i, t] + 0.5)
            Hv = np.ones(2); S = Hv @ P @ Hv + r; Kg = P @ Hv / S; m = m + Kg * (y - Hv @ m); P = P - np.outer(Kg, Hv @ P)
        c = 0.0
        for h in range(HOR):
            k = h + 1; a = np.array([1.0, rho ** k])
            c += E[i, t0[i] + h] * math.exp(a @ m + mu_m[(t0[i] + h) % 12] + 0.5 * (a @ P @ a + ve * sum(rho ** (2 * j) for j in range(k))))
        out.append(c)
    return np.array(out)


def W14_v2_no_measurement_noise(X): return V2_state_space(X, noise=False)


def W15_population_mean_cf(X):
    D, E, t0 = X["D"], X["E"], X["t0"]; si = season_index_totals(X); rate = D[:, :LAUNCH].sum() / E[:, :LAUNCH].sum()
    return result(X, np.array([rate * (E[i, t0[i]:t0[i] + HOR] * si[np.arange(t0[i], t0[i] + HOR) % 12]).sum() for i in enr(X)]))


def W16_v2_no_seasonality(X): return V2_state_space(X, season=False)
def W17_wrong_time_zero(X): return V2_state_space(X, h_shift=-1)
def W18_future_info_filter(X): return V2_state_space(X, include_post=True)


def W20_treated_trend_extrapolation(X):
    D, E, t0 = X["D"], X["E"], X["t0"]; out = []
    for i in enr(X):
        tt = np.arange(t0[i] - 12, t0[i]); y = np.log((D[i, tt] + 0.5) / E[i, tt]); b1, b0 = np.polyfit(tt, y, 1)
        out.append(sum(E[i, t0[i] + h] * math.exp(b0 + b1 * (t0[i] + h)) for h in range(HOR)))
    return result(X, np.array(out))


def W21_v2_iid_transient(X): return V2_state_space(X, rho_fixed=0.0)
def W22_v1_no_seasonal_adjustment(X): return V1_pseudo_episode(X, season=False)


def W23_launch_cohort_only(X):
    """Uses only suppliers enrolled at launch (t0 = 24) and reports that as the programme ATT."""
    sub = dict(X); t0 = X["t0"].copy(); t0[t0 != LAUNCH] = -1; sub["t0"] = t0
    return V2_state_space(sub)


def W24_hyperparameters_from_all_months(X): return V2_state_space(X, hyper_era=(0, T))


def W26_v2_fixed_rho_half(X): return V2_state_space(X, rho_fixed=0.5)


def W27_v1_fit_all_unit_months(X):
    H = _hist_unit_months(X); si = season_index_totals(X)
    y = H[:, 2] * H[:, 3]; b = poisson_glm(np.column_stack([np.ones(len(H)), H[:, 0], H[:, 1]]), np.round(y), np.log(H[:, 3]))
    Fr = np.array([_feat(X, i, X["t0"][i], si) for i in enr(X)])
    return result(X, Fr[:, 2] * np.exp(b[0] + b[1] * Fr[:, 0] + b[2] * Fr[:, 1]))


def W28_pre_mean_excl_trigger_shrunk_to_fleet(X):
    """EB-style shrinkage of each supplier's pre-trigger rate toward the fleet rate (Poisson-gamma), no transient persistence."""
    D, E, t0 = X["D"], X["E"], X["t0"]; si = season_index_totals(X)
    pre_d = np.array([D[i, :t0[i] - X["L"]].sum() for i in enr(X)], float)
    pre_e = np.array([E[i, :t0[i] - X["L"]].sum() for i in enr(X)], float)
    allr = D[:, :LAUNCH].sum(1) / E[:, :LAUNCH].sum(1); m, v = allr.mean(), allr.var()
    a0 = m * m / max(v - m / E[:, :LAUNCH].sum(1).mean(), 1e-12); b0 = a0 / m
    rate = (a0 + pre_d) / (b0 + pre_e)
    return result(X, np.array([rate[k] * (E[i, t0[i]:t0[i] + HOR] * si[np.arange(t0[i], t0[i] + HOR) % 12]).sum() for k, i in enumerate(enr(X))]))


WRONG = {k: v for k, v in globals().items() if k.startswith("W") and k[1:3].isdigit() and callable(v)}
AMBIGUOUS = {"W09_match_S_historical_any_month", "W11_rd_extrapolation", "W27_v1_fit_all_unit_months"}  # labelled before scoring


# ------------------------------------------------------------------------------------------ runner
def run(draws, scale="R1_supplier", fixtures=None, methods=None):
    methods = methods or {**{k: ("valid", v) for k, v in VALID.items()}, **{k: ("legit", v) for k, v in LEGIT.items()},
                          **{k: ("ambiguous" if k in AMBIGUOUS else "wrong", v) for k, v in WRONG.items()}}
    res = {"scale": scale, "fixtures": {}, "methods": {m: {"kind": k, "fx": {}} for m, (k, _) in methods.items()}}
    for fx in (fixtures or FIX):
        p = params(fx, scale); rng = np.random.default_rng(p["seed"])
        err = {m: {"q1": [], "q2": []} for m in methods}; dec = {m: [] for m in methods}; truths = []
        for _ in range(draws):
            X, Tr = draw(p, rng); truths.append(Tr)
            if Tr["n_enr"] < 5:
                continue
            for m, (_, fn) in methods.items():
                try:
                    r = fn(X)
                except Exception:
                    r = {"q1": float("nan"), "q2": float("nan"), "decision": "error"}
                err[m]["q1"].append(r["q1"] - Tr["q1"]); err[m]["q2"].append(r["q2"] - Tr["q2"])
                dec[m].append(r["decision"] == Tr["decision"])
        ref = "V2_state_space"
        se = {q: float(np.sqrt(np.nanmean(np.square(err[ref][q])))) for q in ("q1", "q2")}
        q1s = np.array([t["q1"] for t in truths])
        res["fixtures"][fx] = {"params": {k: v for k, v in p.items() if not k.startswith("_")}, "se_ref": se,
                               "truth_q1_mean": float(q1s.mean()), "truth_q1_p05": float(np.percentile(q1s, 5)),
                               "truth_q1_p95": float(np.percentile(q1s, 95)),
                               "truth_q2_mean": float(np.mean([t["q2"] for t in truths])),
                               "n_enr_mean": float(np.mean([t["n_enr"] for t in truths])),
                               "expand_share": float(np.mean([t["decision"] == "expand" for t in truths]))}
        for m in methods:
            z = {q: np.abs(np.array(err[m][q])) / se[q] for q in ("q1", "q2")}
            res["methods"][m]["fx"][fx] = {
                "bias_se": {q: float(np.nanmean(err[m][q]) / se[q]) for q in ("q1", "q2")},
                "sd_se": {q: float(np.nanstd(err[m][q]) / se[q]) for q in ("q1", "q2")},
                "p01": {q: float(np.nanpercentile(z[q], 1)) for q in ("q1", "q2")},
                "p99": {q: float(np.nanpercentile(z[q], 99)) for q in ("q1", "q2")},
                "decision_correct": float(np.mean(dec[m]))}
    return res


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    scale = sys.argv[2] if len(sys.argv) > 2 else "R1_supplier"
    r = run(n, scale)
    Path(__file__).with_name("g38_%s.json" % scale).write_text(json.dumps(r, indent=1) + "\n")
    for fx, v in r["fixtures"].items():
        print("%-9s enrollees %.0f  truth Q1 %.1f [%.1f, %.1f]  Q2 %.3f  SE_REF %s  expand-share %.2f" % (
            fx, v["n_enr_mean"], v["truth_q1_mean"], v["truth_q1_p05"], v["truth_q1_p95"], v["truth_q2_mean"],
            {q: round(s, 4) for q, s in v["se_ref"].items()}, v["expand_share"]))
