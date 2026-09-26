# Hostile review, and the one revision pass

Written in the voice of an APEX researcher who has read the four APEX papers, Turk, CausalDS and Weng et al., who
maintains Archipelago, and whose default is to reject. Then one revision pass, then stop.

---

## The ten questions

**Q1. You claim eight siblings per family with determinate correct decisions. Getting *one* defensible answer took
us multiple audit passes per task and we still deleted twenty-four tasks. Why should I believe you can adjudicate
eight?**

You shouldn't, on assertion. Which is why the flip-sibling discard rate is now a reported finding rather than a
risk line, and why family size is a floor of two validated flip siblings rather than a fixed eight. If the discard
rate is high, that *is* the paper's most useful result for a benchmark team: it prices the construction of
decision-flipping variants.

**Q2. Your entire concrete example is a model writing a literal zero into a dictionary. A linter or a static check
for hard-coded constants in an output field would catch that for nothing. Why do I need generated worlds?**

Fair, and it is now an instrument in the primary experiment rather than an unexamined assumption — a static-analysis
baseline runs over the same 150 defects alongside visible-instance grading, the expert rubric and the family. My
expectation is that it catches the hard-coded-constant class and almost nothing else: of the ten family-only defects
in the pilot, a static check plausibly reaches one or two, while the rest are wrong window, wrong denominator, wrong
governing document, wrong stratification and unconditional acceptance of an incumbent verdict — all perfectly
idiomatic code. But that is a prediction, and the experiment now tests it.

**Q3. 10 out of 42 is 24 % with a confidence interval you have not quoted.**

10/42 = 23.8 %, Wilson 95 % CI **[13.5 %, 38.5 %]**, and clustered in three self-authored worlds so the true interval
is wider than that. The proposal now carries the interval. The point estimate is not the claim; the claim is that the
family-only class is non-empty and composed of substantive analytical choices.

**Q4. We removed incomplete-information tasks because refusal grading was unreliable — models refuse for the wrong
reasons and the judge cannot tell. Why is your deferral leg any better?**

It is better only in that identification is a constructed property rather than an inferred one: the
identification-removed sibling is built by deleting the specific evidence that identified the estimand, and the
expectation is validated by two experts who must independently agree the quantity is unrecoverable. Deferral is also
scored asymmetrically — declining on an identified sibling is penalised as heavily as a wrong decision — so constant
refusal scores zero. Still, the revision now reports the deferral leg's own reliability separately, so that if its
inter-rater agreement is poor the leg can be dropped and the invariance/flip result stands on its own.

**Q5. Our leaderboard users want to know whether a model does the job. You are proposing a metric on which a model
can fail for being insufficiently *sensitive*. That is not what a buyer asks.**

Agreed, and conditional correctness is proposed as a second axis reported *alongside* single-instance pass rate,
never as a replacement — exactly as Pass^k sits alongside Pass@1 today. The buyer's question changes when the
analysis is redeployed: "does it do the job" becomes "does it keep doing the job when the month's data differs",
and that is the question this axis answers.

**Q6. Our worlds are expert-built partly so they read as real. What happens when your agent notices the data is
generated and games it?**

Two checks, both now explicit. The leak check already asks a frontier model to predict each sibling's mechanism
value from the visible corpus; above-chance prediction invalidates the family. Added: experts rate whether each
sibling reads as a real organisation, and trajectories are scanned for the agent remarking that the data looks
synthetic. If agents routinely detect the generator, that is a finding about generative world authoring generally —
including for anyone else who tries this — and it is worth reporting.

**Q7. Six families is not a benchmark. What am I supposed to do with six families?**

Nothing, as a benchmark, and the proposal should not have implied otherwise. The deliverable is a **method, a
generator, a specification format and the evidence about whether it detects anything** — plus a family verifier
against your harness interface. Six families is the sample size for the claim, not a product. The follow-on that
makes it a benchmark is cheap precisely because the generator exists; that is the point of shipping the generator.

**Q8. You say replay is nearly free and authoring is the real cost, then assert one family per week. Evidence?**

The pilot's three parameterised families, their verifiers, and 45 defect suites were built and frozen inside a
single implementation phase — days, not weeks — but with heavy tooling assistance and a single author, which is the
easy case. The plan's one-family-per-week rate therefore assumes **expert review, not engineering, is the
bottleneck**, and the week-6 gate accepts five families rather than six precisely because that assumption may be
wrong. If authoring runs long the accounting probe drops first, then the fresh-rollout arm narrows.

**Q9. Your H3 arm may show that fresh rollouts succeed where replay fails. Then your metric measured code
brittleness and your framing collapses.**

Then the paper says so in the abstract. The metric survives — a professional deliverable that breaks on next
month's data is a defective deliverable — but the interpretation changes from "the analysis was not conditioned on
the mechanism" to "the submitted artifact was not, whatever the agent understood", and the claim about professional
reasoning goes away. That outcome is pre-registered as an alternative result, not as a failure, and it is the single
most decision-relevant number for anyone considering replay as a cheap proxy.

**Q10. We have no APEX data-science benchmark because our demand is in law, finance, consulting and software. Why
should we fund a domain we did not pick?**

Because the method needs a re-executable deliverable to be measurable at all, and data science is where that is native —
so it is the cleanest place to establish whether the method detects anything. **Accounting close is the natural applied
target**: it has the document corpus, the written thresholds and the re-executable deliverables, and it is where your
demand is. To be precise about what is and is not claimed: the method requires parameterisation at authoring time, so no
shipped static world can be converted into a family. The probe therefore uses the workflow of a *public*
APEX-Accounting dev-set task as a reference for authoring one small new parameterised family of my own, without
modifying the benchmark or claiming compatibility with it. It stays small and secondary.

---

## The revision (one pass, applied)

| # | change | where |
|---|---|---|
| R1 | family size is a **floor of two validated flip siblings**, not a fixed eight; the sibling discard rate becomes a reported finding | `EXPERIMENT_DESIGN.md` §4, §7; `THREE_MONTH_PLAN.md` week-6 gate |
| R2 | **static-analysis baseline added as a fourth instrument** in the primary experiment | `EXPERIMENT_DESIGN.md` §4, §8, H1 |
| R3 | **Wilson CI [13.5 %, 38.5 %] quoted** wherever 24 % appears | `PROPOSAL_FULL.md`, `PILOT_VERIFICATION.md` |
| R4 | deferral-leg **reliability reported separately** so the leg is droppable without losing the result | `EXPERIMENT_DESIGN.md` §8, §9 |
| R5 | conditional correctness stated as a **second axis reported alongside** single-instance pass, never replacing it | `PROPOSAL_FULL.md`, `METHODOLOGY.md` §5 |
| R6 | **realism rating + synthetic-detection scan** added to the validity checks | `EXPERIMENT_DESIGN.md` §7, §12 |
| R7 | deliverable reframed as **method + generator + evidence**, explicitly not a benchmark | `PROPOSAL_FULL.md`, `THREE_MONTH_PLAN.md` |
| R8 | authoring-rate assumption stated with its **evidence and its weakness** | `THREE_MONTH_PLAN.md` |
| R9 | H3's null **pre-committed to the abstract** | `EXPERIMENT_DESIGN.md` H3 |
| R10 | accounting named as the natural applied target, with the probe scoped as **authoring one new parameterised family using a public task's workflow as a reference** — no conversion of an existing APEX world, no compatibility claim | `METHODOLOGY.md` §8, `THREE_MONTH_PLAN.md`, `PROPOSAL_FULL.md` |

### Second pass (editorial only, 2026-09-25)

Applied after review feedback, without reopening the design: absolute absence claims across all files restated as
findings of the audit rather than proofs of absence ("I did not find…"); the accounting probe reframed so it no longer
contradicts the generative-authoring requirement (it authors a new family using a public task's workflow as a
reference, rather than converting an APEX world); the pilot's 23.8 % labelled explicitly as calibration and not a
prevalence estimate; scale stated as five to six families; and the full and short proposals rewritten for a single-read
APEX audience with the statistical apparatus moved to `EXPERIMENT_DESIGN.md`.

No further revision. The remaining weaknesses — six families is a small sample, the flip-sibling construction cost is
unknown until it is attempted, and the method does not reach prose deliverables — are real, stated, and not fixable
by more editing.
