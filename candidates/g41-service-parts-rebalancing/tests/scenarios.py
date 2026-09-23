"""Graded extracts for G41. Hidden extracts are never present in the agent's environment.

The regimes are operational weeks a field-service planner actually sees: a normal week, a week with a
large QA hold, a week where the network is spread out (long lanes), and a week carried by inbound
receipts. All keep the same policy constants (dock-to-stock, safety stock semantics, SLA limit).
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: a large QA hold on inbound lots; more stock exists than is usable
    _spec(name="hidden_a", seed=51120993, quarantine_share=0.30, consignment_share=0.10, alloc_share=0.35),
    # B: a spread-out network week - longer lanes, so transfers often cannot land before need-by
    _spec(name="hidden_b", seed=27604415, transit_days=(3, 7), alloc_share=0.40, stock_units=(4, 18)),
    # C: a light week just after a restock - stock is plentiful and inbound lands early
    _spec(name="hidden_c", seed=93318726, inbound_per_depot=(2, 5), inbound_late_share=0.15,
          stock_units=(9, 28), alloc_share=0.25, n_jobs=185, quarantine_share=0.08),
]

ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)
