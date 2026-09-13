# metrics_layer changelog

## 2.1.0 - 2026-06-08
- Segment retention model and board extract (FP&A request FPA-219).

## 2.0.0 - 2026-04-06
- Retention metrics move from the FP&A retention workbook to the semantic layer (FPA-201). Models:
  stg_recurring_lines, arr_boundaries, customer_quarter, retention_quarterly. History restated from the warehouse.
- Lifecycle classification per account and quarter (new logos vs existing customers from CRM
  account data).

## 1.3.0 - 2026-01-15
- Faster boundary ARR (set-based join instead of correlated subqueries); ARR rounded to the cent.

## 1.0.0 - 2025-09-01
- Recurring-line staging and boundary ARR for the ARR dashboard.
