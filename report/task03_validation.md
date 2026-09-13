# Task 03 validation report

Task: `candidates/03-lead-score-evaluation` (`forensicds/lead-score-evaluation-03`) · Harbor 0.21.0 · Docker (arm64)
· 2026-09-13. All results below come from commands actually run **after** the per-task and cross-task review fixes (§6–§7); raw job
directories are in `jobs/` (git-ignored). **No model (Gemini) trials have been run on this task.**

## 1. Incident reproduction (visible extract, as of 2026-09-01)

| Population | n | Conversion | ROC AUC | Top-decile lift | Recommended threshold |
|------------|--:|-----------:|--------:|----------------:|----------------------:|
| All matured accepted leads (lead_eval 2.0.3, the bug) | 8,733 | 0.071 | 0.848 | 3.98 | 0.284 |
| Intake exploration holdout, intent-to-treat (oracle = reference) | 920 | 0.117 | 0.754 | 3.24 | 0.151 |
| Holdout, per-protocol (reached by an SDR) | 846 | 0.126 | 0.746 | 3.20 | 0.215 |
| Worked leads | 3,456 | 0.174 | 0.667 | 2.18 | 0.098 |

Holdout leads SDRs reached have mean score 0.231 against 0.122 for unreached ones (SDRs work the queue highest score
first), so per-protocol is selected by the score. Workspace history: 1.4.2 reports (Feb–Jul 2026, n 790–853, AUC
0.706–0.755, sales-led labels), 2.0.0 on 2026-08-01 (n 8,197, AUC 0.848), 2.0.3 on 2026-09-01.

## 2. Hidden extracts (reference; intent-to-treat vs per-protocol)

| Extract | Holdout ITT n / AUC / threshold | Per-protocol n / AUC / threshold | Boundary cases |
|---------|------------------------------|---------------------------------|----------------|
| visible | 920 / 0.754 / 0.151 | 846 / 0.746 / 0.215 | 1 holdout lead at window end |
| hidden_a (2025-10-01) | 726 / 0.682 / 0.296 | 653 / 0.664 / 0.122 | 1 at window end |
| hidden_b (2026-03-01) | 1,086 / 0.719 / 0.130 | 1,005 / 0.705 / 0.137 | 4 at window start, 1 at end |
| hidden_c (2027-01-01) | 960 / 0.740 / 0.337 | 937 / 0.736 / 0.344 | 7 at window start; 1 conversion at exactly 60 days |

## 3. Harbor runs (final)

| Run | Command | Reward | Verifier |
|-----|---------|-------:|----------|
| Oracle | `harbor run -p candidates/03-lead-score-evaluation -a oracle -o jobs --job-name task03-oracle-final -y` | **1.0** | 14 passed |
| Nop | `harbor run -p candidates/03-lead-score-evaluation -a nop -o jobs --job-name task03-nop-final -y` | **0.0** | 8 failed, 6 passed |

Earlier runs: `task03-oracle-1`/`-nop-1` (pre-review) and `-2` (after the per-task review): 1.0 / 0.0 each.

## 4. Mutation suite (inside the task image, real hardened `tests/test.sh`)

Command: `python3 tools/task03/shortcuts.py --docker forensicds-task03:dev --jobs 3 --report report/task03_mutations.json`

| Mutation | What it does | Expected | Reward | Visible fails | Hidden fails | Caught by |
|----------|--------------|---------:|-------:|------:|------:|-----------|
| `nop` | No change (Nop agent). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `oracle` | Reference solution. | 1 | **1** | 0 | 0 | — |
| `alt_correct_sql` | Independent correct repair: cohort built in SQLite (window function for intake policy, labels from conversions). | 1 | **1** | 0 | 0 | — |
| `alt_correct_python` | Independent correct repair: plain-Python loops over routing events and conversions. | 1 | **1** | 0 | 0 | — |
| `worked_leads_only` | Evaluate only leads an SDR actually worked (outcomes 'observed under treatment'). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `any_holdout_routing_event` | Leads with any exploration_holdout routing event (intake or router-release re-evaluation). | 0 | **0** | 2 | 2 | visible + hidden_a |
| `holdout_per_protocol` | Intake holdout, but only holdout leads an SDR reached. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `current_sdr_queue` | Leads whose current lifecycle queue is the SDR queue (routed, holdout and claimed leads). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `above_threshold_only` | Only leads routed on score (score >= router threshold at intake): 'evaluate where the model decides'. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `below_threshold_sdr_reconstruction` | Reconstruct the random slice as intake SDR leads scoring below the router threshold. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `qualified_as_label` | Intake holdout with the SDR 'qualified' flag as the outcome (a downstream operational decision). | 0 | **0** | 2 | 3 | visible + hidden_a/hidden_b/hidden_c |
| `sales_led_conversions_only` | Intake holdout, but self-serve purchases are not counted as conversions. | 0 | **0** | 2 | 0 | visible only |
| `holdout_without_maturity` | Intake holdout, but immature leads (outcome window still open) are evaluated too. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `challenger_scores` | Intake holdout scored with the shadow challenger where available. | 0 | **0** | 2 | 3 | visible + hidden_a/hidden_b/hidden_c |
| `ipw_worked_population` | Worked leads re-weighted by inverse routing propensity (holdout share for sub-threshold leads) in the metrics. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `change_target_rate` | Leave the population; lower the target conversion rate so the threshold recommendation looks conservative. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `patch_report_numbers` | Cohort unchanged; report metrics recomputed on the intake holdout and written over the report. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `edit_source_outcomes` | Edit data/revops.db: remove lifecycle and conversion rows for nurture leads so they drop out. | 0 | **0** | 3 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `exclusive_window_bounds` | Intake holdout, but the creation window excludes both endpoints (docs: inclusive). | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `label_strictly_before_day_60` | Intake holdout, labels from conversions closed strictly less than 60 days after creation (docs: <= 60). | 0 | **0** | 0 | 1 | hidden only: hidden_c |
| `import_verifier_reference` | Cheat: the cohort step imports the verifier's hidden reference implementation at run time if it can find it. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |
| `overfit_latest_routing_policy` | Holdout identified by the lead's latest routing event (release re-evaluations and territory re-routes change it). | 0 | **0** | 2 | 4 | visible + hidden_a/hidden_b |
| `overfit_visible_router_versions` | Intake holdout restricted to the router versions present in this extract. | 0 | **0** | 0 | 6 | hidden only: hidden_a/hidden_b/hidden_c |
| `overfit_hardcoded_lead_ids` | Hard-coded list of this extract's holdout lead ids. | 0 | **0** | 2 | 6 | visible + hidden_a/hidden_b/hidden_c |

24/24 cases as expected.


Visible-pass / hidden-fail overfits: `overfit_visible_router_versions` (all hidden), `overfit_hardcoded_lead_ids`
(all hidden), `label_strictly_before_day_60` (hidden_c only, a single point of detection). After router-release
re-evaluation was added, `overfit_latest_routing_policy` and `any_holdout_routing_event` are also caught on the visible
extract (66 and 54 leads differ). `import_verifier_reference` scores 0 only because of the pipeline sandbox (§7).

## 5. harbor check

`task03-check-2` (after the per-task review): **11/11 pass**. The final re-check after the cross-task fixes is
`task03-check-final`; see §8 for its result. `task03-check-1` (pre-review) failed `behavior_in_task_description`.

## 6. Independent adversarial review → changes

Reviewer: separate agent with no authoring context. It built the workspace and ran variants in `/tmp`. Findings and
what was done:

| # | Finding | Action |
|---|---------|--------|
| A1 | 1.4.2 history reports were an exact answer key (same population, same labels) | 1.x labels now use sales-led CRM opportunities only, as documented in RA-512 (v1 consumers missed self-serve). History matches on n but not on metrics; "make it match 1.4.2" is a trap (`sales_led_conversions_only`) |
| A2/A3 | Router doc ruled on SLA-miss membership; model card bolded "if worked" | Router doc rewritten as router behaviour (draw made once at intake; pauses; SDR queue worked highest score first). Model card: estimand is "if routed to the SDR queue" |
| B1 | Per-protocol holdout was defensible (SLA misses independent of score) | Generator: SLA misses depend on score (SDR queue order), some late work. Per-protocol is now score-selected (threshold 0.215 vs 0.151) |
| B3 | Window/label boundaries untested (strict variant passed 14/14) | Partner-referral leads imported at 00:00:00; sales-led close dates at 00:00:00 (documented). Boundary leads now exist; hidden_c adds late closes around day 60. New mutations `exclusive_window_bounds`, `label_strictly_before_day_60` are caught |
| C1 | Instruction pointed to a doc that defined no population | Evaluation definition now has "What the evaluation measures" (population property); instruction wording updated |
| C2 | Holdout pauses in hidden_b were undocumented | Router doc documents pauses; `router_config_log` records them (`exploration_holdout_pct = 0`) |
| D | Boolean labels crashed parsing | Verifier accepts 0/1, 0.0/1.0, True/False |
| E1/E2/E3/E7 | Timeline inconsistencies (router/model deployment dates; `by_source` in 1.4.2 reports; 2.0.3 claimed before deploy; conversion note before June cohorts matured; "high 0.6s") | Fixed: router-2025.03 / lsm-3.2 on 2025-03-03; 1.x without `by_source`; August run labelled 2.0.0; note dated 2026-09-03; VP note "low 0.7s" |
| E6 | Distractors each refuted by one fact; symptom→cause path short | Not changed (documented risk in the design doc) |
| F | Reference AUC divides by zero with no positives | Not reachable in any fixture; left as is |

Re-validation after the fixes, from scratch: image rebuilt; local Nop 8 failed / Oracle 14 passed; mutation suite
22/22; Harbor Oracle 1.0 / Nop 0.0; harbor check 11/11.

## 7. Cross-task review → changes (see `research/cross_task_review.md`)

| Finding | Action |
|---------|--------|
| Pipeline code could import `/tests/reference.py` at grading time (reviewer: 14/14 on this task) | `tests/test.sh` runs the pipeline as uid 65534 with `/tests` unreadable; `tests/test_lead_eval.py` strips verifier variables; fresh venv; start-up hooks refused. Mutation `import_verifier_reference` → 0 |
| A one-line "any holdout routing event" filter passed 14/14 | Router releases re-evaluate unworked leads from the previous 14 days with the holdout draw re-applied (router doc, data dictionary, deployment log). Mutation `any_holdout_routing_event` → 0 |
| CHANGELOG prefixes and the `cohort.py` docstring pointed at the faulty module | Removed / neutralised |
| `latest.json` never checked | `test_cohort_one_row_per_lead` asserts `latest.json` equals the dated report |
| Stale numbers in `task.toml`, `solve.sh`, design §7 | Fixed |
| Verifier timeout vs pipeline runs | 2400 s |

Re-validation from scratch after these changes: image rebuilt; local Nop 8 failed / Oracle 14 passed; mutation suite
24/24 as expected; Harbor Oracle 1.0 / Nop 0.0 (`-final` jobs); harbor check re-run (§8).

## 8. Final harbor check

`harbor check candidates/03-lead-score-evaluation -c tools/task01/harbor_check_config.yaml -o jobs --job-name task03-check-final` → **11/11 pass** (all criteria, including `anti_cheating_measures` and `behavior_in_task_description`).

## 9. Remaining risks


- The evaluation definition now states the population property; the task mainly tests operationalising it (intake
  decision, ITT, window/label boundaries, outcome channels) and validating by membership, not discovering it.
- One detection point for `label_strictly_before_day_60` (hidden_c, one conversion at exactly 60 days).
- Hidden extracts are separate synthetic worlds; hidden_a's calendar precedes the visible model-card history.
- Holdout cohort is ~900 leads; month-to-month metrics are noisy (grading is exact because it is deterministic).
- Loaded-but-unused `routing_events` / `sdr_activities` in `sources.py` hint at the data needed.
- The sandbox relies on `setpriv` and uid 65534 inside the task image; a root agent can still tamper with the base
  interpreter in ways not checked (e.g. `.pth` files). Trajectory greps are the backstop.
