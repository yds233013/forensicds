# lead-score-evaluation

Monthly evaluation of the inbound lead-score model (`lsm`). Owned by RevOps Analytics (#revops-analytics).
The evaluation report feeds the monthly Sales & Marketing operating review and the inbound router's threshold
reviews.

## Layout

| Path | What |
|------|------|
| `data/revops.db` | RevOps warehouse extract (SQLite). Read-only source data. |
| `src/lead_eval/` | Evaluation pipeline: cohort, metrics, reports. |
| `config/evaluation.toml` | Evaluation configuration. |
| `artifacts/` | Outputs of the last evaluation run. |
| `reports/model_monitoring/` | One evaluation report per as-of date (`lead_score_eval_<as_of>.json`, `latest.json`). |
| `docs/` | Model card, inbound router design, evaluation definition, data dictionary, ops notes. |
| `notes/` | Stakeholder notes. |
| `logs/` | Deployment and scheduler history. |

## Running

```bash
cd /workspace
python -m lead_eval run --config config/evaluation.toml [--as-of YYYY-MM-DD]
```

`PYTHONPATH` must include `src/` (set in the runtime image). The scheduler runs the evaluation on the 2nd of
each month with `--as-of` set to the 1st.

## Outputs

| File | Grain | Content |
|------|-------|---------|
| `artifacts/eval_cohort.csv` | one row per lead in the evaluation population | `lead_id, created_at, source, score, label` |
| `reports/model_monitoring/lead_score_eval_<as_of>.json`, `latest.json` | one report per as-of date | metrics computed from the evaluation cohort (definitions in `docs/monitoring/lead_score_evaluation.md`) |
