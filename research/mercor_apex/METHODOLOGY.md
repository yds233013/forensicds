# Methodology

## 1. The contribution, in one sentence

**A professional analysis is graded not by whether its answer matches on the world it was shown, but by
re-executing the deliverable it submitted against sibling worlds — generated from the same artifact corpus, with one
decision-relevant latent mechanism set differently — and requiring the correct decision to hold where the mechanism
is unchanged, to flip where the mechanism flips it, and to be withheld where the sibling removes identification.**

The name for the graded quantity is **conditional correctness**. The unit of evaluation is the **world family**,
not the task instance.

## 2. Why this is a different measurement rather than a harder one

Two agents that are indistinguishable under single-instance grading:

- Agent A estimates the tool-wear contribution from tool-hours, finds it is 0.17 pp on the world it was given,
  attributes the residual to material, and recommends no supplier action.
- Agent B writes `"tooling": 0.0` as a literal, attributes the residual to material, and recommends no supplier
  action.

Both are correct. Both reach the correct decision. Both pass every rubric criterion that grades the deliverable's
conclusions. On a sibling world in which the insert-change interval was extended and a faster-wearing grade fitted, so
that the wear contribution is 3.08 pp, A still recommends correctly; B charges the unmodelled wear to material, reports
3.92 pp against a true 0.82, pushes the material-attributable rate above the supply agreement's 5.5 % limit and raises a
contractual nonconformance where the correct decision has not changed. **Conditional correctness separates A from B.
Nothing that grades one world can.**

This is the *invariance* leg: the mechanism moved, the correct decision did not, and B's output did. The same family's
decision-*flip* leg is a different sibling, where the true material contribution genuinely crosses the threshold and a
correct analysis must change its recommendation.

This is not a claim that B reasoned badly. It is a claim that B's *deliverable* is conditionally incorrect, which is
the property that matters when the analysis is re-run next month. See objection E in `IDEA_RED_TEAM.md`; the
distinction is enforced in the metric and in the language.

## 3. Construction

### 3.1 A world family

A **world** is a persistent fictional organisation with one set of systems of record, one document estate, one cast
of teams and one dated calendar of events. This is the same construct APEX-Agents uses, and it is the part of
APEX's design that this method depends on rather than competes with.

A **family** is one world authored as a *generator*: a fixed artifact corpus — data dictionary, contract or policy,
governance standard, incident log, the incumbent analysis and its documentation — plus a parameter vector over the
decision-relevant latent mechanisms. Instantiating the parameter vector yields a **sibling**: the same corpus, the
same documents verbatim, the same cast, different numbers underneath.

The visible sibling is the one the agent sees. The others are never shown to the agent, never referenced in any
document, and are regenerated at grading time by the shipped generator.

### 3.2 The three sibling types

| type | construction | required behaviour of a correct analysis | required behaviour of the **decision** |
|---|---|---|---|
| **invariance sibling** | a latent quantity that the professional procedure should be insensitive to is changed (nuisance scale, operator mix, unrelated seasonal amplitude) | conclusions unchanged within tolerance | unchanged |
| **flip sibling** | one decision-relevant latent mechanism is set to a different value such that the governing document's threshold is crossed | conclusions change, in the pre-registered direction, to the pre-registered value | **changes to a specified different decision** |
| **identification-removed sibling** | the evidence that identifies the estimand is withdrawn — an instrument's dual-measurement overlap removed, a holdback stratum absent, a parallel-run period deleted | the estimand is reported as not identified from the available evidence | **declines**, and names what evidence would identify it |

Every sibling requires a pre-registered expectation *before* any agent is run. The flip sibling is the design's
centre of gravity and the one I did not find in prior work (see `RELATED_WORK.md` §10).

### 3.3 The graded object

The agent submits a **re-executable deliverable**: the analysis code plus a machine-readable readout of the
scientific object, the quantitative results, the identification verdict and the decision. The verifier re-executes
*that artifact, unmodified* against each sibling's regenerated data and compares the readout with that sibling's
generated truth at frozen tolerances.

The family score is a **profile**, not a mean:

```
family_pass  =  all siblings meet their pre-registered expectation
```

and the reported decomposition is `(invariance_met, flip_met, deferral_met)` per family, so that a model which is
robust but insensitive is distinguishable from one that is sensitive but unstable. Averaging across sibling types is
not reported as a headline, because it destroys the distinction the method exists to make (objection D).

Deferral is scored asymmetrically: declining on a sibling where the estimand *is* identified counts as a failure of
the same severity as a wrong decision. A constant-deferral agent and a never-deferral agent both score zero
(objection M).

### 3.4 Why the siblings are nearly free

The verifier re-executes the agent's artifact. It does not re-query the model. In the pilot, nine rollouts cost
**$1.4667** in total model spend and each was graded on **four** worlds; the complete reference trial, generating
and grading four worlds, took **32 seconds** of wall clock. **The marginal cost of the Nth sibling is compute, not
inference.**

Three consequences, and they are the practical case for the design:
- A family of 8–12 siblings is affordable where 8–12 re-prompts are not. Turk's design pays N× inference.
- Because siblings are regenerated from a parameterised generator at grading time, **contamination resistance is
  structural**: there is no fixed instance to memorise, and the numbers an agent could have seen are not the
  numbers it is graded on. This is a named fellowship focus area obtained as a property rather than as an add-on.
- The evaluation's cost profile is reportable: cost per family, cost per resolved reliability question, and the
  replay-versus-re-rollout cost ratio — which is itself the cost-adjusted-scoring result (H3).

## 4. What this method cannot do

Stated here rather than in an appendix, because two of these are hard limits (objections E and F).

1. **It requires a re-executable deliverable.** Natural in production data science, analytics, accounting close,
   actuarial work and financial modelling. It does not apply to legal drafting, consulting narrative, or any prose
   deliverable, and no extension to those is proposed.
2. **It requires a generatively authored world.** It cannot be applied retroactively to an expert-authored estate whose
   latent mechanisms were never parameterised, and no existing static world — APEX-Agents, APEX-Accounting or otherwise
   — can be converted into a family. **What transfers is the construction pattern, not the artifact.** The
   trap-register practice described in the APEX-Accounting paper already requires an author to enumerate the seeded
   mechanisms of a world, which is the same enumeration a family needs; a family additionally requires each of those
   mechanisms to be *parameterised at authoring time*. So the pattern is a short conceptual step away, and an existing
   world is not.
3. **It measures a property of the artifact, not of the agent's understanding.** The fresh-rollout arm quantifies
   the difference rather than assuming it away, but the metric's claim is about conditional correctness of a
   submitted analysis, full stop.
4. **It does not replace rubric criteria.** In the pilot, 2 of 42 injected defects were numerically invisible on all
   four worlds and were caught only by procedure-inspecting rubric criteria. The two instruments are complementary,
   and the null condition in `EXPERIMENT_DESIGN.md` is designed to find out how complementary.

## 5. Relation to the existing APEX stack

This is an addition to APEX's construction pipeline, not a competitor to it:

- APEX-Agents' world-first authoring supplies exactly the artifact corpus the method needs. The change is to author
  the world as a generator rather than as a fixed instance.
- APEX-Accounting's trap-register practice — enumerating a world's seeded mechanisms during authoring — is the same
  enumeration a family needs; the additional requirement is that each mechanism be parameterised as the world is built.
  That is a change to the authoring process, not a transformation applicable to worlds already shipped.
- Archipelago's verifier types are `output`, with `trajectory` and `value` marked COMING SOON. A **family verifier**
  — regenerate sibling, re-execute submitted artifact, compare against generated truth, aggregate the profile — is
  a well-specified addition to an Apache-2.0 repository Mercor actively maintains.
- Pass^k measures whether an agent repeats itself on one world. Conditional correctness measures whether its answer
  survives the world being different. They are orthogonal reliability axes and should be reported together: the
  APEX-Accounting result that no model exceeds 2.6 % Pass^8 is the strongest existing evidence that Mercor already
  treats reliability, not accuracy, as the live question.
- **Conditional correctness is a second axis reported alongside single-instance pass rate, never a replacement for
  it.** A buyer's question "does it do the job" is answered by the existing metric; "does it keep doing the job when
  the month's data differs" is answered by this one. Presenting it as a successor metric would be both wrong and
  strategically pointless.

## 6. Naming discipline

Terms already claimed in adjacent 2026 work, to be avoided: "latent world" (AvalancheBench, enterprise analytics),
"latent failure" (arXiv:2606.14574), "counterfactual evaluation" unqualified (collides with off-policy evaluation in
the causal-inference sense — Bottou et al. 2013 — and with Turk's benchmark usage), "consistency" unqualified
(BECEL's taxonomy; and self-consistency decoding, which reviewers will conflate). The vocabulary used here is
*world family*, *sibling*, *conditional correctness*, *invariance / flip / identification-removed*.

## 7. Final title

> ### Conditional Correctness: Evaluating Professional AI Analysts by Re-executing Their Deliverables Against Mechanism Variants

Chosen over the working title "Beyond Pass/Fail: Counterfactual Evaluation of Professional AI Agents" because
"beyond pass/fail" is a cliché that appears in at least four adjacent 2026 titles, and because "counterfactual
evaluation" is ambiguous between this sense and off-policy evaluation. Not named APEX-anything: the proposal is from
an applicant, and borrowing the benchmark's name implies an affiliation that does not exist.

## 8. Domain decision

**Option A: one domain — production data science and analytics — plus a small, secondary two-week accounting probe in
month 3.**

Reasons, in order of weight:
1. **The method needs a re-executable deliverable**, and in production data science the deliverable natively *is*
   the pipeline plus the readout. This is not a convenience; it is the precondition from §4.1.
2. **There is no APEX data-science or analytics benchmark.** The domain gap and the method gap compose, so one
   project addresses two of the fellowship's openings rather than one.
3. **Three months at 30+ h/week buys one domain done properly.** The expensive item is not compute; it is
   generatively parameterising worlds and paying experts to adjudicate each sibling's correct decision.
4. **Accounting close is the natural applied target; data science is the validation domain.** Month-end close has the
   document corpus, the written thresholds and the re-executable deliverables the method needs, and it is where
   Mercor's demand is. Data science is chosen to *validate* the method because the deliverable there is natively
   re-executable, which is the precondition from §4.1.
5. **What the accounting probe is, stated precisely.** It **does not convert an APEX world into a family** — §4.2 rules
   that out, and claiming otherwise would be unsupported. It uses the *structure and professional workflow* represented
   in a public APEX-Accounting dev-set task as a reference for authoring **one small new parameterised accounting
   family of my own**, with no modification of the original benchmark and no claim of compatibility with it. It answers
   one question — can this method's authoring pattern be applied to an accounting workflow at all — and it stays small
   and secondary to the data-science study.

Option B (two full domains) fails on item 3; option C (several) fails on 3 and would produce a shallow result in
each.
