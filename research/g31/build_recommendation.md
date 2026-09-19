# G31 build recommendation

# **B. REDESIGN — do not build.**

The capability is worth pursuing. **This design is not salvageable by parameter changes** and must not be
implemented in its current form. The independent adversarial review returned **BLOCK**; I verified its four
decisive findings myself and they hold. A reasonable maintainer could read the same evidence and choose **C**, and
§5 states honestly what would make C correct.

## 1. Why not A (build)

Four independent disqualifiers, each measured (`simulation_results.md` §2):

1. **A label-free heuristic solves it.** Summing gross transaction value over each model's top-k recovers every
   per-segment decision — 9/9 in my test, 15/15 in the reviewer's, including the regime that flips the answer. An
   agent can skip the entire observation-process reconstruction and be right.
2. **The task has one mechanism, not three.** The delay leg shifts Δ by ≤ 0.0058 against a 0.010 decision bar; the
   selective-verification leg contributes exactly zero rows. What remains is inverse-probability weighting on a
   logged randomised bypass — which is G24's shape, and which the brief explicitly ruled out as a sole route.
3. **The designed decision-correct/analysis-wrong case is not wrong.** `W10_count_recall` passes 20/20 with lower
   RMSE than three of four accepted estimators, because the fraud-value multiplier is a within-segment constant
   that cancels in a ratio.
4. **The evaluation threshold is degenerate** — identical to the band boundary in 15/15 cells, which makes two of
   the wrong methods fail for a bookkeeping reason rather than a scientific one.

The gate passing 20/20 accepted and 0/20 on nine wrong methods is not a counter-argument. It is the finding: **the
gate certified a task that a heuristic defeats**, because the gate has no representation of a solver that never
estimates anything.

## 2. Why not C (drop) — yet

The capability question is genuinely unmeasured. Reading the cross-task matrix, no built task requires an agent to
reason about *why a label exists at all*: Task 02 asks when a feature was knowable, G10 what a censored quantity
would have been, G24 which action was taken and with what probability, G05 what would have happened without
treatment. "The incumbent model decided who would ever be measurable" has no analogue.

And the two inert mechanisms are inert because of **specific, identifiable generator choices**, not because the
phenomena are unreal:

- censoring is inert because `delay ⟂ everything`. In reality dispute lag correlates with fraud type and therefore
  with risk. Making lag depend on `z` would make the leg bite, and is *more* realistic, not less;
- selective verification is inert because investigators are perfect and released rows carry `Y* = 0`. In reality
  the review band's determinations are the labels a naive analysis actually uses, and they are score-selected.

So the honest statement is: **this DGP fails; the capability has not been shown to fail.**

## 3. What a redesign must do — and it is a new task, not an edit

| # | Defect | Required change | Knock-on |
|---|---|---|---|
| R1 | value leaks the label | fraud and legitimate transactions must be **identically distributed in value**, or value must be dropped and the estimand defined on counts | the "fraud loss in dollars" business framing weakens; the estimand becomes count-based recall or expected loss under an explicit cost model where the cost is not a function of `Y*` |
| R2 | censoring inert | dispute lag must depend on latent risk, so a short horizon differentially drops high-risk fraud | **the identification proof changes**: I3 no longer holds as written, and maturity correction becomes a modelling step rather than a filter |
| R3 | verification inert | review determinations must enter the natural analysis as labels (e.g. SLA-declined rows recorded with an outcome code that invites treating them as fraud), and investigators must be imperfect or the release rule must not be a function of `Y*` | adds a second unidentified quantity; must be checked that the estimand remains identifiable |
| R4 | degenerate threshold | evaluation budget must differ from the historical band boundary | trivial |
| R5 | prompt names the answer | the incident must not name the segment where the challenger loses | trivial |
| R6 | estimators read `spec` | the pilot hands every estimator the generator's parameters; a real solver must read the bypass rate, budget and horizon out of artefacts | pilot-only defect, but it means the current results **do not** demonstrate the methods survive artefact reconstruction |

R1, R2 and R3 each change the structural equations, and R2 changes the identification proof. That is a new
generator, a new identification argument and a new gate — not a revision.

**R1 and R2 also pull against each other**, which is the reviewer's strongest point and I accept it: making value
carry no signal removes the cheap solve but weakens the business framing, while making censoring bite requires lag
to correlate with risk, which introduces a *new* path by which observable timing leaks the label. A redesign must
show that both can hold at once. That is the first thing to test, before anything else is built.

## 4. Pre-registered kill criteria for the redesign

Written now, before any redesign work, so the decision cannot be made after seeing results:

1. **Two mechanisms must independently bite.** Correcting only mechanism *i* and handling the others perfectly must
   leave a bias exceeding the decision bar, for at least two of the three `i`. If only one bites, the task is
   G24-redundant → **DROP**.
2. **A cheap-solve panel must fail.** Label-free heuristics (gross value, score-rank agreement, volume in top-k),
   constant answers, and single-artefact readings must all be measured in the gate and must all fail. If any
   passes → **DROP**.
3. **No accepted estimator may be beaten by a mislabelled wrong method.** Every wrong method's RMSE must exceed
   every accepted method's.
4. **Distinctness from Task 03** must be argued explicitly. Task 03 is already "evaluation population / selective
   labels", is built, and scored **3/3 — TOO EASY**. That is a warning this turn did not take seriously enough:
   the nearest existing neighbour to G31 is a task we found trivial. The redesign must state what G31 requires
   that Task 03 did not, in terms of the S0–S9 matrix.

If any of 1–4 fails, drop the line of work rather than iterating. Two failed gates on one capability is enough.

## 5. What would make C correct

If the redesign cannot satisfy kill criterion 1 — if the honest DGP has one identification device and the other
mechanisms are decoration — then G31 is **G24 with different nouns** and should be dropped. On present evidence
that is a live possibility, not a remote one: the single-mechanism collapse happened here without my noticing,
and it took an adversarial reviewer to find it.

## 6. Estimated cost if the redesign proceeds

| Item | Estimate |
|---|---|
| Redesign: new generator, identification proof, gate | ~1.5 days |
| Gate with a cheap-solve panel, 4 regimes | ~2 h compute, $0 |
| Build to G05 standard (workspace, verifier, mutation suite, two reviews, Oracle/Nop, clean clone) | ~3–4 days |
| `harbor check` | ~$0.5 per invocation, several invocations |
| Gemini baseline, 3 trials | ~$0.50 |

**None of this should be spent until kill criteria 1 and 2 are demonstrated on the redesigned generator.**

## 7. Benchmark-level note

The benchmark does not need a sixth task to lower its pass@3; it stands at 1/5 = 20% on measured tasks, already
below the <30% target. It needs **capability breadth**. A sixth task that turns out to be G24-shaped would reduce
the benchmark's claimed breadth while adding cost, which is worse than having five tasks.

The most valuable output of this turn is not the task. It is §3 of `simulation_results.md`: **the Phase-0 gate
protocol cannot detect a cheap solve, and should be extended to include an explicit cheap-solve panel.** That
applies retroactively to every task already built, and should be checked against G05 and G24 before the final
report is written.
