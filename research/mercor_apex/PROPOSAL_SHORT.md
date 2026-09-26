# Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism Variants

## One sentence

Grade a professional AI analysis by re-executing its executable deliverable against hidden sibling worlds where one
mechanism differs, so a correct analysis must stay invariant, flip, or defer as that mechanism requires.

## Short version

A frontier agent, given a manufacturing quality dispute, correctly diagnoses a drifted gauge and correctly recommends
no supplier action. It also writes `"tooling": 0.0` as a literal, because on this quarter's data tool wear contributes
0.17 points. Regenerate the organisation so wear contributes 3.08 points, and that same analysis charges the wear to
the supplier, raising a contractual nonconformance where the correct answer is still no action — yet every rubric
criterion passes on the world it was shown.

Professional benchmarks grade one instance of one world, deliberately: APEX-Accounting verifies that each task "admits
a single defensible answer" and removed twenty-four incomplete-information tasks. That leaves one property out of
reach — whether a deliverable is correct because the analysis identified the mechanism, or merely because it coincided
with that mechanism's value in the world it saw.

**Conditional correctness** measures it. Author the world as a generator over its decision-relevant mechanisms, then
re-execute the agent's deliverable, unchanged, against siblings it never saw. A correct analysis stays invariant where
the mechanism should not matter, changes where it crosses the governing threshold, and defers where the sibling
withdraws the evidence that identified the answer. The unit is the world family, and siblings cost compute, not
inference.

Hidden variants, invariance, sensitivity, deferral and variant generators are prior work — Turk (arXiv:2605.30590),
CausalDS (arXiv:2607.08093), metamorphic testing. What I did not find is the conjunction: an executable professional
deliverable, re-executed rather than re-prompted, against siblings where a changed mechanism flips the correct
decision, over a fixed rule corpus, compared against the strongest visible-world expert rubric.

Pilot calibration, model-free: of 45 single-defect mutations of expert reference analyses, 10 of the 42 defects are
invisible on the visible world and caught by a sibling, and all three reference analyses pass all four. Three
synthetic worlds, defects written by their own author — evidence the instrument may add information, not an estimate
of how often this occurs in deployment.

The primary comparison can end the project. 150 defects written by practitioners who did not author the worlds are
graded by visible-instance grading, the strongest rubric two independent experts can write for the visible world
alone, and the family. **If incremental detection is under ten percentage points — a decision rule, not a significance
threshold — I report that expert rubrics appear sufficient.**

This needs Mercor for validity, not convenience: my pilot's weakness is single authorship, and that confound goes only
by separating mechanism authors, blind sibling adjudicators, uninformed rubric writers, defect injectors, expert
solvers and failure coders. Scope is bounded to generatively authored worlds with re-executable deliverables, and five
to six families are a research sample.
