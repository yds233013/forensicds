# Forecast accuracy KPI

Owner: Head of Trading Analytics.

## Purpose

The desk buys power day-ahead and hedges the rest of the week against its own volume forecasts. Any error becomes an
imbalance position. The KPI measures how accurate the forecasts the desk trades on are against the volume the desk
is charged imbalance on.

## Definition

- **Forecast unit:** supply region x portfolio x delivery day.
- **Horizon:** days from the forecast run day to the delivery day, for every horizon the day-ahead process issues
  (currently D+1 to D+7).
- **Forecast evaluated:** for each run day and horizon, the forecast the desk traded on (see
  `docs/trading/day_ahead_process.md`).
- **Actual:** the settled volume on which the imbalance charge for the delivery day is calculated (see
  `docs/settlement/settlement_process.md`).
- **Metric:** WAPE = sum of |forecast - actual| / sum of actual, over scored forecasts.
- **Reporting grain:** model x delivery month x portfolio x horizon, pooled across regions.
- **Models:** every model run through the day-ahead process is measured, production and shadow, so candidate models
  can be compared with the production model on the same forecasts.

## Publication

The KPI for a delivery month is published in the monthly **forecast accuracy pack** at KPI close, and the close is
recorded in `kpi_close_log`. The pack is signed off by the Head of Trading Analytics and feeds the desk scorecard
(`docs/finance/scorecard_policy.md`). Forecasts without a settled volume are shown in the pack's forecast count but not
scored.
