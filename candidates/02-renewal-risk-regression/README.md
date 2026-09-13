# forensicds/renewal-risk-regression-02

Temporal provenance incident in a renewal churn-risk model.

- **Agent sees:** a Customer Analytics memo (v2.4 scores unusable in production; offline evaluation far above
  v2.3) and a realistic model repository at `/workspace` with a SQLite warehouse extract.
- **Hidden root cause:** CRM pipeline and customer-success health features read current-state objects
  (`crm_opportunities`, `cs_account_health`) for historical examples, so training/evaluation see post-prediction
  outcomes. Correct availability is warehouse load time (`synced_at`), which differs from business timestamps
  under nightly batches, a replication outage and weekly partner syncs.
- **Correct repair:** point-in-time reconstruction from field history for all affected features; everything
  else unchanged.
- **Verifier:** 19 behavioural checks on the current extract and three hidden extracts; binary reward.

Design: `research/task02_design.md`. Validation: `report/task02_validation.md`. Dev tooling: `tools/task02/`.
