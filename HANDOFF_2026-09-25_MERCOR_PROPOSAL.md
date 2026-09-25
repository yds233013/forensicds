# HANDOFF — Mercor Research Fellowship (APEX) proposal
**Date:** 2026-09-25 · **Repository:** `forensicds` · **Branch:** `main` · **Status:** proposal drafted, nothing
submitted, no implementation started.

This document is self-contained. A reader who has seen none of the preceding work should be able to act on it.

---

## 1. What was asked, and what was done

The brief: develop a research proposal for the Mercor Research Fellowship (APEX) in the "novel evaluation
methodology" area, starting from the idea that a professional AI agent should be graded against multiple causally
meaningful hidden variants of a world rather than on one instance — and, before writing anything, to audit APEX, audit
the literature, and try to kill the idea.

Done, in this order: (1) verified the pilot claim I was given and **found it partly false**; (2) computed new
model-free evidence from the repository; (3) audited APEX from primary sources; (4) audited the literature; (5)
independently re-verified the load-bearing citations and **found one wrong arXiv ID and two overstated claims**;
(6) ran thirteen objections against the idea, two of which forced real changes; (7) wrote the proposal; (8) ran a
hostile review and applied exactly one revision pass.

**Nothing was submitted. No implementation was begun.**

## 2. Files created

All under `research/mercor_apex/` unless noted.

| file | what it is |
|---|---|
| `RESEARCH_GAP.md` | the APEX audit and the gap, with Mercor's own contradictions flagged |
| `RELATED_WORK.md` | prior work as a threat assessment: what each paper removes from us |
| `IDEA_RED_TEAM.md` | thirteen objections, verdicts, and the six changes they forced |
| `METHODOLOGY.md` | the method, its scope limits, the final title, the domain decision |
| `EXPERIMENT_DESIGN.md` | questions, four hypotheses, materials, metrics, statistics, controls, ablations |
| `THREE_MONTH_PLAN.md` | 13-week schedule, expert-labour budget, gates, risks |
| `PILOT_VERIFICATION.md` | the verified pilot arithmetic and the model-free mutation calibration |
| `SOURCES.md` | every source with date, claim, primary/secondary and **verification status** |
| `PROPOSAL_FULL.md` | the one-page proposal (1,147 words) |
| `PROPOSAL_SHORT.md` | one-sentence version (59 words) + short version (464 words) |
| `REVIEW.md` | the hostile review (ten questions) and the single revision pass |
| `mutation_visible_vs_family.json` | machine-readable output of the new calibration |
| `tools/bench/visible_vs_family.py` | the script that produced it |
| `HANDOFF_2026-09-25_MERCOR_PROPOSAL.md` | this file (repository root) |

## 3. Does Mercor already do anything equivalent? — stated explicitly

**No. Mercor does not do anything equivalent, and this is a clean negative rather than a judgement call.**

Across all four APEX papers (arXiv:2509.25721, 2601.14242, 2607.27189, 2601.08806) the terms `counterfactual`,
`latent`, `perturb` and `invarian` return **zero** hits each. The only `variant` matches are MathML attributes; the
only `sensitivity` matches are finance task-category labels; the only "stress test" is a *judge* self-preference
check. The released dataset has 240 tasks as 240 single instances with no variant or seed field. Archipelago's
config schema has no variant, seed or parameter-sweep primitive, and its `trajectory` and `value` verifiers are
marked *COMING SOON*.

**Critically, Mercor has moved deliberately in the opposite direction and said so.** APEX-Agents 1.1's audits existed
"to ensure a single correct and well-specified answer exists"; APEX-Accounting verifies each task "admits a single
defensible answer" and **removed twenty-four incomplete-information tasks** — the ones where a model should refuse or
ask. Any framing that treats this as an oversight will be rejected; it is the correct call for scoring, and the
proposal says so.

Two Mercor-internal contradictions that must not be repeated as fact: APEX-1's task count is 300 on `/apex/` and 400
on the leaderboard page and in the paper; and the methodology page claims APEX-Agents grades trajectories, which
APEX-Agents §4.2 explicitly denies ("…but not the agent trajectory") and which the harness cannot yet do.

## 4. The closest prior work, identified — not a list

| rank | work | what it removes from us |
|---|---|---|
| 1 | **Turk, arXiv:2605.30590** — hidden pre-registered clinical variants, Causal Sensitivity Score | the idea of hidden decision-relevant variants of professional cases, and the finding that variant scoring reorders a leaderboard |
| 2 | **CausalDS, arXiv:2607.08093** — hidden SCM, scored abstention on non-identifiable estimands, matched-variant ablations (A.12, A.13) | deferral-on-non-identifiability in data science; the matched-variant invariance idea in the abstract |
| 3 | **Weng et al., arXiv:2605.06161** — invariance + sensitivity + ambiguity in one Policy Invariance Score | the three-legged *scoring architecture* |
| 4 | **AgentAbstain, arXiv:2607.10059** — 263 paired tasks, paired accuracy | making the pattern across controlled variants the graded unit |
| 5 | **ReplaySCM, arXiv:2605.08197** — mechanism scored by replay on held-out intervention worlds | the mechanical core: replay an artifact on unseen worlds |
| 6 | **CliniCARE-Bench, arXiv:2608.07796** — two distinct indeterminate verdicts, calibrated abstention | deferral credit in professional work; "stricter composite reorders the leaderboard" |
| 7 | **OpenRCA 2.0, arXiv:2606.27154** — causal-path grading via fault injection; 76.0 % vs 61.5 % | the best existing evidence for the failure mode; our strongest supporting citation |

**The honest verdict, which is stated in `RELATED_WORK.md` §head and in the red team:** combine Turk with CausalDS and
roughly 85 % of a naive version of this proposal is already published. No single work holds the full conjunction, and
the coverage matrix in `RELATED_WORK.md` §8 shows no complete row — but this is a defensible increment, not a new
paradigm, and the write-up must not pretend otherwise.

## 5. Citation verification

Every load-bearing citation was independently re-fetched from arXiv. Results:
- **All seven Tier-1 papers exist** with the titles and dates claimed, and their load-bearing quotes were confirmed
  verbatim.
- **One wrong arXiv ID was caught and corrected**: Kaushik/Hovy/Lipton counterfactually-augmented data is
  **arXiv:1909.12434**, not 1910.12543 (which is a cold-collision physics paper).
- **Two claims were overstated and were softened**: (a) Turk never states in words that models are unaware of the
  mutations — the design implies it; (b) Turk's Appendix M **commits the camera-ready to adding a refusal-credit
  branch**, so "Turk does not score deferral" is a v1 property with a known expiry. The contribution was restated so
  it does not depend on that gap.
- **CausalDS's two matched-variant claims come from two different appendices** (A.12 and A.13); citing one for both
  would not check out.
- **Fellowship facts corrected:** the posting states **no deadline** ("rolling admission"); the widely circulated
  26 September 2026 date is aggregator-only and uncorroborated. The word "navigation" does **not** appear anywhere in
  the posting — **"negotiation" does**, in a different bullet, which is almost certainly the source of the misreading
  in the brief. The relevant bullet is verbatim: *"Novel evaluation methodology: contamination resistance, rubric
  design, human-vs-model grading agreement, cost-adjusted scoring."*

`SOURCES.md` marks each row `V` (independently verified), `A` (agent-reported from a primary source) or `U`
(unverified, unused). **No statistic appears in the proposal unless its row is `V` or the number was computed in this
repository.**

## 6. The red team: what survived

Thirteen objections in `IDEA_RED_TEAM.md`. Six forced changes; two were strong enough that a different project would
have been a reasonable response.

- **Near-fatal (G): "experts could just write better rubrics."** Response: the expert-rubric arm is now the
  pre-registered **null condition** of the primary experiment, with a threshold that can end the project.
- **Fatal to the original framing (K): "Turk + CausalDS already did this."** Response: the contribution was narrowed
  and restated; the three-legged-score framing was abandoned as the claim.
- **Largest design change (E): "you test whether an answer generalises, not whether an agent reasons."** Response: a
  fresh-rollout arm (H3) was added to measure the difference, and every claim about reasoning was demoted.
- **Hard scope limit (F): "professional work has no causal ground truth."** Response: the generative-authoring
  requirement is now stated in the proposal body, not an appendix.
- Also changed: lead with the decision-flip sibling not degradation (B); concede metamorphic-testing ancestry early
  (C); joint profile rather than mean (D); asymmetric deferral scoring with a penalty for over-deferral (M); three
  pre-registered controls against "your gap is non-negative by construction" (L).

## 7. The contribution, stated crisply

**A professional analysis is graded not by whether its answer matches on the world it was shown, but by re-executing
the deliverable it submitted against sibling worlds — generated from the same artifact corpus with one
decision-relevant latent mechanism set differently — requiring the correct decision to hold where the mechanism is
unchanged, to flip where the mechanism flips it, and to be withheld where the sibling removes identification.**

The graded quantity is **conditional correctness**; the unit of evaluation is the **world family**.

**Is this a substantive distinction from prior work? Yes, but narrowly, and only on three points.** Stated plainly so
it can be checked:
1. **The decision-flip sibling.** No prior work builds paired variants where the same surface world and the same
   professional artifacts yield an *opposite correct decision* because one latent mechanism differs. CausalDS's A.13
   explicitly preserves the mechanism and "never flips an identifiability label"; Turk perturbs case inputs.
2. **Re-execution rather than re-prompting, for a professional deliverable.** ReplaySCM has replay for Boolean-DSL
   mechanisms on synthetic items; nobody has it for a professional analysis against a professional document estate.
   This is what makes the Nth sibling cost compute rather than inference.
3. **A shared professional rule corpus held fixed across a family.** APEX has the best artifacts in the field and one
   world per task; METR has the family container and no mechanism contrast; nobody has combined them.

Everything else — invariance/sensitivity relations, deferral credit, joint scoring over variants, variant generators —
is borrowed and credited. **If a reviewer rejects all three points above, the idea is not sufficiently differentiated
and should be dropped.** I judge that it is differentiated; I do not judge that it is a large contribution.

## 8. Final title

> **Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism
> Variants**

Rejected: the working title "Beyond Pass/Fail: Counterfactual Evaluation of Professional AI Agents" — "beyond
pass/fail" is a cliché in adjacent 2026 titles and "counterfactual evaluation" collides both with off-policy
evaluation and with Turk's usage. Not named APEX-anything: the applicant has no affiliation and implying one would be
a mistake.

## 9. Method summary

Author the world as a **generator** over its decision-relevant latent mechanisms: a fixed corpus (data dictionary,
governing contract with its amending schedule, governance standard with a written threshold, incident log, incumbent
analysis) plus a parameter vector. Instantiating it gives **siblings** — identical documents, different numbers
underneath. Three sibling types with pre-registered expectations: **invariance** (conclusions unchanged),
**flip** (conclusions change to a stated different decision because a threshold is crossed), **identification-removed**
(the estimand is reported unrecoverable and the missing evidence named). The agent submits a re-executable deliverable;
the verifier re-executes it unmodified against each regenerated sibling. A family is passed only if every sibling's
expectation is met; the profile `(invariance, flip, deferral)` is reported separately and never averaged.

## 10. Scope limits

1. **Requires a re-executable deliverable.** Fits data science, analytics, accounting close, actuarial and financial
   modelling. Does **not** fit legal drafting or consulting prose, and no extension there is proposed.
2. **Requires a generatively authored world.** Cannot be retrofitted to an expert-authored estate whose mechanisms
   were never parameterised — including existing APEX-Agents worlds. It *can* build on APEX-Accounting's trap
   register, which already enumerates mechanisms and fixes each at one value.
3. **Measures a property of the artifact, not of the agent's understanding.** H3 quantifies the difference instead of
   assuming it away.
4. **Does not replace rubric criteria.** 2 of 42 pilot defects were numerically invisible on all four worlds and were
   caught only by procedure-inspecting criteria. The instruments are complementary.

## 11. Domain decision

**Option A: one domain — production data science and analytics — plus a committed two-week transfer probe into
accounting reconciliation** using APEX-Accounting's public dev-set world.

Data science is the **validation** domain because the deliverable there is natively re-executable, which is the
method's precondition; and because no APEX benchmark covers data science, so the domain gap and the method gap
compose. **Accounting is the intended application** — Mercor already has the corpus, the world architecture and the
trap register — which is why the probe is a deliverable rather than slack. Options B (two full domains) and C
(several) both fail the three-month budget, whose binding constraint is expert adjudication, not compute.

## 12. Pilot numbers — verified, with provenance

Computed from the repository. **The claim I was given was partly false and the correction is recorded.**

**Claim as given:** "P22 and P20 would each appear 3/3 successful under visible-only grading but score 0/3 across the
hidden variants."
**Verified:** true for P22, **false for P20.**

| task | visible-instance | world-family | did the family change the verdict? |
|---|---|---|---|
| P22 | **3/3** | **0/3** | yes — the clean case |
| P20 | **0/3** | 0/3 | **no.** All three trials already failed on the *visible* extract |
| P31 | 1/3 | 0/3 | yes, for one trial of three |
| **all nine** | **4/9** | **0/9** | — |

P20's three trials failed `quantitative_results` on the visible extract: trial 1 reported the programme effect as
−10.59 pp against a truth of +10.85 (sign inversion); trials 2 and 3 reported feed-defect shares of 51.15 % and
63.80 % where the visible truth is 0.00 %.

**Mechanism of the P22 case.** Frozen truth for the tooling component is **0.167 pp on the visible extract** and
**3.083 pp on hidden_c**. All three trials wrote `"tooling": 0.0` as a literal; two retained the incumbent pipeline's
docstring asserting tooling was on schedule. Against a frozen ±0.8 pp tolerance a hard-coded zero is correct on the
visible world and wrong by 3.08 pp on hidden_c, pushing the material-attributable rate past the supply agreement's
5.5 % limit and flipping the decision from `no_supplier_action` to `raise_supplier_nonconformance`. The token `wear`
appears **zero times** in all three trajectories; trial 1 closed with *"I'm confirming there are no other significant
factors."*

**New model-free calibration** (`tools/bench/visible_vs_family.py`, run this session). Of 45 frozen single-defect
mutations, 42 defective:

| | count | share |
|---|---|---|
| numerically caught on the visible world | 30 | 71.4 % (CI 56.4–82.8) |
| **invisible on the visible world, caught by a sibling** | **10** | **23.8 % (CI 13.5–38.5)** |
| invisible on all four worlds | 2 | 4.8 % (CI 1.3–15.8) |
| reference procedures passing 4/4 | 3/3 | — |

The ten are substantive analytical choices (basis, window, denominator, governing document, decision rule), not
rounding artefacts. The two invisible everywhere are caught by `estimator_implementation` /
`evidence_reconstruction`.

**Cost property.** Nine trials = **$1.4667** total model spend; each graded on **four** worlds; the complete P22
reference trial took **32 seconds** of wall clock. The marginal cost of the Nth sibling is compute, not inference.

## 13. Pilot limitations — what must not be claimed

Explicitly, and all of these are stated in the proposal itself:
- **Not** a universal failure mode. Nine trials, one model.
- **Not** representative of frontier models. `gemini-3-flash-preview` at one snapshot is not all frontier models.
- **Nine trials are not conclusive.** No power for any rate. They are an existence proof of the dissociation, not an
  effect size.
- **Synthetic worlds are not real enterprise workflows.** The method requires generative authoring; that is a scope
  limit, not a claim about enterprise data.
- **The auxiliary-assumption pattern is not proven.** It is one located mechanism in one task.
- **Long-horizon performance was not established.** Nothing here measures it.
- **The 24 % figure is single-domain, three worlds, defects written by the worlds' own author** — the principal
  internal-validity weakness, which is why independent defect authoring is in the study's critical path.
- **Family-pass ⊆ visible-pass by construction**, so a non-negative gap is guaranteed. Magnitude and composition are
  the claims; three controls exist for exactly this objection.

## 14. Experiment: hypotheses, controls, metrics, analysis

**Questions.** Primary: does re-execution against mechanism-flipping siblings detect decision-relevant defects that
single-instance grading *and* the best visible-world expert rubric both miss, and by how much? Secondary: does it
reorder a model ranking; how much of family failure is artifact brittleness versus analysis failure; how many
siblings are needed; what is the cost per resolved reliability question.

**Hypotheses.**
- **H1** family grading beats the best visible-world expert rubric by Δ ≥ 10 pp. *Null: Δ < 10 pp → expert rubrics
  suffice and the method's marginal value is small.*
- **H2** among visible-passing rollouts a non-trivial fraction fail the family, and a majority of those failures are
  classified by independent experts as professional-reasoning rather than bookkeeping. *Null: mostly bookkeeping.*
- **H3** replay failures are reproduced by fresh rollouts on the sibling. *Null: replay measures artifact brittleness
  — pre-committed to the abstract.*
- **H4** conditional-correctness ranking differs from single-instance ranking (Kendall τ < 1). *Null: rankings agree.*

**Materials.** Six world families, target 8 siblings each with a **floor of two validated flip siblings**; a bank of
**150 defects authored by experts who did not author the worlds**; **two independent expert rubrics per family**
written for the visible world alone; and a **static-analysis baseline** as a fourth instrument.

**Model sample.** Six frontier agents spanning ≥4 developers, 5 rollouts per (model, family) = 180 rollouts, plus 162
fresh-rollout runs for H3. Order $1,000–2,000 of model spend; the 1,440 sibling gradings cost compute only.

**Metrics.** `VP` visible pass; `CC` conditional correctness; `d = P(VP ∧ ¬CC)`; the three-part profile; `Δ`
incremental detection; Kendall τ; `P(fresh fails ∣ replay fails)`; deferral-leg κ with every result recomputed
without that leg; and costs ($ per family-graded rollout, replay:re-rollout ratio, $ per detected defect). Nothing
invented for sophistication.

**Analysis.** Exact McNemar on paired binary outcomes plus mixed-effects logistic models with family random
intercepts; Δ with a **cluster bootstrap over families**; Clopper–Pearson for H3; Kendall τ with a bootstrap CI;
Holm–Bonferroni over four primary hypotheses. **Power stated honestly:** 150 defects clustered in 6 families with
ρ ≈ 0.2 gives an effective n ≈ 26 — enough for Δ ≈ 25 pp, not Δ ≈ 10 pp. The Δ ≥ 10 pp threshold is therefore a
**decision rule, not a powered test**, and the report will say so.

**Controls.** (1) reference procedure must pass all siblings; (2) degraded oracle — one step removed — must pass
visible and fail family; (3) **seed-only siblings must change no verdict** (the control the pilot lacks); (4) leak
check — a frontier model must not predict sibling mechanism values from the visible corpus above chance; (5) constant
analyses must fail every family; (6) the static-analysis baseline must be beaten.

**Ablations.** Sibling-count curve; sibling-type ablation; tolerance sensitivity at 0.5×/1×/2×; judge-with-trajectory.

**Failure analysis.** Two independent expert coders, seven categories, κ reported; trajectories read only *after*
coding.

## 15. Expert-network contributions — designed in, not bolted on

This is the part that fixes the pilot's single-author weakness, and the roles are **disjoint by construction**: an
expert who authored a family may not adjudicate, rubric or defect it.

| role | what they do | why it is load-bearing |
|---|---|---|
| family authors | specify the corpus, the governing documents and the mechanism axes | the professional procedure and decision rule must come from practice, not from me |
| sibling adjudicators (2 per sibling, blind) | state the correct decision on each sibling | **the validity instrument for the whole method**; disagreement discards the sibling |
| rubric authors (2 per family) | write the strongest visible-world rubric they can, uninformed about the method | the pre-registered null condition — the arm that can end the project |
| defect authors | write 150 single-step defects independently of the worlds | removes the pilot's self-authorship bias |
| expert solvers (2 per family) | solve the visible sibling under the agent's brief | human reference point and a validity check that families are passable |
| failure coders (2) | classify every family-only failure | H2's composition claim depends entirely on them |

Budget ≈ **30 expert-days** plus 20 % for re-adjudication. This is the dominant cost of the project and the reason it
needs a fellowship rather than a laptop.

## 16. Three-month feasibility

13 weeks at 30–40 h/week. Weeks 1–2 specification + reference family; 3–6 families 2–6 with rolling adjudication;
week 6 freeze and pre-registration; **weeks 7–8 the model-free primary experiment, which carries the kill gate**;
9–10 the model study and the H3 arm; 11 ablations, controls and failure coding; 11–12 the accounting transfer probe in
parallel; 13 write-up and release.

It is feasible because the hard infrastructure **already exists and has been exercised**: a parameterised generator
producing a visible instance plus hidden siblings; a verifier that re-executes the agent's submitted pipeline against
each sibling and emits per-criterion rewards; a defect-injection harness; freeze, digest-pinning, hash-pinned offline
install and pre-registered-plan tooling; and one completed prospective evaluation under that protocol with 9/9 valid
trials, zero protocol violations, and $1.47 of spend.

**The load-bearing assumption is one family per week, and it is stated with its weakness:** the pilot's three families
were built in days, but by one author with tooling assistance and no external adjudication. The plan assumes expert
review is the bottleneck. The week-6 gate accepts five families rather than six because that assumption may be wrong.
Degradation order if authoring runs long: fresh-rollout arm narrows to two families → model count to four → and only
then anything else.

## 17. Success, null, alternative and methodological-failure conditions

**The project is informative under every branch, and that is deliberate.**

| branch | condition | what gets reported |
|---|---|---|
| **success** | Δ ≥ 10 pp, family-only failures majority professional-reasoning, H3 largely confirms replay, τ < 1 | conditional correctness is a distinct, cheap reliability axis; ship generator + evidence + verifier |
| **null** | Δ < 10 pp | **expert rubrics on one world are a sufficient instrument.** A direct, useful answer to a question a benchmark team has an operational interest in, and a reason not to spend on generators |
| **alternative** | H3 null: fresh rollouts succeed where replay fails | the metric measures **artifact brittleness**, not analysis quality. Reported in the abstract. Still decision-relevant — a deliverable that breaks on next month's data is defective — but the reasoning claim is withdrawn |
| **alternative** | flip siblings fail expert adjudication at a high rate | **the cost of constructing decision-flipping variants** becomes the finding, which is the number any future attempt needs |
| **alternative** | agents routinely detect the generator | a finding about generative world authoring in general, reported not suppressed |
| **methodological failure** | reference procedures fail siblings, or seed-only siblings change verdicts, or expert solvers fail families at a high rate | the instrument is invalid and the families are mis-specified. Reported as such; no result is claimed from a broken instrument |

## 18. Deliverables

The family specification format and generator; six families with all siblings and adjudication records; the
independently authored defect bank; the control-arm expert rubrics; a **family verifier implemented against
Archipelago's verifier interface** (whose `trajectory` and `value` verifiers are currently unimplemented); one family
built from APEX-Accounting's public trap register; and the paper, including the sibling-count curve that prices how
many worlds are worth buying. **Six families is a sample size, not a benchmark, and the proposal says so.**

## 19. Submission-ready prose

| artifact | file | length | target | status |
|---|---|---|---|---|
| one-page proposal | `research/mercor_apex/PROPOSAL_FULL.md` | **1,147 words** | 800–1,100 | **47 words over** — see §22 |
| short version | `research/mercor_apex/PROPOSAL_SHORT.md` | **464 words** | 300–450 | 14 words over |
| one-sentence version | same file | 59 words | one sentence | one sentence, but long |

All three are written as submission prose, not as notes. The full version states the problem in its first paragraph
through a concrete worked case with real numbers; the method is legible by word ~330; prior work is credited before
any novelty claim; no dramatic safety rhetoric; no hype adjectives.

## 20. The economic argument

A professional analysis is not consumed once. It is a procedure that runs again next month on next month's data, and
its economic value is the number of periods over which its decision stays correct. That is the quantity a firm needs
before handing a recurring close, a pricing review or a monitoring decision to an agent, and single-instance grading
cannot report it. APEX already treats reliability rather than accuracy as the live question — no model exceeds 2.6 %
Pass^8 on APEX-Accounting. **Pass^k asks whether an agent repeats itself on one world; conditional correctness asks
whether its answer survives the world differing.** Orthogonal axes, reported together, neither replacing the other.

## 21. The hostile review

Ten questions in `REVIEW.md`, written as an APEX researcher who maintains Archipelago and defaults to rejecting.
Genuinely adversarial ones included: *eight adjudicated siblings per family when one defensible answer took us
multiple audit passes*; *a linter would catch your only concrete example*; *we deleted incomplete-information tasks
because refusal grading was unreliable, why is yours better*; *our buyers do not ask whether a model is insufficiently
sensitive*; *six families is not a benchmark*; *why fund a domain we did not pick*.

**One revision pass was applied and then stopped**, producing ten specific changes (R1–R10 in `REVIEW.md`, all
propagated into the files they touch): floor of two validated flip siblings with the discard rate as a finding; a
static-analysis baseline as a fourth instrument; Wilson CIs quoted everywhere; the deferral leg's reliability reported
separately so the leg is droppable; realism and synthetic-detection checks; the deliverable reframed as method +
generator + evidence rather than a benchmark; the authoring-rate assumption stated with its weakness; H3's null
pre-committed to the abstract; conditional correctness framed as a second axis alongside single-instance pass; and the
accounting probe promoted to a committed deliverable with accounting named as the intended application.

Remaining weaknesses, stated and not fixable by more editing: six families is a small sample; the cost of constructing
flip siblings is unknown until attempted; the method does not reach prose deliverables.

## 22. What still needs deciding or editing

**Decisions only the applicant can make:**
1. **Word limits.** `PROPOSAL_FULL.md` is 1,147 words against a 1,100 target. If a hard limit applies, cut the
   "Deliverables" paragraph (86 words) — its content is in `THREE_MONTH_PLAN.md` — and the short version's final
   scope/credits paragraph. Do **not** cut the worked example in paragraph 1 or the Δ-threshold sentence; they are
   what make the proposal concrete and falsifiable.
2. **Which programme to apply to.** The Fellowship (rolling admission, 3–6 months, $40k/$80k, individual) versus the
   **$5M AI Research Fund Grants** posted 2026-09-22, which specifies a one-to-two-page EOI with three required
   sections and names "underspecified tasks" and "robust measures of capability, reliability" among wanted topics —
   but routes funding through an institution, is US/UK-only, expects open-licence publication, grants Mercor exclusive
   rights to a private held-out test set, and carries a 12-month non-compete on similar benchmarks. **The grant is
   the better topical fit; the fellowship is the better fit for an unaffiliated applicant.** This is a
   personal/contractual decision, not a research one.
3. **The deadline.** No Mercor-controlled page states one. The circulated 26 September 2026 date is aggregator-only
   and unverified. Act as though it is imminent.
4. **Whether to name the pilot repository.** The proposal currently says "a pilot I ran" without naming ForensicDS or
   linking it. Standing repository policy is that ForensicDS remains unpublished. **Do not publish or link it to
   support this application without deciding that separately.** The claims in the proposal stand on their own; they
   simply cannot be externally audited while the repository is private, and a reviewer may reasonably ask.
5. **Whether to soften "conditional correctness".** If a reviewer finds the term overloaded, the fallback is
   "mechanism-conditional correctness". Avoid "latent world" (taken by AvalancheBench), "latent failure" (taken), and
   unqualified "counterfactual evaluation" (ambiguous with off-policy evaluation and with Turk's usage).

**Editing that would improve it but was not done:**
6. The proposal has no figure. A single panel — visible world versus flip sibling, with the same submitted pipeline
   and two different correct decisions — would do more than any paragraph. Worth adding if the format allows.
7. The `A`-marked rows in `SOURCES.md` (mainly APEX quotations and the second-tier literature) were reported from
   primary sources by a research agent but not re-fetched by me. Before submission, spot-check the APEX quotations
   in §3 of `RESEARCH_GAP.md`, since they carry the gap claim.
8. The one-sentence version is 59 words. If a genuine one-liner is needed: *"Grade a professional AI analysis by
   re-executing its deliverable against hidden sibling worlds where one latent mechanism differs, so a correct answer
   must survive, flip, or defer as the mechanism requires."*

---

## Final confirmations

- **No target model was run in this phase.** No Harbor job, no agent rollout, no API call to any target model.
- **No ForensicDS task was changed.** `git status` shows no modification under `candidates/`.
- **No verifier, tolerance or hidden extract was changed.** Nothing under the frozen task trees was touched.
- **No prospective result was changed.** `research/phase3/exposure/` and the frozen analysis plan
  (sha256 `c590cb56…`) are untouched.
- **No additional benchmark task was built.** The only new code is `tools/bench/visible_vs_family.py`, a read-only
  analysis script that re-executes existing reference procedures against existing generators.
- **No website was built. No public release was made. Nothing was submitted.**
- **No force push, no history rewrite.** One normal commit of the research and proposal files.
- Untracked and deliberately **not** committed: `submission_5task_fallback.zip` (the pre-existing fallback archive).
- Standing environment note carried forward: a research subagent previously installed `pypdf` 6.19.0 into the
  Homebrew system Python with `pip --break-system-packages`. Still present, unrelated to the benchmark, awaiting a
  decision to remove.

**Stopped here. Awaiting review.**
