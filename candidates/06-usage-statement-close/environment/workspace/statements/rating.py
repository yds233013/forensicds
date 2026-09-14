"""Usage charges under a rate card."""
from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from statements.terms import Terms

CENT = Decimal("0.01")


def usage_charge(terms: Terms, quantity: Decimal) -> Decimal:
    """Charge for a month's quantity: units above the included allowance, Tier 1 rate up to tier1_units, Tier 2 above."""
    overage = max(Decimal(0), quantity - terms.included_units)
    tier1 = min(overage, terms.tier1_units)
    amount = tier1 * terms.tier1_rate + (overage - tier1) * terms.tier2_rate
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)
