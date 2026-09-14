"""Issued statements exported by the billing system (ledger/issued/)."""
from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


def billed_to_date(issued_dir: Path, before_statement_month: str) -> dict:
    """(customer_id, meter, service_month) -> (quantity, amount) billed on all statements issued before the month."""
    totals = defaultdict(lambda: [Decimal(0), Decimal(0)])
    for path in sorted(Path(issued_dir).glob("statement_*.csv")):
        with open(path, newline="") as fh:
            for row in csv.DictReader(fh):
                if row["statement_month"] >= before_statement_month:
                    continue
                t = totals[(row["customer_id"], row["meter"], row["service_month"])]
                t[0] += Decimal(row["quantity"])
                t[1] += Decimal(row["amount"])
    return {k: (q, a) for k, (q, a) in totals.items()}
