"""G35 interference simulation: two finalist incidents, measured against the kill criteria.

Research/dev only.  No model call, no container, no network.

    python research/g35/simulation.py            # all gates, visible regime + hidden regimes
    python research/g35/simulation.py f2         # finalist 2 comparison only

F1  SUPPLY DISPLACEMENT - food-delivery dispatch priority.
    Merchants are randomised to a courier-dispatch priority flag inside (city, day) blocks whose
    treatment SATURATION is itself randomised.  Couriers are a scarce shared resource inside a block,
    so priority granted to one merchant is priority taken from another.  In the limit where everybody
    has priority, priority is worth nothing: only the algorithm's genuine routing efficiency (delta)
    survives.  The naive treated-vs-control comparison therefore measures a reshuffle, not a gain.

F2  AUCTION EQUILIBRIUM - sponsored-listing bid optimiser.
    Advertisers are randomised to an automated bidder inside (category, day) blocks with randomised
    saturation.  A treated advertiser wins more impressions by outbidding controls; when everybody
    runs the optimiser the clearing price rises and the private advantage largely cancels.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, replace

import numpy as np

SATURATIONS = (0.0, 0.25, 0.5, 0.75, 1.0)


# --------------------------------------------------------------------------- F1: supply displacement
@dataclass(frozen=True)
class SpecF1:
    name: str = "visible"
    seed: int = 20260920
    n_cities: int = 30
    n_days: int = 28
    merchants_per_city: int = 45    # mean; city sizes vary a lot, which is why weighting matters
    city_size_sigma: float = 0.55
    demand_mu: float = 2.6          # lognormal mean-log of merchant daily order volume
    demand_sigma: float = 0.55
    capacity_ratio: float = 0.78    # courier capacity / expected demand  (<1 => rationing)
    # Deliberately modest.  Heterogeneity here only adds variance to every unbiased estimator; it
    # does not make the task about interference.  Keeping it small ensures that EVERY valid route to
    # the right estimand agrees, so the task cannot be failed by choosing a less efficient but
    # equally correct analysis (the K11 requirement).
    cap_city_sigma: float = 0.06    # persistent market tightness differences  (city fixed effect)
    cap_day_sigma: float = 0.04     # weather / holiday shocks common to a day (day fixed effect)
    cap_idio_sigma: float = 0.03    # irreducible block noise
    priority_weight: float = 2.6    # dispatch weight multiplier for a merchant with priority
    delta: float = 0.030            # GENUINE routing efficiency of the new algorithm
    adoption: float = 0.80          # assigned-treated merchants that actually switch on
    adopt_size_tilt: float = 0.55   # larger merchants switch on more often (they have ops staff),
                                    # which is why conditioning on REALISED saturation is not safe
    gate: float = 0.015             # launch iff policy effect >= +1.5pp fulfilment


def _blocks(sp: SpecF1, rng):
    """Per-block merchant demand and courier capacity, shared by every counterfactual."""
    nb = sp.n_cities * sp.n_days
    n = sp.merchants_per_city
    # merchant identity is stable within a city; demand varies by day
    base = np.exp(rng.normal(sp.demand_mu, sp.demand_sigma, size=(sp.n_cities, n)))
    # city sizes differ by an order of magnitude, as real marketplaces do
    size = np.clip(np.round(n * np.exp(rng.normal(0, sp.city_size_sigma, size=(sp.n_cities, 1)))), 8, n)
    exists = np.arange(n)[None, :] < size
    base = base * exists
    dem = rng.poisson(base[:, None, :].repeat(sp.n_days, axis=1)).astype(float)  # city x day x merchant
    dem = np.where(exists[:, None, :], np.maximum(dem, 1.0), 0.0)
    D = dem.sum(axis=2)                                                          # city x day
    # Courier tightness is structured, not iid: a persistent city level, a shared day shock, and a
    # small idiosyncratic term.  An analysis that respects the city/day design absorbs the first two.
    f_city = np.exp(rng.normal(0, sp.cap_city_sigma, size=(sp.n_cities, 1)))
    f_day = np.exp(rng.normal(0, sp.cap_day_sigma, size=(1, sp.n_days)))
    f_idio = np.exp(rng.normal(0, sp.cap_idio_sigma, size=D.shape))
    cap = D * sp.capacity_ratio * f_city * f_day * f_idio
    city_id = np.repeat(np.arange(sp.n_cities), sp.n_days)
    day_id = np.tile(np.arange(sp.n_days), sp.n_cities)
    return dem.reshape(nb, n), D.reshape(nb), cap.reshape(nb), city_id, day_id


def _serve(dem, cap, adopted, sp, rng):
    """Fulfilment rate per merchant under weighted proportional courier rationing.

    Each merchant's claim on block capacity is proportional to its demand times its dispatch weight;
    priority raises that weight.  Capacity a priority merchant gains is capacity somebody else loses,
    so at full saturation every weight is equal again and priority is worth exactly nothing - only
    `delta`, the routing efficiency, survives.  Water-filling passes stop a merchant being allocated
    more than it asked for.
    """
    D = dem.sum(axis=1)
    DT = (dem * adopted).sum(axis=1)
    S = cap * (1.0 + sp.delta * np.divide(DT, D, out=np.zeros_like(D), where=D > 0))

    w = np.where(adopted, sp.priority_weight, 1.0)
    claim = dem * w
    served = np.zeros_like(dem)
    remaining = S.copy()
    active = np.ones_like(dem, dtype=bool)
    for _ in range(4):
        tot = (claim * active).sum(axis=1)
        share = np.divide(claim * active, np.maximum(tot, 1e-9)[:, None],
                          out=np.zeros_like(dem), where=active)
        alloc = np.minimum(share * remaining[:, None], dem - served)
        served += alloc
        remaining = np.maximum(remaining - alloc.sum(axis=1), 0.0)
        active = active & ((dem - served) > 1e-9)
        if remaining.max() < 1e-9 or not active.any():
            break
    live = dem > 0
    rate = np.zeros_like(dem)
    np.divide(served, dem, out=rate, where=live)
    rate = np.clip(rate, 0.0, 1.0)
    drawn = rng.binomial(dem.astype(int), rate)
    out = np.zeros_like(dem)
    np.divide(drawn, dem, out=out, where=live)
    return out          # cells with no merchant are 0 and always carry demand weight 0


def _adopt_p(dem, sp: SpecF1):
    """Adoption probability rises with merchant size.  Assignment is still random, so the ITT
    estimand is untouched; but REALISED adoption share is now an outcome-correlated quantity and
    conditioning on it is post-treatment conditioning."""
    with np.errstate(divide="ignore", invalid="ignore"):
        z = np.log(np.maximum(dem, 1.0))
    z = (z - z.mean()) / (z.std() + 1e-9)
    p = sp.adoption * (1.0 + sp.adopt_size_tilt * z * 0.5)
    return np.clip(p, 0.05, 0.99)


def _block_draw(sp: SpecF1):
    """The block population.  Truth and experiment MUST share this draw, otherwise the 'truth' is
    the estimand of a different population and the estimators look biased when they are not."""
    return _blocks(sp, np.random.default_rng(sp.seed))


def world_f1(sp: SpecF1):
    """One experiment: randomised saturation across blocks, complete randomisation within block."""
    rng = np.random.default_rng(sp.seed + 101)
    dem, D, cap, city_id, day_id = _block_draw(sp)
    nb, n = dem.shape

    pi = rng.choice(SATURATIONS, size=nb)
    assigned = np.zeros((nb, n), dtype=bool)
    for b in range(nb):
        live = np.flatnonzero(dem[b] > 0)
        k = int(round(pi[b] * live.size))
        if k:
            assigned[b, rng.choice(live, size=k, replace=False)] = True
    adopted = assigned & (rng.random((nb, n)) < _adopt_p(dem, sp))

    Y = _serve(dem, cap, adopted, sp, rng)
    return dict(spec=sp, dem=dem, D=D, cap=cap, pi=pi, assigned=assigned, adopted=adopted,
                Y=Y, city_id=city_id, day_id=day_id)


def truth_f1(sp: SpecF1, n_mc: int = 12):
    """Ground truth by counterfactual replay on the SAME blocks.

    tau_policy : everybody offered the feature  vs  nobody   (the deployment contrast, ITT)
    tau_direct : treated minus control inside 50%-saturated blocks
    spillover  : control merchants at 50% saturation vs merchants at 0% saturation
    All demand-weighted, because the business counts orders, not merchants.
    """
    rng = np.random.default_rng(sp.seed + 7777)
    dem, D, cap, city_id, day_id = _block_draw(sp)   # same population as the experiment
    nb, n = dem.shape
    w = dem / dem.sum()

    pol, non, dir_, spill = [], [], [], []
    for _ in range(n_mc):
        all_on = (dem > 0) & (rng.random((nb, n)) < _adopt_p(dem, sp))
        none_on = np.zeros((nb, n), dtype=bool)
        Y1 = _serve(dem, cap, all_on, sp, rng)
        Y0 = _serve(dem, cap, none_on, sp, rng)
        pol.append((Y1 * w).sum())
        non.append((Y0 * w).sum())

        half = np.zeros((nb, n), dtype=bool)
        for b in range(nb):
            live = np.flatnonzero(dem[b] > 0)
            half[b, rng.choice(live, size=live.size // 2, replace=False)] = True
        half_ad = half & (rng.random((nb, n)) < _adopt_p(dem, sp))
        Yh = _serve(dem, cap, half_ad, sp, rng)
        wt, wc = dem * half, dem * (~half)
        dir_.append((Yh * wt).sum() / wt.sum() - (Yh * wc).sum() / wc.sum())
        spill.append((Yh * wc).sum() / wc.sum() - (Y0 * wc).sum() / wc.sum())

    tp = float(np.mean(pol) - np.mean(non))
    return dict(tau_policy=tp,
                mean_fulfilment_0=float(np.mean(non)), mean_fulfilment_1=float(np.mean(pol)),
                tau_direct_50=float(np.mean(dir_)), spillover_50=float(np.mean(spill)),
                decision="launch" if tp >= sp.gate else "hold")


# ------------------------------------------------------------------------------------- estimators
def _wmean(y, w):
    return float((y * w).sum() / w.sum())


def est_f1(w):
    """Valid and wrong analyses of one F1 experiment.  Keys prefixed V_ are valid, W_ are wrong."""
    dem, pi, A, Y = w["dem"], w["pi"], w["assigned"], w["Y"]
    nb, n = dem.shape
    out = {}

    # ---- VALID: block-level contrast between the 100% and 0% saturation arms, demand weighted.
    m1, m0 = pi == 1.0, pi == 0.0
    y_b = (Y * dem).sum(axis=1) / dem.sum(axis=1)          # block fulfilment rate
    d_b = dem.sum(axis=1)
    out["V_saturation_contrast"] = _wmean(y_b[m1], d_b[m1]) - _wmean(y_b[m0], d_b[m0])

    # ---- VALID: fit the block-level saturation response and evaluate at 1 vs 0 (uses all arms).
    x = pi
    X = np.column_stack([np.ones(nb), x, x ** 2])
    beta = np.linalg.lstsq(X * np.sqrt(d_b)[:, None], y_b * np.sqrt(d_b), rcond=None)[0]
    out["V_saturation_curve"] = float((beta[1] * 1 + beta[2] * 1) - 0.0)

    # ---- VALID and PRECISE: same contrast, but absorbing the city and day structure of the design.
    # Saturation is randomised independently of city and day, so this changes precision, not the
    # estimand; it is the analysis a team that respects its own switchback design would run.
    cid, did = w["city_id"], w["day_id"]
    Xc = np.zeros((nb, cid.max() + 1)); Xc[np.arange(nb), cid] = 1
    Xd = np.zeros((nb, did.max() + 1)); Xd[np.arange(nb), did] = 1
    Xs = np.column_stack([(pi == s).astype(float) for s in SATURATIONS[1:]])
    X = np.column_stack([Xc, Xd[:, 1:], Xs])
    sw = np.sqrt(d_b)
    coef = np.linalg.lstsq(X * sw[:, None], y_b * sw, rcond=None)[0]
    out["V_design_regression"] = float(coef[-1])      # coefficient on the 100% saturation indicator

    # ---- VALID: Horvitz-Thompson style, treating the block as the unit of randomisation.
    num = {}
    for s in SATURATIONS:
        m = pi == s
        num[s] = _wmean(y_b[m], d_b[m])
    out["V_arm_means_1_minus_0"] = num[1.0] - num[0.0]

    # ---- WRONG: the dashboard.  Pool every merchant, treated vs control, ignore blocks entirely.
    t, c = A, ~A
    out["W1_naive_ab"] = _wmean(Y[t], dem[t]) - _wmean(Y[c], dem[c])

    # ---- WRONG: same point estimate, "fixed" by clustering the standard errors.
    out["W2_clustered_se"] = out["W1_naive_ab"]

    # ---- WRONG: block fixed effects with an individual treatment dummy (within-block direct effect).
    num_, den_ = 0.0, 0.0
    for b in range(nb):
        wt, wc = dem[b] * A[b], dem[b] * (~A[b])
        if wt.sum() > 0 and wc.sum() > 0:          # mixed blocks only; 0% and 100% contribute nothing
            num_ += ((Y[b] * wt).sum() / wt.sum() - (Y[b] * wc).sum() / wc.sum()) * d_b[b]
            den_ += d_b[b]
    out["W3_block_fe_direct"] = num_ / den_ if den_ > 0 else float("nan")

    # ---- WRONG: direct effect measured at 50% saturation, reported as the rollout effect.
    m = pi == 0.5
    wt, wc = dem[m] * A[m], dem[m] * (~A[m])
    out["W5_direct_as_policy"] = ((Y[m] * wt).sum() / wt.sum()) - ((Y[m] * wc).sum() / wc.sum())

    # ---- WRONG: treated units in fully-treated blocks vs controls drawn from mixed blocks.
    mt = (pi == 1.0)
    mc = (pi > 0) & (pi < 1)
    yt = _wmean(Y[mt], dem[mt])
    cc = dem[mc] * (~A[mc])
    out["W6_full_vs_mixed_controls"] = yt - ((Y[mc] * cc).sum() / cc.sum())

    # ---- WRONG: unweighted block means (merchant-weighted, not demand-weighted).
    yb_u = Y.mean(axis=1)
    out["W14_unweighted_blocks"] = yb_u[m1].mean() - yb_u[m0].mean()

    # ---- WRONG: condition on REALISED adoption share rather than assigned saturation.
    real = w["adopted"].mean(axis=1)
    hi, lo = real >= 0.9, real <= 0.001
    out["W10_realised_saturation"] = (_wmean(y_b[hi], d_b[hi]) - _wmean(y_b[lo], d_b[lo])
                                      if hi.any() and lo.any() else float("nan"))

    # ---- WRONG: treated-only before/after style contrast against the grand mean.
    out["W13_treated_only"] = _wmean(Y[t], dem[t]) - _wmean(Y, dem)
    return out


# ------------------------------------------------------------------ F2: auction equilibrium (rival)
@dataclass(frozen=True)
class SpecF2:
    name: str = "f2"
    seed: int = 4242
    n_cat: int = 40
    n_days: int = 21
    advertisers: int = 30
    slots: int = 6
    value_mu: float = 1.0
    value_sigma: float = 0.35
    lift: float = 0.18      # bid-efficiency multiplier from the optimiser
    gate: float = 0.02


def world_f2(sp: SpecF2):
    rng = np.random.default_rng(sp.seed)
    nb = sp.n_cat * sp.n_days
    n = sp.advertisers
    val = np.exp(rng.normal(sp.value_mu, sp.value_sigma, size=(nb, n)))
    pi = rng.choice(SATURATIONS, size=nb)
    A = np.zeros((nb, n), dtype=bool)
    for b in range(nb):
        k = int(round(pi[b] * n))
        if k:
            A[b, rng.choice(n, size=k, replace=False)] = True
    bid = val * np.where(A, 1.0 + sp.lift, 1.0) * np.exp(rng.normal(0, 0.12, size=(nb, n)))
    order = np.argsort(-bid, axis=1)
    win = np.zeros((nb, n), dtype=bool)
    rows = np.arange(nb)[:, None]
    win[rows, order[:, :sp.slots]] = True
    # payment = next bid down (second price); surplus = value - price when winning
    srt = np.sort(bid, axis=1)[:, ::-1]
    price = srt[:, sp.slots][:, None]
    surplus = np.where(win, val - price, 0.0)
    return dict(spec=sp, pi=pi, assigned=A, Y=surplus, val=val, win=win)


def truth_f2(sp: SpecF2, n_mc: int = 8):
    rng = np.random.default_rng(sp.seed + 99)
    nb, n = sp.n_cat * sp.n_days, sp.advertisers
    pol, non = [], []
    for _ in range(n_mc):
        val = np.exp(rng.normal(sp.value_mu, sp.value_sigma, size=(nb, n)))
        for on, acc in ((True, pol), (False, non)):
            bid = val * (1.0 + sp.lift if on else 1.0) * np.exp(rng.normal(0, 0.12, size=(nb, n)))
            srt = np.sort(bid, axis=1)[:, ::-1]
            price = srt[:, sp.slots][:, None]
            order = np.argsort(-bid, axis=1)
            win = np.zeros((nb, n), dtype=bool)
            win[np.arange(nb)[:, None], order[:, :sp.slots]] = True
            acc.append(float(np.where(win, val - price, 0.0).mean()))
    return dict(tau_policy=float(np.mean(pol) - np.mean(non)))


def est_f2(w):
    pi, A, Y = w["pi"], w["assigned"], w["Y"]
    m1, m0 = pi == 1.0, pi == 0.0
    return dict(V_saturation_contrast=float(Y[m1].mean() - Y[m0].mean()),
                W1_naive_ab=float(Y[A].mean() - Y[~A].mean()))


# ---------------------------------------------------------------------------------------- reporting
# Operating points chosen so the DECISION is far from the gate for the correct estimator.  This is
# regime selection on the physics of the DGP, fixed before any model is run; it is not tolerance
# tuning.  G34's hidden_a taught that a correct estimator sitting on its own decision boundary makes
# a task ungradeable no matter how good the mechanism is.
REGIMES = [
    # tight market, solid routing gain -> the gain is real and survives
    SpecF1(name="visible", n_cities=60, capacity_ratio=0.78, delta=0.060),
    # very tight market, almost no real gain -> biggest naive lift, smallest true effect
    SpecF1(name="hidden_a_tight_hollow", seed=515151, n_cities=60, capacity_ratio=0.65, delta=0.010),
    # slack market, decent routing gain -> little scarcity to relieve, so little to win
    SpecF1(name="hidden_b_slack", seed=626262, n_cities=60, capacity_ratio=1.05, delta=0.030),
    # very tight market, large real gain -> clear launch
    SpecF1(name="hidden_c_tight_real", seed=737373, n_cities=60, capacity_ratio=0.70, delta=0.090),
]


def report_f1():
    print("=" * 96)
    print("F1  SUPPLY DISPLACEMENT - dispatch priority.  All quantities are fulfilment-rate points.")
    print("=" * 96)
    hdr = ("regime", "tau_policy", "decision", "naive_AB", "naive_err", "direct50", "spill50")
    print("%-18s %10s %9s %10s %10s %10s %10s" % hdr)
    rows = []
    for sp in REGIMES:
        t = truth_f1(sp)
        w = world_f1(sp)
        e = est_f1(w)
        rows.append((sp, t, e))
        print("%-18s %10.4f %9s %10.4f %10.4f %10.4f %10.4f" % (
            sp.name, t["tau_policy"], t["decision"], e["W1_naive_ab"],
            e["W1_naive_ab"] - t["tau_policy"], t["tau_direct_50"], t["spillover_50"]))
    return rows


def report_estimators(rows):
    print()
    print("=" * 96)
    print("CORRECT-DATA-TABLE GATE - every analysis gets perfect operational semantics.")
    print("Error against tau_policy, in fulfilment-rate points.")
    print("=" * 96)
    keys = [k for k in rows[0][2] if k != "W2_clustered_se"]
    print("%-28s %s" % ("analysis", "".join("%12s" % r[0].name[:11] for r in rows)))
    for k in keys:
        line = "".join("%12.4f" % (r[2][k] - r[1]["tau_policy"]) for r in rows)
        print("%-28s %s" % (k, line))
    print()
    print("decision implied by each analysis (truth in brackets):")
    for k in keys:
        s = ""
        for sp, t, e in rows:
            d = "launch" if e[k] >= sp.gate else "hold"
            s += "%12s" % (d + ("" if d == t["decision"] else "*"))
        print("%-28s %s   [%s]" % (k, s, " ".join(r[1]["decision"][:1] for r in rows)))
    print("\n  * = disagrees with the truth for that regime")


def report_f2():
    print()
    print("=" * 96)
    print("F2  AUCTION EQUILIBRIUM - rival finalist, mechanism-strength comparison only")
    print("=" * 96)
    sp = SpecF2()
    t = truth_f2(sp)
    e = est_f2(world_f2(sp))
    print("  tau_policy (truth)        : %+.4f" % t["tau_policy"])
    print("  naive A/B                 : %+.4f" % e["W1_naive_ab"])
    print("  valid saturation contrast : %+.4f" % e["V_saturation_contrast"])
    print("  naive error / |tau_policy|: %.1fx" % abs(e["W1_naive_ab"] / (t["tau_policy"] or 1e-9)))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "f2":
        report_f2()
    else:
        rows = report_f1()
        report_estimators(rows)
        report_f2()
