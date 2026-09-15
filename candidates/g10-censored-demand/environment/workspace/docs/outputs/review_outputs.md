# Review outputs: specification

Owner: Demand Science. `python -m demandsci review --db <warehouse> --out <dir>` writes three files. Numbers are
written unrounded.

Definitions used below:
- **Trading store-SKU-day:** a date on which the store traded (`store_calendar.status = 'open'`), for an SKU with a
  daily inventory row.
- **Period:** `pre` is before the LEAN-26 go-live date (`programme_assignment.go_live_date`); `post` is from that date.
- **Arm:** the store's LEAN-26 arm (`lean26` or `holdout`).
- **Promotional day:** a date inside one of the SKU's `promotions` ranges (inclusive).

## `demand_history.csv`

One row per trading store-SKU-day.

| Column | Meaning |
|---|---|
| `store_id`, `sku_id`, `date` | key |
| `units_sold` | units sold that day (sum of `sales_hourly`) |
| `expected_demand` | unconstrained demand for the day: the expected number of units customers would have bought during trading hours had the item been on the shelf throughout, given everything observed (`docs/planning/demand_definitions.md`) |
| `lost_units` | `expected_demand - units_sold` |

## `category_trends.csv`

One row per category.

| Column | Meaning |
|---|---|
| `baseline_pre`, `baseline_post` | category baseline for the period, from `demand_history.csv`: the sum over the category's store-SKUs of each store-SKU's average `expected_demand` over its non-promotional trading days in the period |
| `baseline_change_pct` | `100 * (baseline_post / baseline_pre - 1)` |
| `action` | buy-plan action from `docs/planning/buy_plan_process.md` |

## `programme_impact.json`

```json
{"go_live_date": "YYYY-MM-DD",
 "lost_units": {"pre": {"lean26": 0.0, "holdout": 0.0}, "post": {"lean26": 0.0, "holdout": 0.0}},
 "lost_share": {"pre": {"lean26": 0.0, "holdout": 0.0}, "post": {"lean26": 0.0, "holdout": 0.0}},
 "forecast_bias_pct": {"v3_pre_all_stores": 0.0, "v4_post_lean26": 0.0}}
```

- `lost_units`: the sum of `lost_units` over the arm's trading store-SKU-days in the period.
- `lost_share`: `lost_units` divided by the same rows' summed `expected_demand`.
- `forecast_bias_pct`: `100 * (sum of forecast - sum of expected_demand) / sum of expected_demand` for the production
  forecast:
  - v3 over all stores before go-live;
  - v4 over LEAN-26 stores from go-live.
