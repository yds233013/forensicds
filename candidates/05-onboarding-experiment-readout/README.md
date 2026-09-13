# forensicds/onboarding-experiment-readout-05

Experiment unit / exposure / identity regression in an A/B readout.

- **Agent sees:** a memo (a significant "ship" readout with a sample-ratio warning), the Growth PM note, the
  `xp_analysis` readout repository at `/workspace`, the experiment plan, metric and platform docs, an incident
  report, and a SQLite product extract.
- **Hidden root cause:** readouts are exposure-triggered and user-level (xp_analysis 3.0) although XP-231 randomizes
  workspaces and exposure logging differs between arms; the SDK logs cached variants for multi-workspace users.
- **Correct repair:** as-assigned eligible workspaces (first assignment row), matured, 14-day workspace activation
  from assignment; estimator unchanged.
- **Verifier:** behavioural checks at the default analysis date and on three hidden extracts; binary reward.

Design: `research/task05_design.md`. Validation: `report/task05_validation.md`. Dev tooling: `tools/task05/`.
