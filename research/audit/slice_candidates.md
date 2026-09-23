# Audit 2026-09-23 — candidate slice framings, tested against the built tasks

Tested against what was actually built (15 measured tasks), not against what the model happened to fail.

## A. "Production ML Incident Investigation"
- **Fits naturally:** Task02 (training/serving skew), G24 (off-policy evaluation of a ranker), Task03
  (evaluation under a score-driven router), G08 (forecast vintages).
- **Fits awkwardly:** Task01, Task06, G05, G10, G34, G41, G42, G44 — none involves an ML model.
- **Verdict: too narrow for what exists.** Only 4 of 15 tasks are about ML systems; it would throw away
  the strongest task in the suite on difficulty grounds (G05) and the whole optimisation family.

## B. "Enterprise Data Science Incident Investigation"
- **Fits naturally:** all 15.
- **Problem: it fits everything, including the three tasks this audit judges to be documentation
  lookups.** A slice that admits Task05 (one file rewritten from a plan that specifies the fix) is not
  selecting a capability. Too broad; describes a setting, not a skill.

## C. "Forensic Data Science"
- Evocative, and the project's own name. But "forensic" is a posture, not a task property: it does not
  say what makes one task admissible and another not, and it does not tell an author what to build.
  Fails the test "does it describe task DESIGN rather than observed failures".

## D. "Scientific Debugging of Production Analytics and Decision Systems"
- **Fits naturally:** Task01, Task02, Task06, G05, G10, G24, G34, G41, G42, G44 — every task has an
  incumbent pipeline that produces a specific wrong number, and the deliverable is a repaired pipeline.
  This is the one framing that matches the *contract shape* every task actually has.
- **Fits awkwardly:** nothing, except that it admits tasks whose debugging is trivial (Task05).
- **Describes design, not failures:** yes — it specifies an incumbent artefact, a decision that rides on
  its output, and a repair deliverable.

## E. "Scientific Object Reconstruction in Production Data Science"
- **Fits naturally:** Task02, G05, G10, G24, G34 (the shipped five), plus G42/G44.
- **Fits awkwardly:** G41 — its difficulty is *executing* a constrained optimum, not identifying the
  object; and Task01/Task06, whose difficulty is entity/temporal reconciliation rather than an estimand.
- **Risk:** this framing is closest to the observed failure mode (F9), which is exactly the trap the
  audit brief warns against — defining the benchmark by what the model got wrong. It also excludes the
  second real difficulty axis this project demonstrated (G41: right object, wrong optimum).

## F. Proposed: **"Decision-Grade Analytics Repair"** — the incumbent-number framing
> An organisation already computes a number, a named decision rides on it, and the number is wrong for
> a scientific reason rather than a crash. The agent must repair the pipeline that produces it and
> defend the repaired quantity.

- Covers both demonstrated difficulty axes: **object identification** (Task02, G05, G10, G24, G34) and
  **object execution** (G41), without being defined by either failure label.
- Gives an author an admission test that is checkable before any model is run:
  1. is there an incumbent artefact that produces a specific wrong number?
  2. does a named decision with a stated rule ride on that number?
  3. is the correct object *underdetermined by the workspace documents* — must it be derived from how
     the data came to exist, or from an optimisation the documents do not solve?
  4. is the correct answer deterministic given the extract, and are the plausible wrong answers
     separated from it by more than the reporting precision?
- Test (3) is the one the current suite fails on Task03/Task05/Task06/G42, and it is exactly the test
  that the evidence of this project supports adding.
