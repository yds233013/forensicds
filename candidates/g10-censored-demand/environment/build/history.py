#!/usr/bin/env python3
"""Reproduce the operating history of the G10 workspace after the warehouse is generated (build stage only).

- runs the deployed review (`python -m demandsci review`) and writes the Q3 category review from its outputs;
- runs the availability KPI query;
- writes the July analyst notebook that estimated LEAN-26 lost sales by filling stockout days at the clean-day average;
- writes the LEAN-26 week-8 finance readout.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd


def main(root: Path) -> None:
    sys.path.insert(0, str(root.resolve()))
    for sub in ("reports", "notebooks", "out"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "demandsci", "review", "--db", "data/warehouse.sqlite", "--out", "out/review"],
                   cwd=root, check=True)
    con = sqlite3.connect(root / "data/warehouse.sqlite")
    go_live = con.execute("SELECT MIN(go_live_date) FROM programme_assignment").fetchone()[0]
    gl = date.fromisoformat(go_live)

    # -------------------------------------------------------------------- category review (deployed outputs)
    trends = list(csv.DictReader(open(root / "out/review/category_trends.csv")))
    sales = pd.read_sql_query(
        """SELECT s.category, CASE WHEN h.date >= ? THEN 'post' ELSE 'pre' END AS period, SUM(h.units) AS units,
                  COUNT(DISTINCT h.date) AS days
           FROM sales_hourly h JOIN skus s ON s.sku_id = h.sku_id GROUP BY 1, 2""", con, params=(go_live,))
    sales["per_day"] = sales["units"] / sales["days"]
    sp = sales.pivot(index="category", columns="period", values="per_day")
    lines = ["# Q3 category review: demand baselines and buy plan", "",
             f"Prepared by Supply Planning from `demandsci review` (release 2.3.1). Periods: before and after the LEAN-26 go-live ({go_live}).", "",
             "| Category | Sales per day, change | Baseline pre | Baseline post | Baseline change | Proposed action |",
             "|---|---|---|---|---|---|"]
    n_reduce = 0
    for r in trends:
        ch_sales = 100 * (sp.loc[r["category"], "post"] / sp.loc[r["category"], "pre"] - 1)
        n_reduce += r["action"] == "reduce"
        lines.append(f"| {r['category']} | {ch_sales:+.1f}% | {float(r['baseline_pre']):.0f} | {float(r['baseline_post']):.0f} | "
                     f"{float(r['baseline_change_pct']):+.1f}% | {r['action']} |")
    lines += ["", f"**Proposal:** reduce next quarter's buys in {n_reduce} of {len(trends)} categories and put the SKUs "
              "with the steepest baseline declines forward for range review.", "",
              "Baselines are computed on clean (stockout-free) non-promotional days, so availability issues are "
              "already excluded from the trend.", ""]
    (root / "reports/category_review_2026-09.md").write_text("\n".join(lines))

    # -------------------------------------------------------------------- availability KPI
    kpi = pd.read_sql_query((root / "sql/availability_kpi.sql").read_text(), con)
    kpi.to_csv(root / "reports/availability_weekly.csv", index=False)

    # -------------------------------------------------------------------- July analyst notebook (clean-day fill-in)
    from demandsci import warehouse as wh
    w4_end = gl + timedelta(days=28)
    d = wh.trading_days(con).merge(wh.daily_sales(con), how="left", on=["store_id", "sku_id", "date"])
    so = wh.stockout_days(con).assign(stockout=True)
    d = d.merge(so, how="left", on=["store_id", "sku_id", "date"])
    d["units_sold"] = d["units_sold"].fillna(0)
    d["stockout"] = d["stockout"].eq(True)
    w = d[(d["arm"] == "lean26") & (d["date"] >= go_live) & (d["date"] < w4_end.isoformat())].copy()
    clean_mean = w[~w["stockout"]].groupby(["store_id", "sku_id"])["units_sold"].mean().rename("clean_mean")
    w = w.join(clean_mean, on=["store_id", "sku_id"])
    filled = w["units_sold"].where(~w["stockout"], w[["units_sold", "clean_mean"]].max(axis=1).fillna(w["units_sold"]))
    so_share = 100 * w["stockout"].mean()
    lost_pct = 100 * (1 - w["units_sold"].sum() / filled.sum())
    nb = {
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": [
                "# LEAN-26: quick lost-sales estimate (first 4 weeks)\n", "\n",
                "Demand Science, July 2026. Fill each stockout day with the store-SKU's average sales on clean days "
                "in the same window, then compare with actual sales across LEAN-26 stores.\n"]},
            {"cell_type": "code", "execution_count": 1, "metadata": {}, "outputs": [], "source": [
                "import sys, sqlite3\n", "sys.path.insert(0, '..')\n", "from demandsci import warehouse as wh\n",
                "con = sqlite3.connect('../data/warehouse.sqlite')\n",
                f"GO_LIVE, END = '{go_live}', '{w4_end.isoformat()}'\n"]},
            {"cell_type": "code", "execution_count": 2, "metadata": {}, "outputs": [
                {"name": "stdout", "output_type": "stream", "text": [
                    f"LEAN-26 store-SKU-days: {len(w)}\n", f"stockout days: {so_share:.1f}%\n",
                    f"sales units: {w['units_sold'].sum():.0f}\n",
                    f"sales with stockout days filled at clean-day average: {filled.sum():.0f}\n",
                    f"estimated lost sales: {lost_pct:.1f}% of demand\n"]}],
             "source": [
                "d = wh.trading_days(con).merge(wh.daily_sales(con), how='left', on=['store_id', 'sku_id', 'date'])\n",
                "d = d.merge(wh.stockout_days(con).assign(stockout=True), how='left', on=['store_id', 'sku_id', 'date'])\n",
                "d['units_sold'] = d['units_sold'].fillna(0); d['stockout'] = d['stockout'].eq(True)\n",
                "w = d[(d.arm == 'lean26') & (d.date >= GO_LIVE) & (d.date < END)].copy()\n",
                "w = w.join(w[~w.stockout].groupby(['store_id', 'sku_id']).units_sold.mean().rename('clean_mean'), on=['store_id', 'sku_id'])\n",
                "filled = w.units_sold.where(~w.stockout, w[['units_sold', 'clean_mean']].max(axis=1).fillna(w.units_sold))\n",
                "print(f'estimated lost sales: {100 * (1 - w.units_sold.sum() / filled.sum()):.1f}% of demand')\n"]},
            {"cell_type": "markdown", "metadata": {}, "source": [
                f"Stockouts are frequent ({so_share:.0f}% of store-SKU-days) but cost only about {lost_pct:.0f}% of demand: "
                "most items run out late in the day, after they have already sold a normal day's volume.\n"]},
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "nbformat": 4, "nbformat_minor": 5}

    # -------------------------------------------------------------------- LEAN-26 week-8 readout (Finance)
    w8_end = gl + timedelta(days=56)
    pre_start = gl - timedelta(days=56)
    arms = dict(con.execute("SELECT arm, COUNT(*) FROM programme_assignment GROUP BY arm").fetchall())
    win = d[(d["date"] >= pre_start.isoformat()) & (d["date"] < w8_end.isoformat())]
    inv = pd.read_sql_query("SELECT store_id, sku_id, date, on_hand_close FROM inventory_daily WHERE date >= ? AND date < ?",
                            con, params=(pre_start.isoformat(), w8_end.isoformat()))
    win = win.merge(inv, on=["store_id", "sku_id", "date"])
    g = win.groupby(["arm", "period"]).agg(units=("units_sold", "sum"), stock=("on_hand_close", "mean"),
                                           stockout=("stockout", "mean"))
    ch = lambda col, a: 100 * (g.loc[(a, "post"), col] / g.loc[(a, "pre"), col] - 1)
    readout = f"""# LEAN-26 week-8 readout (Finance Transformation)

Window: 8 weeks from go-live ({go_live} to {(w8_end - timedelta(days=1)).isoformat()}) against the 8 weeks before.

| Arm | Stores | Closing shelf stock per store-SKU, change | Sales units, change | Stockout days, pre → post |
|---|---|---|---|---|
| LEAN-26 | {arms.get('lean26', 0)} | {ch('stock', 'lean26'):+.1f}% | {ch('units', 'lean26'):+.1f}% | {100 * g.loc[('lean26', 'pre'), 'stockout']:.0f}% → {100 * g.loc[('lean26', 'post'), 'stockout']:.0f}% |
| Holdout | {arms.get('holdout', 0)} | {ch('stock', 'holdout'):+.1f}% | {ch('units', 'holdout'):+.1f}% | {100 * g.loc[('holdout', 'pre'), 'stockout']:.0f}% → {100 * g.loc[('holdout', 'post'), 'stockout']:.0f}% |

- Shelf stock (working capital) fell sharply in LEAN-26 stores.
- Sales fell in both arms, in line with the category declines in the Q3 review and the lower promotion calendar.
- More stockout days were expected with leaner shelves; Demand Science estimated lost sales at about {lost_pct:.0f}% of demand
  in the first four weeks (notebook `lost_sales_quick_estimate.ipynb`).
- **Recommendation:** extend LEAN-26 to the holdout stores after the Q3 review.
"""
    (root / "reports/lean26_week8_readout.md").write_text(readout)
    (root / "notebooks/lost_sales_quick_estimate.ipynb").write_text(json.dumps(nb, indent=1) + "\n")
    con.close()


if __name__ == "__main__":
    main(Path(sys.argv[1] if len(sys.argv) > 1 else "."))
