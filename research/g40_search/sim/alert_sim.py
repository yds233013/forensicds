"""G40 Stage-2 minimal simulation: challenger fraud model at a fixed SIU investigation budget, evaluated on a
dual-frame stratified review sample (RESEARCH ONLY).

PRE-REGISTERED (same philosophy as G37-G39):
  SE_REF(q, regime) = RMSE of V1 (Horvitz-Thompson with union inclusion probabilities) vs latent population truth.
  VALID_BOUND = max over valid routes, regimes, quantities of p99(|err|/SE_REF).
  detect(m, regime) = max over quantities of p05(|err|/SE_REF);  WRONG_BOUND(m) = 2nd-largest detect over regimes.
  ratio = min_m WRONG_BOUND(m) / VALID_BOUND;  pass >= 3, prefer >= 5.
Graded quantities: recall@budget (incumbent, challenger), challenger precision@budget, recall gain (chal - inc).

    python research/g40_search/sim/alert_sim.py [draws]
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import numpy as np

K_FRAC = 0.015                                         # SIU capacity: 1.5 % of monthly claims
R1 = np.array([.01, .01, .01, .02, .02, .03, .05, .08, .15, .40])   # frame 1: incumbent-score deciles
R2 = np.array([0, 0, 0, 0, 0, 0, 0, .02, .10, .30])                  # frame 2: challenger-score deciles
REG = {  # regimes: genuine business variation
    "chal_better": dict(p=.04, fA=.6, inc=(3.0, .8), ch=(2.6, 2.6), N=60000),
    "chal_worse_at_top": dict(p=.04, fA=.8, inc=(3.4, .8), ch=(2.4, 2.4), N=60000),
    "low_fraud": dict(p=.02, fA=.6, inc=(3.0, .8), ch=(2.7, 2.7), N=60000),
    "similar_models": dict(p=.04, fA=.6, inc=(3.0, 1.6), ch=(2.9, 1.9), N=60000),
    "large_book": dict(p=.035, fA=.5, inc=(3.0, .9), ch=(2.6, 2.6), N=120000),
}
Q = ("rec_inc", "rec_ch", "prec_ch", "gain")


def world(rng, r):
    c = REG[r]; N = c["N"]
    y = rng.random(N) < c["p"]; typeA = rng.random(N) < c["fA"]
    zi = rng.standard_normal(N) + y * np.where(typeA, c["inc"][0], c["inc"][1])
    zc = rng.standard_normal(N) * 1.1 + y * np.where(typeA, c["ch"][0], c["ch"][1])
    si, sc = 1 / (1 + np.exp(-(zi - 2.5))), 1 / (1 + np.exp(-(zc - 3.0)))       # different calibrations
    b1 = np.minimum((np.argsort(np.argsort(si)) * 10) // N, 9); b2 = np.minimum((np.argsort(np.argsort(sc)) * 10) // N, 9)
    u1, u2 = rng.random(N) < R1[b1], rng.random(N) < R2[b2]
    lab = u1 | u2
    batch = np.where(u1, 1, np.where(u2, 2, 0))       # a claim sampled by both is logged once, under batch 1
    return dict(y=y, si=si, sc=sc, b1=b1, b2=b2, lab=lab, batch=batch, N=N)


def thr(s, K):
    return np.sort(s)[-K]


def truth(W):
    K = int(K_FRAC * W["N"]); y = W["y"]; out = {}
    ai, ac = W["si"] >= thr(W["si"], K), W["sc"] >= thr(W["sc"], K)
    out["rec_inc"] = (y & ai).sum() / y.sum(); out["rec_ch"] = (y & ac).sum() / y.sum()
    out["prec_ch"] = (y & ac).sum() / ac.sum(); out["gain"] = out["rec_ch"] - out["rec_inc"]
    return out


def _metrics(W, w, ai, ac, K=None, prec_denominator="K"):
    """Generic weighted estimator over labelled rows with weights w (0 for unlabelled)."""
    y = W["y"]
    fraud = (w * y).sum()
    tp_i, tp_c = (w * (y & ai)).sum(), (w * (y & ac)).sum()
    Kc = K if prec_denominator == "K" else (w * ac).sum()
    r = {"rec_inc": tp_i / fraud, "rec_ch": tp_c / fraud, "prec_ch": tp_c / Kc}
    r["gain"] = r["rec_ch"] - r["rec_inc"]; return r


def pi_union(W):
    return 1 - (1 - R1[W["b1"]]) * (1 - R2[W["b2"]])


def budget_alerts(W):
    K = int(K_FRAC * W["N"]); return W["si"] >= thr(W["si"], K), W["sc"] >= thr(W["sc"], K), K


# ------------------------------------------------------------------ valid routes
def V1_ht_union(W):
    ai, ac, K = budget_alerts(W); w = np.where(W["lab"], 1 / pi_union(W), 0); return _metrics(W, w, ai, ac, K)


def V2_poststratified_cells(W):
    """Post-stratify on the 10x10 (b1, b2) design cells: cell fraud rates from labelled rows x population cell counts."""
    ai, ac, K = budget_alerts(W); y = W["y"]; lab = W["lab"]
    fraud = tp_i = tp_c = 0.0
    cell = W["b1"] * 10 + W["b2"]
    for c in np.unique(cell):
        m = cell == c; ml = m & lab
        if ml.sum() == 0:
            continue
        Nc = m.sum()
        fraud += Nc * y[ml].mean()
        # alert status is known for every claim: split each cell by alert flag, estimate fraud rate within it
        for flag, acc in ((ai, "i"), (ac, "c")):
            ma = m & flag; mla = ma & lab
            if ma.sum() and mla.sum():
                v = ma.sum() * y[mla].mean()
                if acc == "i":
                    tp_i += v
                else:
                    tp_c += v
    r = {"rec_inc": tp_i / fraud, "rec_ch": tp_c / fraud, "prec_ch": tp_c / K}; r["gain"] = r["rec_ch"] - r["rec_inc"]; return r


def L1_hajek_precision(W):
    ai, ac, K = budget_alerts(W); w = np.where(W["lab"], 1 / pi_union(W), 0); return _metrics(W, w, ai, ac, K, prec_denominator="est")


VALID = {"V1_ht_union": V1_ht_union, "V2_poststratified_cells": V2_poststratified_cells, "L1_hajek_precision": L1_hajek_precision}


# ------------------------------------------------------------------ wrong objects (labelled before scoring)
def W01_unweighted(W):
    ai, ac, K = budget_alerts(W); return _metrics(W, W["lab"].astype(float), ai, ac, K, prec_denominator="est")


def W02_fixed_threshold_half(W):
    w = np.where(W["lab"], 1 / pi_union(W), 0); ai, ac = W["si"] >= .5, W["sc"] >= .5
    return _metrics(W, w, ai, ac, None, prec_denominator="est")


def W03_budget_in_sample_units(W):
    lab = W["lab"]; k = int(K_FRAC * lab.sum()); w = np.where(lab, 1 / pi_union(W), 0)
    ti, tc = np.sort(W["si"][lab])[-k], np.sort(W["sc"][lab])[-k]
    return _metrics(W, w, W["si"] >= ti, W["sc"] >= tc, None, prec_denominator="est")


def W04_frame1_weights_only(W):
    ai, ac, K = budget_alerts(W); w = np.where(W["lab"], 1 / R1[W["b1"]], 0); return _metrics(W, w, ai, ac, K)


def W05_logged_batch_weights(W):
    ai, ac, K = budget_alerts(W); w = np.where(W["batch"] == 1, 1 / R1[W["b1"]], np.where(W["batch"] == 2, 1 / R2[W["b2"]].clip(1e-9), 0))
    return _metrics(W, w, ai, ac, K)


def W06_sum_of_inverse_rates(W):
    ai, ac, K = budget_alerts(W)
    w = np.where(W["lab"], 1 / R1[W["b1"]] * (W["batch"] == 1) + np.where(R2[W["b2"]] > 0, 1 / np.maximum(R2[W["b2"]], 1e-9), 0) * (R2[W["b2"]] > 0), 0)
    return _metrics(W, w, ai, ac, K)


def W07_incumbent_threshold_for_both(W):
    K = int(K_FRAC * W["N"]); t = thr(W["si"], K); w = np.where(W["lab"], 1 / pi_union(W), 0)
    return _metrics(W, w, W["si"] >= t, W["sc"] >= t, None, prec_denominator="est")


def W08_mixed_weighting(W):
    ai, ac, K = budget_alerts(W); y = W["y"]; lab = W["lab"]; w = np.where(lab, 1 / pi_union(W), 0)
    fraud = (lab & y).sum()                             # unweighted denominator, weighted numerator
    r = {"rec_inc": (w * (y & ai)).sum() / fraud, "rec_ch": (w * (y & ac)).sum() / fraud, "prec_ch": (w * (y & ac)).sum() / K}
    r["gain"] = r["rec_ch"] - r["rec_inc"]; return r


def W09_top_decile_recall(W):
    w = np.where(W["lab"], 1 / pi_union(W), 0); ai, ac = W["b1"] == 9, W["b2"] == 9
    return _metrics(W, w, ai, ac, None, prec_denominator="est")


def W10_bands_from_sample_quantiles(W):
    lab = W["lab"]; ai, ac, K = budget_alerts(W)
    qi = np.quantile(W["si"][lab], np.linspace(0, 1, 11)[1:-1]); qc = np.quantile(W["sc"][lab], np.linspace(0, 1, 11)[1:-1])
    b1, b2 = np.searchsorted(qi, W["si"]), np.searchsorted(qc, W["sc"])
    w = np.where(lab, 1 / (1 - (1 - R1[b1]) * (1 - R2[b2])), 0); return _metrics(W, w, ai, ac, K)


def W11_each_model_on_own_frame(W):
    ai, ac, K = budget_alerts(W); y = W["y"]
    w1 = np.where(W["batch"] == 1, 1 / R1[W["b1"]], 0); w2 = np.where(W["batch"] == 2, 1 / np.maximum(R2[W["b2"]], 1e-9), 0)
    ri = (w1 * (y & ai)).sum() / (w1 * y).sum(); rc = (w2 * (y & ac)).sum() / max((w2 * y).sum(), 1e-9)
    return {"rec_inc": ri, "rec_ch": rc, "prec_ch": (w2 * (y & ac)).sum() / K, "gain": rc - ri}


def W12_precision_from_unweighted_alert_rows(W):
    r = V1_ht_union(W); ai, ac, K = budget_alerts(W); lab = W["lab"]; y = W["y"]
    r["prec_ch"] = (y & ac & lab).sum() / max((ac & lab).sum(), 1); return r


WRONG = {k: v for k, v in globals().items() if k.startswith("W") and k[1:3].isdigit() and callable(v)}


def main(draws=150):
    res = {"regimes": {}, "methods": {}}
    errs = {m: {r: {q: [] for q in Q} for r in REG} for m in list(VALID) + list(WRONG)}
    dec = {m: {r: [] for r in REG} for m in list(VALID) + list(WRONG)}
    for ri, r in enumerate(REG):
        rng = np.random.default_rng(4000 + ri); gains = []
        for _ in range(draws):
            W = world(rng, r); T = truth(W); gains.append(T["gain"])
            for m, fn in list(VALID.items()) + list(WRONG.items()):
                e = fn(W)
                for q in Q:
                    errs[m][r][q].append(e[q] - T[q])
                dec[m][r].append((e["gain"] >= .02) == (T["gain"] >= .02))
        res["regimes"][r] = {"truth_gain_mean": float(np.mean(gains)), "truth_gain_sd": float(np.std(gains)),
                             "labelled_n_example": int(W["lab"].sum())}
    se = {r: {q: float(np.sqrt(np.mean(np.square(errs["V1_ht_union"][r][q])))) for q in Q} for r in REG}
    for m in errs:
        z = {r: {q: np.abs(np.array(errs[m][r][q])) / se[r][q] for q in Q} for r in REG}
        res["methods"][m] = {"kind": "valid" if m in VALID else "wrong",
                             "p99": max(float(np.percentile(z[r][q], 99)) for r in REG for q in Q),
                             "detect": {r: max(float(np.percentile(z[r][q], 5)) for q in Q) for r in REG},
                             "bias_se": {r: {q: float(np.mean(errs[m][r][q]) / se[r][q]) for q in Q} for r in REG},
                             "decision_correct": {r: float(np.mean(dec[m][r])) for r in REG}}
    VB = max(v["p99"] for v in res["methods"].values() if v["kind"] == "valid")
    wb = {m: sorted(v["detect"].values(), reverse=True)[1] for m, v in res["methods"].items() if v["kind"] == "wrong"}
    hard = min(wb, key=wb.get)
    res.update(se_ref=se, VALID_BOUND=VB, WRONG_BOUND=wb[hard], hardest=hard, ratio=wb[hard] / VB, wrong_bound=wb)
    print("SE_REF:", {r: {q: round(v, 4) for q, v in d.items()} for r, d in se.items()})
    print("truth gain by regime:", {r: round(v["truth_gain_mean"], 3) for r, v in res["regimes"].items()})
    for m, v in res["methods"].items():
        if v["kind"] == "valid":
            print("  VALID %-28s p99 %.2f" % (m, v["p99"]))
    print("VALID_BOUND %.2f  WRONG_BOUND %.2f (%s)  ratio %.2f" % (VB, wb[hard], hard, wb[hard] / VB))
    for m in sorted(wb, key=wb.get):
        v = res["methods"][m]
        print("  %-40s WB %7.2f  detect %s  dec %s" % (m, wb[m], " ".join("%.1f" % x for x in v["detect"].values()),
              " ".join("%.0f" % (100 * x) for x in v["decision_correct"].values())))
    Path(__file__).with_name("alert_results.json").write_text(json.dumps(res, indent=1) + "\n")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 150)
