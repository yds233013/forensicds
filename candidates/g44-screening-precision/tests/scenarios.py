"""Graded extracts for G44. Hidden extracts are never present in the agent's environment.

Each is a quarter Kestrel would actually file: the visible quarter, a quarter with a heavy chargeback
backlog feeding ad-hoc reviews, a quarter where the quality programme was cut to one in twenty with a
larger pending tail, and a quarter on a tightened screen. The contract terms travel with the extract,
so the sampling fraction must be read rather than assumed.
"""
import copy

from world import VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: a chargeback backlog - twice the ad-hoc reviews, heavily enriched for fraud
    _spec(name="hidden_a", seed=3310891, ad_hoc_per_1000=14.0, ad_hoc_fraud_share=0.70, specificity=0.9985),
    # B: the quality programme cut to one in twenty, with a larger pending tail at extract time
    _spec(name="hidden_b", seed=1190337, quality_sample_n=20, pending_share=0.08),
    # C: a tightened screen - fewer flags, higher specificity, lower catch rate
    _spec(name="hidden_c", seed=5528117, sensitivity=0.90, specificity=0.9990, fraud_rate=0.028),
]

ALL_NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def by_name(name):
    if name == "visible":
        return copy.deepcopy(VISIBLE_SPEC)
    for s in HIDDEN_SPECS:
        if s["name"] == name:
            return copy.deepcopy(s)
    raise KeyError(name)
