# G31 — model evaluation under selectively observed and delayed outcomes

**Status: research, design and simulation only.** No Harbor task exists, no `candidates/g31-*` directory has been
created, no model has been run, and no API credits have been spent on this work.

## The question

> Can a frontier data agent correctly compare two predictive models when the ground-truth label is missing for
> three different reasons at once — the incumbent model's own decisions prevented the outcome from occurring,
> an investigation process produced labels for a score-selected subset, and the outcomes that do occur arrive
> months late — and when the population that *has* labels was created by the model being replaced?

Domain: payment fraud at a card processor. The incident is a challenger fraud model (v7) that a risk team wants
to ship on the strength of an evaluation run over the labelled population.

## Files

| File | What it contains |
|---|---|
| `domain_comparison.md` | seven candidate domains scored against nine criteria; why payments fraud won and why credit, T&S, healthcare, marketplace and insurance lost |
| `dgp_design.md` | the latent world, variable roles, structural equations, data-flow graph, the three missingness mechanisms, positivity, and the realism caveats |
| `estimand_and_identification.md` | the business incident, the exact estimand, the identification proof, assumptions I1–I5, the ambiguity test, and point-by-point distinction from Task 02 / G05 / G10 / G24 |
| `wrong_methods.md` | ten pre-registered wrong analyses with the assumption each violates |
| `valid_estimators.md` | four legitimate estimator families spanning weighting, stratification and modelling |
| `hidden_regimes.md` | four regimes that preserve the invariant while changing the surface statistics |
| `artifact_graph.md` | the proposed workspace, what each artefact contributes, and the single-file-giveaway check |
| `expected_failures.md` | what would count as an interesting model failure, written before any baseline |
| `cross_task_matrix.md` | the S0–S9 stage matrix across Task 02 / G08 / G10 / G24 / G05, and what G31 would uniquely probe |
| `adversarial_review.md` | independent hostile review of this design |
| `simulation_results.md` | measured calibration and validation results from the Phase-0 gate |
| `build_recommendation.md` | the A / B / C decision and its justification |
| `g31_sim.py` | the generator |
| `g31_estimators.py` | four accepted families, ten wrong analyses |
| `run_gate.py` | the gate runner |
| `results/` | raw gate output |

## The core claim, in one paragraph

A blocked authorisation never settles, so it can never produce a chargeback: the incumbent model's decisions
determine which outcomes are *knowable at all*. A logged, randomised bypass programme allows a known fraction of
would-be-blocked and would-be-reviewed authorisations through, and that programme — plus a maturity horizon
estimated from fully mature cohorts — is what makes the challenger's performance identifiable on the full
eligible population. Fixing only the delay gives a rigorous-looking analysis on the settled population, which is
wrong. Fixing only the selection gives a rigorous-looking analysis on the wrong population, which is also wrong.
The task asks for the number the business decision is actually defined on, per segment, and the correct answer
recommends the challenger in two segments and the incumbent in a third.

## Gate protocol, pre-registered before the first run

Four regimes × (10 calibration + 20 validation) worlds, **disjoint seed blocks per regime** so that regimes are
independent draws — the fix that resolved G05's round-5 failure.

Wrong analyses are judged by the three-part criterion recommended in `research/g05/G05_O1_adjudication.md` §G and
adopted here for the first time, replacing the per-regime pass-rate rule that proved unmeasurable at small n:

1. **analytic invalidity** — each must violate a stated assumption or target a different estimand;
2. **joint separation** — estimated probability of passing every regime below 10⁻³;
3. **deterministic failure on the graded fixture** — evaluable only if the task is built.

Accepted families must recover the estimand in every regime without re-tuning.

## Standing constraints honoured in this work

No Harbor task was created. No model was run. No frozen candidate was touched — checksums for Tasks 01–06,
02-explicit-invariant, G08, G10, G24 and G05 were verified unchanged before and after. `$0` of model or API spend.
