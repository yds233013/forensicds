# forensicds/retention-metrics-regression-04

Metric population / lifecycle regression in a SQL semantic layer.

- **Agent sees:** an FP&A memo (board NRR above published figures, restated quarters), a CFO note, published FP&A
  figures, and a semantic-layer repository at `/workspace` with a SQLite warehouse extract.
- **Hidden root cause:** `customer_quarter` identifies existing customers by CRM account creation date; pre-created
  prospect accounts and win-backs enter the retention cohort and are classified as expansion.
- **Correct repair:** cohort = ARR > 0 at quarter start; handbook movements (incl. reactivation); segment by starting ARR.
- **Verifier:** behavioural checks on every model at the default as-of date and three hidden extracts; binary reward.

Design: `research/task04_design.md`. Validation: `report/task04_validation.md`. Dev tooling: `tools/task04/`.
