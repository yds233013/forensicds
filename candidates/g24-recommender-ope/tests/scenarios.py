"""Hidden extracts for G24 (never present in the agent's environment).

Every fixture keeps the documented mechanisms (retrieval pool, uniform exploration ordering, downstream eligibility
filter, cache TTL and reloads, position-based clicks, launch rule) and changes the regime: device mix and examination
curves, pool sizes, exploration share, reload rates, and which candidate ranker is actually worth launching.

Build-time requirement (tools/g24/fixture_audit.py): every candidate's true lift is at least 3 reference standard
errors away from the launch rule's boundary (lift / SE = 1.96), and every accepted estimator reproduces the true
launch on the frozen extract.
"""
import copy

from world import THETA, VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: TV-heavy traffic with a much steeper TV examination curve and less exploration; launching v7_pd is right.
    _spec(name="hidden_a", seed=20251104, start="2025-10-06", days=84, n_decisions=150_000,
          device_mix=(0.25, 0.30, 0.45), explore_share=0.35, ab_window=(30, 55),
          theta={**THETA, "tv": [1.00, 0.45, 0.27, 0.17, 0.11]},
          reload_lambda={"web": 0.12, "mobile": 0.22, "tv": 0.70}, v7_order_novelty=0.50),
    # B: neither candidate beats production (keep v6): v7 over-weights novelty, v7_pd picks a weak row.
    _spec(name="hidden_b", seed=20260213, start="2026-01-12", days=90, n_decisions=130_000,
          explore_share=0.50, ab_window=(40, 62), v7_order_novelty=1.10, v7pd_noise=0.30,
          pool_k_device={"web": (14, 20), "mobile": (10, 16), "tv": (7, 11)}),
    # C: v7 is a genuinely better relevance ranker (launch v7); v7_pd is weak; mobile-heavy with more reloads.
    _spec(name="hidden_c", seed=20261207, start="2026-09-14", days=88, n_decisions=130_000,
          device_mix=(0.35, 0.45, 0.20), explore_share=0.42, ab_window=(35, 58),
          v7_mode="relevance", v7_noise=0.010, v7pd_noise=0.20,
          reload_lambda={"web": 0.20, "mobile": 0.35, "tv": 0.55}),
]
