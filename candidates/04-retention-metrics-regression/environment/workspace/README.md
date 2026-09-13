# revenue-metrics-layer

SQL semantic layer for revenue retention metrics (NRR, GRR, logo churn, ARR bridge). Owned by Analytics
Engineering; metric definitions owned by FP&A. Board and operating-review retention numbers come from the extracts
this project builds.

## Layout

| Path | What |
|------|------|
| `data/warehouse.db` | Warehouse extract (SQLite): CRM accounts, contracts, subscription lines. Read-only source data. |
| `semantic/models/*.sql` | SQL models, built in file-name order. |
| `src/metrics_layer/` | Build runner (reporting calendar, model execution, board extracts). |
| `config/metrics_layer.toml` | Paths and reporting configuration. |
| `analytics/analytics.db` | Built models (full rebuild each run). |
| `reports/board/` | Board extracts: `retention_quarterly.csv`, `retention_by_segment.csv`. |
| `reports/finance/` | Retention figures published by FP&A before the semantic layer took over (FY2024-FY2025 quarters as published, quarter end + 12 days; not restated for later bookings). From 2026-Q1 retention is published from this layer. |
| `docs/` | Metrics handbook, data dictionary, semantic-layer notes, ops notes. |
| `notes/`, `logs/` | Stakeholder notes; deployment log. |

## Build

```bash
cd /workspace
python -m metrics_layer build --config config/metrics_layer.toml [--as-of YYYY-MM-DD]
```

`PYTHONPATH` must include `src/` (set in the runtime image). The build reports the last `n_quarters` complete
calendar quarters before the as-of date and rebuilds every model and extract from the warehouse extract.
Model and extract schemas: `docs/data/data_dictionary.md`.
