# Phase 2 — design principles, each traced to evidence rather than intuition

## From the benchmark review

**DP1. Anchor every graded quantity to a declared latent world, not to a reference answer.**
AvalancheBench's construction (latent state `Z` in a config; artifacts derived from it; rubric items derived
from `Z`) is what makes it possible to grade *why* an answer is right. Adopt; ForensicDS already does this
and should state it as the reason its verifiers are defensible.

**DP2. Grade the scientific object separately from the deliverable.** Otherwise the score measures
formatting. DataSpace: **52 %** of the best model's failures were "answer materialisation", not analysis.
CausalReasoningBenchmark: strategy correct **79.2 %** but the full identification spec only **34.1 %** — a
30-point gap that is only visible because the layers were scored apart. KramaBench: pipeline design **41.6 %**
vs sub-task implementation **19.8 %**. Therefore: make the estimand, population, grain, temporal state,
denominator, feasible set and adjustment set **named, separately-graded outputs**.

**DP3. ⚠️ The wrong-but-authoritative artefact must not always be wrong.** A suite in which the published
number is always wrong is gamed by an agent that always disagrees; that measures contrarianism, not
forensics. **All five current ForensicDS tasks have a wrong published number — a structural bias.** Every
world must therefore contain (a) authoritative artefacts that are correct and should be deferred to, and
(b) at least one incident whose published number is right and whose complainant is wrong (candidate **P31**),
with hidden extracts that vary which side is correct. Evidence: no reviewed benchmark plants a wrong
authoritative artefact at all, and BAITBENCH shows the adjacent failure — **57.1 % of runs exploit a planted
shortcut, and telling the model not to reduces it by only 6.21 pp**.

**DP4. Score detection-and-reporting of a defect, not merely avoidance of it.** MLE-bench documents real
target leakage in its own corpus (`giver_username_if_known`) and treats it as a defect to patch, while an
agent exploiting it is rewarded. Invert: the leak is the finding; grade naming the mechanism.

**DP5. Require a precommitted falsifying observation, and grade whether the test could actually refute the
claim.** Popper's audit of its own runs: **ineffective falsification design 28.1 %**, "falsification test
breaks implication" **17.2 %**, misinterpreted p-values 35.9 %. So "ran a test" is not the measurement —
implication-validity must be graded separately.

**DP6. Make abstention and non-identifiability scoreable.** Exactly one reviewed benchmark scores abstention
(CausalDS, which routes any abstention to a binary and finds frontier models abstain at only 56–75 %
accuracy); no data-agent benchmark does. Candidate **P32** implements this, with hidden extracts where
identification *is* available so "always abstain" fails.

**DP7. Penalise merges and fluent wrongness.** AvalancheBench's merged-temporal-events failure was invisible
to topic recall and rating-trend metrics. SCIRIGOR: agent claims agree with faithful and unfaithful results
at **91.8 % vs 91.0 %** — the prose is identical whether the underlying result is right or wrong. DataCross
shows the rubric version: GPT-4o scores higher on Logic (0.41) than on Factuality (0.33). Any rubric with an
"insight" axis and no faithfulness gate rewards well-argued nonsense.

**DP8. Instrument where the first error entered.** Not just end-to-end. LongDS-Bench: **~47-point** decline
from early to late turns, with 52–69 % of failures long-horizon. Traverse: frontier judges locate the first
mistake in fewer than a third of runs. ForensicDS should declare the commitment list per task *before*
freeze so first-error attribution is pre-registered rather than post-hoc.

**DP9. Audit the gold answers adversarially and report agreement.** Measured gold error rates: **BIRD
Mini-Dev 52.8 %, Spider 2.0-Snow 62.8 %**; ELT-Bench-Verified found benchmark-attributable errors in
**82.7 %** of failed transformation tasks and **9.85 points** of apparent model progress came from fixing the
benchmark. BLADE's expert–expert agreement of **75–80 %** is the realistic ceiling for any human-anchored
judgement. Budget an adversarial audit pass; report the ceiling.

**DP10. Prefer deterministic checks; distrust judges.** InfiAgent-DABench rejected LLM judging because
"GPT-4 could only achieve 67 % consistency with human experts". AvalancheBench flags judge bias on length,
position and lexical overlap, with a judge from the agent's own family.

**DP11. Seal the environment and log tool calls.** CausalGame documents agents probing simulator APIs to
recover hidden scenario identifiers for **+18.5 points**, and **39 sessions declaring success below
threshold**. ForensicDS's existing unprivileged-execution and hidden-extract machinery already covers this;
keep it and keep the runtime-integrity checks.

## From the production-failure review

**DP12. Build from documented failure structures, not invented ones.** Every candidate in this phase cites a
real instance: Walmart's SKU-rationalisation reversal; the Twente static-meter study (**+582 %/−30 %**
reading errors across nine meters, ≥750,000 households); high-sensitivity troponin moving MI incidence
**18 % → 22 %** with no outcome improvement in a stepped-wedge trial; observation stays accounting for
**~40 %** of the HRRP readmission reduction; MedPAC's **~16 %** MA coding intensity; Milliman's **8.0 %**
one-year reserve development adverse for every year back to 2016; Southwest's **16,700** cancellations and
**$140 M** settlement; the ORR's May-2018 timetable inquiry; Fowlie–Greenstone–Wolfram's **2.5×** deemed-vs-
realised gap; the NAO's **35 %** possibly-overstated savings; Lee–Padmanabhan–Whang's bullwhip.

**DP13. Design the wrong route to pass the organisation's own controls.** The six documented
"coherent-but-wrong" cases all did: the **Epic Sepsis Model** (AUC 0.63 vs a vendor-reported 0.76–0.83,
missing 67 % of sepsis cases, deployed at hundreds of sites); the **JPMorgan CIO VaR** change, approved
through model governance and disclosed to the OCC, projected to cut VaR **44 %**, ahead of **$6.2 bn** of
losses; **Ofqual 2020**, which reproduced national grade distributions *exactly* and failed at the unit of
decision; **Target Canada**, where system-to-system checks all passed and nothing compared system to shelf;
**PHE's 65,536-row truncation**, which produced a complete-looking file showing a plateau; **Google Flu
Trends**, validated against CDC ILINet for years. The lesson for L1 design: the wrong analysis must tie out.

**DP14. The discriminating test must be a thing practitioners actually run.** In every documented case one
existed and was cheap: external validation on local patients; parallel-running old and new model; evaluating
at the unit of the decision; counting shelves; reconciling row counts; comparing against a naive
autoregressive baseline; bureau performance on *rejected* applicants; calendar-year diagonals of a loss
triangle; a waiting-list cohort; POS variance ratios; retained reference parts.

**DP15. Prefer mechanisms with an independent physical or contractual aggregate.** SCADA feeder peaks,
network offtake, the general ledger, RMA records, payroll rules engines, customer goods-receipts. These make
ground truth unarguable and give the verifier a second derivation (DP1's identifiability requirement).

**DP16. Small-count metrics are a trap unless the noise is the point.** TRIR changes are **96–98 % random
variation**; Backblaze requires **50,000 drive-days** before a model's AFR is reportable. Either give the task
enough exposure that the estimate is stable, or make the *uncertainty* the graded object (candidate P23).

## Carried from the phase-1 audit

**DP17. Object must be derived, not stated** (the strongest phase-1 regularity: five stated-object tasks
solved, four derived-object tasks not).
**DP18. Decision margin must be narrow enough that the wrong object changes the decision** (six phase-1
failures had the decision right; decision-robustness measures the author's threshold choice).
**DP19. Never grade a stylistic choice; accept every legitimate method, and if two defensible methods
disagree materially, the task is not gradable** (the G10 mixing-family lesson).
**DP20. Verify the discriminating-test inventory before build** — ≥2 routes, with their expected outcome
under each hypothesis written down.
