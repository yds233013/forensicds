#!/usr/bin/env python3
"""Reproduce the operating history of the G08 workspace after the warehouse is generated.

Runs the accuracy mart as it was deployed (nightly run at the extract instant) and writes the September accuracy
review that Data Platform and Forecasting circulated from its outputs. Deleted from the image after the build.
"""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

AS_OF = "2026-09-22T06:00:00Z"


def main(root: Path) -> None:
    subprocess.run([sys.executable, "-m", "fcaccuracy", "build", "--as-of", AS_OF], cwd=root, check=True)
    out = root / "out/accuracy"
    summary = json.loads((out / "summary.json").read_text())
    h = summary["head_to_head"][0]
    sums = defaultdict(lambda: [0.0, 0.0])
    with open(out / "evaluation_examples.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["status"] == "scored":
                k = (r["kpi_month"], r["model"], r["portfolio"])
                sums[k][0] += float(r["abs_error_mwh"])
                sums[k][1] += float(r["actual_mwh"])
    packs = {}
    with open(root / "reports/kpi_packs/pack_history.csv", newline="") as fh:
        for r in csv.DictReader(fh):
            packs[(r["kpi_month"], r["model"], r["portfolio"])] = r
    rows = []
    for k in sorted(set(packs) | set(sums)):
        month, model, portfolio = k
        if month >= "2026-07":
            continue
        signed = packs.get(k, {}).get("wape_pct", "")
        restated = f"{100 * sums[k][0] / sums[k][1]:.1f}" if k in sums and sums[k][1] else ""
        rows.append(f"| {month} | {model} | {portfolio} | {signed + '%' if signed else '-'} | {restated + '%' if restated else '-'} |")
    text = f"""# Forecast accuracy review: September 2026

Prepared 22 September 2026 by Data Platform with Forecasting for the September model board. Source: accuracy mart
(`fcaccuracy`), nightly run {AS_OF}.

## Headline

v4 has been in production since 6 April 2026. Measured over each model's production period, v4's WAPE is
**{100 * h['wape_b']:.2f}%** against v3's **{100 * h['wape_a']:.2f}%**: a **{100 * h['relative_change']:.1f}%** change
({h['n_pairs']} v4 forecasts, KPI months {h['first_month']} to {h['last_month']}).

## What changed with the mart

- Accuracy is now measured against the most accurate settled volume available for each delivery day (reconciliation
  runs included) rather than early settlement estimates.
- The most recent forecast issued for each run is scored, so late weather updates are reflected.
- Portfolios follow the governed portfolio dimension.

History has been restated on this basis. The table compares the signed-off packs with the restated mart for the
months produced by the legacy notebook. BUSINESS is not part of the governed portfolio dimension and has no restated
history.

| KPI month | Model | Portfolio | Signed-off pack WAPE | Restated (mart) WAPE |
|---|---|---|---|---|
""" + "\n".join(rows) + """

## Recommendation (Forecasting)

Keep v4 in production and retire v3 shadow runs at the end of Q4.
"""
    (root / "reports/accuracy_review_2026-09.md").write_text(text)


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
