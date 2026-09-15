"""Hidden extracts for G10 (never present in the agent's environment).

Every fixture keeps the documented mechanisms (traffic shapes by day type, order-up-to replenishment from the production
forecast, delivery slots, promotions, randomized LEAN-26 holdout, store calendar, lost shoppers at empty shelves) and
changes the calendar, the regime parameters and which categories genuinely change.
"""
import copy

from world import CATEGORIES, VISIBLE_SPEC


def _spec(**over):
    s = copy.deepcopy(VISIBLE_SPEC)
    s.update(over)
    return s


HIDDEN_SPECS = [
    # A: autumn/winter window (soups and hot drinks grow, ice cream declines); heavier day-to-day demand variability; flatter weekday traffic; leaner programme
    #    multiplier; more afternoon-slot stores; different go-live week, holiday hours and closure.
    _spec(name="hidden_a", seed=11011, start="2025-10-06", weeks=22, golive_week=10, alpha_scale=0.6, m_lean=1.15,
          afternoon_slot_stores=9, short_hours=[("2025-12-24", 8, 17)], closures=[(4, "2025-11-11")],
          competitor={"stores": 2, "week": 13, "effect": 0.90},
          profiles={**VISIBLE_SPEC["profiles"], "weekday": [4, 5, 6, 7, 7, 7, 7, 7, 7, 7, 8, 8, 7, 6]},
          categories={**CATEGORIES, "Soups & broths": (3.0, +0.26, 2.0), "Hot beverages": (4.0, +0.22, 1.9),
                      "Ice cream & frozen desserts": (3.5, -0.30, 2.4)}),
    # B (weak-censoring control): generous multipliers, half the stores in the holdout, no promotion cut,
    #    no competitor; different categories genuinely decline / grow.
    _spec(name="hidden_b", seed=22022, start="2026-01-05", weeks=26, golive_week=13, m_pre=2.4, m_lean=2.0,
          m_holdout=2.4, holdout_stores=8, promo_share_post=0.12, competitor=None,
          short_hours=[("2026-04-03", 9, 18)], closures=[],
          categories={**CATEGORIES, "Breakfast cereals": (5.0, -0.26, 1.8), "Soft drinks": (3.0, +0.30, 2.2),
                      "Soups & broths": (3.0, 0.0, 2.0)}),
    # C: late-summer to autumn window (soups grow, ice cream declines); strong evening peak; promotion-heavy; v4 under-reacts strongly to promotions; less day-to-day variability;
    #    shorter Sunday trading; two closures.
    _spec(name="hidden_c", seed=33033, start="2026-05-04", weeks=24, golive_week=11, alpha_scale=1.3,
          promo_share_pre=0.20, promo_share_post=0.15, v4_promo_under=0.7,
          hours={"weekday": (8, 22), "saturday": (8, 22), "sunday": (11, 17)},
          profiles={"weekday": [1, 2, 3, 3, 4, 4, 4, 4, 5, 7, 12, 16, 15, 10],
                    "saturday": VISIBLE_SPEC["profiles"]["saturday"], "sunday": [8, 12, 13, 12, 10, 8]},
          short_hours=[("2026-08-31", 8, 18)], closures=[(2, "2026-07-14"), (9, "2026-09-01")],
          competitor={"stores": 2, "week": 16, "effect": 0.90},
          categories={**CATEGORIES, "Soups & broths": (3.0, +0.30, 2.0), "Hot beverages": (4.0, 0.0, 1.9),
                      "Ice cream & frozen desserts": (3.5, -0.26, 2.4)}),
]
