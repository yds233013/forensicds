#!/usr/bin/env python3
"""Build-time only: reproduce the workspace's operating history after the world is generated.

- Pipeline runs for the July and August closes (out/), exactly as the streaming consumer produced them.
- Customer usage console export for Northwind as downloaded on 2026-09-12 07:00 UTC (exports/console/).
- Finance tie-out notebook for the August close (finance/).
- Capacity dashboard panel export with daily landing volume (dashboards/).
Deleted from the image after the build.
"""
import csv
import gzip
import json
import subprocess
import sys
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT))

for month in ("2026-07", "2026-08"):
    subprocess.run([sys.executable, "-m", "jobs.close_month", "--month", month], cwd=ROOT, check=True,
                   capture_output=True)

from metering.landing import read_deliveries  # noqa: E402
from metering.normalize import normalize  # noqa: E402
from statements.calendar import previous_month, statement_close  # noqa: E402

deliveries = read_deliveries(ROOT / "raw/landing")

# --- console export (event-time daily usage, current revision as known at download time)
EXPORT_AT = "2026-09-12T07:00:00Z"
best = {}
for part in sorted((ROOT / "raw/landing").glob("received_date=*/*.jsonl.gz")):
    with gzip.open(part, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            if d["received_at"] >= EXPORT_AT:
                continue
            r = d["record"]
            if r["customer_id"] != "cus_northwind":
                continue
            if r["event_id"] not in best or r["rev"] > best[r["event_id"]]["rev"]:
                best[r["event_id"]] = r
daily = defaultdict(Decimal)
for r in best.values():
    day = r["window_start"][:10]
    if "2026-08-01" <= day <= "2026-09-11":
        daily[(day, r["meter"])] += Decimal(r["quantity"])
out = ROOT / "exports/console"
out.mkdir(parents=True, exist_ok=True)
with open(out / "northwind_usage_daily_2026-09-12.csv", "w", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["usage_date", "meter", "quantity"])
    for (day, meter), q in sorted(daily.items()):
        w.writerow([day, meter, f"{q:.3f}"])

# --- finance tie-out notebook for the August close
usage = normalize(deliveries, 24)
rows = []
for month in ("2026-07", "2026-08"):
    opens, closes = statement_close(previous_month(month), 72), statement_close(month, 72)
    committed = usage[(usage["received_at"] >= opens) & (usage["received_at"] < closes)]
    issued = list(csv.DictReader(open(ROOT / f"out/statements/{month}/statement_lines.csv")))
    for meter in sorted(committed["meter"].unique()):
        vol = sum((Decimal(x) for x in committed.loc[committed["meter"] == meter, "quantity"]), Decimal(0))
        st = sum((Decimal(r["quantity"]) for r in issued if r["meter"] == meter), Decimal(0))
        rows.append((month, meter, f"{st:.3f}", f"{vol:.3f}", f"{st - vol:.3f}"))
table = "statement_month  meter            statement_quantity  collector_volume  difference\n" + "\n".join(
    f"{m:<16} {mt:<16} {a:>18} {b:>17} {c:>11}" for m, mt, a, b, c in rows)


def cell(kind, src, outputs=None):
    c = {"cell_type": kind, "metadata": {}, "source": src.splitlines(keepends=True)}
    if kind == "code":
        c["execution_count"] = None
        c["outputs"] = outputs or []
    return c


nb = {
    "cells": [
        cell("markdown", "# Usage statement tie-out: August 2026 close\n\nFinance, revenue operations (M. Okafor), "
                         "2026-09-04 01:40 UTC, before issuing. Statement quantity per meter must equal the collector "
                         "volume committed in the statement period (previous close to this close), after removing "
                         "collector redeliveries."),
        cell("code", "import sys; sys.path.insert(0, '..')\nfrom metering.landing import read_deliveries\n"
                     "from metering.normalize import normalize\nfrom statements.calendar import previous_month, "
                     "statement_close\n\nusage = normalize(read_deliveries('../raw/landing'), 24)"),
        cell("code", "import csv\nfrom decimal import Decimal\n\n"
                     "def tieout(usage, months):\n"
                     "    print('statement_month  meter            statement_quantity  collector_volume  difference')\n"
                     "    for month in months:\n"
                     "        opens, closes = statement_close(previous_month(month), 72), statement_close(month, 72)\n"
                     "        committed = usage[(usage.received_at >= opens) & (usage.received_at < closes)]\n"
                     "        lines = list(csv.DictReader(open(f'../out/statements/{month}/statement_lines.csv')))\n"
                     "        for meter in sorted(committed.meter.unique()):\n"
                     "            vol = sum(map(Decimal, committed.loc[committed.meter == meter, 'quantity']), Decimal(0))\n"
                     "            st = sum((Decimal(l['quantity']) for l in lines if l['meter'] == meter), Decimal(0))\n"
                     "            print(f'{month:<16} {meter:<16} {st:>18.3f} {vol:>17.3f} {st - vol:>11.3f}')\n\n"
                     "tieout(usage, ['2026-07', '2026-08'])",
             [{"output_type": "stream", "name": "stdout", "text": (table + "\n").splitlines(keepends=True)}]),
        cell("markdown", "Both closes tie out exactly. No reconciling items. Signed off for issuing."),
    ],
    "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
    "nbformat": 4, "nbformat_minor": 5,
}
(ROOT / "finance").mkdir(exist_ok=True)
(ROOT / "finance/tieout_2026-08.ipynb").write_text(json.dumps(nb, indent=1) + "\n")

# --- capacity dashboard panel (landing volume by received day and collector)
vol = deliveries[(deliveries["received_at"] >= "2026-08-15") & (deliveries["received_at"] < "2026-09-16")]
series = defaultdict(dict)
for (day, coll), n in vol.groupby([vol["received_at"].dt.strftime("%Y-%m-%d"), "collector"]).size().items():
    series[coll][day] = int(n)
panel = {
    "dashboard": "Metering / Landing volume", "exported_at": "2026-09-16T08:00:00Z",
    "panels": [{"title": "Records received per day", "unit": "records", "time_field": "received_at",
                "series": [{"collector": c, "points": [[d, n] for d, n in sorted(p.items())]}
                           for c, p in sorted(series.items())]}],
}
(ROOT / "dashboards").mkdir(exist_ok=True)
(ROOT / "dashboards/landing_volume_2026-09-16.json").write_text(json.dumps(panel, indent=1) + "\n")
print("history ok", len(rows))
