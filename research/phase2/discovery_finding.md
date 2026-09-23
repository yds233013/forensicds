# Phase 2 — what the discovery set actually established (corrected)

The 15 measured tasks and 45 valid target-model trials are the **discovery set**. The audit of
2026-09-23 corrected the project's own earlier interpretation. What follows is what survives.

## Established

1. **Recognition is not the bottleneck.** In every one of the 13 failed final-suite trials the agent named
   the broad problem class correctly.
2. **The failures localise to a commitment step, not an execution step.** All four 0/3 tasks were
   reconstructed *correctly* at the operational-state layer — G05's analysis panel was byte-exact on all
   four extracts in all four trials; every G10 trial passed the in-stock identity; every G24 trial rebuilt
   the exploration stream. The failure is at choosing the counterfactual, the conditional expectation's
   conditioning set, the action space and decision unit, or the availability clock.
3. **Near-absence of discriminating tests.** Across 45 valid trials: **0 placebo tests, 0 pre-trend or
   parallel-trends checks, 0 negative controls, 0 held-out/back-test validations, 0 known-answer
   simulations.** One trial (G10 `cLtM9yi`) ran a falsification-class check — on its diagnosis, not on its
   own estimator. Every task shipped a cheap, decisive route that was never taken.
4. **Coherence checks computed inside a wrong frame reliably confirm it.** Demonstrated mechanically in at
   least five trials. The sharpest: G24 `wVmAykK` compared its IPS estimate (0.305) with an on-policy anchor
   (0.2975) **at the same wrong grain** and called the agreement "astonishingly close… highly accurate";
   at the correct grain the comparison is 0.305 vs 0.3846 and fails.
5. **Right decision, wrong science, in 6 of 13 failures.** On G24 all three trials got the launch call right
   on all four extracts while every policy value was outside tolerance; a decision-only grader would have
   scored the task 3/3 instead of 0/3.
6. **Difficulty tracks one design property.** Every task whose scientific object is *stated* in the
   workspace was solved; every task whose object must be *derived* was not — with G34 the single exception,
   solved in ~20 steps with **zero warehouse queries**.
7. **The failures are model-side.** Zero tool errors, timeouts, permission failures, OOM or import failures
   in any failed final-suite trial; all 13 reproduce from the agents' own submitted code.

## Corrected

- **F9 is not dominant.** The report claimed 10/13 failed trials were "right method family, wrong
  statistical object". Under a strict bar it is **4/13** (6 across the whole pool). The dominant labels are
  **F1** (committed to an identifying assumption, never tested it) and **F4** (correct diagnosis,
  semantically wrong repair), each with **F7** as a secondary.
- **A new label was needed:** **F11 coherence stopping** — a check is run, agreement obtained, and agreement
  treated as confirmation when the check had no discriminating power. This is what actually terminated most
  trials, and it is distinct from "no validation".
- **Two task-side defects exist, both outside the final five.** The Task02 explicit-invariant *ablation* is
  contradicted by its own graded reference and its 0/3 is uninterpretable; G36's frozen grader used a
  household-weighted response against a load-weighted contract, so its "0/3" would be **2/3 under a correct
  grader** with one genuine model failure.
- **Four of the twelve pilot tasks are documentation-lookup exercises** (Task03, Task05, G35, G42) by the
  project's own admission test, and Task06 has two answer leaks.

## Why this cannot yet support the general claim

The finding was generated from tasks built by one author, measured on one model family, with n = 3 per task,
and the "stated vs derived" property was named *after* the results were seen. It is consistent with the
project's preferred explanation and also with at least eight rivals (capability rather than disposition;
budget economics; objective framing; route availability; grading artefact; domain knowledge; single-model
artefact; instruction-induced anchoring). Distinguishing them requires a **prospective** set, frozen before
any target-model contact, with the predictions and rivals written down first. That is what phase 2 designs.
