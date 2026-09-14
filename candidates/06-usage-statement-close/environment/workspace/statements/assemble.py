"""Assemble a month's usage statement."""
from __future__ import annotations

from decimal import Decimal

import pandas as pd

from statements.calendar import previous_month, statement_close
from statements.rating import usage_charge
from statements.terms import Terms, terms_for

LINE_COLUMNS = ["statement_month", "customer_id", "meter", "line_type", "service_month", "quantity", "amount"]


def assemble_statement(usage: pd.DataFrame, cards: list[Terms], month: str, close_hours: int) -> pd.DataFrame:
    opens = statement_close(previous_month(month), close_hours)
    closes = statement_close(month, close_hours)
    period = usage[(usage["received_at"] >= opens) & (usage["received_at"] < closes)]
    lines = []
    for (customer_id, meter), rows in period.groupby(["customer_id", "meter"], sort=True):
        quantity = sum((Decimal(x) for x in rows["quantity"]), Decimal(0))
        if quantity <= 0:
            continue
        amount = usage_charge(terms_for(cards, customer_id, meter, month), quantity)
        lines.append([month, customer_id, meter, "usage", month, f"{quantity:.3f}", f"{amount:.2f}"])
    return pd.DataFrame(lines, columns=LINE_COLUMNS)
