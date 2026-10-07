"""Graded extracts for G50. Hidden extracts never appear in the agent's environment.

The four regimes differ in WHICH channel dominates the policy contrast, so that neither a constant
decision nor a constant magnitude can pass:

  visible   idling cost slightly exceeds the small supply gain -> Boost is not worth buying
  hidden_a  a large courier-supply response and almost no idling cost -> Boost is worth buying
  hidden_b  a large idling cost and a negligible supply response -> Boost makes the metric worse
  hidden_c  a moderate supply response with a strong density payoff -> Boost is worth buying, but the
            supply response is less than half hidden_a's, so a memorised magnitude fails
  hidden_d  a supply response that just outweighs the idling cost -> Boost helps, but by far less than
            it costs. This is the only world in which the memo's break-even figure is BINDING: the
            estate-wide effect is a reduction of about 0.30 pp against a 1.4961 pp break-even, so an
            analysis that rolls out on any reduction at all reaches the wrong decision, while every
            estimator that is accepted elsewhere still reads above -1.4961 and so still declines.
"""
import copy
from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    _spec(name="hidden_a", seed=730221, promise_min=36.6, delta_accept_min=0.55,
          beta_supply=0.235, gamma_idle=0.010),
    _spec(name="hidden_b", seed=884413, promise_min=38.6, delta_accept_min=0.10,
          beta_supply=0.018, gamma_idle=0.095),
    _spec(name="hidden_c", seed=196077, promise_min=37.2, delta_accept_min=0.40,
          beta_supply=0.120, eta_density=1.15, gamma_idle=0.020),
    _spec(name="hidden_d", seed=515309, beta_supply=0.100),
]

ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)
