# Task 02 validation report

Task: `candidates/02-renewal-risk-regression` · Harbor 0.21.0 · Docker (arm64) · 2026-09-13.
All results were produced by commands actually run after the independent review fixes; raw job
directories are in `jobs/` (git-ignored). **No model (Gemini) trials have been run on this task.**

## 1. Incident reproduction (visible extract)

| Evaluation | ROC AUC |
|------------|--------:|
| Incident-time pipeline, as of 2026-08-15 | 0.9258 |
| Correct point-in-time features (oracle = reference), as of 2026-08-15 | 0.7806 |
| Workspace history: v2.3 offline (as of 2025-08-15, 24 features, 2-year window) | 0.801 |
| Workspace history: v2.4 offline (as of 2026-02-15, actual pipeline run) | 0.936 |
| Live v2.3 (scores 2025-09-01 – 2026-01-31, 451 decided) | 0.777 |
| Live v2.4 (scores 2026-03-02 – 2026-05-17, 214 decided) | 0.750 |

Live v2.4: mean score 0.339 vs churn 17.3%; churn rate in the lowest 30% of scores 10.9% (v2.3: 3.7%).

Feature-level: the incident pipeline differs from point-in-time values in 9/9 CRM features and 4/4
health features (e.g. `renewal_stage_ordinal` 1,236 examples, `health_score` 2,782 of 2,896); the 12
contract/usage/support features match exactly. The oracle matches the pure-Python reference on all 72,400
visible feature cells. `changed_at`-based availability misstates 149 visible examples.

Data invariants of the generated extract (re-verified after fixes): 0 same-field ties or load-order
inversions per record, 0 load timestamps at 00:00:00, 0 ticket closures loaded on a later day, 0 accounts
loaded after their first contract. Generation is deterministic (seeded; stdlib only).

## 2. Hidden extracts (incident pipeline vs correct features)

| Extract | Examples (train/eval) | Incident AUC | Correct AUC |
|---------|-----------------------|-------------:|------------:|
| hidden_a (as of 2025-12-10) | 1,402 (1,011/391) | 0.943 | 0.787 |
| hidden_b (as of 2024-09-20) | 1,280 (906/374) | 0.928 | 0.793 |
| hidden_c (as of 2026-03-05) | 1,516 (1,089/427) | 0.918 | 0.781 |

(Re-measured after all review fixes; identical to the pre-fix values because the fixes do not touch CRM or
health generation.)

## 3. Harbor runs

| Run | Command | Reward | Verifier |
|-----|---------|-------:|----------|
| Oracle | `harbor run -p candidates/02-renewal-risk-regression -a oracle -o jobs --job-name task02-oracle-2` | **1.0** | 19 passed |
| Nop | `harbor run -p candidates/02-renewal-risk-regression -a nop -o jobs --job-name task02-nop-2` | **0.0** | 9 failed, 10 passed |

Pre-review runs `task02-oracle-1` / `task02-nop-1`: 1.0 / 0.0.
Nop passes exactly what a no-op should: integrity, run succeeds, examples, contract/usage/support
features, predictions/report consistency, determinism, scoring, and hidden examples (3).

## 4. Mutation suite (inside the task image, real `tests/test.sh`)

Command: `python3 tools/task02/shortcuts.py --docker forensicds-task02:dev --jobs 3 --report report/task02_mutations.json`
Result: **21/21 cases as expected** ("info" = informational probe, not required).

| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |
|----------|--------------|---------:|-------:|------:|------:|-----------|
| `nop` | No change (Nop agent). | 0 | **0** | 3 | 6 | visible + hidden |
| `oracle` | Reference solution. | 1 | **1** | 0 | 0 | — |
| `alt_correct_sql_window` | Independent correct repair: point-in-time state via SQLite window functions (no pandas as-of joins). | 1 | **1** | 0 | 0 | — |
| `alt_correct_event_replay` | Independent correct repair: replay loaded change events per record (bisect on synced_at). | 1 | **1** | 0 | 0 | — |
| `probe_oracle_unweighted_model` | Informational: correct features but class_weight reverted to None (a model-spec change). | info | **1** | 0 | 0 | — |
| `constant_leaky_features` | Set every CRM and health feature to its default (columns kept). | 0 | **0** | 2 | 5 | visible + hidden |
| `drop_leaky_columns` | Remove CRM and health features from the feature set. | 0 | **0** | 3 | 5 | visible + hidden |
| `exclude_known_leaky_columns` | Keep current-state data but neutralize the obviously leaky stage/forecast/amount/health color columns. | 0 | **0** | 3 | 6 | visible + hidden |
| `pit_by_changed_at` | Point-in-time reconstruction using the business timestamp (changed_at) as availability. | 0 | **0** | 2 | 3 | visible + hidden |
| `pit_crm_only` | Point-in-time CRM features; health still read from the current-state object. | 0 | **0** | 2 | 6 | visible + hidden |
| `pit_health_only` | Point-in-time health features; CRM still read from the current-state object. | 0 | **0** | 2 | 6 | visible + hidden |
| `creation_time_values` | Use each record's values at creation (first history rows) instead of the latest known values. | 0 | **0** | 2 | 4 | visible + hidden |
| `fixed_cutoff_date` | State as of a fixed date (last pre-migration day) for every example. | 0 | **0** | 3 | 6 | visible + hidden |
| `filter_examples_with_closed_opps` | Drop examples whose renewal opportunity is already closed in the CRM object. | 0 | **0** | 6 | 9 | visible + hidden |
| `random_split` | Replace the temporal split with a seeded random split. | 0 | **0** | 5 | 9 | visible + hidden |
| `train_on_fewer_rows` | Oracle features, but train only on the most recent year of the training window. | 0 | **0** | 2 | 3 | visible + hidden |
| `weaker_model` | Oracle features with a heavily regularized model (C=0.001) and no class weights. | 0 | **0** | 1 | 3 | visible + hidden |
| `patch_report_metrics` | Leave features alone; write plausible metrics into the evaluation report. | 0 | **0** | 4 | 6 | visible + hidden |
| `edit_warehouse_current_state` | Rewrite the current-state tables in data/warehouse.db to remove closed/red values. | 0 | **0** | 4 | 6 | visible + hidden |
| `overfit_hardcoded_load_schedule` | Point-in-time repair with availability reverse-engineered from this extract's outage and load schedules. | 0 | **0** | 0 | 1 | hidden only |
| `overfit_sync_log_outages_fixed_schedules` | Availability = changed_at, corrected with outage windows read from warehouse_sync_log, plus this | 0 | **0** | 0 | 1 | hidden only |

Observations
- Two independently written correct repairs (SQLite window functions; pure-Python event replay) score 1,
  so the verifier is not coupled to the oracle's pandas implementation.
- Both **overfit** repairs (availability reverse-engineered from this extract's outage window, partner Sunday
  batch and nightly health lag; or outages read from `warehouse_sync_log` plus hard-coded schedules) pass all
  16 visible checks and fail only `hidden_c`. Only one fixture catches them — a single point of detection.
- `pit_by_changed_at` fails visible CRM and health checks (149 examples) and three hidden checks.
- Neutralizing CRM/health features is caught by the feature checks, not by the model-behaviour check: the
  specified model on correct features barely uses them, so AUC stays within the band.
- **Leniency found:** the probe that keeps correct features but reverts `class_weight` to None scores 1.
  The instruction forbids changing the model; the verifier tolerates this particular change because AUC and
  score ranking stay within tolerance. Documented, not changed.

## 5. Independent rubric review

A fresh-context reviewer applied Harbor's default rubric: **11/11 PASS**, reproduced Oracle 19/19 and the
incident pipeline 10/19, and reported leakage pointers, specification gaps, verifier brittleness and realism
issues. All actionable findings were fixed and everything in sections 1–4 was re-run afterwards (see
`research/task02_design.md` §16).

## 6. harbor check

`harbor check candidates/02-renewal-risk-regression -c tools/task01/harbor_check_config.yaml -o jobs --job-name task02-check-1`
(claude-code evaluator, default rubric, longer agent-setup timeout; `ANTHROPIC_API_KEY` from the user's shell
profile, never printed): **11/11 pass** — behavior_in_task_description, behavior_in_tests,
informative_test_structure, anti_cheating_measures, structured_data_schema, pinned_dependencies, typos,
tests_or_solution_in_image, test_deps_in_image, hardcoded_solution, file_reference_mentioned. Evaluator cost
$0.55. Report: `jobs/task02-check-1/check_report.json`.

## 7. Known residual risks

- Leakage is a well-known failure class; strong agents may suspect it quickly. Discrimination is intended
  to come from availability semantics and complete synthesis.
- The overfit repairs are caught only by `hidden_c`.
- Model-behaviour tolerance accepts a class-weight reversion.
- Live AUC gap between v2.3 and v2.4 is modest (0.777 vs 0.750); the symptom relies on calibration and
  churn among low scores.
- `build/pit_reference.py` (a copy of the verifier reference) exists in an intermediate image layer during
  the build; it is deleted and not reachable from the running container.
