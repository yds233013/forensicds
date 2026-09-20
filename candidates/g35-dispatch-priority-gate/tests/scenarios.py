"""Graded extracts for G35. The hidden ones never exist in the agent's environment.

Every extract keeps the documented mechanism - a fixed courier pool per city-day, proportional
rationing weighted by dispatch priority, a randomised-saturation two-stage design - and varies only
the operating regime: how tight couriers are, and how much genuine routing efficiency the new
dispatcher actually adds.

SE_REF holds, per extract and graded quantity, the reference standard error: the RMSE of the accepted
estimator over Monte-Carlo redraws of the same design (tools/g35/fixture_audit.py).
Tolerance = TOL_MULTIPLIER x SE_REF.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: couriers very tight, but the new dispatcher adds almost no real routing efficiency.
    #    The largest pooled lift in the whole set sits on the smallest true rollout effect.
    _spec(name="hidden_a", seed=8814423, capacity_ratio=0.65, delta=0.010,
          n_cities=56, start_date="2026-02-09"),
    # B: couriers only moderately tight, and again little real efficiency -> hold.
    _spec(name="hidden_b", seed=6627159, capacity_ratio=0.92, delta=0.012,
          n_cities=64, start_date="2026-05-11"),
    # C: couriers very tight AND the dispatcher genuinely routes better -> launch.
    #    Its pooled lift is within 5% of hidden_a's, and its rollout effect is ten times larger.
    _spec(name="hidden_c", seed=4432901, capacity_ratio=0.70, delta=0.090,
          n_cities=58, start_date="2026-03-02"),
]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)


ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]

QUANT = ("direct_effect_50", "spillover_50", "policy_effect_full")

# filled in by tools/g35/fixture_audit.py (Monte-Carlo redraws of the same design)
SE_REF = {
    'visible': {
        'direct_effect_50': 0.00639069,
        'spillover_50': 0.00884640,
        'policy_effect_full': 0.00481720,
    },
    'hidden_a': {
        'direct_effect_50': 0.00561478,
        'spillover_50': 0.00687510,
        'policy_effect_full': 0.00453188,
    },
    'hidden_b': {
        'direct_effect_50': 0.00521855,
        'spillover_50': 0.00748449,
        'policy_effect_full': 0.00439895,
    },
    'hidden_c': {
        'direct_effect_50': 0.00447701,
        'spillover_50': 0.00542645,
        'policy_effect_full': 0.00474999,
    },
}
SE_REF_REDRAWS = 60

# Tolerance = TOL_MULTIPLIER x SE_REF, chosen from a MEASURED window rather than inherited.
# The widest legitimate route (the largest-pools subsample) errs by 1.85 SE_REF at worst, and the
# sharpest wrong analysis that must be caught - reporting the whole 50%-saturated experiment as the
# rollout effect - errs by 4.42 SE_REF at best. Any multiplier in (1.85, 4.42) separates them; 3.0
# sits near the geometric centre, leaving the worst valid route at 0.62 of tolerance and catching
# that wrong analysis at 1.47x tolerance.
# G34's multiplier of 5.0 was explicitly rejected here: it would put tolerance at 0.024 and let the
# wrong analysis through.
TOL_MULTIPLIER = 3.0
