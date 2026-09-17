"""Hidden warehouses for G05 (never present in the agent's environment).

Every fixture keeps the documented mechanisms (format-led wave sequencing, bay-dependent kit versions, install
closures before go-live, slips against the plan, comparable trading weeks, the tranche-2 gate) and changes the regime:
chain size and calendar, which kit version actually lifts net sales, the direction of format trends, slip rates and
install timing.

SE_REF holds, per extract and graded quantity, the reference standard error: the RMSE of the least efficient accepted
estimator over Monte-Carlo noise redraws with the design held fixed (tools/g05/fixture_audit.py). Tolerance = 3.5 x
SE_REF (research/g05/G05_phase0_gate.md).
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: the compact kit lifts net sales too (tranche 2 should continue); smaller chain, earlier calendar.
    _spec(name="hidden_a", seed=20250308, start="2022-10-03", T=152, n_stores=840,
          planned_week=(70, 82, 92, 102), remaining_weeks=(166, 178),
          basket_effect={"full": 0.070, "compact": 0.060}),
    # B: large formats in secular decline and neighbourhood stores growing (untreated trends reversed), a slower
    # learning ramp, and some Supercentres without a usable bay (compact kit); stop.
    _spec(name="hidden_b", seed=20251119, start="2023-03-06", T=158, n_stores=940,
          planned_week=(80, 88, 98, 108), remaining_weeks=(172, 184),
          trend_per_year={"Supercentre": -0.045, "Market": 0.000, "Neighbourhood": 0.020}, ramp_scale=14.0,
          full_kit_prob={"Supercentre": 0.85, "Market": 0.75, "Neighbourhood": 0.25},
          wave_probs={**VISIBLE_SPEC["wave_probs"], "Supercentre|compact": (0.10, 0.15, 0.20, 0.20, 0.35)}),
    # C: heavy slips, installs mostly two weeks before go-live, compact kit moderately effective; continue.
    _spec(name="hidden_c", seed=20260622, start="2023-06-05", T=154, n_stores=900,
          planned_week=(74, 86, 94, 104), remaining_weeks=(168, 180),
          slip_rate=0.32, install_week_probs=(0.20, 0.65, 0.15),
          basket_effect={"full": 0.070, "compact": 0.050}),
]

SE_REF_REDRAWS = 30
SE_REF = {
    "visible": {
        "wave.1": 0.001882,
        "wave.2": 0.002069,
        "wave.3": 0.00147,
        "wave.4": 0.001952,
        "gate": 0.001303
    },
    "hidden_a": {
        "wave.1": 0.002615,
        "wave.2": 0.00238,
        "wave.3": 0.002395,
        "wave.4": 0.001967,
        "gate": 0.001193
    },
    "hidden_b": {
        "wave.1": 0.001659,
        "wave.2": 0.002017,
        "wave.3": 0.001915,
        "wave.4": 0.001465,
        "gate": 0.001074
    },
    "hidden_c": {
        "wave.1": 0.001851,
        "wave.2": 0.001891,
        "wave.3": 0.002027,
        "wave.4": 0.001608,
        "gate": 0.001084
    }
}
