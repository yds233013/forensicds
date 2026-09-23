# Phase 2 — the prospective hypothesis and its rivals

## H1 (primary, prospective)

> **Discriminating-test omission.** When a production incident admits ≥3 defensible interpretations and
> the workspace contains a cheap test whose outcome differs across them, a frontier data-science agent
> will commit to one interpretation early, validate it with checks computed *inside* that interpretation,
> and not run the discriminating test — and this, rather than an inability to execute the analysis, will
> be the proximate cause of most failures.

**Pre-registered predictions**, each measurable from a frozen trial without further model exposure:

| # | prediction | measurement | what would disconfirm it |
|---|---|---|---|
| **P1** | in ≥70 % of failed trials, no L3 test from the task's inventory was attempted | the pre-registered per-task discriminating-test inventory, checked against the trajectory | L3 attempts in most failures |
| **P2** | trials that run any L3 test pass at a materially higher rate than those that do not | pass rate conditional on L3 attempt | no difference, or L3-attempting trials fail as often |
| **P3** | the first consequential error is at a *commitment* step (object, assumption, population, feasible set) in ≥60 % of failures, not at an execution step | first-error classification against the task's declared commitment list | failures dominated by arithmetic/implementation |
| **P4** | ≥2 of every 5 failures pass ≥3 of the agent's own coherence checks | count of L1 checks passed in failed trials | failures are incoherent, not coherent |
| **P5** | the business decision is nevertheless correct in 20–50 % of failures where the margin permits it | graded decision vs graded quantities | decisions fail whenever quantities fail |
| **P6** | agents almost never *revise* a committed interpretation after seeing contradictory evidence they themselves produced | count of revisions following a self-produced contradiction | frequent revision |

H1 is **not** "the model is bad at statistics". It is a claim about the *epistemic loop*: generation and
execution are competent, selection of discriminating evidence is not. The six predictions are designed so
that a competing explanation can beat it on the same data.

## Rival hypotheses (any of which would disconfirm or reframe H1)

**A1 — Capability, not disposition.** Agents fail because they cannot execute the correct analysis even
when told which one it is; falsification would not help. *Discriminator:* an oracle-hint condition on a
frozen task — reveal the correct object in the instruction and re-measure. If pass rates stay low, A1
beats H1. (Phase-1 has a partial precedent: the Task02 invariant-disclosed ablation did not lift the
score, but that ablation is confounded by a defect and cannot carry the weight.)

**A2 — Budget economics.** Agents stop because continuing costs tokens and time, not because they are
epistemically satisfied. *Discriminator:* a large-budget condition, and measurement of budget used at
stop. Phase-1 evidence is against A2 but not decisive: failing trials used 200–900 s of 5,400 s.

**A3 — Objective framing.** The instruction asks for a deliverable, so agents optimise the deliverable.
Asked for a *defence*, they would test. *Discriminator:* a paired condition in which the contract requires
a falsification artefact as a graded output. This is the cheapest and most informative single experiment
available to the project, and it is a design recommendation regardless of outcome.

**A4 — Route availability.** The discriminating test is not in fact cheap or findable; practitioners
would miss it too. *Discriminator:* an expert human baseline on 2–3 tasks, and a documented "expert
solve path" recorded before any model run.

**A5 — Grading artefact.** Falsification is invisible to the verifier, so we cannot see the behaviour
paying off; agents that do test are not rewarded and the correlation in P2 is unmeasurable.
*Discriminator:* grade the diagnostic explicitly (A3's design), making the behaviour visible.

**A6 — Domain knowledge, not epistemic behaviour.** Failures are textbook-knowledge gaps (what a
competing risk is, what a switchback carryover is) rather than a failure to seek disconfirmation.
*Discriminator:* tasks whose object is *elementary* once identified but whose identification requires a
discriminating test; if agents still fail, A6 is weakened. Several candidates (P22, P24) are elementary
in method and hard only in identification, precisely to separate these.

**A7 — Single-model artefact.** The phenomenon is specific to one small model. *Discriminator:* run the
frozen prospective set on ≥2 model families before drawing behavioural conclusions.

**A8 — Instruction-induced anchoring.** Our incident framings name a suspect ("the vendor says…", "Ops
disagree…"), which may *cause* early commitment. *Discriminator:* a neutral-framing arm on one task.

Recording these as rivals, with discriminators, is the point: phase 1's finding came from a discovery set
and cannot distinguish H1 from A1–A8. The prospective set is designed so that it can.
