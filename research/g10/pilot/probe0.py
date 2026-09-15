"""Feasibility probe for G10 statistics (not the final DGP). Per-series base demand with known relative factors,
Gamma day heterogeneity, evening-peak intraday profile, forecast-driven inventory (informative censoring)."""
import numpy as np
from scipy.optimize import minimize
from scipy.special import gammaln

rng = np.random.default_rng(1)
S, D, H = 400, 84, 14                      # series, days per period, trading hours
prof = np.array([3,4,5,6,7,7,6,6,7,9,12,14,9,5], float); prof /= prof.sum()
cum = np.concatenate([[0], np.cumsum(prof)])

def simulate(alpha, mult, under=1.0):
    base = rng.lognormal(np.log(6), 0.6, S)
    promo = rng.random((S, D)) < 0.10
    dow = np.tile([0.9, 0.9, 0.95, 1.0, 1.1, 1.3, 1.2], D // 7 + 1)[:D]
    r = dow[None, :] * np.where(promo, 2.2, 1.0)
    lam = base[:, None] * r * rng.gamma(alpha, 1 / alpha, (S, D))
    fc = base[:, None] * r * np.where(promo, under, 1.0) * rng.lognormal(0, 0.15, (S, D))
    inv = np.maximum(1, np.round(mult * fc)).astype(int)
    N = np.zeros((S, D), int); G = np.ones((S, D)); dem = np.zeros((S, D), int)
    for h in range(H):
        a = rng.poisson(lam * prof[h])
        dem += a
        left = inv - N
        s = np.minimum(a, np.maximum(left, 0))
        # fraction of hour in stock if it runs out during this hour (arrivals uniform within hour)
        out_now = (left > 0) & (a >= left) & (a > 0)
        frac = np.where(out_now, left / np.maximum(a, 1) , 1.0)  # approx time of the left-th arrival
        G = np.where(out_now & (G == 1.0), cum[h] + prof[h] * frac, G)
        G = np.where((left <= 0) & (G == 1.0), cum[h], G)
        N += s
    cens = G < 1.0 - 1e-12
    return dict(base=base, r=r, lam=lam, N=N, G=G, cens=cens, dem=dem)

def estimates(x):
    base, r, N, G, cens = x["base"], x["r"], x["N"], x["G"], x["cens"]
    out = {}
    out["A_sales"] = (N / r).mean(1)
    Nm = np.where(cens, np.nan, N / r); out["B_drop_censored"] = np.nanmean(Nm, 1)
    out["C_per_day_scale"] = (N / (r * np.maximum(G, 1e-3))).mean(1)
    out["F_poisson_offset"] = N.sum(1) / (r * G).sum(1)
    Gu = np.where(cens, np.clip((np.argmax(np.cumsum(np.ones(1)) ) * 0 + G), 0, 1), 1.0)
    # uniform-time exposure: fraction of hours in stock
    hours_in = np.where(cens, np.searchsorted(cum, G, side='right') - 1 + 0.5, H) / H
    out["C2_uniform_time_scale"] = N.sum(1) / (r * np.clip(hours_in, 1e-3, 1)).sum(1)
    bu = out["B_drop_censored"]
    out["D_mean_impute"] = (np.where(cens, N + np.nan_to_num(bu)[:, None] * r * (1 - G), N) / r).mean(1)
    # NB MLE with offset: per-series base, common alpha
    E = r * G
    def nll(p):
        a = np.exp(p[0]); b = np.exp(p[1:])
        mu = b[:, None] * E
        ll = gammaln(N + a) - gammaln(a) + a * np.log(a / (a + mu)) + N * np.log(mu / (a + mu))
        return -ll.sum()
    p0 = np.concatenate([[np.log(3)], np.log(np.maximum(out["F_poisson_offset"], 0.1))])
    res = minimize(nll, p0, method="L-BFGS-B")
    out["NB_offset"] = np.exp(res.x[1:]); out["_alpha_hat"] = np.exp(res.x[0])
    return out

for alpha in (8, 4, 2):
    for mult, under, label in ((1.6, 1.0, "pre generous"), (1.15, 0.85, "post lean + v4 under")):
        x = simulate(alpha, mult, under)
        est = estimates(x)
        truth = x["base"]
        cr = x["cens"].mean()
        lost_share = 1 - x["N"].sum() / x["dem"].sum()
        line = f"alpha={alpha} {label:22} censored_days={cr:.2f} lost_share={lost_share:.3f} | "
        for k, v in est.items():
            if k.startswith("_"): line += f" alpha_hat={v:.2f}"; continue
            line += f" {k}={100*(np.sum(v)/np.sum(truth)-1):+.1f}%"
        print(line)
