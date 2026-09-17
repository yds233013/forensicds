"""Imputation estimator for a staggered rollout.

Untreated-outcome model: log net sales = store effect + format-by-week effect, fitted on comparable store-weeks that
are not yet (or never) live. Store effects over the run-rate weeks are averaged per wave and per kit version; the
continuation-gate figure reweights kit-version effects to the kit mix of the stores still to be installed.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

RUN_RATE = (12, 25)          # weeks 13-26 after go-live, go-live week = week 1
ITERS = 80


def _arrays(p: pd.DataFrame, tables: dict) -> dict:
    stores = sorted(p["store_id"].unique())
    weeks = sorted(p["week_start"].unique())
    si = {s: i for i, s in enumerate(stores)}
    wi = {w: i for i, w in enumerate(weeks)}
    S, T = len(stores), len(weeks)
    r, c = p["store_id"].map(si).to_numpy(), p["week_start"].map(wi).to_numpy()
    y = np.full((S, T), np.nan); y[r, c] = p["log_net_sales"].to_numpy()
    comp = np.zeros((S, T), bool); comp[r, c] = p["comparable"].to_numpy() == 1
    ev = np.full((S, T), np.nan); ev[r, c] = p["event_week"].astype("float").to_numpy()
    fmt_map = dict(zip(tables["stores"]["store_id"], tables["stores"]["format"]))
    formats = sorted(set(fmt_map.values()))
    fmt = np.array([formats.index(fmt_map[s]) for s in stores])
    live = dict(zip(tables["go"]["store_id"], tables["go"]["kit"]))
    planned = dict(zip(tables["plan"]["store_id"], tables["plan"]["planned_kit"]))
    wave = dict(zip(tables["plan"]["store_id"], tables["plan"]["wave"]))
    installed = np.array([s in live for s in stores])
    kit = np.array([live.get(s, planned.get(s)) for s in stores])
    return dict(stores=stores, S=S, T=T, y=y, comp=comp, ev=ev, fmt=fmt, n_fmt=len(formats), installed=installed,
                kit=kit, wave=np.array([wave[s] for s in stores]))


def _fit(a: dict, wts: np.ndarray) -> np.ndarray:
    """Weighted alternating projections for y = alpha_s + lambda_{format, t} on untreated comparable cells."""
    y, S, T = a["y"], a["S"], a["T"]
    untreated = a["comp"] & ~(a["ev"] >= 0) & ~np.isnan(y)
    W = untreated * wts[:, None]
    yz = np.where(untreated, y, 0.0)
    alpha = np.zeros(S)
    lam = np.zeros((a["n_fmt"], T))
    ws = np.maximum(W.sum(1), 1e-12)
    for _ in range(ITERS):
        alpha = (W * (yz - lam[a["fmt"]])).sum(1) / ws
        num = np.zeros((a["n_fmt"], T)); den = np.zeros((a["n_fmt"], T))
        np.add.at(num, a["fmt"], W * (yz - alpha[:, None]))
        np.add.at(den, a["fmt"], W)
        lam = num / np.maximum(den, 1e-12)
    return alpha[:, None] + lam[a["fmt"]]


def _effects(a: dict, wts: np.ndarray) -> dict:
    tau = a["y"] - _fit(a, wts)
    lo, hi = RUN_RATE
    win = a["comp"] & (a["ev"] >= lo) & (a["ev"] <= hi) & a["installed"][:, None]
    cnt = win.sum(1)
    theta = np.where(cnt > 0, np.where(win, tau, 0.0).sum(1) / np.maximum(cnt, 1), np.nan)
    ok = a["installed"] & (cnt > 0)
    def wmean(mask):
        m = mask & ok
        return float((theta[m] * wts[m]).sum() / wts[m].sum())
    waves = {str(int(w)): wmean(a["wave"] == w) for w in sorted(set(a["wave"][ok]))}
    kits = {k: wmean(a["kit"] == k) for k in ("full", "compact")}
    remaining = ~a["installed"]
    share_full = float(np.mean(a["kit"][remaining] == "full"))
    gate = share_full * kits["full"] + (1 - share_full) * kits["compact"]
    return {"waves": waves, "gate": gate}


def estimate(p: pd.DataFrame, tables: dict, reps: int = 99, seed: int = 20260914) -> dict:
    a = _arrays(p, tables)
    point = _effects(a, np.ones(a["S"]))
    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(reps):
        wts = np.zeros(a["S"])
        for f in range(a["n_fmt"]):                    # resample stores within format
            idx = np.flatnonzero(a["fmt"] == f)
            np.add.at(wts, rng.choice(idx, size=len(idx), replace=True), 1.0)
        boots.append(_effects(a, wts))
    def ci(est, draws):
        se = float(np.std(draws, ddof=1))
        return {"estimate": est, "ci_low": est - 1.96 * se, "ci_high": est + 1.96 * se}
    return {
        "effect_by_wave": {w: ci(v, [b["waves"][w] for b in boots]) for w, v in point["waves"].items()},
        "gate_effect": ci(point["gate"], [b["gate"] for b in boots]),
    }
