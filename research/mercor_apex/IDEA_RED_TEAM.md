# Trying to kill the idea

Ground rule for this document: each objection is written in the strongest form I can construct, from the position
of a reviewer who wants to reject. Then a verdict — **fatal**, **survivable but forces a change**, or
**answerable** — and if it forces a change, the change is recorded and carried into `METHODOLOGY.md` and
`EXPERIMENT_DESIGN.md`. Six of the thirteen objections below changed the proposal. Two of them changed it a lot.

---

## A. "This is just hidden tests."

**Strongest form.** SWE-bench hides the test patch. MLE-bench hides a private split. Terminal-Bench hides the
verifier and holds out 53 of 89 tasks. APEX-1 keeps 400 cases closed, APEX-Accounting keeps 160. You have
reinvented a held-out set and dressed it in causal language. Every benchmark in the field already grades against
something the agent cannot see; calling your held-out thing "a world" changes nothing.

**Verdict: answerable, and the answer is precise.** A hidden test hides an **oracle** — the answer to the question
that was asked. Every benchmark listed above hides a *label for the observed instance*. A sibling world hides a
**mechanism**: the observed instance's label is fully available and the agent gets it right, and what is hidden is
the value of a latent quantity under a different setting of the world. The distinction is operational, not
semantic: a hidden oracle cannot tell you whether a correct answer was correct for the right reason, because there
is exactly one world in which to be correct. ARC-AGI-2 is the nearest counterexample — each task has a latent rule
— but the rule is inferable from the given pairs within the task, the output is one grid, and there is no
cross-variant credit.

**The clean demonstration is the pilot's cleanest case.** Three trials recovered the instrument offset to 7.81 µm
against a design value of 8.20 µm and the corrected nonconforming rate to 3.81 % against a frozen 3.83 %, and
reached the correct decision. A hidden oracle scored them 3/3, correctly. A sibling world in which the tool-wear
contribution is 3.083 pp rather than 0.167 pp scored the same submitted procedure 0/3, because all three had
written `"tooling": 0.0` as a literal. No hidden oracle can distinguish those cases. That is the whole content of
the distinction and it needs no further defence.

## B. "This is just robustness evaluation."

**Strongest form.** Distribution shift, stress testing and perturbation robustness are a solved research genre with
a decade of infrastructure: WILDS, DomainBed, Group DRO, Spawrious, D'Amour et al.'s stress tests, and for agents
specifically *A Jagged Frontier* (arXiv:2608.18389), which perturbs SWE-bench inputs semantics-preservingly and
reports up to a 6.7 pp resolve-rate drop. You are running a robustness eval on agents and claiming a new category.

**Verdict: survivable, and it forces the framing.** Robustness evaluation asks *does performance degrade under
perturbation*, and treats all change as defect. That is exactly half of what we measure and the less interesting
half. The other half is that on a properly constructed sibling the output **must change**, and change to a
specific different decision — a model whose output is invariant there is wrong, and a robustness metric scores it
as maximally robust. *A Jagged Frontier* is the perfect illustration: invariance direction only, no sensitivity
controls, so a model that ignores the input entirely would score perfectly. D'Amour et al. is the cleanest
differentiator in the other direction: **they vary the predictor and hold the data-generating process fixed; we
hold the analysis fixed and vary the data-generating process.**

**Change made:** the write-up leads with the decision-flip sibling, not with the invariance sibling, and the metric
is explicitly not a degradation curve.

## C. "This is just metamorphic testing."

**Strongest form.** Metamorphic relations were defined by Chen, Cheung and Yiu in 1998. There is an IEEE TSE
survey (2016), an ACM CSUR review (2018), a 2026 survey of 93 LLM studies explicitly covering agentic closed-loop
testing, and an ICSME 2025 paper implementing 36 metamorphic relations over ~560,000 LLM tests. "Change one input
property, assert a relation on the output" is a twenty-eight-year-old idea with a mature literature. You are
applying a known technique to a new target and calling it novel methodology.

**Verdict: survivable only if we concede the ancestry outright, which we now do.** The honest statement is that
this *is* metamorphic testing, with three specific properties that the metamorphic literature does not have:
(i) the metamorphic relation is over a **professional decision** with expert-adjudicated ground truth in each
sibling, not over a program output property; (ii) the transformation is applied to a **latent mechanism in a
generated world**, not to the input artifact, so the agent cannot detect it from what it reads; (iii) the relation
is **three-valued** — must not change, must change to a stated different decision, must decline — and the
declining branch has no metamorphic-testing analogue, because software under test does not get credit for refusing
to compute.

**Change made:** metamorphic testing is cited as the framing ancestor in the first third of the proposal, not
buried. Claiming otherwise is the fastest way to lose a reviewer who works in software engineering.

## D. "This is just running the same task with multiple variants."

**Strongest form.** GSM-Symbolic generates variants from 100 symbolic templates. DyVal generates them
dynamically. MATH() makes functional variants. RE-IMAGINE (ICML 2025) mutates a symbolic representation along
Pearl's ladder. METR's task standard has had a `variants` dictionary for years, across ~200 task families. Variant
generation is standard practice.

**Verdict: answerable, but only because of what is done with the variants.** In every work listed, each variant is
scored independently against its own ground truth and the results are averaged — per-variant accuracy, or a
difficulty ladder in METR's case. Averaging destroys exactly the information we want: a model that passes the
invariance sibling and fails the flip sibling and a model that does the reverse have the same mean. The unit of
credit here is the **joint profile over the family**, and a family is passed only if every sibling's expectation is
met. *AgentAbstain* (arXiv:2607.10059) is the closest existing instance of joint scoring — its paired accuracy
requires correctness on both sides of a pair — and it is binary act/abstain over instruction perturbations, with
no invariance leg.

## E. "You are testing whether an answer generalises, not whether an agent reasons."

**Strongest form, and this is the best objection in the list.** Your verifier re-executes a Python file the agent
wrote. Whether that file generalises to a sibling world is a property of the *file*, not of the agent. An agent
could reason perfectly, understand the wear mechanism completely, and still write a script that hard-codes a
constant because that was the efficient thing to do for the deliverable it was asked for. Conversely an agent could
write a fully general script by reflex, with no understanding at all, and pass. You have built a static-analysis
test for code generality and attached a story about professional reasoning to it. The pilot even shows this:
`"tooling": 0.0` is a *coding* choice.

**Verdict: not fatal, but it forced the largest change in the proposal, because the objection is substantially
right as originally framed.**

Two things are true and they must be separated. (1) Re-execution measures a property of the artifact. (2) The
artifact is the professional deliverable — in production data science, a recalibration analysis *is* the pipeline
plus the readout, and an analysis whose conclusion is hard-coded is a defective deliverable regardless of what its
author understood. So (1) is not a bug when the deliverable is the object of professional interest. But (1) is
also not the claim "the agent failed to reason", and the pilot evidence that the token `wear` appears **zero
times** in all three trajectories is what licenses the stronger reading in that specific case — trajectory
evidence, not replay evidence.

**Changes made, both substantive:**
- **A second arm is added to the primary experiment.** For a stratified subset of families, the *agent* is re-run
  from scratch on each sibling world (N rollouts, N× inference) and its fresh-rollout profile is compared with its
  artifact-replay profile. The difference between the two decomposes family failure into *artifact brittleness*
  (replay fails, fresh rollout succeeds) and *reasoning failure* (both fail). This converts the objection into a
  measured quantity with its own hypothesis (H3 in `EXPERIMENT_DESIGN.md`) and it is the most informative single
  number the project can produce. It is also the number that tells Mercor whether cheap replay is a valid proxy
  for expensive re-rollout — which is directly a cost-adjusted-scoring result.
- **The claim language is demoted throughout.** The project measures *conditional correctness of a submitted
  analysis*. It does not claim to measure understanding. Trajectory evidence is used only as supporting failure
  analysis, never as the metric.

## F. "Professional work does not have causal ground truth, so you cannot construct meaningful variants."

**Strongest form.** In a real enterprise there is no known structural causal model. Nobody knows the true tool-wear
contribution to a defect rate. The moment you generate the world yourself so that you *do* know it, you have left
professional work behind and are evaluating on a simulator — which is exactly the criticism APEX's world-first,
expert-authored, 166-files-per-world construction was designed to avoid. Your worlds are synthetic; APEX's are
built by 42 accountants with a median of 11 years' experience.

**Verdict: survivable, and it hard-bounds the scope. This is the objection that most constrains what may be
claimed.**

The concession is unavoidable: **the method requires generatively authored worlds and cannot be applied
retroactively to expert-authored estates.** There is no way to build a sibling world for an APEX-Agents world
whose latent mechanism nobody wrote down. Any proposal implying otherwise is wrong.

What makes the residual defensible is that the professional *procedure* and the *decision rule* are not synthetic
— they come from documents an expert wrote (a supply agreement's 5.5 % limit, a model-governance standard's
retraining trigger, a contract's amending schedule), and the generator only supplies the numbers underneath. APEX
already accepts this trade: APEX-Accounting states most world files were "synthetically populated, always under
expert specification and review," and ships a trap register of seeded contradictions. A variant axis is a short
step from a trap register — the trap register already enumerates the mechanisms; it just fixes each at one value.

**Changes made:**
- **Scope limit stated in the proposal, not in an appendix:** applies where the deliverable is re-executable and
  the world is generatively authored. Natural in data science, analytics, accounting close, actuarial and financial
  modelling. Not applicable to legal drafting, consulting narrative, or any prose deliverable. And explicitly: **no
  existing static world can be converted into a family.** The accounting probe therefore authors a new small
  parameterised family, using a public accounting task's workflow only as a reference — it does not transform that task.
- **A construct-validity check becomes a deliverable, not an assumption.** For every sibling, independent experts
  who did not author the world are shown the sibling and asked what the correct decision is, blind to our label.
  If experts do not agree that the decision differs, the sibling is not a valid flip sibling and is discarded. This
  is human-vs-model grading agreement — a named fellowship focus area — used as the validity instrument rather
  than as a metric.

## G. "Domain experts could just write better rubrics."

**Strongest form.** APEX-Accounting has 2,186 criteria over 160 tasks, written by Big Four accountants, with
97.1 % agreement against expert ground truth. If an analysis hard-codes a constant that should have been estimated,
an expert writes the criterion "the tool-wear contribution is estimated from tool-hours, not assumed zero" and the
judge catches it — on the single visible world, for a fraction of your cost, with no generator, no sibling worlds
and no new methodology. Your elaborate machinery is a very expensive way to detect something a good rubric line
detects directly.

**Verdict: this is the objection that could actually kill the project, and it is therefore promoted to the primary
experiment's control arm rather than argued against.**

I can make the counter-argument — that a rubric line must be written in advance for each possible omission, that
the space of decision-relevant auxiliary assumptions in a real analysis is large, that judging "was this estimated
or assumed?" from a final deliverable requires reading code the APEX judges are explicitly not shown, and that
rubric criteria are graded by an LLM with 3 % error while re-execution is deterministic — but an argument is not
evidence, and a reviewer is right to be unmoved.

**Change made: the expert-rubric arm becomes a falsification condition.** Independent experts, who did not author
the worlds and never see the sibling worlds, write the best rubric they can for the visible world. That rubric is
then applied to the agent outputs the family caught and the visible instance did not. **If expert rubrics on the
visible world catch most of the family-only failures, the method's marginal value is small and the project reports
that.** This is written into `EXPERIMENT_DESIGN.md` as the primary null condition, with a pre-registered threshold.
It is the single most important experiment in the proposal and it is designed to be able to end the project.

## H. "APEX already grades trajectories, so it already catches this."

**Strongest form.** Mercor's methodology page states that APEX-Agents grades "expert-authored rubrics over final
deliverables and agent trajectories." If the judge reads the trajectory, it sees the hard-coded constant, sees that
the agent never queried tool-hours, and marks it down. Your failure mode is already visible.

**Verdict: answerable on the evidence, but the reviewer's underlying point survives.**

The premise is false as stated and the sources conflict. APEX-Agents §4.2 says the judge receives the prompt, the
output and a log of induced changes "**but not the agent trajectory**", and relies on that to mitigate judge
self-preference — Gemini 3 Flash is both judge and leaderboard entrant. APEX-Accounting §3.4 says the same.
Archipelago's `trajectory` verifier is marked *COMING SOON*. APEX-SWE's rubric judge does read execution logs, and
its rubric scores are excluded from the leaderboard. So no APEX leaderboard number is trajectory-informed today,
and the methodology page is most likely stale.

But the honest version of the objection is "they could implement it next quarter", and they could. The response is
that the two measure different things and compose: trajectory grading is an LLM judging a transcript, which
inherits judge error, cannot be automated across variants, and scales linearly in judge cost; conditional
correctness is a deterministic re-execution against generated ground truth. A trajectory judge asks *did it look
like the agent did the right thing*; re-execution asks *does the thing it produced give the right answer where the
mechanism differs*. The second is the property that matters on redeployment.

## I. "The pilot is synthetic and single-model, so it shows nothing."

**Strongest form.** Nine trials. One model, `gemini-3-flash-preview`. Three tasks, all authored by you, in worlds
you generated, verified by a verifier you wrote, with defects you chose. The headline "4/9 visible → 0/9 family"
is an artefact of a construction you controlled end to end. The effect could be entirely your authorship.

**Verdict: largely correct, and the proposal must not lean on the nine trials.**

The nine trials are a **existence proof of the dissociation, not an estimate of its rate**: they show that a
frontier agent can produce an analysis that is correct on the observed world, reaches the correct decision, and
fails across the family for a locatable reason. Every stated limitation stands: one model, one snapshot, three
tasks, one domain, self-authored, 9 trials, no power for any rate.

**The load-bearing pilot evidence is instead model-free, and it was computed for this objection.** Across the 45
frozen mutation suites — the expert reference procedure with exactly one defect injected — **42 defective mutants:
30 (71 %) are numerically caught on the visible world, 10 (24 %) are numerically invisible on the visible world and
caught by a sibling, and 2 (5 %) are numerically invisible on all four worlds.** All three reference procedures pass
4/4, which is the control showing siblings are not simply harder. The ten are substantive analytical choices —
basis, window, denominator, governing document, decision rule — not rounding artefacts. And the two invisible
everywhere *are* caught by the frozen verifier's procedure-inspecting criteria, which is direct evidence that
sibling worlds and rubric criteria are complementary rather than competing. Full table and caveats in
`PILOT_VERIFICATION.md`.

**Changes made:** the full study commits to at least four model families; defects and siblings for the study are
authored by experts who did not author the worlds; and the proposal presents 24 % as a single-domain calibration
figure with a self-authorship bias stated, not as an expected effect size.

## J. "This is prohibitively expensive."

**Strongest form.** You want N worlds per task. APEX-Agents worlds take teams of professionals 5–10 days each and
average 166 files. Multiply by N and the benchmark is unaffordable, which is plausibly why it has not been built.

**Verdict: answerable on the runtime cost, which is measured, and conceded on the authoring cost, which is the
real one.**

Runtime is genuinely close to free, and this is the design's best property. In the pilot, nine trials cost
**$1.4667** in total model spend, each graded on **four** worlds, because the verifier re-executes the agent's own
submitted pipeline against each regenerated extract rather than re-querying the model. The complete P22 reference
trial, generating and grading four worlds, took **32 seconds** of wall clock. **The marginal cost of the Nth
sibling is compute, not inference.** That is a structural consequence of grading a re-executable artifact, and it
is what separates this from Turk's design, where N variants cost N inferences.

The conceded cost is authoring: a world must be *generatively parameterised*, which is more work per world than
authoring a fixed one, and expert adjudication of each sibling's correct decision is paid expert time. This is
precisely the cost the fellowship's expert-labour budget exists to absorb, and it buys a family rather than an
instance. The honest budget is in `THREE_MONTH_PLAN.md` and it is the reason the domain scope is one.

## K. "Turk 2026 and CausalDS 2026 already did this."

**Strongest form, and the most dangerous objection here because it is nearly true.** Turk (arXiv:2605.30590) builds
hidden pre-registered decision-relevant variants of expert-annotated professional cases, scores directional
correctness, and shows the scoring reorders a frontier leaderboard. CausalDS (arXiv:2607.08093) hides a sampled
SCM in a data-science world, scores abstention on non-identifiable estimands as a first-class outcome, and already
runs matched-variant ablations whose members share the same numbers, target and private truth — stating that a
competent agent "would score identically on all four members." Between them you have the professional domain, the
hidden variants, the directional scoring, the deferral leg and the invariance criterion. You are proposing their
union.

**Verdict: fatal to the proposal as I first framed it. Survivable only in a narrowed form, which is what is now
proposed.**

The union claim is correct and the original framing — "invariance, sensitivity and deferral over hidden variants of
a professional world" — has to be abandoned as the contribution, because a third paper (arXiv:2605.06161) already
aggregates exactly those three legs into one score, on judges. What survives is smaller and sharper:

- CausalDS's matched variants **deliberately preserve** the conceptual SCM, the target estimand and the
  identifiability label, and "never flip an identifiability label". The contrast where the *correct decision differs
  between siblings* is the one thing A.13 is designed not to build. Turk perturbs case **inputs**, not mechanisms,
  and discards its no-op mutations rather than scoring them as controls.
- **A caveat that must be stated rather than hidden:** Turk's Appendix M commits the camera-ready version to adding
  a refusal-credit branch. So "Turk does not score deferral" is a v1 property with a known expiry, and the
  contribution must not depend on it. In the narrowed framing it does not — the deferral leg is not the claim; the
  decision-flip sibling and the re-executed deliverable are.
- Neither holds a **persistent professional rule corpus** fixed across the family. CausalDS samples a fresh SCM and
  a fresh story per scene; Turk perturbs individual cases. Holding the document estate fixed is what isolates
  *the analysis's dependence on a latent quantity* from *the agent's ability to read documents* — and it is the one
  thing APEX is already world-class at supplying.
- Neither **re-executes a deliverable**. Both re-prompt, so both pay N× inference and neither can scale the family.

**Change made: the contribution is restated and narrowed.** It is no longer "a three-legged robustness score". It
is *conditional correctness measured by re-executing a professional deliverable against mechanism-flipping siblings
of a fixed artifact corpus*, with the three-valued expectation as the scoring rule and explicit credit to Turk,
CausalDS, Weng et al. and ReplaySCM for the components. §7 of `METHODOLOGY.md` states this in one sentence. A
reviewer who has read all four papers should find nothing overclaimed.

## L. "Your headline gap is non-negative by construction, so it measures nothing."

**Strongest form.** Passing the family requires passing the visible world plus three more. Family-pass is a subset
of visible-pass by definition. Reporting "4/9 → 0/9" or "24 % of defects are family-only" is reporting that adding
conditions cannot increase the pass rate. Any harder test would produce a "gap". You have discovered that four
hurdles are harder than one.

**Verdict: correct as arithmetic, and the proposal must foreclose it with controls rather than rhetoric.**

The gap's existence is uninformative; its **magnitude** and its **composition** are the claims. Three controls,
all pre-registered:

1. **Reference-procedure control.** The expert reference analysis must pass every sibling. If siblings were merely
   harder, the reference would fail too. In the pilot all three reference procedures pass 4/4.
2. **Degraded-oracle control.** Take the reference procedure and remove exactly one professional step. It must pass
   the visible world and fail the family. This is a positive control for the instrument's sensitivity, and it is
   what the 45 mutation suites are: 10 of 42 single-defect mutants behave exactly this way.
3. **Composition adjudication.** Every family-only failure is classified, by an expert who did not author the
   world, as a *professional-reasoning* failure or a *bookkeeping/implementation* failure. The claim is only about
   the first class. If the majority are bookkeeping, the finding is much weaker and is reported as such.

And the negative direction is the real test: **a sibling on which the decision should flip and the analysis does
not change** is a failure that no amount of added hurdles produces, because it is not a hurdle — it is a
requirement that the output *differ*. That arm cannot be explained by "harder test".

## M. "Crediting deferral rewards hedging, and you cannot falsify it."

**Strongest form.** Once "I decline to conclude" earns credit, the dominant strategy is to decline. APEX
understands this — it penalises scattergunning precisely because one answer is right. A benchmark that rewards
abstention will be gamed by models that abstain, and you will have measured caution, not competence.

**Verdict: answerable, but only with an explicit penalty, which was missing from the first framing.**

**Change made: deferral is scored three-valued and asymmetric.** Declining on a sibling where the estimand *is*
identified is scored as a failure exactly as severe as a wrong decision, and the family profile requires the
declining to occur **only** on the sibling constructed to remove identification. A model that always defers scores
zero, as does one that never defers. This is checkable and it was checked: the pilot's mutation suite contains
`M08_always_defer` and `M07_always_overturn` for P31, and both fail. `M09_always_accept` is one of the ten caught
only by a sibling. A constant-strategy agent cannot pass a family, which is the property that makes the metric
non-gameable in the obvious direction.

---

## Summary: what changed because of this document

| objection | verdict | change carried into the design |
|---|---|---|
| A hidden tests | answerable | none; sharpen oracle-vs-mechanism language |
| B robustness eval | survivable | lead with the decision-flip sibling, not degradation |
| C metamorphic testing | survivable | concede ancestry explicitly and early |
| D multiple variants | answerable | make the joint profile, not the mean, the unit of credit |
| **E artifact not agent** | **survivable** | **add the fresh-rollout arm (H3); demote all claims about reasoning** |
| **F no causal ground truth** | **survivable** | **state the generative-authoring scope limit; make expert sibling adjudication a deliverable** |
| **G better rubrics** | **near-fatal** | **expert-rubric arm becomes the pre-registered null condition** |
| H APEX grades trajectories | answerable | premise is false today; argue composition, not superiority |
| I pilot weak | largely correct | lean on the model-free 24 %, not the 9 trials; ≥4 model families |
| J too expensive | answerable + conceded | runtime measured; authoring cost conceded and budgeted |
| **K Turk + CausalDS** | **fatal to the first framing** | **contribution narrowed and restated; components credited** |
| L gap non-negative | correct | three pre-registered controls; the flip arm is the real test |
| M deferral gaming | answerable | asymmetric three-valued scoring with a penalty for over-deferral |

Two objections (G, K) were strong enough that a different project would have been the right response. The reason
the project survives is narrow and should be stated narrowly: **I did not find work that re-executes a professional
deliverable against mechanism-flipping siblings of a fixed artifact corpus**, and that specific combination is what makes
the measurement both valid and cheap. That is a claim about what my audit found, not a proof of absence.
