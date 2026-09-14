# fcaccuracy release notes

## 1.0.1 (2026-08-10)

- Faster example query (warehouse views indexed by Data Platform).
- `actual_run_ids` sorted.

## 1.0.0 (2026-07-27)

First release, replacing `notebooks/kpi_pack_legacy.ipynb` (last used for the June 2026 pack). The notebook's inputs are no longer produced:
`billing.charge_basis_snapshot` was retired in the Billing platform consolidation, and `trading.locked_forecasts` was
retired with the trading system upgrade (see `docs/finance/billing_feed_retirement_2026.md`). The mart reads the
warehouse directly and runs nightly. The pack for a month is taken from the first nightly run after KPI close.

Design decisions (Data Platform, reviewed with Forecasting):

- **Scope:** closed KPI months only, from `kpi_close_log`, as in the output specification.
- **Metric:** WAPE pooled across regions by model, KPI month, portfolio and horizon, unchanged from the packs.
- **Horizon:** days from the forecast run day to the delivery day, unchanged from the packs.
- **Models:** every model in the forecast store is evaluated, so shadow models stay comparable.

- **Actuals:** `settled_volumes_latest`, the most accurate settled volume available for each delivery day,
  reconciliation runs included, so accuracy is measured against the best data we have rather than early estimates.
- **Forecasts:** `forecast_latest`, the most recent forecast issued for each run, so late weather updates are
  reflected.
- **Portfolios:** mapped through `dim_portfolio`, the governed portfolio dimension.
- **KPI months:** follow the forecast run month, so a month's KPI covers the forecasts produced in that month.
- **Head-to-head:** each model is measured over its own production period, reflecting the forecasts the business
  actually used.
