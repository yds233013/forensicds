# Cross-task Gemini 3 Flash analysis (Tasks 01–05, diagnosis condition)

## Scope and conditions

- **Model and agent:** `google/gemini-3-flash-preview` via gemini-cli, Harbor 0.21.0, `-k 3 -n 3`, `--artifact /workspace`.
- **Trials:** three valid diagnosis-condition trials per task, 15 in total. No invalid infrastructure attempts occurred in the Task 03–05 runs.
- **Task state:** tasks were frozen before the runs, and checksums were identical before and after.
- **Excluded evidence:** the Task 02 explicit-invariant ablation is confounded by its wording and is not used as causal evidence here.

Sources:
- `research/task01_gemini_analysis.md`, `research/task02_gemini_analysis.md` (earlier runs)
- `research/task03_gemini_analysis.md`, `research/task04_gemini_analysis.md`, `research/task05_gemini_analysis.md`
- Per-trial CSVs

## 1. Summary table

| task | mechanism | trials | successes | empirical_success_rate | pass_at_3 | root_cause_identified_count | correct_invariant_recovered_count | correct_grain_count | causal_repair_count | aggregate_only_validation_count | reward_hacking_attempt_count | dominant_failure_pattern |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 01 revenue reconciliation | entity grain / canonical identity after account migrations | 3 | 2 | 0.67 | 1 | 2 | 2 | 2 | 2 | 1 | 0 | F5: dedupe symptom patch without reading the identity standard (1 trial) |
| 02 renewal-risk regression | temporal leakage (load-time availability) | 3 | 0 | 0.00 | 0 | 3 | 2 partial (load-time semantics understood in 2; none complete) | 0 | 0 complete (3 attempted) | 3 | 0 | F4/F7: point-in-time state keyed at the wrong grain (entity instead of example × cutoff); existence and expansion errors |
| 03 lead-score evaluation | evaluation population under a score-driven router (selective labels, ITT) | 3 | 3 | 1.00 | 1 | 3 | 3 (finer invariants inherited, not reasoned) | 3 | 3 | 3 | 0 | none; shallow aggregate validation |
| 04 retention metrics layer | KPI population / lifecycle semantics (CRM proxy vs ARR state) | 3 | 1 | 0.33 | 1 | 3 | 1 complete (lifecycle semantics correct in 3) | 3 | 1 | 3 | 0 | F4: added a publication-snapshot filter to reproduce published history exactly; correct otherwise (counterfactual 18/18) |
| 05 experiment readout | randomization unit / exposure trigger / identity | 3 | 3 | 1.00 | 1 | 3 | 3 (transcribed from plan and scaffolding) | 3 | 3 | 3 | 0 | none; plan transcription, no unit-level checks |

Definitions and caveats:
- **Empirical success rate** is successes divided by trials. It estimates per-attempt success from three trials and is not an exact pass@1.
- **pass@3** is 1 if at least one of the three valid trials passed.
- **Task 01 counts** come from `task01_trials.csv`: `root_cause_found`, `causal_repair`, and "no account-level check".
- **Task 02 counts** come from `task02_trials.csv`: grain = `state_keyed_per_example_and_cutoff`; aggregate-only = no feature-level validation.

## 2. Benchmark-level numbers

| Metric | Value |
|---|---|
| Tasks with pass@3 = 1 | **4 / 5 = 0.80** (only Task 02 has pass@3 = 0) |
| Tasks meeting the < 30% headroom target | 1 / 5 (Task 02 only) |
| Per-attempt successes, all trials | 9 / 15 = 0.60 (Tasks 03–05: 7 / 9 = 0.78) |
| Root-cause identification | 14 / 15 (Task 01 DuhAh5u found the duplication mechanism but not the identity root cause) |
| Complete invariant recovery | 9 / 15 overall: 01 2, 02 0, 03 3, 04 1, 05 3 |
| Core semantics recovered on 03–05 | 9 / 9 (Task 04 lifecycle correct in all three) |
| Reward-hacking attempts | 0 / 15; the Task 03–05 sandbox was never tested by an attempt |
| Gemini cost, Tasks 03–05 | $1.16 (Harbor-reported: 03 $0.48, 04 $0.42, 05 $0.26) |

The five-task distribution does **not** meet the assessment's headroom target, and the tasks were not changed to reach it.

## 3. What the 15 trajectories show

**1. Recognition is rarely the bottleneck for this model on these tasks.**
- 14 of 15 trials named the root-cause class.
- On 03–05 this took 8–20 steps and one to three minutes.
- In every 03–05 trial it followed directly from a document that states the relevant property:
  - the evaluation definition's population sentence (03)
  - the metrics handbook (04)
  - the pre-registered plan (05)

**2. The failures are all post-recognition.**
- All 6 failures are F4, F5 or F7:
  - 01: F5
  - 02: F4, F4, F7
  - 04: F4, F4
- None is F0–F3 as a dominant label.
- Where the invariant needed reconstruction beyond a documented recipe, trials failed on exactness: 02's example × cutoff grain, and 01's migration chain in the failing trial.

**3. Validation is aggregate-level almost everywhere, in successes as well as failures.**
- 13 of 15 trials never checked state at the graded grain after their fix.
- Aggregate-only validation therefore does not separate success from failure. What separates them is whether the implemented rule happened to be correct.
- The 03–05 successes left membership discrepancies in their own scripts unreconciled.

**4. A new, informative failure pattern appeared: optimising agreement with a trusted historical number.**
- Both Task 04 failures had correct lifecycle semantics.
- They then added a documented publication-snapshot rule ("quarter end + 12 days") so that rebuilt history matched the published workbook exactly on all six quarters.
- That broke the handbook's definition of ARR on a date, dropped accounts, and applied to unpublished and future quarters.
- The verifier rejected it; the pre-registered `published_snapshot_arr` mutation already scored 0.
- This is H3 in a sharper form: validating against a reference number *destroyed* a correct repair.

**5. Designed traps were passed by default, not by reasoning.**
- On 03 and 05, per-protocol, label-channel, window-boundary and first-assignment traps are only traps for agents that rewrite the working code.
- The agents left that logic untouched or reused it from the buggy file.
- The one trap requiring an active choice was resolved correctly by all trials:
  - 03: intake vs any/latest holdout event
  - 05: assignments vs exposures
- Only one trial per task argued for the choice from the data or mechanism.

**6. Final write-ups were often wrong in ways the behavioural verifier does not grade.**
- Wrong causal stories: 03 blamed the June threshold change in 2 of 3 trials.
- Unrun tests claimed as passing.
- Mechanisms misdescribed.
- "Inconclusive" read as "no effect".
- Historical reports silently overwritten: 03 in 3 of 3 trials, 05 in 1.

## 4. Success vs failure: behavioural comparison

The only within-task contrasts are Task 04 (1 vs 2), Task 01 (2 vs 1) and, across tasks, 02 vs the others.

| Dimension | Observation |
|---|---|
| Breadth of evidence | Did not separate outcomes. The Task 04 failure 3SUW3gh read *more* operational docs than the success. |
| Reading business definitions | Present in all 03–05 trials. Task 01's failure skipped the identity standard; Task 04's failures read the handbook but let a README rule override it. |
| Checking data directly | Mostly aggregate queries in all trials. The Task 04 success did account-level checks before its fix only. |
| Alternative hypotheses | Low everywhere; distractors were rarely weighed explicitly. |
| Correct grain | Separated 02 (wrong grain in all) from the others. Not a separator within 03–05. |
| Validating intermediate state | Low in successes and failures alike. |
| Aggregate or reference reliance | Universal. The *choice of reference* separated outcomes on 04: handbook definition vs published workbook. |
| Stopping after a plausible number | Universal. Successes stopped after a correct plausible number; failures after an incorrect one. |

Honest reading: on these tasks, success was determined mainly by whether the documented definition was implemented literally and not overridden. Deeper investigation or validation did not decide it.

## 5. Hypothesis update

Hypothesis under test: "Frontier data-science agents fail more often at operationalizing, preserving, and validating recovered business or statistical invariants than at recognizing the headline failure class."

**SUPPORTED observations**
- 14 of 15 trials recognised the failure class, while all 6 failures occurred after recognition (F4, F5, F7).
- Validation at the graded grain was nearly absent: 13 of 15 aggregate-only. Two failure modes are validation-target errors:
  - Task 04: matched published figures instead of the definition.
  - Task 02 JctTpSi: saw an implausible AUC and did not investigate.
- Preservation failures occurred once a correct core rule was in place:
  - Task 04 added a rule that dropped accounts and broke ARR continuity.
  - Task 01's failure deduplicated rows.

**CONTRADICTORY observations**
- When the invariant is written down operationally, operationalisation succeeded almost trivially: 03 and 05 in 6 of 6 trials, and Task 04 lifecycle logic in 3 of 3.
- "Operationalisation is hard" held only when the rule had to be *reconstructed* (Task 02's per-example point-in-time state), not *transcribed*.
- Deeper validation did not distinguish successes from failures. Successes validated just as shallowly, so shallow validation is not sufficient to explain failure.
- The pre-registered per-task predictions (`benchmark_hypothesis.md` §6) did not hold:
  - 03: predicted per-protocol or worked-lead failures; there were no failures.
  - 04: predicted reactivation or segment errors; the failure was a snapshot filter.
  - 05: predicted exposure-triggered or latest-row failures; there were no failures.

**UNTESTED claims**
- The recognition side, meaning whether agents recover an invariant that is *not* documented as a property. Tasks 03–05 document the property. There is no clean localized-vs-diagnosis pair; the Task 02 ablation is confounded.
- Generalisation to "frontier agents": one Flash-tier model, one agent harness.
- Effect sizes. With 3 trials per task (15 in total), rates carry very wide intervals; for example, a 3/3 result is compatible with a per-attempt success rate well below 1.
- Whether better validation *would* have prevented the failures. No failing agent performed grain-level validation, so this is not observed.

**Net:** the data are consistent with a narrower claim. When invariants are documented, current agents transcribe them easily and fail mainly by overriding them with a competing reference or by incomplete reconstruction. They almost never validate at the graded grain. The broader claim remains plausible but largely untested on its recognition side.

## 6. Difficulty verdicts

| Task | Verdict | Basis |
|---|---|---|
| 01 | USEFUL EASY ANCHOR | 2/3 with one genuine symptom-patch failure. It requires reading an identity standard and following migration chains; it gives little headroom. |
| 02 | DIFFICULT BUT INFORMATIVE | 0/3 genuine failures after correct recognition. The failures are near misses on reconstruction grain, e.g. JctTpSi passes with grouping keys corrected. |
| 03 | TOO EASY | 3/3 in about 2.5 minutes. The population sentence plus router table make the repair a lookup; finer invariants were inherited. |
| 04 | USEFUL EASY ANCHOR (with an attractor or underspecification risk) | The core lifecycle repair is mechanical (3/3). Headroom came only from a documented snapshot rule that exactly reproduces published history, which contradicts the design doc's "no exact answer key" claim. |
| 05 | TOO EASY | 3/3 in about 75 seconds. Plan transcription plus reuse of scaffolding in the buggy file; no rows inspected. |

No task is BROKEN or INVALID. All verifiers behaved as intended: no false passes found, and every failure was genuine.

## 7. Benchmark flaws found in these runs (no task modified)

1. **Task 04:** the README's exact publication-snapshot rule reproduces the published workbook, so the workbook *is* an exact answer key for a wrong rule. The design and validation claim that it is not an answer key is inaccurate.
2. **Task 03 and Task 05:** documenting the graded property, added so that harbor check `behavior_in_task_description` passes, plus scaffolding left in the faulty module, made the repairs transcriptions. This confirms the pre-baseline cross-task review.
3. **Behavioural grading ignores harmful side effects and write-up errors.** Overwriting historical reports (4 trials) and wrong causal narratives (several trials) were unpenalised. This is a limit of the verifier design, not a bug.
4. **Sandbox untested.** No trial attempted reward hacking, so these runs provide no evidence about the hardening's effectiveness beyond the mutation suite.

## 8. Recommendation

**Outcome A, mostly easy, with one useful lesson from B.**
- Tasks 03 and 05 provide no headroom.
- Task 04's headroom came from an attractor rather than from its intended invariant.
- Only Task 02 meets the target.
- The benchmark should expand with qualitatively harder Tasks 06/07 rather than modify 03–05.

Design constraints drawn from the evidence:
1. **The invariant must be reconstructed, not transcribed.** Documents should describe the business meaning and system mechanics, while the operational rule depends on data behaviour at a non-obvious grain. This is Task 02's per-example × cutoff state, the only mechanism that produced genuine near-miss failures. Stay compatible with harbor check by specifying outputs and definitions without writing the population or recipe as a rule.
2. **Include a competing trusted reference deliberately** (the Task 04 pattern), and make the case for the definition over the reference clear and discoverable, so the attractor is fair rather than underspecified.
3. **Keep repair breadth.** Multiple interacting components or feature families, so that a single edit cannot pass.
4. **Leave no scaffolding in the faulty module**, and no loaded-but-unused data or config that point at the fix.
5. **Diversify mechanisms** beyond "rewrite the population filter". Candidates: a data-side defect such as late-arriving or backfilled data, event-time vs processing-time windows, or many-to-many allocation. Also consider a "no bug" or mix-shift negative control.
6. **Consider grading validation evidence**, for example requiring a reconciliation artifact at the graded grain, only if it can be done behaviourally without prescribing the method.

Not done, per instruction: no task modified, no Task 06 built, no extra trials, no Task 02 ablation rerun.
