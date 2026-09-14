# Accuracy mart: output specification

Owner: Trading Analytics. Written as the requirement for replacing the pack notebook (June 2026); the mart must keep
producing these outputs.

`python -m fcaccuracy build --as-of <UTC instant>` writes three files to `out/accuracy/`. Numbers are written
unrounded. Only **closed KPI months**
are included: delivery months whose KPI close is recorded in `kpi_close_log` at or before `--as-of`.

## `evaluation_examples.csv`

One row per model, region, portfolio, delivery day and horizon for every forecast the KPI evaluates in closed months.

| Column | Meaning |
|---|---|
| `model` | forecasting model |
| `run_date` | forecast run day |
| `issue_id` | forecast issue the evaluated value comes from |
| `region`, `portfolio` | forecast unit |
| `target_date` | delivery day |
| `horizon` | days from run day to delivery day |
| `kpi_month` | KPI month (`YYYY-MM`) the forecast belongs to |
| `forecast_mwh` | evaluated forecast |
| `status` | `scored`: a settled volume is available and the forecast is scored; `unsettled`: no settled volume is available, so the forecast is counted but not scored |
| `actual_run_ids` | settlement run ids whose volumes make up the actual, `;`-separated, ascending (empty when unsettled) |
| `actual_mwh` | actual volume (empty when unsettled) |
| `abs_error_mwh` | absolute error in MWh (empty when unsettled) |

## `monthly_kpi.csv`

One row per model, KPI month, portfolio and horizon with at least one example.

| Column | Meaning |
|---|---|
| `n_examples` | examples |
| `n_scored` | scored examples |
| `abs_error_mwh`, `actual_mwh` | sums over scored examples |
| `wape` | `abs_error_mwh / actual_mwh` (empty when nothing is scored) |

## `summary.json`

```json
{"as_of": "...", "closed_months": ["2025-07", "..."],
 "head_to_head": [{"model_a": "v3", "model_b": "v4", "n_pairs": 0, "first_month": "...", "last_month": "...",
                   "wape_a": 0.0, "wape_b": 0.0, "relative_change": 0.0}]}
```

`head_to_head` has one entry per pair of models (`model_a` < `model_b`) for which a comparison exists, comparing them
on the forecasts both models have scored (same region, portfolio, delivery day and horizon) in the closed months.
`n_pairs` is the number of such forecasts, `first_month`/`last_month` their KPI month range, `wape_*` the pooled WAPE
of each model on them, and `relative_change = wape_b / wape_a - 1`.
