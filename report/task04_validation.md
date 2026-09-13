# Task 04 validation report

Task: `candidates/04-retention-metrics-regression` (`forensicds/retention-metrics-regression-04`) · Harbor 0.21.0 ·
Docker (arm64) · 2026-09-13. All results come from commands actually run **after** the per-task and cross-task review
fixes (§6–§7). Raw job directories are in `jobs/` (git-ignored). **No model (Gemini) trials have been run on this
task.**

## 1. Incident reproduction (visible extract, as of 2026-08-05)

| Quarter | Published cohort | Published NRR | Layer 2.1 NRR (bug) | Correct NRR (oracle = reference) | Correct cohort | Bug cohort |
|---------|-----------------:|--------------:|--------------------:|---------------------------------:|---------------:|-----------:|
| 2024-Q3 | 971 | 0.991 | 1.012 | 0.994 | 978 | 1,012 |
| 2024-Q4 | 1,025 | 0.985 | 1.027 | 0.997 | 1,027 | 1,056 |
| 2025-Q1 | 1,082 | 0.987 | 1.019 | 0.990 | 1,085 | 1,121 |
| 2025-Q2 | 1,136 | 0.979 | 1.020 | 0.985 | 1,140 | 1,182 |
| 2025-Q3 | 1,197 | 0.975 | 1.034 | 0.981 | 1,201 | 1,254 |
| 2025-Q4 | 1,263 | 1.011 | 1.092 | 1.024 | 1,265 | 1,329 |
| 2026-Q1 | (from the layer) | 1.102 | 1.102 | 1.028 | 1,344 | 1,423 |
| 2026-Q2 | — | — | 1.074 | 0.999 | 1,403 | 1,491 |

The bug reports `reactivated_customers = 0` in every quarter; the correct layer has 5–16 per quarter. Published
figures are a publication-date snapshot (quarter end + 12 days), so they differ slightly from a correct restatement in
both cohort size (2–7 customers) and NRR.

## 2. Fixtures (reference)

| Extract | customer_quarter rows | new | reactivated | pre-created zero-start accounts (bug puts them in the cohort) | Latest quarter NRR correct vs bug |
|---------|---------------------:|----:|------------:|-------------------------------------------:|-----------------------------------|
| visible (2026-08-05) | 10,301 | 774 | 84 | 425 | 2026-Q2: 0.998 vs 1.074 |
| hidden_a (2025-11-12) | 10,010 | 597 | 258 | 659 | 2025-Q3: 0.975 vs 1.034 |
| hidden_b (2026-02-20) | 11,677 | 1,095 | 241 | 989 | 2025-Q4: 0.985 vs 1.083 |
| hidden_c (2027-05-02) | 7,146 | 536 | 39 | 285 | 2027-Q1: 1.010 vs 1.085 |

hidden_c also has 10 customers that start quarters at exactly 25,000.00 or 100,000.00 ARR (37 rows), so segment
thresholds are tested.

## 3. Harbor runs (final)

| Run | Command | Reward | Verifier |
|-----|---------|-------:|----------|
| Oracle | `harbor run -p candidates/04-retention-metrics-regression -a oracle -o jobs --job-name task04-oracle-final -y` | **1.0** | 18 passed |
| Nop | `harbor run -p candidates/04-retention-metrics-regression -a nop -o jobs --job-name task04-nop-final -y` | **0.0** | 12 failed, 6 passed |

Earlier runs `task04-oracle-2` / `task04-nop-2` (pre-review): 1.0 / 0.0. Nop passes only integrity, build succeeds,
calendar, rows and boundary ARR, board extracts equal the models, and determinism.

## 4. Mutation suite (inside the task image, real hardened `tests/test.sh`)

Command: `python3 tools/task04/shortcuts.py --docker forensicds-task04:dev --jobs 3 --report report/task04_mutations.json`

| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |
|----------|--------------|---------:|-------:|------:|------:|-----------|
| `nop` | No change (Nop agent). | 0 | **0** | 6 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `oracle` | Reference solution. | 1 | **1** | 0 | 0 | — |
| `alt_correct_sql` | Independent correct repair: customer spells from first/last line dates via window CTEs, segment via lookup table. | 1 | **1** | 0 | 0 | — |
| `alt_correct_python` | Independent correct repair: customer_quarter classified in Python inside the build (no SQL CASE logic). | 1 | **1** | 0 | 0 | — |
| `exclude_abm_target_accounts` | Keep CRM-based cohort, but treat ABM target-list accounts without starting ARR as new logos. | 0 | **0** | 6 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `first_contract_signed_before_quarter` | Existing customer = first contract signed before the quarter (booking date instead of CRM creation). | 0 | **0** | 6 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `crm_contract_type_new_business` | New logo = has a new_business contract whose lines start in the quarter (Sales Ops contract categories). | 0 | **0** | 7 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `cohort_fixed_movement_unchanged` | Cohort = ARR on S (NRR/GRR/logo churn fixed) but lifecycle movement and segment logic left as in 2.0. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `no_reactivation_category` | Cohort, movements and segments by ARR, but every account without starting ARR is 'new'. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `segment_from_ending_arr` | Correct cohort and movements; segment assigned from ending ARR (falling back to starting ARR for churned). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `tenure_based_cohort` | Existing customer = any recurring line started before the quarter (win-backs join the cohort). | 0 | **0** | 7 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `renewal_grace_period` | ARR-based cohort, plus accounts whose last line ended within 45 days before S (late renewals kept in cohort). | 0 | **0** | 6 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `drop_precreated_accounts` | Keep 2.0 logic but drop rows for accounts created before the quarter with no starting ARR. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `published_snapshot_arr` | Reconcile to the FP&A workbook: ignore lines signed after quarter end + 12 days, with ARR-based cohort. | 0 | **0** | 7 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `quarter_end_last_day` | Correct classification, but ending ARR measured on the last day of the quarter instead of E. | 0 | **0** | 5 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `scale_nrr_to_published` | Leave the model; scale NRR in retention_quarterly toward the published level before export. | 0 | **0** | 6 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `restore_published_quarters` | Leave the model; overwrite published quarters' metrics with the FP&A workbook values before export. | 0 | **0** | 6 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `edit_warehouse_created_at` | Edit data/warehouse.db: set CRM created_at to the account's first subscription start (2.0 logic then 'works'). | 0 | **0** | 7 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `segment_boundaries_inclusive` | Correct cohort and movements; segment thresholds inclusive (SMB <= 25,000, Mid-Market <= 100,000). | 0 | **0** | 0 | 2 | hidden only: hidden_c |
| `reactivation_requires_ended_spell` | Reactivated only if an earlier recurring line ended strictly before S (a line ending on S does not count). | 0 | **0** | 0 | 2 | hidden only: hidden_b |
| `import_verifier_reference` | Cheat: the build replaces customer_quarter with the verifier's hidden reference implementation if it can find it. | 0 | **0** | 11 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `overfit_reactivation_lookback_540d` | Reactivated only if a prior line ended within 540 days before S (visible win-back gaps are shorter). | 0 | **0** | 0 | 2 | hidden only: hidden_a |
| `overfit_reactivation_from_quarter_snapshots` | Reactivated if the account had ARR on an earlier quarter start date (misses spells between boundaries). | 0 | **0** | 2 | 4 | visible + hidden_a/hidden_b |
| `overfit_visible_quarters_only` | Correct logic for the eight visible reporting quarters; 2.0 logic elsewhere. | 0 | **0** | 0 | 6 | hidden only: hidden_a/hidden_b/hidden_c |

24/24 cases as expected.


Visible-pass / hidden-fail overfits and single-fixture detections: `overfit_reactivation_lookback_540d` (hidden_a only),
`overfit_visible_quarters_only` (all hidden), `segment_boundaries_inclusive` (hidden_c only),
`reactivation_requires_ended_spell` (hidden_b only; few rows). `import_verifier_reference` scores 0 only because of
the pipeline sandbox.

## 5. harbor check

`task04-check-1` (pre-review): **11/11 pass**. Final re-check after the fixes: see §8.

## 6. Independent adversarial review → changes

Reviewer: separate agent with no authoring context. It built the workspace from git-trackable files only, ran nine
alternative implementations and scanned all four extracts.

| # | Finding | Action |
|---|---------|--------|
| F1 | **Blocker:** the image build failed from a git checkout (empty `notes/` directory not kept by git) | `history_artifacts.py` creates `notes/` |
| F2 | Reference did not filter zero-length lines (oracle and handbook do) | `reference.py` filters `end_date > start_date` |
| B/D | Ratio tolerance 1e-9 rejected ratios rounded to 8 dp | Tolerance 1e-6; data dictionary says ratios are unrounded fractions |
| D | Inclusive segment thresholds passed (no exact-threshold accounts) | hidden_c boundary accounts (new spec key, visible digest unchanged); mutation `segment_boundaries_inclusive` |
| D | "Reactivation requires a spell ended before S" caught by 2 checks only | Mutation added (still few rows) |
| C | Empty segments behaviour undocumented | Data dictionary: rows only for segments with cohort customers |
| A | Published cohort counts were an exact key; faulty SQL comment stated the rule | Very late renewals (3%, 100–240 days) so published counts differ; comment removed; CHANGELOG reworded |
| E | Timeline: 2026-Q1 missing from workbook; ABM accounts before import date; reorg year | 2.0.0 now 2026-04-06 (Q1 published from the layer, CFO note says so); ABM import 2025-03-31; reorg wording aligned |
| E | README "build history" | Removed |
| — | Difficulty rating optimistic | Expert estimate 90 → 60 min |
| D7 | Inner join to `crm_accounts` indistinguishable (CRM coverage complete) | **Not changed**; documented risk |

## 7. Cross-task review → changes (see `research/cross_task_review.md`)

- Pipeline sandbox in `tests/test.sh` (uid 65534, `/tests` unreadable, stripped env, fresh venv, start-up hooks
  refused); mutation `import_verifier_reference` → 0.
- CHANGELOG module prefixes removed; verifier timeout 2400 s.

Re-validation from scratch after all changes: image rebuilt; local Nop 12 failed / Oracle 18 passed; mutation suite
24/24; Harbor Oracle 1.0 / Nop 0.0 (`-final` jobs); harbor check re-run (§8).

## 8. Final harbor check

`harbor check candidates/04-retention-metrics-regression -c tools/task01/harbor_check_config.yaml -o jobs --job-name task04-check-final` → **11/11 pass** (all criteria, including `anti_cheating_measures` and `behavior_in_task_description`).

## 9. Remaining risks

- The handbook is a complete specification. Once the agent compares it with the SQL, the repair is clear; difficulty
  is in completeness (bridge, reactivation, segments). The cross-task reviewer rated it close to Task 01 (too easy).
- Accounts billed without a CRM row are not generated, so an inner join to `crm_accounts` is not distinguished.
- `03_customer_quarter.sql` is the only model joining `crm_accounts`, and `reactivated_customers = 0` is a visible
  tell.
- Single-fixture detections listed in §4.
