# revenue-analytics

Recognized revenue reporting for Finance and the executive team. The `revrec`
pipeline reads the nightly source extracts from Billing and CRM, builds the
recognition schedule, attributes revenue to customers, converts to USD and
publishes warehouse tables and the executive dashboard extracts.

Owners: Revenue Analytics (#rev-analytics). Finance contact: Controllership.

## Layout

| Path | What |
|------|------|
| `data/billing/billing.db` | Billing system extract (SQLite). System of record for invoices, credit notes, FX and accounting periods. |
| `data/crm/` | CRM account export and the Billing Ops account migration register. |
| `src/revrec/` | Pipeline code (`python -m revrec`). |
| `config/` | Pipeline, metric and dashboard configuration. |
| `warehouse/analytics.db` | Published warehouse tables (full refresh on each run). |
| `reports/exec_dashboard/` | Extracts consumed by the executive dashboard. |
| `reports/finance/` | Billing revenue reports and close tie-out notes from Finance. |
| `docs/` | Finance policy, data standards, data dictionary, runbooks, announcements. |
| `logs/` | Pipeline run logs, scheduler history, deployment history. |

## Running

```bash
cd /workspace
python -m revrec run --config config/pipeline.toml
```

`PYTHONPATH` must include `src/` (already set in the analytics runtime image).
A run is a full refresh: every reportable accounting period is rebuilt from the
current extracts and all warehouse tables and dashboard extracts are replaced.

The scheduler runs the pipeline nightly and at each month-end close
(see `docs/finance/month_end_close_runbook.md`).
