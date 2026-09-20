"""Graded extracts for G34 (the hidden ones are never present in the agent's environment).

Every extract keeps the documented mechanisms - the 24-month overhaul SOP with shutdown-window
scheduling, retirement on commercial grounds, telemetry channels that fail with the housings they
monitor, and the FY27 procurement rule - and changes the operating regime: how early assemblies are
exchanged, how fast units leave the fleet, and how long an assembly lasts.

SE_REF holds, per extract and graded quantity, the reference standard error: the RMSE of the
accepted estimator over Monte-Carlo redraws of the same design (tools/g34/fixture_audit.py).
Tolerance = TOL_MULTIPLIER x SE_REF.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: a materially longer assembly life, so fewer reach an unplanned failure -> baseline build
    _spec(name="hidden_a", seed=77310441, n_units=8200, cut_off="2026-05-31",
          wb_scale=50.0),
    # B: the fleet is being wound down; units leave before their assemblies can fail -> baseline build
    _spec(name="hidden_b", seed=41920673, n_units=9600, cut_off="2026-09-30",
          retire_scale=32.0, retire_shape=1.4),
    # C: a materially shorter assembly life -> expanded build
    _spec(name="hidden_c", seed=60518824, n_units=8800, cut_off="2026-03-31",
          history_months=78, wb_scale=30.0),
]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)


ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]

# filled in by tools/g34/fixture_audit.py (Monte-Carlo redraws of the same design)
SE_REF = {
    'visible': {
        'unplanned_failure_rate_36m': 0.00275468,
        'overhaul_rate_36m': 0.00336493,
        'retirement_rate_36m': 0.00204133,
        'still_original_assembly_36m': 0.00213713,
        'assembly_failure_rate_36m': 0.00980079,
    },
    'hidden_a': {
        'unplanned_failure_rate_36m': 0.00259979,
        'overhaul_rate_36m': 0.00336642,
        'retirement_rate_36m': 0.00241851,
        'still_original_assembly_36m': 0.0023744,
        'assembly_failure_rate_36m': 0.0092204,
    },
    'hidden_b': {
        'unplanned_failure_rate_36m': 0.00247415,
        'overhaul_rate_36m': 0.0026568,
        'retirement_rate_36m': 0.00268803,
        'still_original_assembly_36m': 0.0012654,
        'assembly_failure_rate_36m': 0.0165894,
    },
    'hidden_c': {
        'unplanned_failure_rate_36m': 0.00299371,
        'overhaul_rate_36m': 0.00309229,
        'retirement_rate_36m': 0.002258,
        'still_original_assembly_36m': 0.00158789,
        'assembly_failure_rate_36m': 0.00790124,
    },
}
SE_REF_REDRAWS = 100

# Tolerance = TOL_MULTIPLIER x SE_REF.  Set from the accepted estimator's own sampling
# behaviour: SE_REF itself carries ~1/sqrt(2*100) ~ 7% sampling error, and 20 numeric checks
# must pass jointly, so the multiplier has to cover the joint tail, not a single 2-sigma test.
TOL_MULTIPLIER = 5.0
