# Model card - renewal-risk

Owner: Revenue Data Science. Consumers: Customer Success (save plays), Sales (renewal forecasting),
RevOps (capacity planning). Current production model: `renewal-risk-v2.4` (since 2026-03-02).

## Intended use

Rank contracts coming up for renewal by their risk of churning so that Customer Success can
intervene early. Scores are produced 90 days before the renewal date; interventions (executive
sponsor, success plan, commercial concessions) take most of that window.

## Prediction point

The production scoring job runs every day at 00:30 UTC. For score date `D` it scores every contract
whose renewal date is `D + 90 days` and whose renewal has not been decided, using the warehouse as it
stands at the start of `D` (00:00 UTC). A contract is scored exactly once.

Training and offline evaluation reproduce this: each example is a past renewal scored at its
prediction date (`renewal_date - 90 days`).

## Label

`label = 1` when the renewal outcome is `churned`, `0` when `renewed` (`renewal_outcomes`).

## Examples and split

- Eligible: renewals whose outcome is in the warehouse at the training run date (`--as-of`) and whose
  renewal date is at least `label_grace_days` (30) before it.
- Evaluation (`split = eval`): the most recent `eval_window_days` (270) of eligible renewal dates.
- Training (`split = train`): the preceding `train_window_days` (1,095) of renewal dates.
- One example per contract renewal. Examples are never filtered on feature values.

## Model

scikit-learn pipeline, fitted on the training split only:

1. Quantile winsorization per feature (p1/p99 learned on the training split).
2. Standardization.
3. L2-regularized logistic regression (`C = 0.5`, `class_weight = "balanced"`, lbfgs).

Features and their order: `src/renewal_risk/features/registry.py`; definitions:
`docs/feature_dictionary.md`. Hyperparameters: `config/pipeline.toml`.

## Evaluation

`reports/model_evaluation/eval_<as_of>.json`: ROC AUC, PR AUC, Brier score, log loss, calibration by
score decile, ROC AUC by segment - all computed from `artifacts/eval_predictions.csv`.

## Monitoring

`reports/monitoring/`: daily production scores and live performance once renewals are decided.

## Version history

| Version | Trained as of | Deployed | Notes |
|---------|---------------|----------|-------|
| v2.0 | 2024-04-15 | 2024-05-06 | contract + usage features |
| v2.3 | 2025-08-15 | 2025-08-18 | + support, CRM pipeline and CS health features (daily snapshot tables) |
| v2.4 | 2026-02-15 | 2026-03-02 | CRM v3 readers, expansion pipeline feature, balanced class weights, winsorization, 3-year window |
