"""Settling the consequences, and the verdict on the published figure.

Where Schedule 4 is unexecuted, the agreement admits two readings of any line amended after confirmation. A
consequence follows from the evidence only where both readings give the same answer; where they differ, the
evidence does not settle it, and saying so is the finding.
"""


def settle(low, high, predicate):
    a, b = predicate(low), predicate(high)
    if a != b:
        return "not_determinable"
    return "yes" if a else "no"


def verdict(published_pct, contract_pct, ambiguity_material, tol_pp=0.05):
    if ambiguity_material:
        # The agreement does not define a single figure for this period, so whether the published figure is
        # that figure cannot be settled.
        return "not_determinable_from_available_evidence"
    return "incumbent_correct" if abs(published_pct - contract_pct) <= tol_pp else "incumbent_incorrect"
