# demandsci release notes

## 2.3.1 (2026-07-06)

- Availability KPI query moved to `sql/availability_kpi.sql`.

## 2.3.0 (2026-05-18)

- **Stockout cleaning:** days with a stockout during trading hours, or no stock at opening, are flagged in the demand
  history and excluded from category baselines, so baselines are computed on clean trading days.
- Programme impact report added for LEAN-26 (lost units, forecast bias).

## 2.2.0 (2026-02-02)

- Category baselines use the sum over store-SKUs of average daily demand on non-promotional trading days
  (buy-plan process v4).
