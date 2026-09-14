"""Assemble a month's usage statement (contract §4.3-4.4, billing schedule)."""
from __future__ import annotations

from decimal import Decimal

import pandas as pd

from metering.normalize import current_records
from statements.calendar import statement_close
from statements.rating import usage_charge
from statements.terms import Terms, terms_for

LINE_COLUMNS = ["statement_month", "customer_id", "meter", "line_type", "service_month", "quantity", "amount"]


def assemble_statement(records: pd.DataFrame, cards: list[Terms], month: str, close_hours: int,
                       billed: dict) -> pd.DataFrame:
    """Usage reported by the close: the month's usage, plus adjustments for earlier months whose usage known at the
    close differs from what issued statements billed for them. Each month is rated under its own rate card."""
    known = current_records(records, statement_close(month, close_hours))
    known = known[known["service_month"] <= month]
    quantities = (known.groupby(["customer_id", "meter", "service_month"], sort=True)["quantity"]
                       .agg(lambda s: sum((Decimal(x) for x in s), Decimal(0))).to_dict())
    keys = set(quantities) | {k for k in billed if k[2] < month}
    lines = []
    for customer_id, meter, service_month in sorted(keys):
        quantity = quantities.get((customer_id, meter, service_month), Decimal(0))
        terms = terms_for(cards, customer_id, meter, service_month)
        if service_month == month:
            if quantity > 0:
                lines.append([month, customer_id, meter, "usage", month, f"{quantity:.3f}",
                              f"{usage_charge(terms, quantity):.2f}"])
            continue
        billed_q, billed_a = billed.get((customer_id, meter, service_month), (Decimal(0), Decimal(0)))
        if quantity != billed_q:
            lines.append([month, customer_id, meter, "adjustment", service_month, f"{quantity - billed_q:.3f}",
                          f"{usage_charge(terms, quantity) - billed_a:.2f}"])
    return pd.DataFrame(lines, columns=LINE_COLUMNS)
