# Semantic layer - retention models

Models run in file-name order against a fresh `analytics.db` with the warehouse extract attached as `src`. The
runner creates `dim_quarters` for the reporting calendar before the models run.

| Model | Purpose |
|-------|---------|
| `01_stg_recurring_lines` | recurring lines that carry ARR |
| `02_arr_boundaries` | ARR per account at quarter boundaries |
| `03_customer_quarter` | lifecycle classification per account and quarter |
| `04_retention_quarterly` | board retention metrics and ARR bridge |
| `05_retention_by_segment` | retention metrics by segment |

Review: FP&A signed off the 2.0.0 release on 2026-04-03 after reconciling quarter-end ARR totals for FY2024 and
FY2025 against the retention workbook.
