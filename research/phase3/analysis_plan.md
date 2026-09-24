# Pre-registered analysis plan — P22, P20, P31

**Written and committed at freeze, before any target-model contact.** Phase-2 handoff §29 rule R4. Its purpose is
that the labelling rules and the disconfirming outcomes cannot be chosen after the results are seen.

Frozen task digests this plan applies to:

| task | `lock.json` → `task.digest` |
|---|---|
| p22-gauge-recalibration | `sha256:72fedb37da7b48c8488ad8afbcdf0d46b501dcdb52a6b05698a20370425629a7` |
| p20-noshow-monitoring | `sha256:f033ea1f5a8876514566174e8a99cf36d24e09cd54e9bba7ddfb5c16ffe60d8a` |
| p31-fill-rate-dispute | `sha256:3208a6d39014bff924784636da9a0837d528833f22e0666197d445330821f3ae` |

If a trial's `task.digest` is not one of these three, the trial does not belong to this plan.

## 1. Exposure design, fixed now

Exactly **three** valid trials per task, sequential, one trial per Harbor job, all on the digest above. No
adjudication between trials. Two model families before any behavioural claim (phase-2 rival A7); the second
family's trials are reported separately and are not pooled with the first.

## 2. Validity rule, applied before any reasoning is read

A trial is **invalid** and replaced by one authorised re-run if it shows any of: an API, quota or authentication
error; an agent-setup timeout; a verifier that never executed; or the container-teardown signature documented in
`research/harness_process_sweep_defect.md` — **reward 0 with 0-byte verifier stdout and a verifier phase of
roughly 2 seconds**. The adjudication is made from the job artefacts alone. Reading a trial's reasoning before
adjudicating it is a protocol violation.

At most one replacement per task without a written reason. Invalid trials are reported with their count and
cause; they never enter an aggregate.

## 3. What is recorded per trial

From the verifier, with no interpretation: the binary `reward`; each of the seven `criterion_*` values; which
graded extracts failed and on which quantity, from `criteria_notes.txt`; and the cost and wall clock.

From the trajectory, against the per-task inventories already written in `research/phase3/audits.md` (three
discriminating routes per task, fixed before freeze):

| label | definition, fixed now |
|---|---|
| **L3 attempted** | the trial executed at least one of that task's three inventoried discriminating routes, or a route that is functionally the same test on the same evidence. Reading the evidence without computing the contrast does not count |
| **L1 only** | the trial ran checks computed entirely inside its own frame (internal reconciliation, re-running its own pipeline, a sensitivity sweep over its own parameters) and no L3 route |
| **first consequential error** | the earliest step whose correction would change a graded quantity, classified against the task's declared commitment list: P22 — conformance reference / residual allocation / which rate the agreement names; P20 — evaluation population / scoring basis / clause order; P31 — governing instrument / whether the incumbent code implements it / whether Schedule 4 leaves the consequence open |
| **revision after self-produced contradiction** | the trial produced a number inconsistent with its own committed interpretation and then changed that interpretation |
| **decision correct with quantities wrong** | `criterion_decision` = 1 while any of the other six criteria = 0 |

Labelling is done by me against these definitions, recorded per trial with the supporting trajectory excerpt, and
is not revised once written.

## 4. Pre-registered predictions and their disconfirming outcomes

These are the phase-2 H1 predictions instantiated on this set. **Each row states in advance what would count as
disconfirmation**, so a null result is reportable rather than reframed.

| # | prediction on this set | disconfirmed if |
|---|---|---|
| **P1** | in ≥70 % of failed trials, no inventoried L3 route was attempted | L3 routes are attempted in more than 30 % of failures |
| **P2** | trials attempting any L3 route pass at a higher rate than those that do not | the rates are equal or inverted |
| **P3** | the first consequential error is at a commitment step in ≥60 % of failures | failures are dominated by arithmetic or implementation errors |
| **P4** | ≥2 of every 5 failures pass ≥3 of their own coherence checks | failures are incoherent rather than coherent |
| **P5** | `criterion_decision` = 1 with another criterion = 0 in 20–50 % of failures | decisions fail whenever quantities fail, or the share is outside that band |
| **P6** | revision after a self-produced contradiction occurs in <20 % of trials that produce one | revision is frequent |
| **P7** (new, specific to P31) | on P31, wrong verdicts are asymmetric toward `incumbent_incorrect` on the extracts where the incumbent is right | wrong verdicts are symmetric, or skewed toward deference |

With nine trials per model family the confidence intervals are wide; **no prediction is claimed to be settled by
this set alone**. The set is sized to detect a gross departure, not to estimate a rate.

## 5. Reporting, fixed now

pass@1, pass@3 and **pass^3** per task from the same spend; the criterion breakdown per task and per trial; the
invalid-trial count with causes; and the labels above with their trajectory evidence. Per-criterion pass rates
are reported beside the binary rate, because a task can be 0/3 on reward while separating cleanly on five of
seven criteria, and that distinction is the instrument this phase adds.

## 6. What is forbidden after the first trial

No change to any frozen task, for any reason short of a demonstrated verifier defect — and a verifier defect
**excludes the task from aggregates rather than licensing a revision** (the G36 precedent). No change to this
plan. No re-labelling of a trial once labelled. No tolerance change. No addition or removal of a graded
quantity. If the set turns out to be too easy or too hard, that is the result.
