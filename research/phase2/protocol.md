# Phase 2 — prospective-validation protocol (freeze → validate → expose)

The discovery set (the 15 measured tasks) is spent. The prospective set must be protected from the
model it will be used to measure. Four rules govern the whole phase.

**R1. No target-model exposure during design.** No "quick test to see if it is hard". A task that has
been shown to any target model is a discovery-set task for ever.

**R2. Expert solve path recorded first.** Before freeze, the author writes the intended solution *and*
the intended discriminating test as a dated document, plus the sophisticated wrong route and its
coherence checks. This is what P1/P3 are measured against, so it cannot be written afterwards.

**R3. Gates pass before spend.** The full gate list below, all model-free.

**R4. Analysis plan pre-registered.** How the trials will be labelled, and what each prediction's
disconfirming result looks like, written before the first trial.

## Gate list (all before any target-model call)

| gate | what it checks | fail action |
|---|---|---|
| scientific specification frozen | estimand, population, grain, temporal state, decision rule, tolerance basis | rewrite before build |
| workspace frozen + checksum | tracked-content hash recorded; generator copies identical | re-freeze |
| **Oracle = 1** | the reference solution passes on the visible and all hidden extracts | fix task |
| **Nop = 0** | the untouched incumbent fails | fix task |
| wrong-analysis mutation suite | ≥10, ideally 20–40, scientifically plausible wrong solutions each scored 0; ≥1 behaviour-preserving mutant scored 1 | fix verifier |
| **separation margin** | every wrong object differs from truth by more than the graded tolerance on ≥3 of 4 extracts | reject design |
| **decision-margin test** | the wrong objects flip the decision on ≥half the extracts | narrow the threshold or reject |
| **discriminating-test inventory** | ≥2 named L3 routes present in the workspace, with their expected outcome under each hypothesis | reject design |
| cheap-solve audit | no single filter/join/formula/doc-lookup/decision-guess reaches the graded answer; verified by implementing each shortcut | fix design |
| **stated-object audit** | an independent reviewer searches the workspace for any sentence that states the object; if one exists, remove it or reject | mandatory |
| ambiguity audit | two independent readers derive the same estimand from the documents alone | rewrite docs |
| multiple-valid-method audit | ≥2 legitimate routes implemented and both pass; each accepted method recorded | widen the verifier |
| correct-table / identifiability test | two independent computational derivations of every graded quantity agree exactly | fix generator |
| hidden-extract validation | 3 regimes, decisions not constant, no extract within the tolerance of a threshold | re-parameterise |
| grading evidence map | each graded quantity mapped to the reasoning step it tests, and to the mutation that would break it | complete before freeze |
| secret scan + leakage scan | no credentials; generator, scenarios and truth absent from the shipped image | fix build |

## Exposure procedure

1. Freeze; record checksum and commit; archive the expert solve path and the analysis plan.
2. Run Oracle and Nop on the frozen artefact; record rewards and digests.
3. Run **exactly three** target-model trials per task, sequentially, one trial per job, all on one task
   digest; do not adjudicate between trials.
4. If a trial is infrastructure-invalid (empty verifier output, ~2 s verifier phase, container teardown),
   adjudicate it *before* looking at its reasoning, and replace it with one authorised re-run.
5. Label trials against the pre-registered analysis plan. **No task change is permitted after step 3**,
   for any reason short of a demonstrated verifier defect — and a verifier defect excludes the task from
   aggregates rather than licensing a revision.
6. Run ≥2 model families before making any behavioural claim (rival A7).

## Two conditions worth pre-planning (not required for the main result)

- **A3 condition (falsification-as-deliverable).** On 2 of the 6 tasks, a paired variant whose output
  contract additionally requires a named diagnostic (a pre-trend table, a placebo estimate, a
  design-weighted stratum estimate). Graded. This tests whether the behaviour is absent or merely
  unrequested, and it is the single most informative cheap experiment the project can run.
- **A1 condition (object disclosed).** On 1 task, a variant whose instruction states the correct object
  but not how to compute it. Tests capability-vs-disposition. Must be built as a *separate frozen task*
  with its own verifier so the phase-1 confound (an added paragraph contradicting the reference) cannot
  recur.
