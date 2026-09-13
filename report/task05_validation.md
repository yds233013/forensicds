# Task 05 validation report

Task: `candidates/05-onboarding-experiment-readout` (`forensicds/onboarding-experiment-readout-05`) · Harbor 0.21.0 ·
Docker (arm64) · 2026-09-13. All results come from commands actually run **after** the per-task and cross-task review
fixes (§6–§7). Raw job directories are in `jobs/` (git-ignored). **No model (Gemini) trials have been run on this
task.**

## 1. Incident reproduction (visible extract, analysis date 2026-09-01)

| Readout | Units control / treatment | Effect | 95% CI | Decision | SRM p |
|---------|--------------------------:|-------:|--------|----------|------:|
| xp_analysis 3.1 (bug): users with an exposure, exposure variant, activation from first exposure | 5,164 / 3,285 | +6.9 pp | [+4.8, +9.0] | ship | 7.1e-93 |
| Pre-registered (oracle = reference = independent SQL audit): as-assigned eligible workspaces | 1,680 / 1,717 | −0.3 pp | [−2.1, +1.6] | inconclusive | 0.53 |

Diagnostics:
- Exposed users by arm: 8,904 control vs 4,864 treatment. First assignments are balanced (SRM p = 0.85).
- 239 exposures carry a variant that differs from the workspace's first assignment.
- 43 workspaces have conflicting assignment rows (INC-5521).
- Pre-assignment core actions: a no-lower-bound window would flip 11 workspaces.
- Weekly bug readouts: +3.3 pp (3.0.0, inconclusive), then +5.0, +6.3, +6.3, +7.0 and +6.9 pp ("ship").

## 2. Hidden extracts (reference vs bug)

| Extract | Correct units | Correct effect / decision | Bug effect / decision | Strata | No-lower-bound flips |
|---------|--------------:|---------------------------|-----------------------|-------:|---------------------:|
| hidden_a (2026-04-01) | 2,719 | +0.4 pp [−1.6, +2.4] inconclusive | +11.6 pp ship | 9 (plan×region) | 21 |
| hidden_b (2026-12-15) | 2,599 | +5.2 pp [+2.5, +7.9] ship | +7.3 pp ship | 4 | 35 |
| hidden_c (2027-03-01) | 1,740 | −3.8 pp [−6.0, −1.7] rollback | −4.5 pp rollback | 4 | 9 |

## 3. Harbor runs (final)

| Run | Command | Reward | Verifier |
|-----|---------|-------:|----------|
| Oracle | `harbor run -p candidates/05-onboarding-experiment-readout -a oracle -o jobs --job-name task05-oracle-final -y` | **1.0** | 14 passed |
| Nop | `harbor run -p candidates/05-onboarding-experiment-readout -a nop -o jobs --job-name task05-nop-final -y` | **0.0** | 8 failed, 6 passed |

## 4. Mutation suite (inside the task image, real hardened `tests/test.sh`)

Command: `python3 tools/task05/shortcuts.py --docker forensicds-task05:dev --jobs 3 --report report/task05_mutations.json`

| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |
|----------|--------------|---------:|-------:|------:|------:|-----------|
| `nop` | No change (Nop agent). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `oracle` | Reference solution. | 1 | **1** | 0 | 0 | — |
| `alt_correct_sql` | Independent correct repair: unit table built in SQLite (window function for first assignment, correlated count). | 1 | **1** | 0 | 0 | — |
| `alt_correct_python` | Independent correct repair: plain-Python loops over the loaded frames (no pandas joins or groupbys). | 1 | **1** | 0 | 0 | — |
| `workspace_triggered` | As-assigned workspaces, but only those where some member logged an exposure (triggered at workspace level). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `workspace_exposure_variant` | Exposed workspaces analyzed in the variant their members' exposures logged (majority). | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `user_level_itt` | Users of eligible assigned workspaces (first membership), arm from the workspace, user activation from assignment. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `latest_assignment_row` | Workspace ITT, but the latest assignment row is treated as binding (re-bucketing wins). | 0 | **0** | 2 | 4 | visible + hidden_b/hidden_c |
| `no_maturity_filter` | Workspace ITT including workspaces whose 14-day window has not closed. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `include_sales_assisted` | Workspace ITT without the self-serve eligibility filter (internal still excluded). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `include_internal_workspaces` | Workspace ITT without excluding internal test workspaces. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `anchor_at_workspace_creation` | Workspace ITT with the activation window starting at workspace creation instead of assignment. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `anchor_at_first_exposure` | Workspace ITT with the activation window starting at the workspace's first exposure (assignment if none). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `lower_activation_threshold` | Workspace ITT with 2 active users instead of the configured 3. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `exclude_small_workspaces` | Workspace ITT excluding workspaces with fewer than 3 members (they cannot activate). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `drop_conflicting_assignments` | Workspace ITT excluding workspaces whose assignment rows disagree (INC-5521 cleanup). | 0 | **0** | 2 | 4 | visible + hidden_b/hidden_c |
| `drop_multi_workspace_users` | Workspace ITT excluding workspaces that share a member with another workspace (contamination). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `unstratified_estimator` | Correct units, but the estimator pools strata (simple difference in proportions). | 0 | **0** | 2 | 3 | visible + hidden_a/hidden_b/hidden_c |
| `patch_decision_only` | Leave the units; override the decision to 'inconclusive' in the readout. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `edit_source_exposures` | Edit data/product.db: delete control exposures so exposed samples balance, keep exposure-triggered analysis. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `window_no_lower_bound` | Workspace ITT counting core actions before assignment too (window end only). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `import_verifier_reference` | Cheat: the readout imports the verifier's hidden reference implementation at run time if it can find it. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `overfit_visible_strata` | Workspace ITT restricted to the four strata present in this extract. | 0 | **0** | 0 | 2 | hidden only: hidden_a |
| `overfit_visible_self_serve_plans` | Eligibility by this extract's self-serve plan names instead of signup channel. | 0 | **0** | 0 | 2 | hidden only: hidden_a |
| `overfit_incident_rows` | Drop assignment rows written during INC-5521 (2026-07-29 14:00-15:00) and dedupe by the latest remaining row. | 0 | **0** | 2 | 4 | visible + hidden_b/hidden_c |
| `overfit_hardcoded_units` | Hard-coded list of this extract's analyzable workspace ids. | 0 | **0** | 0 | 6 | hidden only: hidden_a/hidden_b/hidden_c |
| `window_end_inclusive` | Workspace ITT with the activation window closed at assigned_at + 14 days (<=). Probe: boundary sensitivity. | None | **1** | 0 | 0 | — |

27/27 cases as expected.


Visible-pass / hidden-fail overfits: `overfit_visible_strata` (hidden_a only), `overfit_visible_self_serve_plans`
(hidden_a only) and `overfit_hardcoded_units` (all hidden). `window_end_inclusive` is an informational probe that is
not detected (reward 1): events at exactly `assigned_at + 14 days` do not flip any unit.

**Sandbox control.** The same `import_verifier_reference` mutation was run against a copy of `test.sh` with the
sandbox removed; verifier variables were still stripped. It scored **reward 1 (14 passed)**. With the sandbox it
scores 0.

## 5. harbor check

See §8 (first check run for this task).

## 6. Independent adversarial review → changes

Reviewer: separate agent with no authoring context. It built the workspace from the 37 git-trackable files, wrote nine
alternative `units.py` implementations, and ran the verifier on each.

| Finding | Action |
|---------|--------|
| Cheat: pipeline code could import `/tests/reference.py` (14/14) | Pipeline sandbox (uid 65534, `/tests` 700, stripped env); mutation `import_verifier_reference` → 0 |
| Calendar-date reading of "assigned at least 14 days before the analysis date" rejected (59–91 units per extract) | Plan states `assigned_at + 14 days <= analysis date 00:00 UTC` |
| No core action before assignment, so a no-lower-bound window passed | Teammates in late-onboarding workspaces sometimes act before assignment (separate RNG stream); mutation `window_no_lower_bound` → 0 |
| `XP-231_latest.json`, `experiment_id` unchecked | Checked |
| CHANGELOG 3.1.0 contradicted the 3.0.0 run log (SRM) | 3.0.0 readout has no `srm_p_value`; CHANGELOG reworded |
| First-assignment split p = 0.025, units p = 0.073 (would unsettle an expert) | Seed 5153: first split p = 0.85, units p = 0.53 |
| Plan event names absent from data; no power statement | Names removed; MDE note added (~2.6 pp) |
| Agency users joined before their account existed (89 rows) | Generator fixed (0 rows in all extracts) |
| hidden_c carried a 2026 concurrent experiment | XP-270 from 2027-01-18 |
| `recomputed()` raised raw errors | Clear assertion messages |
| Difficulty optimistic (docs + buggy file scaffold the fix) | Expert estimate 90 → 60 min; docstring neutralised; scaffolding kept (documented risk) |

## 7. Cross-task review → changes

- Verifier hardening as above; fresh venv; start-up hooks refused; verifier timeout 2400 s.
- CHANGELOG module prefixes removed; faulty-module docstring neutralised.

Re-validation from scratch after all changes: image rebuilt; local Nop 8 failed / Oracle 14 passed; mutation suite
27/27 as expected; Harbor Oracle 1.0 / Nop 0.0; harbor check (§8).

## 8. harbor check (final)

`harbor check candidates/05-onboarding-experiment-readout -c tools/task01/harbor_check_config.yaml -o jobs --job-name task05-check-final` → **11/11 pass** (all criteria, including `anti_cheating_measures` and `behavior_in_task_description`).

## 9. Remaining risks

- The plan, activation doc and platform docs state every rule; the repair is clear once plan and code are compared.
  The difficulty is recognising that the platform-standard triggered analysis is invalid here, and implementing the
  plan exactly.
- The buggy `units.py` retains useful pieces (eligibility, first-row stratum lookup, maturity helper); config
  `min_active_users` is unused by the buggy code.
- `window_end_inclusive` is undetectable; single-fixture detections for the visible-strata and plan-name overfits.
- Low activation (~8%) makes the correct readout inconclusive by design; the verifier grades the plan, not a true
  effect.
