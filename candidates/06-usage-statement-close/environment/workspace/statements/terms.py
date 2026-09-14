"""Customer rate cards (config/rate_cards.csv): included units and overage tiers, effective by month."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Terms:
    customer_id: str
    meter: str
    effective_month: str
    included_units: Decimal
    tier1_units: Decimal
    tier1_rate: Decimal
    tier2_rate: Decimal


def load_rate_cards(path: Path) -> list[Terms]:
    with open(path, newline="") as fh:
        return [Terms(r["customer_id"], r["meter"], r["effective_month"], Decimal(r["included_units"]),
                      Decimal(r["tier1_units"]), Decimal(r["tier1_rate"]), Decimal(r["tier2_rate"]))
                for r in csv.DictReader(fh)]


def terms_for(cards: list[Terms], customer_id: str, meter: str, month: str) -> Terms:
    matching = [t for t in cards if t.customer_id == customer_id and t.meter == meter and t.effective_month <= month]
    if not matching:
        raise KeyError(f"no rate card for {customer_id}/{meter} in {month}")
    return max(matching, key=lambda t: t.effective_month)
