# Warehouse data dictionary (extract)

All timestamps are UTC, ISO 8601 with a trailing `Z`. Dates are `YYYY-MM-DD`.

## Settlement

**`settlement_runs`**: one row per run published by the settlement agent.
- `run_id`, `region`, `settlement_class`, `delivery_date`.
- `run_type`: `EST`, `IS`, `R1`, `R2`, `RF`, `DF`.
- `reason`: `scheduled`, `withdrawal_rerun`, `data_correction`.
- `replaces_run_id`: the run a re-run or correction replaces.
- `published_at`: when the agent published the run.
- `status`: current status (`published`, `withdrawn`, `superseded`).
- `status_effective_from`: the settlement time from which the current status applies.

**`settlement_volumes`**: one row per run.
- `mwh`.
- `estimated_share`: share of volume from estimated reads.
- `loaded_at`: when the row was loaded into this warehouse. History before 2026-07-02 was backfilled at the warehouse
  migration.

**`run_status_history`**: every status a run has had, as notified by the settlement agent.
- `run_id`, `status`.
- `effective_from`: the settlement time from which the status applies. A withdrawal applies from the run's own
  publication (the run is void from the start); a supersession applies from the correction run's publication.
- `recorded_at`: when the notification was received and recorded.
- A run's first row is its publication (`effective_from` = `recorded_at` = `published_at`).

**`settled_volumes_latest`** (view): the latest published settlement volume per region, class and delivery day across
settlement runs. Used by Finance for reconciliation reporting.

## Forecasts

- **`forecast_issues`**: `issue_id`, `model`, `run_date`, `issued_at`, `issue_kind`, `scope_region`, `note`.
- **`forecast_values`**: `issue_id`, `region`, `portfolio`, `target_date`, `mwh`.
- **`forecast_latest`** (view): values of the most recent issue for each model and run date.
- **`models`**: `model`, `description`, `first_run_date`, `production_from`, `production_to` (NULL = open or never).

## Portfolios

- **`portfolio_membership`**: settlement classes that make up each forecast portfolio.
  - `effective_from` / `effective_to` are inclusive delivery dates; `effective_to` NULL means open.
- **`dim_portfolio`**: current portfolio definitions (governed dimension maintained by Data Platform).
- **`settlement_classes`**, **`regions`**: reference.

## KPI

**`kpi_close_log`**: one row per closed delivery month.
- `kpi_month`.
- `closed_at`: when the month's KPI was closed and the pack signed off.
- `signed_off_by`.
