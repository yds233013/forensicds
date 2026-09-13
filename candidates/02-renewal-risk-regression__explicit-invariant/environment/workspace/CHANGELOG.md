# renewal_risk changelog

## 2.4.1 - 2026-03-10
- scoring: score date is interpreted in UTC (the scheduler runs in UTC; the job previously used the
  container's local date).

## 2.4.0 - 2026-02-16 (model renewal-risk-v2.4, deployed 2026-03-02)
- sources: CRM and Customer Success readers migrated to CRM v3 (RA-DS-298) ahead of the snapshot
  table decommissioning on 2026-01-31.
- features: new `open_expansion_opps` (open expansion pipeline on the account) (RA-DS-302).
- model: `class_weight = "balanced"` to improve recall on churners (RA-DS-311).
- model: quantile winsorization (p1/p99, learned on the training split) replaces hand-set caps (RA-DS-305).
- examples: training window extended from 2 to 3 years of settled renewals (RA-DS-307).
- deps: scikit-learn 1.3.2 -> 1.5.2, pandas 2.1.4 -> 2.2.3, numpy 1.26.4 -> 2.1.3.

## 2.3.4 - 2025-08-18 (model renewal-risk-v2.3)
- Q3 2025 retrain. No code changes besides dependency patch releases.

## 2.3.0 - 2025-02-10
- features: support ticket features (`tickets_90d`, `sev1_tickets_180d`, `open_tickets_at_prediction`).
- features: CRM pipeline and Customer Success health features (RA-DS-240).

## 2.0.0 - 2024-05-06
- First production model: logistic regression on contract and product-usage features, scored 90 days
  before renewal.
