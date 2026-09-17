"""G05 v2 Phase-0 generator: staggered SCO 2.0 rollout, store x week panel, potential outcomes (research only).

Arrays are S x T. Weeks are indexed 0..T-1. G = actual go-live week index (np.inf when not installed in the panel).
"""
from __future__ import annotations

import copy

import numpy as np

FORMATS = ("supercentre", "market", "neighbourhood")
KITS = ("full", "compact")

BASE = {
    "n_stores": 900,
    "T": 156,
    "format_share": (0.20, 0.35, 0.45),
    "sqft_range": {"supercentre": (60, 110), "market": (25, 50), "neighbourhood": (10, 30)},   # thousand sq ft
    # kit version is set by floor layout (a rear bagging bay for the big-basket lane), not by size
    "full_kit_prob": {"supercentre": 1.00, "market": 0.75, "neighbourhood": 0.25},
    # wave assignment probabilities by format and kit: W1..W4 installed in panel, last = remaining programme
    "wave_probs": {"supercentre|full": (0.33, 0.22, 0.15, 0.10, 0.20),
                   "market|full": (0.20, 0.25, 0.20, 0.15, 0.20),
                   "market|compact": (0.05, 0.10, 0.15, 0.25, 0.45),
                   "neighbourhood|full": (0.10, 0.15, 0.20, 0.20, 0.35),
                   "neighbourhood|compact": (0.02, 0.04, 0.08, 0.16, 0.70)},
    "planned_week": (76, 86, 96, 106),
    "slip_rate": 0.20, "slip_max": 4,
    # untreated secular trends (log points per year) by format, common seasonality amplitude
    "trend_per_year": {"supercentre": 0.060, "market": 0.010, "neighbourhood": -0.010},
    "season_amp": 0.06,
    # effects at plateau (log points): basket and transactions by kit
    "basket_effect": {"full": 0.070, "compact": 0.012},
    "txn_effect": {"full": -0.020, "compact": -0.015},
    "effect_sd": 0.25,          # lognormal store multiplier sd (independent of covariates)
    "ramp_scale": 10.0,         # weeks
    # noise
    "sd_txn": 0.014, "sd_basket": 0.010, "ar": 0.5,
    # closures
    "install_week_probs": (0.70, 0.20, 0.10),     # e=-1 only, e=-2 only, both
    "install_hours": (14, 28), "trading_hours_week": 98.0,
    "other_closure_rate": 0.03, "other_hours": (7, 28),
    "gate": 0.025,
    "rr_window": (12, 25),
}

REGIMES = {
    "visible": {},
    "compact_works": {"basket_effect": {"full": 0.070, "compact": 0.060}},
    "reversed_trends": {"trend_per_year": {"supercentre": -0.045, "market": 0.000, "neighbourhood": 0.020},
                        "ramp_scale": 14.0},
    "slip_dip2": {"slip_rate": 0.32, "basket_effect": {"full": 0.070, "compact": 0.050},
                  "install_week_probs": (0.20, 0.65, 0.15)},
}


def regime(name: str) -> dict:
    spec = copy.deepcopy(BASE)
    for k, v in REGIMES[name].items():
        spec[k] = v
    spec["name"] = name
    return spec


def _ar1(rng, S, T, sd, phi):
    e = np.empty((S, T))
    e[:, 0] = rng.normal(0, sd, S)
    inn = rng.normal(0, sd * np.sqrt(1 - phi ** 2), (S, T))
    for t in range(1, T):
        e[:, t] = phi * e[:, t - 1] + inn[:, t]
    return e


def draw_world(spec: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    S, T = spec["n_stores"], spec["T"]
    fmt = rng.choice(3, size=S, p=spec["format_share"])
    sqft = np.array([rng.uniform(*spec["sqft_range"][FORMATS[f]]) for f in fmt])
    kit = np.where(rng.random(S) < np.array([spec["full_kit_prob"][FORMATS[f]] for f in fmt]), 0, 1)  # 0 full
    wave = np.array([rng.choice(5, p=spec["wave_probs"][f"{FORMATS[f]}|{KITS[k]}"]) for f, k in zip(fmt, kit)])
    planned = np.where(wave < 4, np.array(spec["planned_week"] + (10 ** 6,))[wave], np.inf).astype(float)
    slip = np.where((wave < 4) & (rng.random(S) < spec["slip_rate"]), rng.integers(1, spec["slip_max"] + 1, S), 0)
    G = planned + slip
    t = np.arange(T)
    e = t[None, :] - G[:, None]                                 # -inf for remaining stores
    treated = e >= 0

    # effects
    m = np.exp(rng.normal(-spec["effect_sd"] ** 2 / 2, spec["effect_sd"], S))
    ramp = np.where(treated, 1 - np.exp(-(np.where(treated, e, 0) + 1) / spec["ramp_scale"]), 0.0)
    A_b = np.array([spec["basket_effect"][KITS[k]] for k in kit])
    A_n = np.array([spec["txn_effect"][KITS[k]] for k in kit])
    tau_b = (A_b * m)[:, None] * ramp
    tau_n = (A_n * m)[:, None] * ramp

    # untreated structure
    trend = np.array([spec["trend_per_year"][FORMATS[f]] for f in fmt])[:, None] * t[None, :] / 52.0
    season = spec["season_amp"] * np.sin(2 * np.pi * t / 52.0) + 0.03 * (np.isin(t % 52, (50, 51)))
    alpha_n = np.log(np.array([9000, 5000, 2600])[fmt] * rng.lognormal(0, 0.15, S))
    alpha_b = np.log(np.array([48, 38, 22])[fmt] * rng.lognormal(0, 0.08, S))
    eps_n = _ar1(rng, S, T, spec["sd_txn"], spec["ar"])
    eps_b = _ar1(rng, S, T, spec["sd_basket"], spec["ar"])

    # closures
    hours = np.zeros((S, T))
    install = np.zeros((S, T), bool)
    for s in np.where(wave < 4)[0]:
        g = int(G[s])
        u = rng.random()
        p1, p2, _ = spec["install_week_probs"]
        weeks = [g - 1] if u < p1 else ([g - 2] if u < p1 + p2 else [g - 1, g - 2])
        for w in weeks:
            hours[s, w] += rng.uniform(*spec["install_hours"])
            install[s, w] = True
    other = rng.random((S, T)) < spec["other_closure_rate"]
    hours = hours + np.where(other, rng.uniform(*spec["other_hours"], (S, T)), 0.0)
    comparable = hours == 0
    open_frac = 1 - hours / spec["trading_hours_week"]
    closure_n = np.log(open_frac)
    closure_b = np.where(hours > 0, -0.02, 0.0)

    y_n0 = alpha_n[:, None] + trend + season[None, :] + closure_n + eps_n
    y_b0 = alpha_b[:, None] + 0.5 * trend + 0.3 * season[None, :] + closure_b + eps_b
    y_n = y_n0 + tau_n
    y_b = y_b0 + tau_b
    y_s = y_n + y_b
    return dict(spec=spec, S=S, T=T, fmt=fmt, sqft=sqft, kit=kit, wave=wave, planned=planned, G=G, e=e,
                treated=treated, comparable=comparable, install=install, hours=hours,
                y_s=y_s, y_n=y_n, y_b=y_b, tau_s=tau_b + tau_n, tau_b=tau_b, tau_n=tau_n)


def window_mask(w, G=None, lo=None, hi=None, use_comparable=True):
    spec = w["spec"]
    lo = spec["rr_window"][0] if lo is None else lo
    hi = spec["rr_window"][1] if hi is None else hi
    G = w["G"] if G is None else G
    e = np.arange(w["T"])[None, :] - G[:, None]
    m = (e >= lo) & (e <= hi) & (w["wave"] < 4)[:, None]
    if use_comparable:
        m &= w["comparable"]
    return m


def aggregate(w, tau_hat, mask, gate_mode="kit", sqft_model=False):
    """Store run-rate effects -> wave effects, kit effects, pooled, gate."""
    cnt = mask.sum(1)
    inst = (w["wave"] < 4) & (cnt > 0)
    theta_s = np.where(inst, np.where(mask, tau_hat, 0).sum(1) / np.maximum(cnt, 1), np.nan)
    out = {"wave": {f"W{i + 1}": float(np.nanmean(theta_s[inst & (w['wave'] == i)])) for i in range(4)},
           "kit": {KITS[k]: float(np.nanmean(theta_s[inst & (w['kit'] == k)])) for k in (0, 1)},
           "pooled": float(np.nanmean(theta_s[inst]))}
    rem = w["wave"] == 4
    if gate_mode == "kit":
        pi = [np.mean(w["kit"][rem] == k) for k in (0, 1)]
        out["gate"] = pi[0] * out["kit"]["full"] + pi[1] * out["kit"]["compact"]
    elif gate_mode == "pooled":
        out["gate"] = out["pooled"]
    elif gate_mode == "format":
        th_f = [np.nanmean(theta_s[inst & (w["fmt"] == f)]) for f in range(3)]
        out["gate"] = float(sum(np.mean(w["fmt"][rem] == f) * th_f[f] for f in range(3)))
    elif gate_mode == "sqft":
        X = np.c_[np.ones(inst.sum()), w["sqft"][inst]]
        b = np.linalg.lstsq(X, theta_s[inst], rcond=None)[0]
        out["gate"] = float(np.mean(b[0] + b[1] * w["sqft"][rem]))
    out["theta_s"] = theta_s
    return out


def truth(w) -> dict:
    a = aggregate(w, w["tau_s"], window_mask(w))
    a.pop("theta_s")
    a["decision"] = "continue" if a["gate"] >= w["spec"]["gate"] else "stop"
    return a
