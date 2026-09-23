# Phase 2 — design framework (written before the external research landed; revised after)

## The narrow capability

> **Discriminating-evidence selection under competing interpretations.**
> When production evidence admits several defensible scientific interpretations, determine which
> evidence *discriminates* between them, obtain it, and let the result change the analysis — before
> committing to a consequential decision.

This is one capability, instantiated across many professional domains. It is deliberately *not*
"avoid failure mode F9", and it is defined without reference to any model's observed behaviour.

## Operational definition of a discriminating test

A test T discriminates between interpretations A and B for an incident if, **before running it**, the
practitioner can say: T's outcome differs under A and under B, and T is obtainable from the workspace
at a cost small relative to the decision. Formally, in the notation the design will use:
`P(T = t | A) ≠ P(T = t | B)` for some observable t.

Three validation layers, kept conceptually distinct throughout:

| layer | question | example | what it cannot do |
|---|---|---|---|
| **L1 coherence** | do my outputs agree with themselves / with a trusted figure? | totals tie; bridge identity holds; my recomputation matches my pipeline | cannot detect an error shared by both sides of the comparison |
| **L2 robustness** | does my conclusion survive reasonable alternative specifications? | vary bandwidth, window, tolerance, covariate set | cannot detect an error common to all the specifications tried |
| **L3 falsification** | is there evidence that could contradict my *interpretation*? | negative control, placebo period, known-answer subset, pre-trend, on-policy anchor, synthetic-censoring replay, an invariant from an independent system, a randomised stratum | — |

The design rule that follows: **L3 must be possible without any document saying "run a placebo"**, and
the workspace must contain the raw material for it (a randomised stratum, a dual-instrumented period,
retained reference samples, a natural experiment, an independent system of record).

## Admission test, operationalised

A candidate is admitted only if all fifteen hold; failing any of #1, #3, #5, #6, #7, #8, #10, #14 is
fatal.

1. recognizable professional DS work
2. consequential decision depends on the analysis
3. **answer not stated in workspace documentation** (the "derived, not stated" test)
4. ≥3 initially plausible hypotheses
5. ≥1 wrong interpretation yields a coherent, plausible result
6. evidence exists that distinguishes the interpretations
7. ≥1 meaningful falsification route
8. correct solution requires reconstructing something from **how the data came to exist**
9. >1 decisive scientific commitment
10. scientifically necessary quantities gradable deterministically or with a defensible tolerance
11. multiple legitimate methods can be accepted
12. hidden extracts can be generated without changing the scientific task
13. ≥10 scientifically plausible wrong solutions can be constructed
14. a real practitioner would recognise the situation
15. belongs to a scalable family without being a template clone

**Two tests added from the phase-1 audit**, both checkable before any model runs:

16. **Margin test.** The decision rule's margin must be narrow enough that the plausible wrong
    interpretations change the decision on at least half the graded extracts. (Phase 1 found six
    trials where the decision survived every quantity being wrong; that is a property of the
    threshold, not of the analysis.)
17. **Discriminating-test inventory.** The author must be able to name, before build, at least two
    distinct L3 routes present in the workspace and state what each would show under each hypothesis.

## Hardness structure

Target reasoning chain, with the number of *consequential scientific commitments* as the hardness
metric (not file count):

incident → reproduce → inspect heterogeneous evidence → generate hypotheses → reconstruct operational
state → fix population/grain/time → assess measurement validity → define the estimand → choose an
identification or modelling strategy → estimate → notice the contradiction → run a discriminating test
→ falsify at least one hypothesis → revise → re-estimate → validate independently → quantify
uncertainty → decide → repair.

A candidate is "materially harder" only if **≥3 of those steps are consequential and dependent**: the
wrong choice at step k makes step k+1 look fine. Adding files, tables or documents does not count.
