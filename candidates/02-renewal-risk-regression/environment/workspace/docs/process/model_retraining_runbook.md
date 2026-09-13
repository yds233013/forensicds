# Quarterly retraining runbook - renewal-risk

1. Scheduler job `renewal_risk_quarterly_retrain` runs `python -m renewal_risk run --config config/pipeline.toml --as-of <quarter date>`.
2. Owner reviews `reports/model_evaluation/eval_<as_of>.json` against the production model's report:
   ROC AUC, PR AUC, calibration by decile, AUC by segment.
3. Promotion needs: no metric regression beyond 0.02 ROC AUC, calibration within +/-5 points per decile
   band, sign-off from the Customer Success analytics lead.
4. Promote: copy the model artifact to the scoring service; daily scoring switches the next day.
5. After go-live, `reports/monitoring/` tracks live performance as renewals are decided (about 90-120
   days after the first scores).
