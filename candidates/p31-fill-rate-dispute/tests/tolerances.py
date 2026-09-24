"""Graded tolerances for P31, with the basis for each.

The quantities are deterministic counts over the order book, so these are not sampling allowances. They admit
rounding and a defensible reading of the period boundary, and nothing more.

`accounts_below_floor` is graded to +/-1 rather than exactly: on two of the four extracts an account sits within
0.07 pp of the contractual floor, so grading the count exactly would grade precision at a knife edge rather than
the substantive finding. The substantive finding - that the accounts which escalated are materially below the
floor - is graded directly through their own rates, which sit 1 to 7 pp below it.
"""
RATE_PP = 0.15
ACCOUNT_RATE_PP = 0.30
BRIDGE_PP = 0.40
BRIDGE_SUM_PP = 0.25
BELOW_FLOOR_COUNT = 1
TICKET_SHARE_PP = 2.0
