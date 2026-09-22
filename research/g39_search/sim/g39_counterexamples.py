"""G39 top-3 counterexample search (hybrid / locally reasonable alternatives), same worlds and statistics as
g39_sims.py. Each alternative's label ('wrong' or 'valid-alt') is fixed here BEFORE running.

    python research/g39_search/sim/g39_counterexamples.py [worlds]
"""
from __future__ import annotations

import json, math, sys
from pathlib import Path

import numpy as np

import g39_sims as G

X = {
    "C2_forecast_accuracy": {
        "X01_active_proxy_any_actual_gt0": ("wrong", lambda W: _c2_active_proxy(W)),
        "X02_mae_over_mean_actual": ("valid-alt", lambda W: _c2_mae_ratio(W)),
        "X03_volume_weighted_mape": ("valid-alt", lambda W: _c2_vw_mape(W)),
        "X04_winsorised_errors_cap_3x_actual": ("wrong", lambda W: _c2_winsor(W)),
        "X05_exclude_zero_forecast_rows": ("wrong", lambda W: _c2_nzf(W)),
        "X06_mean_of_store_wape": ("wrong", lambda W: _c2_store_mean(W)),
        "X07_drop_first_week": ("wrong", lambda W: _c2_drop_week(W)),
    },
    "B3_dc_power_headroom": {
        "X01_round_down_to_12kW_rack_increments": ("wrong", lambda W: {"headroom": float(sum(max(0, math.floor((G._b3_usable(h) - h["peak"] - h["reserved"]) / 12) * 12) for h in W["halls"]))}),
        "X02_pf_applied_twice": ("wrong", lambda W: {"headroom": float(sum(max(0, G._b3_usable(h) * h["pf"] - h["peak"] - h["reserved"]) for h in W["halls"]))}),
        "X03_reserved_half_counted": ("wrong", lambda W: {"headroom": float(sum(max(0, G._b3_usable(h) - h["peak"] - .5 * h["reserved"]) for h in W["halls"]))}),
        "X04_peak_minus_10pct_safety_on_usable": ("wrong", lambda W: {"headroom": float(sum(max(0, .9 * G._b3_usable(h) - h["peak"] - h["reserved"]) for h in W["halls"]))}),
        "X05_mean_of_avg_and_peak": ("wrong", lambda W: {"headroom": float(sum(max(0, G._b3_usable(h) - .5 * (h["avg"] + h["peak"]) - h["reserved"]) for h in W["halls"]))}),
    },
    "A4_cloud_commitment": {
        "X01_pooled_then_split_by_share": ("wrong", lambda W: _a4_pool_split(W)),
        "X02_ceil_vs_floor_quantile_rounding": ("valid-alt", lambda W: _a4_quantile(W)),
        "X03_include_sunk_existing_in_cost": ("valid-alt", lambda W: {"cores": float(sum(G._a4_brute(G._a4_resid(W, g), W) for g in range(2)))}),
        "X04_p75_usage_rule_of_thumb": ("wrong", lambda W: {"cores": float(sum(round(np.percentile(G._a4_resid(W, g), 75) / 2) for g in range(2)))}),
        "X05_weekday_only_profile": ("wrong", lambda W: {"cores": float(sum(G._a4_marginal(_a4_weekday(W, g), W) for g in range(2)))}),
    },
}


def _c2_mask(W):
    return ~W["disc"]


def _c2_active_proxy(W):
    a = W["A"].sum((1, 2)) > 0; A, F = W["A"][a], W["F"][a]; return {"acc": float(1 - np.abs(F - A).sum() / A.sum())}


def _c2_mae_ratio(W):
    a = _c2_mask(W); A, F = W["A"][a], W["F"][a]; return {"acc": float(1 - np.mean(np.abs(F - A)) / np.mean(A))}


def _c2_vw_mape(W):
    a = _c2_mask(W); A, F = W["A"][a], W["F"][a]; m = A > 0
    num = (A[m] * np.abs(F[m] - A[m]) / A[m]).sum() + np.abs(F[~m] - A[~m]).sum()
    return {"acc": float(1 - num / A.sum())}


def _c2_winsor(W):
    a = _c2_mask(W); A, F = W["A"][a], W["F"][a]; e = np.minimum(np.abs(F - A), 3 * np.maximum(A, 1))
    return {"acc": float(1 - e.sum() / A.sum())}


def _c2_nzf(W):
    a = _c2_mask(W); A, F = W["A"][a], W["F"][a]; m = F > 0.5; return {"acc": float(1 - np.abs(F[m] - A[m]).sum() / A[m].sum())}


def _c2_store_mean(W):
    a = _c2_mask(W); A, F = W["A"][a], W["F"][a]
    return {"acc": float(1 - np.mean([np.abs(F[:, s] - A[:, s]).sum() / A[:, s].sum() for s in range(A.shape[1])]))}


def _c2_drop_week(W):
    a = _c2_mask(W); A, F = W["A"][a][:, :, 1:], W["F"][a][:, :, 1:]; return {"acc": float(1 - np.abs(F - A).sum() / A.sum())}


def _a4_pool_split(W):
    Q = G._a4_marginal(G._a4_resid(W, 0) + G._a4_resid(W, 1), W)
    s = np.array([G._a4_resid(W, g).mean() for g in range(2)]); return {"cores": float(np.round(Q * s / s.sum()).sum())}


def _a4_quantile(W):
    tot = 0
    for g in range(2):
        r = G._a4_resid(W, g); q = np.quantile(r, 1 - W["pc"] / W["od"]); tot += int(math.ceil(q / 2))
    return {"cores": float(tot)}


def _a4_weekday(W, g):
    r = G._a4_resid(W, g); keep = ((np.arange(len(r)) // 24) % 7) < 5; return r[keep]


def main(worlds=60):
    out = {}
    for ci, (name, C) in enumerate(G.CONCEPTS.items()):
        if name not in X:
            continue
        V1 = list(C["valid"].values())[0]; errs = {m: {r: [] for r in C["regimes"]} for m in X[name]}
        for ri, r in enumerate(C["regimes"]):
            rng = np.random.default_rng(1000 * ci + ri)             # SAME worlds as g39_sims.py
            for _ in range(worlds):
                W = C["gen"](rng, r); T = V1(W)
                sc = {q: (C["scale"](W, T) if "scale" in C else abs(T[q])) or 1e-12 for q in C["q"]}
                for m, (_, fn) in X[name].items():
                    errs[m][r].append(max(abs(fn(W)[q] - T[q]) / sc[q] for q in C["q"]))
        res = {}
        for m, (kind, _) in X[name].items():
            det = {r: float(np.percentile(errs[m][r], 5)) for r in C["regimes"]}
            med = {r: float(np.median(errs[m][r])) for r in C["regimes"]}
            p99 = float(np.percentile(np.concatenate([errs[m][r] for r in C["regimes"]]), 99))
            res[m] = {"kind": kind, "detect_p05": det, "median": med, "p99": p99,
                      "wrong_bound": sorted(det.values(), reverse=True)[1],
                      "coincidence": float(np.mean(np.concatenate([np.array(errs[m][r]) <= G.TOL for r in C["regimes"]])))}
            print("%-22s %-44s %-9s WB %.4f  p99 %.4f  coin %.2f  med %s" % (name[:22], m, kind, res[m]["wrong_bound"], p99, res[m]["coincidence"],
                  " ".join("%.3f" % v for v in med.values())))
        out[name] = res
    Path(__file__).with_name("g39_counterexamples.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 60)
