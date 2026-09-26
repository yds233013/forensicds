# HANDOFF — Mercor Research Fellowship (APEX): FINAL PROPOSAL
**Date:** 2026-09-25 · **Repository:** `forensicds` · **Branch:** `main`

Supersedes `HANDOFF_2026-09-25_MERCOR_PROPOSAL.md`, whose §19 gave metadata instead of the proposal. The complete
submission prose is pasted in §9, §10 and §11 below; nothing in this handoff points elsewhere for it.

---

## 1. FINAL STATUS

Editorial pass complete. One research-phase artefact was corrected (see below); the design was not reopened.

What changed in this pass:
1. **Absolute absence claims softened throughout.** "Mercor does not do anything equivalent, and this is a clean
   negative" and every "nobody / no prior work" formulation are now stated as findings of my audit — "in the APEX
   materials and adjacent work I reviewed I did not find…" — with the limit named explicitly: keyword searches and a
   documentation audit are evidence of absence in those materials, not proof that nothing equivalent exists anywhere.
2. **The accounting-probe contradiction is fixed.** The method requires parameterisation at authoring time, so no
   shipped static world can be converted into a family. The probe now authors **one small new parameterised family of
   my own**, using the structure and professional workflow of a *public* APEX-Accounting dev-set task only as a
   reference, with no modification of and no compatibility claim on that benchmark. It is small and secondary, and it
   is the first thing dropped if the schedule slips.
3. **A factual error in the flagship example was caught and corrected.** The earlier prose said the sibling world
   "pushes the rate over the contractual limit while still recommending no action" — internally contradictory, and
   wrong about direction. The frozen record (`jobs/p22-prospective-*/…/verifier/criteria_notes.txt`) reads
   `attribution_pp[material] 3.92 vs 0.817` and
   `decision: hidden_c: supplier_decision 'raise_supplier_nonconformance' vs 'no_supplier_action'`. So the analysis
   charges the unmodelled tool wear to the supplier and raises a **false** contractual nonconformance where the correct
   answer is unchanged. That also means hidden_c exercises the **invariance** leg, not the flip leg; the flip sibling in
   that family is hidden_b (frozen `material = 5.717`, correct decision `raise_supplier_nonconformance`). Corrected in
   the proposal, the short version, `PILOT_VERIFICATION.md` and `METHODOLOGY.md` §2.
4. **The 23.8 % is now labelled PILOT CALIBRATION everywhere**, with an explicit statement that it is not a prevalence
   estimate.
5. **Scale restated as five to six families**, consistently, with six as a ceiling rather than a promise.
6. **Both proposals rewritten for a single read** by an APEX researcher: statistical machinery, the full control list
   and the bibliography now live only in the supporting files.

**Length, stated precisely rather than rounded:** full proposal **1073 words** (target 900–1,050, so 23 over);
short version **437 words** (target 350–425, 12 over); one-sentence version **32 words** (limit 35). §12 names
the exact sentences to cut if the overage matters, and why I did not cut them myself.

Nothing submitted. No model run. No implementation started.

## 2. CORE RESEARCH QUESTION

Does re-executing a professional AI analyst's executable deliverable against controlled sibling worlds — generated from
the same professional world, with one decision-relevant mechanism changed — detect decision-relevant defects that
(a) single-instance grading and (b) the strongest rubric an expert can write for the visible world both miss, and by
how much?

The analysis is expected to remain invariant where the decision should not move, to change where the mechanism should
change the correct decision, and to defer where the available evidence no longer identifies the answer. The unit of
evaluation is the world family. Production data science and analytics is the validation domain; the broader
contribution is evaluation methodology.

## 3. EXACT CONTRIBUTION

**Borrowed, and credited in the proposal itself:**
- invariance and directional-sensitivity relations — metamorphic testing (Chen, Cheung & Yiu 1998 onward), CheckList;
- hidden, pre-registered, decision-relevant variants of expert-annotated professional cases, and the finding that
  variant scoring reorders a frontier leaderboard — Turk, arXiv:2605.30590;
- scored abstention on non-identifiable estimands inside a data-science agent benchmark, with a hidden sampled SCM —
  CausalDS, arXiv:2607.08093;
- aggregating invariance + sensitivity + calibration into one score — Weng et al., arXiv:2605.06161 (on LLM judges);
- making the pattern across controlled variants the graded unit — AgentAbstain, arXiv:2607.10059;
- scoring a submitted mechanism by replay on held-out intervention worlds — ReplaySCM, arXiv:2605.08197;
- deferral credit in a professional domain — CliniCARE-Bench, arXiv:2608.07796.

**Therefore the contribution is NOT** hidden variants, invariance, sensitivity, deferral, variant generators, or
world-family scoring by itself. Turk plus CausalDS remove most of the naive novelty of hidden/counterfactual variant
evaluation, and the proposal says so in its fourth paragraph.

**The proposed increment is the conjunction of five things**, which I did not find together in the APEX materials or the
adjacent work I reviewed:
1. a professional **executable** deliverable as the graded object;
2. **re-execution of that same deliverable**, rather than re-prompting the agent;
3. controlled **sibling worlds in which a decision-relevant mechanism can flip the correct professional decision**;
4. a **fixed professional rule and artifact corpus** held constant across the family;
5. a **direct comparison against the strongest visible-world expert rubric**, pre-registered as able to end the project.

This is an increment, not a new paradigm, and it is claimed as such. Item 2 is what makes items 1–4 affordable: the
marginal cost of the Nth sibling is compute rather than inference.

## 4. PILOT EVIDENCE

**Nine prospective trials, one frontier model, three frozen tasks.** Recomputed from the frozen verifiers'
`criteria_notes.txt`; nothing re-run.

| task | visible-instance grading | world-family grading |
|---|---|---|
| P22 | **3/3** | **0/3** |
| P20 | **0/3** | 0/3 |
| P31 | 1/3 | 0/3 |
| **all nine** | **4/9** | **0/9** |

**P20 was never 3/3 on the visible world** — all three trials failed `quantitative_results` on the *visible* extract
(trial 1 reported the programme effect as −10.59 pp against a truth of +10.85; trials 2 and 3 reported feed-defect
shares of 51.15 % and 63.80 % where the visible truth is 0.00 %). P22 is the clean case, and its mechanism is in §1
above: the frozen tooling truth is 0.167 pp on the visible extract and 3.083 pp on hidden_c; all three trials wrote
`"tooling": 0.0` as a literal; replayed on hidden_c the analysis reports material 3.92 against a true 0.817 and raises a
nonconformance where `no_supplier_action` remains correct. The token `wear` appears zero times in all three
trajectories.

**Model-free calibration — 42 defective single-defect mutations of expert reference analyses:**

| | count | share |
|---|---|---|
| caught numerically on the visible world | 30 | 71.4 % |
| **invisible on the visible world, caught by a sibling** | **10** | **23.8 %** (Wilson CI 13.5–38.5 %) |
| numerically invisible on all four worlds, caught by procedure-inspecting criteria | 2 | 4.8 % |
| reference procedures passing all four worlds | 3/3 | — |

**23.8 % is pilot calibration and nothing more.** Three synthetic worlds, one domain, and defects written by the same
person who authored the worlds — so it is evidence that the instrument *may* add information, and explicitly **not** an
estimate of how often this occurs in professional AI deployment. The 150 independently authored defects are what would
turn a calibration into an estimate. The ten sibling-only defects are substantive analytical choices — basis, window,
denominator, governing document, decision rule — not rounding artefacts.

**Cost property:** nine rollouts cost $1.4667 in total model spend, each graded against four worlds; a complete
reference trial, generating and grading four worlds, took 32 seconds of wall clock.

## 5. EXPERIMENT

**Comparison arms**, over a bank of **150 defects written by practitioners who did not author the worlds**:
1. visible-instance grading;
2. **the strongest rubric two independent experts can write for the visible world alone** — the key scientific
   comparison, written by experts who never see the siblings and are not told the method exists;
3. world-family conditional correctness;
4. a static-analysis baseline (literals in output fields, unused inputs, constant returns), because "a linter would
   have caught your example" is the cheapest way to deflate the project and it should be tested rather than argued.

**Primary metric.** Incremental detection Δ = family detection rate − best-visible-rubric detection rate, with a 95 % CI
from a cluster bootstrap over families.

**Δ decision rule.** **If Δ < 10 percentage points, I report that expert rubrics appear sufficient and that the marginal
value of building mechanism families is small.** This is a pre-registered *decision* threshold, not a powered
significance threshold — with 150 defects clustered in five or six families and an assumed intra-family correlation of
0.2, the effective n is ≈ 26, enough to detect Δ ≈ 25 pp and not Δ ≈ 10 pp. The report states this rather than implying
statistical power it does not have.

**Fresh-rollout arm (H3).** For a stratified subset, the agent is re-run from scratch on each sibling world and its
fresh-rollout profile compared with its artifact-replay profile. This decomposes family failure into *artifact
brittleness* (replay fails, fresh rollout succeeds) and *analysis failure* (both fail), and tells a benchmark team
whether cheap replay is a valid proxy for expensive re-rollout. **Its null is pre-committed to the abstract.**

**Major controls.** Reference procedures must pass every sibling; a degraded oracle with exactly one professional step
removed must pass the visible world and fail the family; **seed-only siblings, with every mechanism at its visible
value, must change no verdict**; a leak check requires that a frontier model cannot predict sibling mechanism values
from the visible corpus above chance; constant-strategy analyses (always act, always defer, always accept) must fail
every family; and deferral is scored asymmetrically, so declining where the estimand *is* identified counts as a failure
as severe as a wrong decision.

**Validity instruments.** Every flip sibling is shown to two experts who did not author the world and must, blind, name
the decision we pre-registered *and* differ from the visible sibling's decision; invalid siblings are discarded and the
**discard rate is itself a reported finding**. Every family-only failure is coded by two independent experts as
professional reasoning or bookkeeping, with κ reported. The deferral leg's reliability is reported separately and every
headline result is recomputed with that leg dropped, so the most contestable part of the design can be amputated without
taking the paper with it.

**Methodological-failure conditions.** If reference procedures fail siblings, or seed-only siblings change verdicts, or
expert solvers fail the families at a high rate, the instrument is invalid and the families are mis-specified. That is
reported as such; no result is claimed from a broken instrument.

## 6. WHY MERCOR

Not "Mercor has experts". The study is **invalid without expert-role separation**, and that separation is the thing the
pilot could not buy.

The pilot's defects were written by the person who authored the worlds, the rubrics by the person who wrote the
verifier, and the adjudication by the person who chose the mechanisms. Every pilot result is therefore confounded by a
single alternative explanation: that I built worlds capable of revealing exactly the defects I already had in mind. No
amount of compute, model access or engineering removes that confound. Only independent practitioners do, in six disjoint
roles:

| role | why independence is a validity requirement |
|---|---|
| mechanism authors | if the mechanisms are not ones practitioners actually encounter, the families measure my imagination |
| sibling adjudicators (2 per sibling, blind) | the correct decision in each sibling is the ground truth of the whole method; if I supply it, I am grading against my own belief |
| control-arm rubric writers (uninformed about the method) | the null condition only has force if the rubric is the strongest a real expert would write, not a straw man I wrote to lose |
| defect injectors | a defect I thought to write is a defect I designed the worlds to see — this is the pilot's single largest weakness |
| expert solvers | establishes that the families are passable by a competent human, and gives the human reference point |
| failure coders | the professional-reasoning-versus-bookkeeping split is the entire content of H2; my own coding would be unfalsifiable |

No role may be held by whoever authored the family it touches. Budget ≈ 30 expert-days plus 20 % for re-adjudication.
That is the dominant cost of the project and the specific reason it needs a fellowship with an expert-labour budget
rather than a laptop.

## 7. THREE-MONTH SCOPE

13 weeks at 30–40 h/week. Weeks 1–2 specification and one reference family; weeks 3–6 author the remainder with rolling
blind adjudication; week 6 freeze and pre-register (five families is the acceptance floor, six the ceiling); **weeks 7–8
the model-free primary comparison, which carries the Δ kill gate**; weeks 9–10 the model study and the fresh-rollout
arm; week 11 ablations, controls and failure coding; weeks 11–12 the small accounting probe in parallel if the schedule
allows; week 13 write-up and release.

Feasible because the infrastructure exists and has been exercised: a parameterised generator, a verifier that
re-executes submitted pipelines against regenerated siblings with per-criterion rewards, a defect-injection harness,
freeze and digest-pinning tooling, and one completed prospective evaluation under a hashed pre-registered plan with 9/9
valid trials and $1.47 of spend. The load-bearing assumption is one family per week, which assumes **expert review, not
engineering, is the bottleneck**; the pilot's three families were built in days, but by one author with tooling
assistance and no external adjudication, which is the easy case. Degradation order if authoring runs long: the
accounting probe drops first, then the fresh-rollout arm narrows to two families, then the model count to four.

**Output:** an evaluation methodology; five to six validated professional world families with their adjudication
records; an independently authored defect bank; the expert-rubric comparison; a multi-model experiment; the generator
and family verifier (written against Archipelago's verifier interface); a technical report; and, if schedule permits,
one small new parameterised accounting family. **Five to six families are a research sample, not the next APEX
benchmark**, and the proposal says so.

## 8. REMAINING LIMITATIONS

1. **Five or six families is a small sample.** The Δ confidence interval will be wide, and more *families* — not more
   defects per family — is the correct way to spend a follow-on. The generator is what makes family seven cheap.
2. **The cost of constructing valid decision-flipping siblings is unknown until attempted.** A high adjudication
   discard rate is a live risk; it becomes a reported finding rather than a hidden failure.
3. **Conditional correctness is a property of the submitted artifact, not of the agent's understanding.** The
   fresh-rollout arm measures the gap instead of assuming it away, but if that arm's null holds, the claim narrows to
   artifact brittleness and the reasoning interpretation is withdrawn.
4. **The method requires generatively authored worlds.** It cannot be retrofitted to any existing static professional
   estate, including APEX's. What transfers is the authoring pattern, not the artifact.
5. **It requires a re-executable deliverable** — data science, analytics, accounting close, financial modelling — and
   does not reach legal drafting, consulting narrative or any prose deliverable.
6. **It does not replace rubric criteria.** Two of 42 pilot defects were numerically invisible on all four worlds and
   were caught only by procedure-inspecting criteria; the instruments are complementary.
7. **Turk's abstention gap has a known expiry.** Its Appendix M commits the camera-ready to adding a refusal-credit
   branch, so "prior work does not score deferral" is a v1 property. The increment in §3 deliberately does not depend
   on it.
8. **The pilot repository is private.** The claims in §4 stand on their own but cannot be externally audited unless
   ForensicDS is opened, which is a separate decision (see §12).

## 9. FINAL FULL PROPOSAL

*1073 words. Complete text, as it would be submitted.*

---

### Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism Variants

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

---

## 10. FINAL SHORT PROPOSAL

*437 words. Complete text.*

---

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

---

## 11. FINAL ONE-SENTENCE VERSION

*32 words.*

> Grade a professional AI analysis by re-executing its executable deliverable against hidden sibling worlds where one
mechanism differs, so a correct analysis must stay invariant, flip, or defer as that mechanism requires.

## 12. EXACT NEXT ACTION FOR CHATGPT

**Read §9 and decide four things. Nothing else is blocking.**

1. **Length.** The full proposal is 1073 words against a 1,050 ceiling and the short version 437 against 425. I did not
   cut the last 23 words because every remaining candidate removes something a reviewer specifically wants. If a
   hard limit applies, cut in this order: (a) the clause "— a second reliability axis alongside single-instance pass
   rate, not a replacement." (13 words, closing sentence); (b) "and regenerating them at grading time leaves nothing
   fixed to memorise" (11 words, paragraph 3 — this is the contamination-resistance signal, a named fellowship focus
   area, so cut it last); (c) "in my pilot, nine rollouts were each graded against four worlds for $1.4667 in total"
   (16 words — this is the cost-adjusted-scoring signal, also a named focus area). **Do not cut** the P22 example, the
   expert-rubric comparison, the Δ decision rule, the calibration caveat, or the Why-Mercor paragraph.
2. **Which programme.** The Fellowship (rolling admission, 3–6 months, $40k/$80k, individual, no stated deadline) versus
   the **$5M AI Research Fund Grants** posted 2026-09-22, which asks for a one-to-two-page EOI with three required
   sections and names "underspecified tasks" and "robust measures of capability, reliability" among wanted topics — but
   routes funding through an institution, is US/UK-only, expects open-licence publication, gives Mercor exclusive rights
   to a private held-out test set, and carries a 12-month non-compete on similar benchmarks. Topically the grant fits
   better; for an unaffiliated applicant the fellowship does. **This is a contractual decision, not a research one, and
   I should not make it.**
3. **Whether to name or open the pilot repository.** The proposal says "a pilot I ran" and names nothing. Standing
   policy is that ForensicDS stays unpublished, and the commit email is unsettled. A reviewer may reasonably ask for the
   artifact. Decide before submission; do not let it be decided by accident.
4. **Whether a figure is worth adding.** One panel — visible world versus sibling, same submitted pipeline, two
   different outputs against one unchanged correct decision — would do more than any paragraph. Not built, because the
   application format is unknown.

**Two smaller items.** The one-sentence version (32 words) uses "flip" as shorthand; if that reads as jargon,
"change" is the substitute. And the `A`-marked rows in `SOURCES.md` — chiefly the APEX quotations — were reported from
primary sources by a research agent and not re-fetched by me; the APEX quotations in the proposal's second paragraph
carry the gap claim, so spot-check those two before submission.

---

## Final confirmations

- **No model was run.** No Harbor job, no rollout, no API call to any target model in this pass.
- **No ForensicDS task was changed.** No modification under `candidates/`.
- **No verifier, tolerance or hidden extract was changed.** The frozen task trees were read only.
- **No prospective result was changed.** `research/phase3/exposure/` and the pre-registered analysis plan
  (sha256 `c590cb56…`) are untouched. The correction in §1 item 3 changed *my description* of a frozen result to match
  the frozen record, not the record.
- **No new benchmark task was built. No website was built. Nothing was submitted.**
- **No force push, no history rewrite.** One normal commit.
- Untracked and deliberately not committed: `submission_5task_fallback.zip`.

**Stopped here. Awaiting ChatGPT's final review.**
