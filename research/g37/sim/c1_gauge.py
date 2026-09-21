"""G37 C1 simulation prototype: in-line thickness gauge replacement, latent Ppk.

RESEARCH ONLY. No task, no candidate, no model. Everything is Monte-Carlo over the design below.

Reference scale: X = thickness the contractual contact method reports without random error.
  old gauge (contact, reference method):  O = X + e_o,                e_o ~ N(0, s_o^2)
  new station (laser, dual scan):        N_k = NOM + c + b (X - NOM) + e_nk,  e_nk ~ N(0, s_n^2), k = 1, 2
                                          reported production value = (N_1 + N_2) / 2
  vendor block certificate: steel blocks read correctly (slope 1, offset 0) with SD s_blk < s_n; the
  laser does NOT treat coated parts like steel blocks (non-commutable), so blocks do not identify c, b.

Evidence the analyst would see (one extract):
  pre_production  : coil_id, reading (old gauge, one reading per part) + check re-measure on every 5th part
  parallel_run    : part_id, coil_id, old reading, new scan 1, new scan 2   (2 coils, commissioning)
  post_production : coil_id, station value (mean of two scans)
  vendor_blocks   : block nominal, 10 readings each on the new station
Truth (verifier only): finite population over the coils actually produced in each window.

    python research/g37/sim/c1_gauge.py [draws]
"""
from __future__ import annotations

import json, math, sys
from pathlib import Path

import numpy as np

LSL, USL, NOM, GATE = 2.440, 2.560, 2.500, 1.33
DESIGN = dict(n_lots=40, per_lot=40, check_every=5, n_par=3000, par_lots=2,
              blocks=(2.40, 2.50, 2.60), blk_reps=10, s_blk=0.0035)

# Regimes chosen for SCIENTIFIC contrast, written before any method was scored (see design_log in README).
FIX = {
    # gauge noisier and expands scale, reads high; process unchanged and capable
    "visible":  dict(seed=101, mu_pre=2.500, om_pre=.0100, ta_pre=.0070,
                     mu_post=2.503, om_post=.0100, ta_post=.0070, c=+.012, b=1.12, s_o=.0060, s_n=.0090),
    # process genuinely deteriorated; new gauge quieter and compresses scale
    "hidden_a": dict(seed=202, mu_pre=2.500, om_pre=.0100, ta_pre=.0070,
                     mu_post=2.508, om_post=.0120, ta_post=.0110, c=-.008, b=0.90, s_o=.0060, s_n=.0050),
    # process unchanged; very noisy new gauge, mild scale, reads low
    "hidden_b": dict(seed=303, mu_pre=2.500, om_pre=.0095, ta_pre=.0065,
                     mu_post=2.500, om_post=.0095, ta_post=.0065, c=-.015, b=1.06, s_o=.0050, s_n=.0120),
    # process re-centred toward USL (mean-limited); strong scale expansion
    "hidden_c": dict(seed=404, mu_pre=2.500, om_pre=.0090, ta_pre=.0060,
                     mu_post=2.522, om_post=.0090, ta_post=.0060, c=+.004, b=1.15, s_o=.0070, s_n=.0080),
    # process deteriorated and shifted low; gauge compresses, reads high
    "hidden_d": dict(seed=505, mu_pre=2.500, om_pre=.0100, ta_pre=.0070,
                     mu_post=2.495, om_post=.0130, ta_post=.0100, c=+.010, b=0.93, s_o=.0055, s_n=.0070),
}
QUANT = ("mean_post", "sd_post", "ppk_post", "sd_pre")


def ppk(mu, sd):
    return min(USL - mu, mu - LSL) / (3 * sd) if sd > 0 else float("nan")


# ------------------------------------------------------------------------------------ generator
def draw(f, rng):
    d = DESIGN
    L, P = d["n_lots"], d["per_lot"]
    z_pre = rng.standard_normal(L) * f["ta_pre"]
    z_post = rng.standard_normal(L) * f["ta_post"]
    X_pre = f["mu_pre"] + np.repeat(z_pre, P) + rng.standard_normal(L * P) * f["om_pre"]
    Pp = d.get("post_per_lot", P)
    X_post = f["mu_post"] + np.repeat(z_post, Pp) + rng.standard_normal(L * Pp) * f["om_post"]
    coil_pre, coil_post = np.repeat(np.arange(L), P), np.repeat(np.arange(L), Pp)
    O_pre = X_pre + rng.standard_normal(L * P) * f["s_o"]
    chk = np.arange(L * P) % d["check_every"] == 0
    O_chk = X_pre[chk] + rng.standard_normal(chk.sum()) * f["s_o"]

    def new(x, k):
        return (NOM + f["c"] + f["b"] * (x - NOM))[:, None] + rng.standard_normal((len(x), k)) * f["s_n"]
    N_post = new(X_post, 2).mean(axis=1)
    zb = rng.standard_normal(d["par_lots"]) * f["ta_pre"]
    npl = d["n_par"] // d["par_lots"]
    X_par = f["mu_pre"] + np.repeat(zb, npl) + rng.standard_normal(npl * d["par_lots"]) * f["om_pre"]
    O_par = X_par + rng.standard_normal(len(X_par)) * f["s_o"]
    N_par = new(X_par, 2)
    blk = np.array([[b + rng.standard_normal() * d["s_blk"] for _ in range(d["blk_reps"])] for b in d["blocks"]])
    truth = {"mean_post": f["mu_post"] + z_post.mean(),
             "sd_post": math.sqrt(f["om_post"] ** 2 + z_post.var()),
             "sd_pre": math.sqrt(f["om_pre"] ** 2 + z_pre.var())}
    truth["ppk_post"] = ppk(truth["mean_post"], truth["sd_post"])
    data = dict(O_pre=O_pre, coil_pre=coil_pre, chk_idx=np.where(chk)[0], O_chk=O_chk,
                N_post=N_post, coil_post=coil_post, O_par=O_par, N_par=N_par, blk=blk)
    return data, truth


# ------------------------------------------------------------------------------------ building blocks
def s2_old_checks(D):             # repeatability of the old gauge from check re-measures
    d = D["O_pre"][D["chk_idx"]] - D["O_chk"]
    return float(np.mean(d ** 2) / 2)


def s2_new_dual(D):                # per-scan repeatability of the new station from dual scans
    d = D["N_par"][:, 0] - D["N_par"][:, 1]
    return float(np.mean((d - d.mean()) ** 2) / 2)


def moments(D):
    o, n = D["O_par"], D["N_par"].mean(axis=1)
    return o, n, float(np.var(o, ddof=1)), float(np.var(n, ddof=1)), float(np.cov(o, n)[0, 1])


def out(D, a, b, s2n_scan, s2o, mean_fn=None, sd_post=None, sd_pre=None):
    Np, Op = D["N_post"], D["O_pre"]
    mu = (Np.mean() - a) / b if mean_fn is None else mean_fn
    v = (np.var(Np, ddof=1) - s2n_scan / 2) / b ** 2          # production value = mean of 2 scans
    sd = math.sqrt(max(v, 1e-12)) if sd_post is None else sd_post
    sdp = math.sqrt(max(np.var(Op, ddof=1) - s2o, 1e-12)) if sd_pre is None else sd_pre
    return {"mean_post": float(mu), "sd_post": float(sd), "ppk_post": ppk(mu, sd), "sd_pre": float(sdp)}


def deming(sxx, syy, sxy, delta):
    """Deming slope, delta = var(error in y) / var(error in x)."""
    t = syy - delta * sxx
    return (t + math.sqrt(t * t + 4 * delta * sxy * sxy)) / (2 * sxy)


# ------------------------------------------------------------------------------------ VALID families
def F1_deming(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D)
    o, n, sxx, syy, sxy = moments(D)
    b = deming(sxx, syy, sxy, (s2n / 2) / s2o)
    a = n.mean() - b * o.mean()
    return out(D, a, b, s2n, s2o)


def F2_attenuation_corrected(D):
    s2o = s2_old_checks(D)
    s2n = s2_new_dual(D)
    o, n, sxx, syy, sxy = moments(D)
    b = sxy / (sxx - s2o)                                      # OLS slope / reliability ratio
    a = n.mean() - b * o.mean()
    return out(D, a, b, s2n, s2o)


def F3_replicate_covariance(D):
    """Uses only cross-covariances of the parallel run: no within-gauge variance subtraction for the slope,
    and every error variance recovered from the covariance structure."""
    o, N1, N2 = D["O_par"], D["N_par"][:, 0], D["N_par"][:, 1]
    c12 = float(np.cov(N1, N2)[0, 1])
    con = 0.5 * (float(np.cov(o, N1)[0, 1]) + float(np.cov(o, N2)[0, 1]))
    b = c12 / con
    sx2 = con / b
    s2n = 0.5 * (np.var(N1, ddof=1) + np.var(N2, ddof=1)) - c12
    s2o = np.var(o, ddof=1) - sx2
    a = 0.5 * (N1.mean() + N2.mean()) - b * o.mean()
    return out(D, a, b, s2n, s2o)


VALID = {"F1_deming": F1_deming, "F2_attenuation_corrected": F2_attenuation_corrected,
         "F3_replicate_covariance": F3_replicate_covariance}


# legitimate variants (not families; reported for the valid bound)
def L1_deming_single_scan(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D)
    o, n1 = D["O_par"], D["N_par"][:, 0]
    b = deming(np.var(o, ddof=1), np.var(n1, ddof=1), float(np.cov(o, n1)[0, 1]), s2n / s2o)
    return out(D, n1.mean() - b * o.mean(), b, s2n, s2o)


def L2_moment_via_new_error(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D)
    o, n, sxx, syy, sxy = moments(D)
    b = (syy - s2n / 2) / sxy
    return out(D, n.mean() - b * o.mean(), b, s2n, s2o)


LEGIT_VARIANTS = {"L1_deming_single_scan": L1_deming_single_scan, "L2_moment_via_new_error": L2_moment_via_new_error}


# ------------------------------------------------------------------------------------ WRONG methods
def _raw(D):
    Np = D["N_post"]
    return Np.mean(), float(np.std(Np, ddof=1)), float(np.std(D["O_pre"], ddof=1))


def _blk_fit(D):
    blk = D["blk"]; x = np.repeat(DESIGN["blocks"], blk.shape[1]); y = blk.ravel()
    b, a = np.polyfit(x, y, 1)
    return a, b, float(np.mean(np.var(blk, axis=1, ddof=1)))


def W01_raw_post(D):
    mu, sd, sdp = _raw(D); return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": sdp}


def W02_vendor_block_calibration(D):
    a, b, _ = _blk_fit(D); Np = D["N_post"]
    mu, sd = (Np.mean() - a) / b, float(np.std(Np, ddof=1)) / b
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": float(np.std(D["O_pre"], ddof=1))}


def W03_bridge_mean_offset(D):
    o, n, *_ = moments(D); Np = D["N_post"]
    mu, sd = Np.mean() - (n.mean() - o.mean()), float(np.std(Np, ddof=1))
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": float(np.std(D["O_pre"], ddof=1))}


def W04_ols_new_on_old(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = sxy / sxx; return out(D, n.mean() - b * o.mean(), b, s2n, s2o)


def W05_ols_old_on_new_inverted(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = syy / sxy; return out(D, n.mean() - b * o.mean(), b, s2n, s2o)


def W06_ols_single_scan(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n1 = D["O_par"], D["N_par"][:, 0]
    b = float(np.cov(o, n1)[0, 1]) / np.var(o, ddof=1)
    return out(D, n1.mean() - b * o.mean(), b, s2n, s2o)


def W07_deming_no_deconvolution(D):
    r = F1_deming(D); s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = deming(sxx, syy, sxy, (s2n / 2) / s2o)
    sd = float(np.std(D["N_post"], ddof=1)) / b
    sdp = float(np.std(D["O_pre"], ddof=1))
    return {"mean_post": r["mean_post"], "sd_post": sd, "ppk_post": ppk(r["mean_post"], sd), "sd_pre": sdp}


def _deming_ab(D, delta=None):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = deming(sxx, syy, sxy, (s2n / 2) / s2o if delta is None else delta(s2o, s2n))
    return n.mean() - b * o.mean(), b, s2o, s2n


def W08_subtract_per_scan_variance(D):              # production value is a 2-scan mean; subtracts full s2n
    a, b, s2o, s2n = _deming_ab(D); return out(D, a, b, 2 * s2n, s2o)


def W09_subtract_wrong_instrument(D):
    a, b, s2o, s2n = _deming_ab(D); return out(D, a, b, 2 * s2o, s2n / 2)


def W10_add_variance(D):
    a, b, s2o, s2n = _deming_ab(D)
    v = (np.var(D["N_post"], ddof=1) + s2n / 2) / b ** 2
    mu = (D["N_post"].mean() - a) / b; sd = math.sqrt(v)
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd),
            "sd_pre": math.sqrt(np.var(D["O_pre"], ddof=1) + s2o)}


def W11_bridge_variance_as_production(D):
    a, b, s2o, s2n = _deming_ab(D); o, n, sxx, syy, sxy = moments(D)
    sd = math.sqrt(max(syy - s2n / 2, 1e-12)) / b
    return out(D, a, b, s2n, s2o, sd_post=sd)


def W12_duplicate_difference_not_halved(D):         # uses var(N1-N2) as the per-scan variance
    a, b, s2o, s2n = _deming_ab(D); return out(D, a, b, 2 * s2n, 2 * s2o)


def W13_correct_post_raw_pre(D):
    r = F1_deming(D); r["sd_pre"] = float(np.std(D["O_pre"], ddof=1)); return r


def W15_ratio_calibration(D):
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, *_ = moments(D)
    b = n.mean() / o.mean(); return out(D, 0.0, b, s2n, s2o)


def W16_cpk_within_coil(D):
    a, b, s2o, s2n = _deming_ab(D); Np, cp = D["N_post"], D["coil_post"]
    within = np.mean([np.var(Np[cp == k], ddof=1) for k in np.unique(cp)])
    sd = math.sqrt(max(within - s2n / 2, 1e-12)) / b
    Op, cpre = D["O_pre"], D["coil_pre"]
    wpre = np.mean([np.var(Op[cpre == k], ddof=1) for k in np.unique(cpre)])
    return out(D, a, b, s2n, s2o, sd_post=sd, sd_pre=math.sqrt(max(wpre - s2o, 1e-12)))


def W17_orthogonal_regression(D):
    a, b, s2o, s2n = _deming_ab(D, delta=lambda so, sn: 1.0); return out(D, a, b, s2n, s2o)


def W18_deming_ratio_inverted(D):
    a, b, s2o, s2n = _deming_ab(D, delta=lambda so, sn: so / (sn / 2)); return out(D, a, b, s2n, s2o)


def W19_block_repeatability_deconvolution(D):
    a, b, s2o, s2n = _deming_ab(D); _, _, sblk2 = _blk_fit(D); return out(D, a, b, sblk2, s2o)


def W20_blocks_only(D):
    a, b, sblk2 = _blk_fit(D); return out(D, a, b, sblk2, s2_old_checks(D))


def W21_pre_period_carryover(D):
    s2o = s2_old_checks(D); mu = float(D["O_pre"].mean()); sd = math.sqrt(np.var(D["O_pre"], ddof=1) - s2o)
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": sd}


def W22_pooled_old_new_raw(D):
    allr = np.concatenate([D["O_pre"], D["N_post"]]); mu, sd = allr.mean(), float(np.std(allr, ddof=1))
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": sd}


def W23_correct_sd_raw_mean(D):
    r = F1_deming(D); r["mean_post"] = float(D["N_post"].mean()); r["ppk_post"] = ppk(r["mean_post"], r["sd_post"]); return r


def W24_correct_mean_raw_sd(D):
    r = F1_deming(D); r["sd_post"] = float(np.std(D["N_post"], ddof=1)); r["ppk_post"] = ppk(r["mean_post"], r["sd_post"]); return r


WRONG = {k: v for k, v in globals().items() if k.startswith("W") and callable(v) and k[1:3].isdigit()}


# ------------------------------------------------------------------------------------ counterexample search
def X01_deconvolve_on_wrong_scale(D):               # subtracts new-scale error variance after rescaling
    a, b, s2o, s2n = _deming_ab(D)
    v = np.var(D["N_post"], ddof=1) / b ** 2 - s2n / 2
    mu = (D["N_post"].mean() - a) / b; sd = math.sqrt(max(v, 1e-12))
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd),
            "sd_pre": math.sqrt(np.var(D["O_pre"], ddof=1) - s2o)}


def X02_offset_mean_deming_variance(D):             # mean mapped by bridge offset only, variance correct
    r = F1_deming(D); o, n, *_ = moments(D)
    r["mean_post"] = float(D["N_post"].mean() - (n.mean() - o.mean())); r["ppk_post"] = ppk(r["mean_post"], r["sd_post"]); return r


def X03_predict_each_part_then_sd(D):               # best linear predictor per part (shrinks), then SD
    a, b, s2o, s2n = _deming_ab(D); Np = D["N_post"]
    v = (np.var(Np, ddof=1) - s2n / 2) / b ** 2
    k = b * v / (b * b * v + s2n / 2)
    x = Np.mean() / 1.0; xhat = (Np.mean() - a) / b + k * (Np - Np.mean())
    mu, sd = float(xhat.mean()), float(np.std(xhat, ddof=1))
    return {"mean_post": mu, "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": math.sqrt(np.var(D["O_pre"], ddof=1) - s2o)}


def X04_common_sigma_pre_post(D):                   # assumes the process spread did not change
    r = F1_deming(D); r["sd_post"] = r["sd_pre"]; r["ppk_post"] = ppk(r["mean_post"], r["sd_post"]); return r


def X05_attenuation_corrected_single_reading_reliability(D):  # reliability from single-scan, applied to 2-scan mean bridge
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = sxy / (sxx - s2o)
    return out(D, n.mean() - b * o.mean(), b, s2n * 2, s2o)


def X06_deming_ignore_scan_averaging_in_delta(D):   # delta uses per-scan s2n vs s2o (bridge uses 2-scan means)
    a, b, s2o, s2n = _deming_ab(D, delta=lambda so, sn: sn / so); return out(D, a, b, s2n, s2o)


def X07_ols_with_deconvolution_both_periods_offset_mean(D):  # plausible "fix everything except attenuation"
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = sxy / sxx
    r = out(D, n.mean() - b * o.mean(), b, s2n, s2o)
    r["mean_post"] = float(D["N_post"].mean() - (n.mean() - o.mean())); r["ppk_post"] = ppk(r["mean_post"], r["sd_post"]); return r


def X08_geometric_mean_regression(D):               # reduced major axis: sign(sxy) sqrt(syy/sxx)
    s2o, s2n = s2_old_checks(D), s2_new_dual(D); o, n, sxx, syy, sxy = moments(D)
    b = math.sqrt(syy / sxx); return out(D, n.mean() - b * o.mean(), b, s2n, s2o)


def X09_deming_ratio_from_blocks(D):
    _, _, sblk2 = _blk_fit(D)
    a, b, s2o, s2n = _deming_ab(D, delta=lambda so, sn: (sblk2 / 2) / so); return out(D, a, b, s2n, s2o)


def X10_median_mad_robust(D):                        # legitimate-looking robust variant (normal data)
    a, b, s2o, s2n = _deming_ab(D); Np = D["N_post"]
    mad = 1.4826 * np.median(np.abs(Np - np.median(Np)))
    v = (mad ** 2 - s2n / 2) / b ** 2; mu = (np.median(Np) - a) / b; sd = math.sqrt(max(v, 1e-12))
    return {"mean_post": float(mu), "sd_post": sd, "ppk_post": ppk(mu, sd), "sd_pre": math.sqrt(np.var(D["O_pre"], ddof=1) - s2o)}


XCE = {k: v for k, v in globals().items() if k.startswith("X") and k[1:3].isdigit() and callable(v)}
XKIND = {"X10_median_mad_robust": "legitimate"}      # fixed before scoring; all others wrong


# ------------------------------------------------------------------------------------ cheap solves
def CS_constant_notify(D): return None
def CS_constant_no_notify(D): return None


def run(draws=400):
    methods = {**{k: ("valid", v) for k, v in VALID.items()},
               **{k: ("legit_variant", v) for k, v in LEGIT_VARIANTS.items()},
               **{k: ("wrong", v) for k, v in WRONG.items()},
               **{k: (XKIND.get(k, "wrong_counterexample"), v) for k, v in XCE.items()}}
    res = {"design": DESIGN, "fixtures": {}, "methods": {m: {"kind": k, "fx": {}} for m, (k, _) in methods.items()}}
    for fx, f in FIX.items():
        rng = np.random.default_rng(f["seed"])
        errs = {m: {q: [] for q in QUANT} for m in methods}
        dec = {m: [] for m in methods}
        truths, raw_ppk = [], []
        for _ in range(draws):
            D, T = draw(f, rng); truths.append(T)
            raw_ppk.append(W01_raw_post(D)["ppk_post"])
            for m, (_, fn) in methods.items():
                r = fn(D)
                for q in QUANT:
                    errs[m][q].append(r[q] - T[q])
                dec[m].append((r["ppk_post"] < GATE) == (T["ppk_post"] < GATE))
        se = {q: float(np.sqrt(np.mean(np.square(errs["F1_deming"][q])))) for q in QUANT}
        tp = np.array([t["ppk_post"] for t in truths])
        res["fixtures"][fx] = {"params": f, "se_ref": se, "truth_ppk_mean": float(tp.mean()),
                               "truth_ppk_min": float(tp.min()), "truth_ppk_max": float(tp.max()),
                               "truth_sd_post": float(np.mean([t["sd_post"] for t in truths])),
                               "truth_mean_post": float(np.mean([t["mean_post"] for t in truths])),
                               "truth_sd_pre": float(np.mean([t["sd_pre"] for t in truths])),
                               "raw_dashboard_ppk_mean": float(np.mean(raw_ppk)),
                               "truth_decision": "notify" if tp.mean() < GATE else "no_notification"}
        for m in methods:
            z = {q: np.abs(np.array(errs[m][q])) / se[q] for q in QUANT}
            res["methods"][m]["fx"][fx] = {
                "bias_se": {q: float(np.mean(errs[m][q]) / se[q]) for q in QUANT},
                "p01": {q: float(np.percentile(z[q], 1)) for q in QUANT},
                "p50": {q: float(np.percentile(z[q], 50)) for q in QUANT},
                "p99": {q: float(np.percentile(z[q], 99)) for q in QUANT},
                "decision_correct_rate": float(np.mean(dec[m])),
                "sd_se": {q: float(np.std(errs[m][q]) / se[q]) for q in QUANT}}
    return res


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    tag = sys.argv[2] if len(sys.argv) > 2 else "D1"
    if tag == "D3":   # FEASIBILITY-FRONTIER PROBE, not a design: low reliability, large scale differences
        DESIGN.update(post_lots=40, post_per_lot=400, n_par=4000)
        for k, (b, sn) in zip(FIX, [(1.30, .016), (0.75, .014), (1.28, .018), (0.74, .015), (1.33, .016)]):
            FIX[k].update(b=b, s_n=sn, s_o=.0090)
    if tag == "D2":   # design iteration D2: realistic in-line volume (station logs every part), manual bridge capped
        DESIGN.update(post_lots=40, post_per_lot=400, n_par=4000)
    r = run(n)
    Path(__file__).with_name("c1_results_%s.json" % tag).write_text(json.dumps(r, indent=1) + "\n")
    for fx, v in r["fixtures"].items():
        print("%-9s truth Ppk %.3f [%.3f,%.3f]  dashboard %.3f  SE_REF %s" % (
            fx, v["truth_ppk_mean"], v["truth_ppk_min"], v["truth_ppk_max"], v["raw_dashboard_ppk_mean"],
            {q: round(s, 5) for q, s in v["se_ref"].items()}))
