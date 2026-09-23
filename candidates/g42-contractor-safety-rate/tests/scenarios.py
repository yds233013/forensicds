"""Graded extracts for G42. Hidden extracts are never present in the agent's environment.

Each is a real reporting period a contractor of this size would file: the visible quarter-end filing,
a heavy-agency period, a large estate with a long entry backlog, and a quiet period on a smaller
estate. Every extract keeps the same contract terms (200,000-hour basis, 12-month window, 1.50 limit).
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: a period carried by agency crews, with more paid non-work time (a heavy training quarter)
    _spec(name="hidden_a", seed=5514097, agency_share=0.41, nonwork_share=0.13, case_rate=1.05),
    # B: a large estate with a long entry backlog, so record dates drift far from occurrence dates
    _spec(name="hidden_b", seed=2244881, n_sites=34, late_entry_days=110, multi_site_share=0.26,
          case_rate=1.55),
    # C: a quieter period on a smaller estate
    _spec(name="hidden_c", seed=4471903, n_sites=24, case_rate=0.85, overtime_share=0.12),
]

ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)
