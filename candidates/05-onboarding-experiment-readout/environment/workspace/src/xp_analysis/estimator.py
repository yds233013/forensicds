"""Stratified difference in proportions with Neyman variance (XPP-7)."""
from __future__ import annotations

import math

import pandas as pd


def estimate(units: pd.DataFrame, z: float, treatment_share: float) -> dict:
    n_total = len(units)
    effect, var, strata = 0.0, 0.0, []
    for stratum, g in units.groupby("stratum", sort=True):
        t = g.loc[g["arm"] == "treatment", "activated"].astype(float)
        c = g.loc[g["arm"] == "control", "activated"].astype(float)
        if len(t) < 2 or len(c) < 2:
            raise ValueError(f"stratum {stratum!r} has fewer than 2 units in an arm")
        w = len(g) / n_total
        diff = t.mean() - c.mean()
        effect += w * diff
        var += w * w * (t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c))
        strata.append({"stratum": stratum, "n_control": int(len(c)), "n_treatment": int(len(t)),
                       "rate_control": float(c.mean()), "rate_treatment": float(t.mean()), "effect": float(diff),
                       "weight": float(w)})
    se = math.sqrt(var)
    lo, hi = effect - z * se, effect + z * se
    n_t = int((units["arm"] == "treatment").sum())
    n_c = n_total - n_t
    exp_t, exp_c = n_total * treatment_share, n_total * (1 - treatment_share)
    chi2 = (n_t - exp_t) ** 2 / exp_t + (n_c - exp_c) ** 2 / exp_c
    return {
        "n_units_control": n_c,
        "n_units_treatment": n_t,
        "rate_control": float(units.loc[units["arm"] == "control", "activated"].mean()),
        "rate_treatment": float(units.loc[units["arm"] == "treatment", "activated"].mean()),
        "effect": float(effect),
        "se": float(se),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "decision": "ship" if lo > 0 else ("rollback" if hi < 0 else "inconclusive"),
        "srm_p_value": float(math.erfc(math.sqrt(chi2 / 2))),
        "strata": strata,
    }
