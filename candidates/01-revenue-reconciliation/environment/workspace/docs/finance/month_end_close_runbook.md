# Month-end close runbook - revenue reporting

Owner: Revenue Analytics with Finance Controllership.

| Day | Step | Who |
|-----|------|-----|
| BD1 | Billing posts final usage invoices for the closing month; Billing Ops sets the period to `closing`. | Billing Ops |
| BD3 05:00 UTC | Extracts land in `data/` (billing.db, CRM export, migration register). | Data Platform |
| BD3 06:10 UTC | Scheduler runs `revrec_close`: `python -m revrec run --config config/pipeline.toml`. | Scheduler |
| BD3 | Finance exports Billing's *Recognized Revenue by Currency* report for the period to `reports/finance/`. | Controllership |
| BD3 | **Tie-out**: dashboard `recognized_revenue_by_month.csv` vs Billing report, total USD. Must tie to the cent. | Controllership |
| BD4 | If tied: period closed, dashboard released to the executive team. If not: Revenue Analytics investigates; the dashboard is held. | Revenue Analytics |
| BD5 | Customer-level restatements (e.g. after account migrations) communicated to Sales Ops and FP&A. | Revenue Analytics |

## Tie-out procedure

1. Company total recognized revenue for the closing month and the prior month.
2. Gross (invoice lines) and credit notes separately.
3. Segment totals must sum to the company total.
4. Any variance is investigated to root cause before release. Manual adjustments
   to dashboard extracts or warehouse tables are not permitted: the numbers must
   come out of a pipeline run on the unmodified extracts.

## Useful checks

- Billing recognized revenue for a month can be recomputed directly from
  `billing.db` using the policy (`docs/finance/revenue_recognition_policy.md`).
- `fct_recognized_revenue` has one row per recognized charge per month; see the
  data dictionary for its key.
- Pipeline logs: `logs/pipeline/`. Scheduler history: `logs/scheduler/`.
  Deployments: `logs/deployments.csv`.
