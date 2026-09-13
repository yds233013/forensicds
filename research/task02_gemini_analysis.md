# Task 02 — Gemini 3 Flash Preview baseline (diagnosis condition)

Status: exploratory baseline, n = 3. Task frozen at commit `0f9a21c` (clean tree); Task 01 untouched.
Per-trial table: `research/task02_trials.csv`. Step ids refer to ATIF `step_id`s in
`jobs/task02-gemini3flash-diagnosis/<trial>/agent/trajectory.json` (agent steps are even).

## 1. Setup

| Item | Value |
|------|-------|
| Command | `harbor run -p candidates/02-renewal-risk-regression -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task02-gemini3flash-diagnosis --artifact /workspace -y` |
| Agent / model | gemini-cli / `google/gemini-3-flash-preview`, paid tier; key from `~/.zshrc`, never printed |
| Infrastructure | 0 exceptions, 0 retries, no API/quota errors in any agent log; job 10 m 42 s; $0.70 |
| Preserved | ATIF trajectory, native gemini-cli trajectory + stdout, verifier ctrf/stdout/reward, result metadata, final `/workspace` |
| Derived (not committed) | `<trial>/analysis/{timeline.txt, touches.json, diff.patch, changed_files.txt, integrity.json}` |

## 2. Results

| Trial | Reward | Checks passed / failed | Agent steps | Agent time | Final eval AUC it produced |
|-------|-------:|------------------------|------------:|-----------:|--------------------------:|
| `nXXMdDm` | 0 | 11 / 8 | 42 | 295 s | 0.7697 |
| `pf9zaPc` | 0 | 10 / 9 | 42 | 216 s | 0.7698 |
| `JctTpSi` | 0 | 10 / 9 | 47 | 285 s | 0.6347 |

Reference (oracle) eval AUC on the same extract: 0.7806; incident pipeline: 0.9258.

- **Empirical success rate:** 0/3 = 0.00 — an empirical estimator of per-attempt success from three trials
  (Wilson 95% interval ≈ 0.00–0.56), not an exact pass@1.
- **pass@3:** 0.
- No reward hacking: no trajectory references `/tests`, `/solution` or verifier outputs; the warehouse extract in
  every final workspace equals a pristine regeneration; no data, report or model-config edits (nXXMdDm also added a CHANGELOG entry).

## 3. Verifier failures (exact)

| Check | nXXMdDm | pf9zaPc | JctTpSi |
|-------|---------|---------|---------|
| extract unmodified, run succeeds, examples, contract/usage/support, predictions/report, determinism, scoring | pass | pass | pass |
| CRM pipeline point-in-time | **fail**: has_renewal_opp 4, stage 4, amount 4, days_to_close 4, open_expansion_opps 127 | **fail**: has_renewal_opp 4, stage 17, commit 2, best_case 2, amount 5, days_to_close 7, competitor 3, open_expansion_opps 127 | **fail**: open_expansion_opps 206 |
| Customer Success point-in-time | pass | **fail**: health_score 93, health_red 3, nps_last 21, sentiment 4 | **fail**: health_score 1,538, health_red 58, nps_last 1,536, sentiment 193 |
| Model specification preserved | **fail**: rank corr 0.946 | **fail**: rank corr 0.946 | **fail**: AUC 0.635 vs 0.781 |
| Hidden A features / evaluation | **fail** (expansions 63) / fail | **fail** (CRM + health + expansions 63) / fail | **fail** (expansions 115 + health ~724) / fail |
| Hidden B features / evaluation | **fail** (existence 2 + expansions 105) / fail | **fail** / fail | **fail** / fail |
| Hidden C features / evaluation | **fail** (expansions 72) / fail | **fail** / fail | **fail** / fail |

Model-behaviour failures are downstream of feature errors in all three trials (no model changes).
No trial passes the visible checks and fails only hidden fixtures; every failure is already visible.

### Independent confirmation of failure causes

Re-running each agent's **submitted code** on a pristine regeneration of the visible extract reproduces the
verifier's mismatch counts exactly (so the verifier is not the source of the failures). Two targeted probes:

- The identical `open_expansion_opps` counts in `nXXMdDm` and `pf9zaPc` (127 visible; 63/105/72 hidden) come from
  the same implementation error: expansion stage reconstructed **once per opportunity** across all examples.
  Existence-by-`created_at` alone explains only 4 of the 127; correcting only the grouping key in `pf9zaPc`
  reduces 127 to 5.
- `JctTpSi` with only its grouping keys corrected (dedupe by entity **and** prediction date; counts per example)
  matches the reference on **all** features of the visible extract and all three hidden extracts.

## 4. Per-trial analysis

### nXXMdDm — F4 (root cause found, repair incorrect) · secondary F7

- **Evidence:** README, Sales note, monitoring (2) → feature dictionary, model card, config (4) → registry,
  pipeline, examples, build (6–8) → `pipeline_signals.py`, `health.py` (10) → data dictionary (12) →
  `sources/warehouse.py` (14) → usage/support (16) → reproduce run, AUC 0.9258 (18). Migration note (76) and
  CHANGELOG (80) only at the end. Never read INC-1874, `warehouse_sync_log`, deployments, experiment notes;
  never mentioned partner deals.
- **Hypotheses:** went straight to a point-in-time hypothesis at 14 ("move to those current state tables … whether
  they did implement point-in-time querying"); confirmed usage/support were correct (18); no distractor explored.
- **Localization:** both CRM and health feature families; expansion pipeline included.
- **Availability:** explicit at 22 — "`changed_at` could precede the `prediction_date` even if `synced_at` is later
  due to replication delays … I am now leaning toward using `synced_at < prediction_date`". Implemented
  `synced_at < P` for field values; ordering by `changed_at` (equivalent on this data).
- **Repair:** new `reconstruct.py`; loaders add history tables. Gaps: renewal-opportunity existence still
  `created_at < P` (CRM time), and created-but-not-loaded records receive invented field defaults (stage
  `Qualification`) rather than the documented no-opportunity defaults; expansion state keyed per opportunity (the
  latest cutoff's state is reused for earlier examples of the same account).
- **Validation:** NaN counts (38, 56), AUC 0.7697 described as "very close to the previous model version and live
  performance" (62), scoring run, headers. No example-level comparison with history.

### pf9zaPc — F4 (root cause found, repair incorrect) · secondary F7

- **Evidence:** README, Sales note, monitoring (2) → Feb eval report (4) → model card (6), feature dictionary (8)
  → `pipeline_signals.py`, registry (12) → `sources/warehouse.py` (14) → `.tables` (16) → migration note (18) →
  history table schemas (20) → data dictionary (22) → `health.py` (24). Never read INC-1874, sync log,
  deployments, CHANGELOG, experiment notes.
- **Hypotheses:** reproduced 0.9355 (Feb) and 0.9258 (Aug) before editing (30–32); leak in both builders
  identified at 34; no distractors explored.
- **Availability:** no trajectory reasoning distinguishes load time from change time for history. Loaders select
  history **without** `synced_at`; every field filtered `changed_at < P`; existence by `created_at`.
- **Repair:** rewrote both builders with per-example "latest change before P"; expansion stage keyed per
  opportunity across examples (same error as nXXMdDm).
- **Validation:** AUC 0.8076 (Feb) and 0.7698 (Aug) "match live production performance"; segment AUCs, headers,
  scoring run. No feature-level check.

### JctTpSi — F7 (substantially correct repair, insufficient validation) · secondary F6

- **Evidence:** README, Sales note, monitoring (2) → model card, feature dictionary, latest report (4) → config (6)
  → features listing, `pipeline_signals.py` (8–10) → `sources/warehouse.py` (12) → migration note (14) → data
  dictionary (16) → contract/usage/support (18) → `health.py` (20) → table sizes (22). Never read INC-1874, sync
  log, deployments, CHANGELOG, experiment notes.
- **Hypotheses:** leak identified at 18 ("look-ahead bias" in both builders); no distractors explored.
- **Availability:** first implementation filtered `changed_at` (26–30); at 38–40 corrected, citing the model card:
  "I had been using `changed_at`, but the model card explicitly says to use the warehouse state at the start of the
  prediction date … `synced_at` for filtering, `changed_at` for ordering". Existence = created before P and a
  loaded history row (equivalent to load-time existence).
- **Repair defect:** `drop_duplicates([entity, field])` omits the prediction date, so for an entity shared by
  several examples only one cutoff survives (health defaults for the others); expansion counts grouped by account.
- **Validation:** its own reruns showed AUC 0.679 → 0.669 → 0.667 as of 2026-02-15 (32–48), below v2.3's 0.777; at
  50 it noted "I'm stuck, since v2.3 was listed at 0.777" and moved on. At 88 it suspected duplicate keys in `_as_of`
  but did not check. Validated scoring thoroughly (found and fixed an empty-batch crash in `usage.py`, values
  unchanged).

## 5. Behavioural checklist (from trajectories and final code)

| Question | nXXMdDm | pf9zaPc | JctTpSi |
|----------|---------|---------|---------|
| 1 Identified temporal leakage | yes (14–20) | yes (34) | yes (18) |
| 2 All affected families (renewal opp, expansions, health) | yes | yes | yes |
| 3 Distinguished source time vs warehouse availability | yes (22) | no | yes (38–40, after first using `changed_at`) |
| 4 `synced_at` governs availability | yes for field values | no | yes |
| 5a CRM history | partial (existence) | partial (`changed_at`) | yes |
| 5b Health history | yes | no (`changed_at`) | semantics yes; implementation broken |
| 5c Record existence | no (`created_at`) | no (`created_at`) | yes |
| 5d Expansion count | no (per-opportunity key) | no (per-opportunity key) | no (per-account counts, per-entity dedupe) |
| 5e Nightly/weekly/replay semantics | implicitly via `synced_at` | no | implicitly via `synced_at` |
| 6 Relied on `changed_at` incorrectly | no | yes | initially, corrected |
| 7 Hard-coded outage/lag/weekday/dates | no | no | no |
| 8 Dropped features | no | no | no |
| 9 Changed model config | no | no | no |
| 10 Modified source data | no | no | no |
| 11 Validation | NaN counts + AUC | AUC + segments | AUC + scoring; ignored AUC red flag |
| 12 Passes visible, fails hidden | no (fails visible) | no | no |
| 13 Benchmark/spec/tool issue | none found | none found | none found |

## 6. Cross-trial comparison

**All three fail at the same conceptual boundary, reached by different routes.** Every agent correctly diagnosed the
incident (current-state CRM and health objects used for historical examples), localized all three affected feature
families, rejected the obvious shortcuts (no dropped features, model changes, data edits, hard-coded dates), and
rebuilt state from field history. None completed the invariant *at the example grain*:

1. **State must be a function of (entity, prediction time), not of the entity.** All three collapsed an entity that
   appears in several examples to a single state: two by reconstructing expansion stage per opportunity (reusing the
   latest cutoff's state for earlier examples — a re-introduced look-ahead), one by de-duplicating per entity (data
   loss for all but one cutoff). This single conceptual slip is the largest contributor to every failure.
2. **Availability semantics:** 2/3 used load time (`synced_at`) for field values; 1/3 used business time throughout.
   Existence was reconstructed by load time in only 1/3.
3. **Validation stopped at the aggregate.** Two partial repairs produced AUC 0.770 — within 0.011 of the correct
   0.781 — and both agents cited this as proof. The one repair with fully correct semantics produced AUC 0.635–0.667,
   visibly below v2.3; the agent noticed and did not investigate. No agent compared any reconstructed feature value
   with the underlying history rows for a single example.

What did *not* separate them: evidence order (all read the Sales note, monitoring, model card, feature dictionary,
data dictionary and the two builders early); leakage recognition (first leak hypothesis 20 s, 81 s and 27 s after start); distractors (none were
investigated by any agent — class weighting, winsorization, window, sklearn and CS recalibration were never
opened); ops notes (no agent read INC-1874 or `warehouse_sync_log`, and none mentioned partner-channel loads).
The closest trial (`JctTpSi`) differed by grounding availability in the model card and by using load-time existence,
but had the weakest validation discipline.

## 7. Benchmark-validity assessment

For every failure: **genuine model failure, not a benchmark problem.**

- The verifier's feature mismatches are reproduced exactly by running each agent's code on a pristine extract.
- Failure causes are (a) state keyed per entity instead of per (entity, prediction time) — a violation of the
  point-in-time invariant, independent of any schedule detail; (b) `changed_at`/`created_at` used as availability,
  against the model card's prediction point and the data dictionary's `synced_at` definition; (c) invented defaults
  for records not yet loaded, against the feature dictionary's no-opportunity defaults.
- No contradictory documentation, inaccessible evidence, environment/tool failure or rejected equivalent solution
  was observed. A corrected version of one agent's own design passes all hidden fixtures.

Design observations (not flaws): `open_expansion_opps` — the one feature where an entity is shared across many
examples of an account — is where all three failed; the CRM-outage / partner / sync-log evidence that the hidden
fixtures stress was never consulted, so this baseline did not test resistance to hard-coded schedules; model-
behaviour checks failed only as a consequence of feature errors.

## 8. Research interpretation

**Assessment: NEAR A USEFUL CAPABILITY FRONTIER.** pass@3 = 0 meets the < 30% target, yet every agent found the root
cause and one produced a semantically correct design with a grouping bug. Failures are genuine, informative and
concentrated at one boundary rather than scattered. Three trials cannot distinguish "near" from "difficult"; the
Wilson interval on success is wide.

**Broader hypothesis** — *frontier data agents may identify technical symptoms but fail to recover and preserve the
latent business/statistical invariant needed for a correct general repair*: these trials **support it (exploratory,
n = 3)**. All agents recovered the headline invariant ("no future information"), but none preserved it at the
example grain, two missed its availability definition for record existence, one missed it for field values, and
two accepted a repair because the aggregate metric looked right. The evidence is more specific than the hypothesis:
the binding constraint was preserving the invariant *consistently across the data model* (entity × prediction time,
existence, availability), and validating it below the aggregate metric — not recognizing leakage.

## 9. Limitations

- Three trials of one model; no paired condition yet.
- gemini-cli thought summaries are summaries; claims rely on tool calls, outputs and final code, with reasoning
  quoted only where it documents a decision.
- The locally re-run "grouping key corrected" probes change the agents' code; they establish how close the designs
  were, not what the agents would have done.

## 10. Recommended next experiment (not run)

**Invariant-disclosed paired condition, 3 trials, same environment and verifier.** The instruction additionally
states the rule the verifier enforces — "each example's features may use only rows loaded into the warehouse
(`synced_at`) before 00:00 UTC on its prediction date; this applies to every record and every example
independently" — without naming files or the leak. If agents then pass, the bottleneck is inferring the invariant;
if they still fail on per-example state and aggregate-only validation, the bottleneck is preserving and validating
it. This directly splits the two halves of the hypothesis that this baseline cannot separate, at ~$0.70.
