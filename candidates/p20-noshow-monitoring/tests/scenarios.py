"""Graded extracts for P20. Hidden extracts are never present in the agent's environment.

The regimes differ in *why* the monitored figure moved, and in what the model risk standard then requires, so
that no constant answer passes:

  visible   the programme's own success is the dominant cause; the model is intact          -> retain_model
  hidden_a  a new driver of attendance that postdates the model: discrimination genuinely
            falls on the policy-invariant population too, and the retrained candidate
            recovers it                                                                    -> replace_with_v4
  hidden_b  the feature enrichment join fails for most bookings, so the served scores lose
            their inputs; discrimination is genuinely below the floor, but rescoring from
            the patient record and the event log restores it                  -> remediate_feature_pipeline
  hidden_c  the backfill widened the feature window to all history, so the monitoring
            rescore is on a vintage the model never saw; the model as served is fine        -> retain_model
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    _spec(name="hidden_a", seed=48120733,
          interpreter_effect_from_week=30, interpreter_coef=3.1, v4_policy_leak=0.10,
          drift_from_week=30,
          drift_coef={"prior_no_shows_12m": 0.25, "age_18-29": 0.3, "age_75+": 0.3}),
    _spec(name="hidden_b", seed=90551428,
          feed_break_from_week=30, feed_break_share=0.88, feed_break_column="all"),
    _spec(name="hidden_c", seed=17734096, current_window_days=None,
          seed_history_days=1460, seed_history_appts=(24, 45)),
]

ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)
