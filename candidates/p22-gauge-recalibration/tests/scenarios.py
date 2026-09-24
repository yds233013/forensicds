"""Graded extracts for P22. Hidden extracts are never present in the agent's environment.

The regimes are plant situations a quality engineer actually meets, and they deliberately differ in *which*
cause is active, so that a constant answer cannot pass:

  hidden_a  a larger as-left bias and a materially harmless heat family - almost all measurement
  hidden_b  a genuinely bad heat family with only a small bias, plus an operator shift - the supplier
            decision REVERSES, so "the gauge is always the answer" fails
  hidden_c  a moderate bias with a real tool-wear ramp running through the window - the attribution must
            allocate to tooling, so "allocate everything to measurement" fails
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    for k, v in over.items():
        s[k] = v
    return s


HIDDEN_SPECS = [
    _spec(name="hidden_a", cert_scale_k=0.81, seed=61240817, bias_um=11.4,
          heat_families={"H2": (0.0, 0.0), "H3": (0.4, 1.2)}),
    _spec(name="hidden_b", cert_scale_k=1.35, seed=38915204, bias_um=3.9,
          heat_families={"H2": (0.0, 0.0), "H3": (5.4, 9.2)},
          operator_shift_um=3.4, operator_shift_who="OP-318", operator_shift_from_week=20),
    # The insert-change interval was extended in week 19 as a consumables saving, and the grade fitted wears
    # faster. Both are visible in tool_changes and in the tool_hours distribution, and they make tooling a
    # large real contributor - large enough that the rate the agreement names and the rate measured against
    # the conformance reference fall on opposite sides of the 5.5 % limit.
    _spec(name="hidden_c", cert_scale_k=0.93, seed=75503391, bias_um=6.7,
          heat_families={"H2": (0.0, 0.0), "H3": (1.6, 4.6)},
          tool_wear_um_per_hour=0.30, tool_hours_post=(2.0, 66.0)),
]

ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)
