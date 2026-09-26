# Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism Variants

An agent is handed a manufacturing quality dispute: a defect rate has risen, and a supply agreement caps
material-attributable defects at 5.5 %. A frontier model finds that the measurement gauge has drifted, recomputes the
corrected nonconforming rate to within 0.02 points of the truth, and recommends no supplier action — which is right.
It also writes `"tooling": 0.0` into the attribution as a literal, because on this quarter's data the tool-wear
contribution happens to be 0.17 percentage points. Regenerate the same organisation with a longer insert-change
interval, so wear contributes 3.08 points, and that same analysis charges the wear to the supplier: replayed there it
reports a material contribution of 3.92 points against a true 0.82, and raises a contractual nonconformance where the
correct answer is still no action. Every rubric criterion still passes on the world the agent was shown. The analysis
was correct; it was not correct for a reason that survives the world being different.

Professional benchmarks grade one instance of one world, and the strongest of them do so deliberately: APEX-Accounting
verified that each task "admits a single defensible answer", removed twenty-four incomplete-information tasks, and
gave each task one world. That is right for scoring, and it leaves one property out of reach — whether a deliverable
is correct **because** the analysis identified the mechanism that makes it correct, or merely because it coincided
with that mechanism's value in the one world it saw.

**Conditional correctness** measures it. Author the professional world as a generator over its decision-relevant
mechanisms, then grade the agent's executable deliverable by re-executing it, unchanged, against sibling worlds it
never saw — same documents, same contract, one mechanism set differently. A correct analysis must stay invariant where
the mechanism does not bear on the decision, change to a specified different decision where a mechanism crosses the
governing document's threshold, and defer where the sibling withdraws the evidence that identified the answer. The
unit is the world family. Because the verifier re-runs the artifact rather than re-prompting the model, siblings cost
compute rather than inference — in my pilot, nine rollouts were each graded against four worlds for $1.4667 in total —
and regenerating them at grading time leaves nothing fixed to memorise.

Most ingredients are borrowed and I want to be exact about that. Invariance-and-sensitivity relations belong to
metamorphic testing. Hidden, pre-registered, decision-relevant variants of professional cases are Turk's
(arXiv:2605.30590). Scored abstention on non-identifiable estimands in a data-science agent benchmark is CausalDS's
(arXiv:2607.08093), whose matched variants "never flip an identifiability label". The contribution is therefore not
hidden variants, invariance, sensitivity, deferral or variant generators. What I did not find in the APEX materials or
adjacent work I reviewed is the conjunction: a professional *executable* deliverable, re-executed rather than
re-prompted, against siblings where a changed mechanism can flip the correct decision, over a *fixed* rule corpus,
compared against the strongest visible-world expert rubric. An increment, not a paradigm.

The pilot evidence is model-free and it is calibration, not prevalence. Across 45 single-defect mutations of expert
reference analyses in three worlds, 42 of them defective, 30 are caught numerically on the visible world, **10 are
invisible there and caught by a sibling**, and 2 are invisible on all four, caught instead by procedure-inspecting
criteria. All three reference analyses pass all four worlds, so siblings are not simply harder. Across nine
prospective trials of one frontier model, visible-instance grading records four successes where family grading records
none. **10 of 42 is 23.8 %, and it is not an estimate of how often this occurs in professional AI deployment** — three
synthetic worlds, one domain, defects written by the worlds' own author. It shows only that the instrument may add
information.

The experiment is designed so its primary comparison can end it. Five to six families in production data science,
frozen under a hashed analysis plan before any model runs; then 150 defects written by practitioners who did not
author the worlds, graded by three instruments — visible-instance grading, the **strongest rubric two independent
experts can write for the visible world alone**, and the family. **If the family's incremental detection over that
rubric is under ten percentage points, I report that expert rubrics appear sufficient and that the marginal value of
building mechanism families is small.** Ten points is a pre-registered decision rule, not a powered significance
threshold. Only then do frontier agents across four-plus developers run the model study, with a second arm re-running
agents from scratch on siblings to separate artifact brittleness from analysis failure. Reference procedures must pass
every sibling, and a static-analysis baseline must be beaten.

This is why the project needs Mercor, for validity not convenience. My pilot's weakness is that one person authored
the worlds, the defects, the rubrics and the verifier, so every result is confounded by the possibility that I built
worlds able to see the defects I thought to write. Removing that confound means separating roles across independent
practitioners: authoring the mechanisms; adjudicating, blind, the correct decision in each sibling; writing the
control-arm rubric uninformed about the method; injecting defects a practitioner would plausibly make; solving the
tasks as a human reference; and classifying each failure as reasoning or bookkeeping. No role may be held by whoever
authored the family it touches. Compute cannot buy that; a network of practising professionals can.

Three months is enough because the infrastructure exists and has been run: the generator, the verifier, the defect
harness, and one prospective evaluation under a hashed plan with nine valid trials of nine. The output is the
methodology, five to six validated families with adjudication records, the independently authored defect bank, the
rubric comparison, the multi-model experiment and a technical report — plus, if schedule allows, a small probe taking
the workflow of a public accounting task as a reference for authoring one new parameterised family of my own. Six
families are a research sample, not a new benchmark, and the method is bounded to generatively authored worlds with
re-executable deliverables.

The reason to measure this is that a professional analytical deliverable is usually reused. A pipeline, close
procedure, monitoring analysis or pricing model that is right this month may be wrong next month when the underlying
business mechanism moves. Single-instance grading asks whether the answer was correct; conditional correctness asks
whether the procedure is correct for the conditions under which it will be reused — a second reliability axis
alongside single-instance pass rate, not a replacement.
