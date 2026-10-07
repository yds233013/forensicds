# 13 — Executive summary

## What we built

Ten Harbor tasks, each a realistic piece of inherited data-science work. An agent gets a business memo, an
operational data warehouse, the governing document that defines the decision (a contract, a regulator's
reserve requirement, a model-risk standard, a break-even memo), and **an inherited analysis that runs, is
documented, and is a correct computation of the wrong quantity.** Ten mechanisms, no two shared: point-in-time
leakage, staggered-adoption identification, informative censoring, off-policy evaluation, population
definition under tariff migration, policy feedback, measurement-system bias, contractual metric definition,
experimental interference, and data vintages. Domains span SaaS, retail, utilities, healthcare,
manufacturing, energy trading, consumer internet and delivery marketplaces.

Four of the ten emit **per-criterion** scores rather than pass/fail, and that distinction turns out to carry
the entire scientific contribution.

Every task is graded against **hidden sibling worlds** — the same company regenerated with a *different
underlying cause*. An analysis that encodes the mechanism it happened to find in the visible world fails
there. One task (`g50`) goes further and re-executes the agent's own command against five unseen worlds.

## What happened

| | Gemini 3 Flash | Claude Opus 5.5 |
|---|---|---|
| valid trials | 31 (10 tasks) | 27 (9 tasks) |
| passes | **1** | **13** |
| trial pass rate | **3.2%** | **48.1%** |
| task-level pass@3 | **10%** (1/10) | **56%** (5/9) |
| cost | not recorded | **$23.07** |

On the nine jointly graded tasks: Gemini 1/28 trials and 1/9 tasks; Claude 13/27 trials and 5/9 tasks.
45 further attempts were **invalid** (credit exhaustion, verifier refusals, provider errors) and are counted
nowhere.

**The headroom target (<30% pass@3) holds for the flash-tier model and fails for the frontier model.** That
is the first honest finding: this suite discriminates sharply by model tier, and five of its nine gradable
tasks are already at or near retirement for a frontier model.

## What failed, and what survived scrutiny

**The naive story failed.** We predicted agents would fail for want of investigation. They did not. They
read the governing document, reproduced the incumbent number, engaged with identification, and revised.
Stating the invariant outright in an ablation still produced **0/3**. Four prospective hypotheses were
disconfirmed (chapter 08).

**The refined story partly survived.** On the instrumented tasks, framing is near ceiling and the
decision-relevant quantity is the floor — for *both* models:

| criterion | Gemini | Claude |
|---|---|---|
| evidence reconstruction | 93% | **100%** |
| scientific object (right question) | 73% | **100%** |
| independent validation | 92% | **100%** |
| **the decision-relevant number** | **17%** | **33%** |

Claude never once mis-framed the problem and still missed the number two times in three. The *ordering* is
identical across models; only the severity moves.

**But "one failure mode" did not survive.** The 24 instrumented trials fall into **eleven distinct
criterion-failure shapes**, including two that are mirror images:

- `p20` — quantity wrong, **decision right**, in 7 trials. A decision-only rubric would have scored
  Claude 3/3 there.
- `p31` — quantity **right**, identification and decision wrong, in 4 trials.

A single cause cannot produce both. The defensible claim is a **statistical regularity** (the quantity is
the modal failure) and **not** a shared mechanism.

**The sharpest single observation.** On `p22`, all three Gemini trials produced *byte-identical, correct*
visible-world output — correctly exonerating the supplier and blaming the measuring instrument — and all
three failed on the one sibling world where tooling is the true cause, reporting `tooling: 0.0`. They wrote
code that encoded the explanation they found rather than a method that recovers whichever holds. **Claude
passed that task once in three**, which proves the generalisation is achievable and the Gemini result is a
capability observation, not a design artifact.

## What this dossier corrected about the project's own record

1. **Both arms' `p20` numbers are partly contaminated by our own defect.** A field-level audit found 12
   sign-flip failures across Claude's three `p20` trials and 7 across Gemini's — magnitudes correct, sign
   convention inverted, because the contract never states it. Claude was run on the unfixed v1. Every
   trial still has independent genuine failures, so the 0/3 stands, but any claim that the model "could not
   compute the programme effect" is **not supportable**. Not recorded anywhere before now.
2. **`p31` already contains a justified-deferral world** — `tests/world.py:300` returns
   `not_determinable_from_available_evidence` and it is in the agent-visible contract. The final report and
   handoff both state that no task tests deferral. **They are wrong.** And both models failed to produce
   the deferral — a result that was sitting unrecognised in the data.
3. **`g50`'s Claude refusal is not the `ld.so.cache` defect recurring.** That fix is verifiably in place;
   `claude-code` trips a *different* pinned file, and which one is **UNKNOWN** because the verifier
   discards the filename.
4. **The README still documents the superseded five-task suite.**

## Why this matters for data science

The failures sit exactly where professional review is weakest. A manager reviewing `p20` would have seen a
competent decomposition, a sensible population, a passing self-check, and the **right recommendation** —
and would have approved an analysis whose attribution numbers were wrong. Seven trials did that. In `p31`
the numbers were right and the £1.8m verdict was wrong. In `g50` all three Gemini trials recommended an
expensive national rollout on a number that measures redistribution rather than benefit.

None of these is a coding error. None would be caught by "does the code run and did the metric improve?",
which is what most agent evaluation measures. **A correct final decision is not evidence of a correct
analysis, and this project measured the gap rather than assuming it.**

## What to do next

**Recommended first move costs nothing: manual trajectory adjudication of the four jointly failed tasks**
(`g10`, `g36`, `p20`, `p31`), two blind coders against a fixed stage codebook, with the four passing `g08`
trials as positive controls. It is the only way to tell whether the eleven failure shapes reflect one
mechanism or several, and no number of further trials will answer it.

Then, in order: a **controlled scaffolding intervention** (~$15) to test the largest threat to validity —
Claude used 13-15 steps on `g36` where Gemini used 40-54, and both failed, so premature stopping cannot be
excluded; **instrumenting the six binary-reward tasks** (~$29) to remove the dossier's biggest limitation;
a **`g50` version both scaffolds can be graded on**; and a **tier-matched Haiku arm** to separate
architecture from tier.

## For the Abundant Research PM deep dive

The deliverable is a benchmark whose value is **not** its difficulty. Its value is that it localises where
capable agents stop being trustworthy on real analytical work, and that it does so with instrumentation
honest enough to have caught four defects in itself — one of them during the writing of this dossier.

Three things we would flag to a reviewer before they read the numbers:

1. **The central claim rests on 4 of 10 tasks and 24 of 58 trials.** The instrumented four share an author
   period and are all attribution/decomposition tasks, which is plausibly the family where a
   "right decision, wrong quantity" split is most likely. This is a real selection-bias risk and the fix
   is cheap.
2. **The cross-model comparison is Opus against Flash** — not tier-matched. Most of Claude's advantage may
   be tier. The experiment that separates them was designed and never run.
3. **Three trials per task.** A task recorded 0/3 is consistent with a true success probability up to
   roughly 0.3. No significance test is run and none should be inferred.

What we would defend without qualification: the ten tasks are frozen and byte-identical to what was
evaluated; every reported number recomputes from raw reward files by two scripts in this directory; no
invalid attempt is counted as a model failure anywhere; and where the artifacts cannot answer a question,
this dossier says **UNKNOWN** instead of guessing.
