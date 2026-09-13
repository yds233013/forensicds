# Task 02 — Explicit-invariant paired ablation (Gemini 3 Flash Preview)

Status: exploratory, 3 trials per condition (6 trajectories total). Neither the diagnosis task nor Task 01
was modified. Per-trial table: `research/task02_explicit_invariant_trials.csv`. Diagnosis baseline:
`research/task02_gemini_analysis.md`, `research/task02_trials.csv`.

## 1. Design

**Question.** Did the diagnosis-condition agents fail because they could not *infer* the precise temporal /
data-grain invariant (A), or because they could not *implement, propagate and validate* it even when known (B)?

**Condition.** `candidates/02-renewal-risk-regression__explicit-invariant` (commit `31ea5ee`): a byte-identical copy
of the validated diagnosis task. Only `instruction.md` differs, by one inserted paragraph before "Requirements":

> The training data must respect this rule: for each training or evaluation example, reconstruct every feature
> independently as of that example's prediction date. A source record or field value may be used only if it had
> landed in the warehouse before 00:00 UTC on that prediction date; warehouse availability is determined by
> `synced_at`, not merely the source-system change time. The same entity may therefore have different valid state
> in different examples.

The paragraph names no file, function, feature family, table, algorithm, grouping key or fixture.

**Equivalence checks (run).** `diff -r` shows only `instruction.md`; per-tree SHA-256 of `environment/`, `tests/`,
`solution/`, `task.toml`, `README.md`, `.gitignore` identical. Harbor Oracle on the variant = **1.0** (19/19);
Nop = **0.0** (9 failed / 10 passed), identical to the diagnosis task.

**Run.** `harbor run -p candidates/02-renewal-risk-regression__explicit-invariant -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task02-gemini3flash-explicit-invariant --artifact /workspace -y`
— 0 exceptions, no API errors, 11 m 6 s, $0.75.

An earlier launch of the same command was interrupted when the controlling session ended while all three trials
were still installing gemini-cli (no agent output, no trajectory, no model call, no verifier run). It is kept as
`jobs/task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup` and excluded; the three
trials analysed here are the only explicit-invariant trials in which the model ran.

## 2. Results

| Trial | Reward | Checks pass / fail | Steps | Time | Final AUC it reported | Failing feature groups |
|-------|-------:|--------------------|------:|-----:|----------------------:|------------------------|
| `j5oNxeF` | 0 | 15 / 4 | 32 | 167 s | 0.7826 | support tickets only (all 4 extracts) |
| `6LSZCFK` | 0 | 13 / 6 | 33 | 184 s | 0.7808 | support tickets; renewal-opportunity existence (1,237 visible) |
| `95Q6LAG` | 0 | 10 / 9 | 62 | 383 s | 0.7895 | support tickets; CRM and health values misassigned across rows |

Reference AUC on correct features: 0.7806. Empirical success rate 0/3 (empirical estimator, not exact pass@1);
pass@3 = 0. No trajectory references tests, solution or verifier outputs; warehouse extract unmodified in all three.

### Minimal-correction probes (analysis only; the task was not changed)

Each trial's submitted `src/` was copied, minimally edited, and re-run against the visible and all hidden extracts
(`tools/analysis/task02_explicit_invariant_probes.py`):

| Trial | Minimal edit(s) | Result on visible + hidden_a/b/c |
|-------|-----------------|----------------------------------|
| `j5oNxeF` | remove `synced_at` filter on `support_tickets` | **exact on all 4 extracts** |
| `6LSZCFK` | remove ticket filter + existence = first history load | **exact on all 4 extracts** |
| `95Q6LAG` | remove ticket filter + fix `merge_asof` index alignment | **exact on all 4 extracts** |

For comparison (diagnosis baseline): `JctTpSi` became exact after correcting its grouping keys; `nXXMdDm` and
`pf9zaPc` needed grain, existence and (pf9zaPc) availability changes.

## 3. A validity problem introduced by the ablation wording

All three explicit-condition agents added `synced_at < prediction_date` to `support_tickets`; **no** diagnosis agent
touched that builder. `support_tickets` holds only each ticket's current version, and its `synced_at` is the load time
of that latest version (for closed tickets, closure). The data dictionary says so ("the row (or its latest version)").
The filter therefore drops tickets that were open and visible in the warehouse at the prediction date but closed
later, producing 138 mismatched examples on the visible extract.

The trajectories show the agents saw the tension and resolved it toward the literal instruction:
`j5oNxeF` step 42 ("I could inadvertently miss a ticket's early version if it had an update later than the
prediction_date"), `6LSZCFK` step 28 ("Tickets opened before prediction_date … were likely synced before"),
`95Q6LAG` step 40 ("synced_at would likely be T2 + epsilon, reflecting its closed state").

**Assessment.** The disclosure sentence "a source record … may be used only if it had landed in the warehouse …;
warehouse availability is determined by `synced_at`" is ambiguous for current-state tables where `synced_at` is not
first-landing time. The verifier's reference is consistent with the documentation, but under this condition the
instruction's literal reading conflicts with it. This is a **condition-design flaw (F8)** for the explicit-invariant
variant only; the diagnosis task is unaffected (its instruction states no such rule, and no diagnosis agent changed
ticket features). Consequences:

- `j5oNxeF`'s reward 0 is attributable solely to this flaw → **not counted as a model failure**.
- `6LSZCFK` and `95Q6LAG` also have independent genuine defects, so their failures stand, with F8 as secondary.
- The headline pass-rate comparison (0/3 vs 0/3) is **confounded** and must not be read as "disclosure did not help".

Smallest fix for a clean re-run (proposed, not implemented): replace the second sentence with wording that refers to
the state that was present rather than a row's current `synced_at`, e.g. "Use only information that was present in
the warehouse at 00:00 UTC on that prediction date — what a query at that moment would have returned — judged by
warehouse load time (`synced_at`), not by source-system change time."

## 4. Per-trial analysis

### j5oNxeF — dominant F8 (instruction-induced); otherwise correct

- Leak identified by step 12 after model card, feature dictionary, data dictionary and both builders.
- Shared `reconstruct_pit(history, id, ids, prediction_dates, fields)`: joins history to (id, prediction_date)
  requests, filters `synced_at < P`, takes latest by (synced_at, changed_at) per (id, prediction_date, field).
  Existence = a loaded history row before P. Expansion stage per (opportunity, prediction_date), counted per example.
- Also added `synced_at` filters to usage (harmless) and tickets (the confound).
- Validation: AUC 0.7826 "closely aligned with v2.3 and live"; SQL counts of contracts/accounts loaded after P (0); no
  feature-value audit.

### 6LSZCFK — dominant F4 · secondary F8

- Health and expansion reconstruction per example and exact.
- Renewal-opportunity existence taken from `crm_opportunities.synced_at` — the load time of the object's latest
  version — so opportunities already present at P but updated later were treated as absent (1,237 visible examples).
  This is the same "current-state `synced_at` ≠ first landing" confusion as the ticket filter, but here the correct
  first-load time is available in the history table and the other two agents in this condition used it → genuine.
- Validation: AUC 0.7808; no feature-value audit.

### 95Q6LAG — dominant F7 · secondary F6, F8

- Most rigorous semantics: `merge_asof(direction="backward", allow_exact_matches=False)` on `synced_at` per field,
  requests per example, existence from first history load, expansions per example.
- Defect: `merge_asof` on requests sorted by prediction date returns a new index, but results were assigned as if the
  original index were preserved → CRM and health values attached to the wrong examples (renewal_stage 1,904;
  health_score 1,043 visible). The agent spent steps 56–72 on "index alignment" and NaN handling without detecting the
  misassignment.
- Validation: accepted AUC 0.7895 — within 0.009 of the correct value — from scrambled features.

## 5. Paired comparison

| condition | trials | successes | empirical_success_rate | pass_at_3 | temporal_leakage_identified | synced_at_semantics_correct | per_example_grain_correct | aggregate_only_validation |
|-----------|-------:|----------:|-----------------------:|----------:|----------------------------:|----------------------------:|--------------------------:|--------------------------:|
| diagnosis | 3 | 0 | 0.00 | 0 | 3/3 | 2/3 | 0/3 | 3/3 |
| explicit-invariant | 3 | 0 | 0.00 | 0 | 3/3 | 3/3 | 3/3 | 3/3 |

Definitions: *synced_at_semantics_correct* = history field values filtered by load time (not `changed_at`);
*per_example_grain_correct* = state reconstructed per (entity, prediction date) for every reconstructed feature,
including expansions, by design (95Q6LAG's index misassignment is counted as implementation, not grain);
*aggregate_only_validation* = no check of reconstructed feature values against source history for any example.

Additional measures:

| Measure | diagnosis | explicit-invariant |
|---------|-----------|--------------------|
| Record existence by load time | 1/3 | 2/3 |
| Current-state `synced_at` misused (tickets / object existence) | 0/3 | 3/3 (tickets), 1/3 (existence) |
| Verifier checks passed (per trial) | 11, 10, 10 | 15, 13, 10 |
| Final AUC reported / accepted | 0.770, 0.770, 0.635 | 0.783, 0.781, 0.790 |
| Distance to exact on all extracts | grouping keys (1); grain + existence (1); availability + grain + existence (1) | ticket filter only (1); ticket + existence (1); ticket + index alignment (1) |

## 6. Interpretation (conservative)

**Did stating the invariant cause agents to implement and validate it correctly?** Partly.

- **Inference was a real bottleneck for the grain.** The per-(entity, prediction date) error occurred in 3/3
  diagnosis trials and 0/3 explicit trials; load-time availability for history rose from 2/3 to 3/3. Every
  explicit-condition design was correct at the grain the diagnosis agents missed.
- **Operationalizing the rule across the data model remained hard.** Given the rule as one sentence, agents applied
  it uniformly — including to tables where `synced_at` means "latest version loaded" rather than "first available"
  (3/3 tickets, 1/3 opportunity existence). Knowing the invariant did not tell them which timestamp represents
  availability for each table, even though the data dictionary documents it.
- **Validation did not change at all.** 6/6 agents validated by aggregate AUC and none audited feature values against
  history for a single example. In the explicit condition an AUC within 0.009 of the correct value was accepted from
  features scrambled across rows.
- **The pass-rate comparison is uninformative** because the disclosure wording introduced a confound that alone
  explains one explicit failure.

Classification: **mixed — both inference and implementation/validation contribute.**

**Strongest conclusion supported by the paired experiment.** Stating the point-in-time invariant eliminated the
grain error that caused every diagnosis failure, but did not produce correct repairs, because agents then
over-applied the stated rule without checking what `synced_at` means per table and validated only by aggregate AUC —
which cannot distinguish correct from wrong features here. In these six trajectories, failure to validate at the
proper grain is the one behaviour that did not move under disclosure. Six trajectories from one model on one task are
exploratory evidence, not a general claim.

## 7. Limitations

- n = 3 per condition; one model; one task.
- The explicit condition's wording flaw confounds its outcome; a re-run with corrected wording is needed for a clean
  pass-rate comparison.
- Probe edits are minimal hand corrections to agent code; they bound how close each design was, not what agents would
  have done next.
- gemini-cli thought summaries are summaries; claims rest on tool calls, outputs and final code.
