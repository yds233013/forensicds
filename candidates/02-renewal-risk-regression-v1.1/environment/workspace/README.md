# renewal-risk

Churn-risk model for contract renewals, owned by Revenue Data Science (#rev-data-science).
Customer Success and Sales work the scores 90 days before each renewal: high-risk accounts get an
executive sponsor and a save plan.

## Layout

| Path | What |
|------|------|
| `data/warehouse.db` | Extract of the analytics warehouse (SQLite). Read-only source data. |
| `src/renewal_risk/` | Examples, features, training, evaluation, production scoring. |
| `config/pipeline.toml` | Run, example-window and model configuration. |
| `artifacts/` | Outputs of the last training run (examples, features, model, eval predictions) and scores. |
| `reports/model_evaluation/` | Evaluation report per training run (`eval_<as_of>.json`, `latest.json`). |
| `reports/monitoring/` | Production score history and live performance monitoring. |
| `docs/` | Model card, feature dictionary, warehouse data dictionary, ops notes, runbooks. |
| `notes/` | Experiment notes and stakeholder feedback. |
| `logs/` | Deployment and scheduler history. |

## Commands

```bash
cd /workspace
python -m renewal_risk run --config config/pipeline.toml [--as-of YYYY-MM-DD]      # full training run
python -m renewal_risk features --config config/pipeline.toml [--as-of YYYY-MM-DD] # examples + features only
python -m renewal_risk score --config config/pipeline.toml --score-date YYYY-MM-DD # production scoring
```

`PYTHONPATH` must include `src/` (set in the runtime image). `--as-of` is the training run date; it
defaults to `[run].as_of`. The quarterly retrain job passes it explicitly.

## Outputs of a training run

| File | Grain | Columns |
|------|-------|---------|
| `artifacts/examples.csv` | one row per example (decided renewal) | `contract_id, account_id, renewal_date, prediction_date, label, split` |
| `artifacts/features.csv` | one row per example | `contract_id, prediction_date` + the model's feature columns (order in `features/registry.py`, definitions in `docs/feature_dictionary.md`) |
| `artifacts/model/renewal_risk.joblib` | model | scikit-learn pipeline |
| `artifacts/eval_predictions.csv` | one row per `eval` example | `contract_id, account_id, prediction_date, label, score` |
| `reports/model_evaluation/eval_<as_of>.json`, `latest.json` | one report per run | metrics computed from `eval_predictions.csv` |
