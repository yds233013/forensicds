"""G36 finalist F2: retail demand forecast after algorithmic repricing.

Runner-up in the incident tournament. Simulated to the same recognition-vs-execution standard as F1
so the selection is measured rather than asserted. Research/dev only; no model, no container.

    python research/g36/f2_repricing.py

Structure. Historical prices were set by category managers who raised prices when demand was strong,
so the historical price coefficient is biased toward zero (or positive) and is NOT the causal
elasticity. A randomised price test ran in a subset of stores. An algorithm will set prices next
quarter by a published rule. The forecast must combine:
  * the causal elasticity (from the test, not from history);
  * transported across the STORE MIX (test stores are not the estate);
  * evaluated over the new PRICE RANGE (the algorithm goes deeper than the test did);
  * with the stable seasonal/base demand component from history.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

FORMATS = ("urban_small", "suburban", "large_format")


@dataclass(frozen=True)
class SpecF2:
    name: str = "visible"
    seed: int = 370001
    n_stores: int = 900
    n_weeks: int = 52
    fmt_share: tuple = (0.42, 0.40, 0.18)
    test_prop: tuple = (0.04, 0.09, 0.20)        # large stores volunteered for the price test
    base: tuple = (520.0, 780.0, 1650.0)
    season_amp: float = 0.16
    elast: tuple = (-1.05, -1.55, -2.35)         # causal elasticity, heterogeneous by format
    elast_curv: float = 0.55                     # elasticity steepens at deeper discounts
    manager_bias: float = 0.85                   # price raised when latent demand is high
    disc_hist: float = 0.06                      # typical historical discount depth
    disc_test: float = 0.10                      # the randomised test went to 10%
    disc_target: float = 0.18                    # the algorithm will go to 18%
    noise_sd: float = 0.18
    margin_gate: float = 1.620                   # adopt iff forecast units index >= gate


def _elasticity(sp, fmt, disc):
    """Causal elasticity at a given discount depth; steepens as the discount deepens."""
    e0 = np.array(sp.elast)[fmt]
    return e0 * (1.0 + sp.elast_curv * (disc - sp.disc_hist) / max(sp.disc_hist, 1e-9))


def world_f2(sp: SpecF2):
    rng = np.random.default_rng(sp.seed)
    fmt = rng.choice(3, size=sp.n_stores, p=np.array(sp.fmt_share))
    base = np.array(sp.base)[fmt]
    weeks = np.arange(sp.n_weeks)
    season = 1.0 + sp.season_amp * np.sin(2 * np.pi * weeks / 52.0)

    # latent demand shock the manager can see but the analyst cannot separate from price
    shock = rng.normal(0, 0.15, size=(sp.n_stores, sp.n_weeks))
    disc_hist = np.clip(sp.disc_hist - sp.manager_bias * sp.disc_hist * shock, 0.0, 0.35)
    e_hist = _elasticity(sp, fmt, sp.disc_hist)[:, None]
    units_hist = (base[:, None] * season[None, :] * np.exp(shock)
                  * (1.0 + e_hist * disc_hist * -1.0)
                  * np.exp(rng.normal(0, sp.noise_sd, size=(sp.n_stores, sp.n_weeks))))

    # randomised price test: volunteer stores, half get the deeper discount
    p_test = np.array(sp.test_prop)[fmt]
    in_test = rng.random(sp.n_stores) < p_test
    treated = in_test & (rng.random(sp.n_stores) < 0.5)
    e_test = _elasticity(sp, fmt, sp.disc_test)
    lift = np.where(treated, 1.0 + (-e_test) * sp.disc_test, 1.0)
    units_test = (base * season.mean() * lift
                  * np.exp(rng.normal(0, sp.noise_sd, size=sp.n_stores)))

    return dict(spec=sp, fmt=fmt, units_hist=units_hist, disc_hist=disc_hist,
                in_test=in_test, treated=treated, units_test=units_test, season=season)


def truth_f2(w):
    """Estate-wide units index next quarter under the algorithm's 18% discount, vs the status quo."""
    sp, fmt = w["spec"], w["fmt"]
    base = np.array(sp.base)[fmt]
    e_t = _elasticity(sp, fmt, sp.disc_target)
    idx = float(np.average(1.0 + (-e_t) * sp.disc_target, weights=base))
    return dict(units_index=idx, decision="adopt" if idx >= sp.margin_gate else "reject")


def estimators_f2(w):
    sp, fmt = w["spec"], w["fmt"]
    base = np.array(sp.base)[fmt]
    pop_w = base
    test_w = base * w["in_test"]
    out = {}

    # causal elasticity per format from the randomised test, at the TEST discount depth
    e_hat = {}
    for f in range(3):
        mt = (fmt == f) & w["treated"]
        mc = (fmt == f) & w["in_test"] & (~w["treated"])
        if mt.sum() < 5 or mc.sum() < 5:
            e_hat[f] = None
            continue
        ratio = w["units_test"][mt].mean() / w["units_test"][mc].mean()
        e_hat[f] = -(ratio - 1.0) / sp.disc_test

    def extrapolate(f, disc):
        """Carry the measured elasticity to a deeper discount using the curvature the test itself
        reveals across its own discount range."""
        if e_hat[f] is None:
            return 0.0
        scale = (1.0 + sp.elast_curv * (disc - sp.disc_hist) / sp.disc_hist) / \
                (1.0 + sp.elast_curv * (sp.disc_test - sp.disc_hist) / sp.disc_hist)
        return e_hat[f] * scale

    def index(e, disc):
        """Units index at a discount depth. Elasticity is negative, so a deeper discount RAISES
        units: index = 1 + (-e) * disc. Keeping this in one helper avoids the sign slip that an
        earlier version of this file made in the estimators but not in the truth."""
        return 1.0 + (-e) * disc

    # VALID: transport across store mix AND price depth
    vals = np.array([index(extrapolate(f, sp.disc_target), sp.disc_target) for f in fmt])
    out["V1_transport_mix_and_depth"] = float(np.average(vals, weights=pop_w))

    # WRONG: historical price coefficient (confounded by manager pricing)
    x = w["disc_hist"].ravel()
    y = (w["units_hist"] / (np.array(sp.base)[fmt][:, None] * w["season"][None, :])).ravel()
    A = np.column_stack([np.ones_like(x), x])
    coef = np.linalg.lstsq(A, y, rcond=None)[0]
    out["W1_historical_price_coef"] = float(coef[0] + coef[1] * sp.disc_target)

    # WRONG: test elasticity, right mix, WRONG depth (no curvature extrapolation)
    v = np.array([index(e_hat[f] or 0.0, sp.disc_target) for f in fmt])
    out["W2_mix_fixed_depth_not"] = float(np.average(v, weights=pop_w))

    # WRONG: test elasticity at correct depth but TEST mix (selection not fixed)
    v = np.array([index(extrapolate(f, sp.disc_target), sp.disc_target) for f in fmt])
    out["W3_depth_fixed_mix_not"] = float(np.average(v, weights=test_w))

    # WRONG: single pooled elasticity from the test, applied flat
    mt, mc = w["treated"], w["in_test"] & ~w["treated"]
    e_pool = -((w["units_test"][mt].mean() / w["units_test"][mc].mean()) - 1.0) / sp.disc_test
    out["W4_pooled_test_elasticity"] = float(index(e_pool, sp.disc_target))

    # WRONG: no price response at all
    out["W5_status_quo"] = 1.0
    return out


REGIMES_F2 = [
    SpecF2(name="visible"),
    SpecF2(name="hidden_a_strong_selection", seed=370002, test_prop=(0.02, 0.06, 0.30)),
    SpecF2(name="hidden_b_flat_curvature", seed=370003, elast_curv=0.08),
    SpecF2(name="hidden_c_steep_curvature", seed=370004, elast_curv=1.10),
]

HINTS_F2 = {
    "H0_no_hint": ["W1_historical_price_coef", "W5_status_quo"],
    "H1_elasticity_does_not_transport_from_test_stores": ["W3_depth_fixed_mix_not"],
    "H2_elasticity_changes_with_discount_depth": ["W2_mix_fixed_depth_not"],
    "H1+H2_both": ["V1_transport_mix_and_depth"],
}


def main():
    print("=" * 96)
    print("F2  ALGORITHMIC REPRICING - runner-up finalist")
    print("=" * 96)
    rows = []
    for sp in REGIMES_F2:
        w = world_f2(sp)
        rows.append((sp, w, truth_f2(w), estimators_f2(w)))
    names = [r[0].name for r in rows]
    print("%-34s %s" % ("quantity", "".join("%22s" % n[:21] for n in names)))
    print("%-34s %s" % ("TRUTH units index",
                        "".join("%22.4f" % r[2]["units_index"] for r in rows)))
    print("%-34s %s" % ("TRUTH decision", "".join("%22s" % r[2]["decision"] for r in rows)))
    print("-" * 96)
    for k in rows[0][3]:
        print("%-34s %s" % (k, "".join("%22s" % ("%+.4f" % (r[3][k] - r[2]["units_index"]))
                                       for r in rows)))
    print("\n(values are ERROR against latent truth)")

    # sampling sd of the accepted estimator
    sds = []
    for sp in REGIMES_F2:
        e = []
        for r in range(8):
            w = world_f2(replace(sp, seed=sp.seed + 811 * r))
            e.append(estimators_f2(w)["V1_transport_mix_and_depth"] - truth_f2(w)["units_index"])
        sds.append(np.std(e))
    sd = float(np.mean(sds))
    print("\naccepted-estimator sampling sd: %.5f" % sd)

    print("\nRECOGNITION-VS-EXECUTION (errors in units of that sd)")
    print("%-52s %s  %s" % ("insight given away", "".join("%12s" % n[:11] for n in names), "worst"))
    for hint, keys in HINTS_F2.items():
        best = [min(abs(r[3][k] - r[2]["units_index"]) for k in keys if k in r[3]) for r in rows]
        print("%-52s %s  %5.1f sd" % (hint, "".join("%12.1f" % (v / sd) for v in best),
                                      max(best) / sd))
    print("\nwrong DECISIONS after each insight:")
    for hint, keys in HINTS_F2.items():
        bad = sum(1 for sp, w, t, e in rows
                  if ("adopt" if e[keys[0]] >= sp.margin_gate else "reject") != t["decision"])
        print("   %-52s %d / %d" % (hint, bad, len(rows)))


if __name__ == "__main__":
    main()
