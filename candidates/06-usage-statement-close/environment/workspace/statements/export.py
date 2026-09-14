"""Write statement outputs (see docs/data_catalog.md)."""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pandas as pd


def write_statement(lines: pd.DataFrame, out_dir: Path, month: str, close_at: pd.Timestamp) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    lines = lines.sort_values(["customer_id", "meter", "line_type", "service_month"], kind="mergesort")
    lines.to_csv(out_dir / "statement_lines.csv", index=False, lineterminator="\n")
    customers = []
    for customer_id, rows in lines.groupby("customer_id", sort=True):
        usage = sum((Decimal(a) for a in rows.loc[rows["line_type"] == "usage", "amount"]), Decimal("0.00"))
        adjust = sum((Decimal(a) for a in rows.loc[rows["line_type"] == "adjustment", "amount"]), Decimal("0.00"))
        customers.append({"customer_id": customer_id, "usage_amount": f"{usage:.2f}",
                          "adjustment_amount": f"{adjust:.2f}", "total_amount": f"{usage + adjust:.2f}"})
    summary = {"statement_month": month, "close_at": close_at.strftime("%Y-%m-%dT%H:%M:%SZ"), "customers": customers}
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
