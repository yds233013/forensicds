# Incumbent peak-load model - backtest

**Owner:** Resource Planning

## Method

Per-segment weighted least squares of peak-window kW on cooling degree days, fitted on the
flat-tariff seasons and standardised over the current estate and the issued weather outlook.

## Holdout performance

Fitted on the 2024 season and scored on the withheld 2025 season:

| metric | value |
|---|---|
| holdout R2 | 0.75 |
| holdout RMSE | 0.73 kW |
| mean bias | under 0.01 kW |

Calibration by segment is within tolerance and the residuals show no structure against temperature
or calendar position. Segment forecasts reconcile to the estate total exactly.

## Standing

This model has supported two planning cycles and has not missed a seasonal peak by more than the
reserve margin. It is the basis of the current capacity position.
