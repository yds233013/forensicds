"""Reporting calendar: calendar quarters [start_date, end_date), end_date = first day of the next quarter."""
from __future__ import annotations

from datetime import date


def reporting_quarters(as_of: date, n: int) -> list[tuple[str, str, str]]:
    y, q = as_of.year, (as_of.month - 1) // 3 + 1
    out = []
    for _ in range(n):
        q -= 1
        if q == 0:
            y, q = y - 1, 4
        start = date(y, 3 * q - 2, 1)
        end = date(y + 1, 1, 1) if q == 4 else date(y, 3 * q + 1, 1)
        out.append((f"{y}-Q{q}", start.isoformat(), end.isoformat()))
    return sorted(out, key=lambda t: t[1])
