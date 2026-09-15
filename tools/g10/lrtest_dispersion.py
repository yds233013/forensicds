import sys, numpy as np
from pathlib import Path
from scipy.special import gammaln
from scipy.stats import chi2
sys.path.insert(0, "tools/g10")
import variant_review as V
for name in sys.argv[1:]:
    X = V.load(Path(f"/private/tmp/claude-501/g10cache/{name}/data/warehouse.sqlite"))
    N = X["sales"]; Ein, Efull = V.exposure(X, V.profiles(X))
    ok = Ein > 1e-9
    def nbll(rate, alpha):
        mu = np.maximum(rate * Ein, 1e-12)[ok]; a = alpha[ok]; y = N[ok]
        return np.sum(gammaln(y + a) - gammaln(a) - gammaln(y + 1) + a * np.log(a / (a + mu)) + y * np.log(mu / (a + mu)))
    r1, a1 = V.fit(X, N, Ein, "nb"); r0, a0 = V.fit(X, N, Ein, "nb", alpha_by_cat=False)
    l1, l0 = nbll(r1, a1), nbll(r0, a0)
    # Poisson-lognormal at the NB rates, sigma by ML per category
    x, wq = np.polynomial.hermite_e.hermegauss(40); wq = wq / wq.sum(); cat = X["A"]["cat"]; lpl = 0.0
    for c in range(len(X["cats"])):
        sel = ok & (cat == c); y = N[sel]; mc = np.maximum(r1[sel] * Ein[sel], 1e-12); best = -np.inf
        for sg in np.linspace(0.15, 1.0, 35):
            lam = mc[:, None] * np.exp(sg * x - sg * sg / 2)[None, :]
            ll = y[:, None] * np.log(lam) - lam - gammaln(y + 1)[:, None]
            mx = ll.max(1, keepdims=True); best = max(best, (mx[:, 0] + np.log((np.exp(ll - mx) * wq).sum(1))).sum())
        lpl += best
    print(name, f"LR per-category vs common alpha = {2*(l1-l0):.1f} (df 7, p={chi2.sf(2*(l1-l0),7):.2g})",
          f"| loglik NB - Poisson-lognormal = {l1-lpl:.1f}", "| alpha by cat", np.round(sorted(set(np.round(a1,2))),2), flush=True)
