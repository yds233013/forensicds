# Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism Variants

## One sentence

Grade a professional AI analysis not by whether its answer is right on the world it was shown, but by re-executing the
deliverable it submitted against sibling worlds built from the same documents with one latent mechanism set differently —
requiring it to hold, to flip, or to decline, according to what that mechanism does to the correct decision.

## Short version

A frontier agent, given a manufacturing quality dispute, recovers a drifted gauge's offset to 7.81 µm against a design
value of 8.20, recomputes the corrected nonconforming rate to 3.81 % against a true 3.83 %, and correctly recommends no
supplier action. It also writes `"tooling": 0.0` into the attribution as a literal, because on this
quarter's data the tool-wear contribution happens to be 0.17 percentage points. Regenerate the same organisation with a
longer insert-change interval, where wear contributes 3.08 points, and that same analysis pushes the rate past the
contract's 5.5 % limit while still recommending no action — and every rubric criterion still passes on the world it was
shown.

Professional benchmarks grade one instance of one world, and APEX does so deliberately: audits ensure "a single correct
and well-specified answer exists", each task belongs to one world, twenty-four incomplete-information tasks were
removed, the judge sees the deliverable not the trajectory. Right for scoring — and it makes one property unmeasurable:
whether a deliverable is correct *because* the analysis identified the mechanism, or merely because it coincided with
that mechanism's value in the world it saw.

I propose to measure it. Author the world as a generator over its decision-relevant latent mechanisms, then re-execute
the agent's deliverable, unchanged, against siblings it never saw. Because the verifier re-runs the artifact rather than
re-prompting the model, the marginal cost of the Nth sibling is compute, not inference: in a pilot, nine rollouts cost
$1.4667 in total and each was graded against four worlds. Contamination resistance comes free — siblings are regenerated
at grading time, so there is no fixed instance to memorise.

Preliminary, model-free: of 45 single-defect mutations of expert reference analyses, 10 of the 42 defects (24 %) are
invisible on the visible world and caught by a sibling, while all three reference analyses pass all four worlds.

The primary experiment can end the project. 150 defects written by experts who did not author the worlds are graded by
three instruments: visible-instance grading, the strongest rubric two independent experts can write for the visible
world alone, and the family. **If the family's incremental detection over that rubric is under ten points, expert
rubrics on one world are sufficient and I report that.** Only then do six frontier agents run the model study, with a
second arm re-running agents from scratch on siblings to separate artifact brittleness from analysis failure.

Scope is bounded: the method needs a re-executable deliverable and a generatively authored world, so it fits data
science, analytics, accounting close and financial modelling, not prose. Components are credited rather than claimed —
hidden decision-relevant variants are Turk's (arXiv:2605.30590), scored abstention on non-identifiable estimands is
CausalDS's (arXiv:2607.08093), invariance/sensitivity is metamorphic testing's. Unoccupied is the decision-flipping
sibling over a fixed artifact corpus, graded by re-execution.
