# G36 — forecasting under an intervention that changes one mechanism and not others

**Status: RESEARCH COMPLETE. Recommendation A — BUILD. Not implemented. No candidate directory.**

No model of any kind was run in this phase: no Gemini, no Claude, no `harbor check`, **$0.00**.

## The finding in one paragraph

A utility must decide whether to procure peaking capacity for next summer. Three summers of
flat-tariff history identify the **stable** mechanism - weather drives air-conditioning load, and a
tariff cannot change physics. A mandatory time-of-use tariff now changes the **unstable** mechanism,
behaviour, which only a voluntary pilot has observed. Two independent things stop the pilot's answer
transporting to the estate: the households that volunteered are far more responsive than the
population, and the pilot summer was mild while the target summer is forecast hot - and demand
response fades in heat, because an air conditioner running flat out cannot be shifted. **Fixing
either one alone still leaves 10-12 sd of error and a wrong capacity decision.** The incumbent
production model holds out at R2 0.75 on a genuine unseen summer and is wrong about the target by
45 sd, because the mechanism it omits did not exist during the period it was validated on.

## Why this design exists

G35 scored 3/3 because recognition handed over the estimator: once "saturation" was named, the
answer was `mean(pi=1) - mean(pi=0)`. The domain tournament here weighted **execution-difficulty-
after-recognition x3** and rejected five otherwise-attractive incidents for collapsing the moment the
policy change is noticed - including supplier lead times, which looks sophisticated and is really a
weighted average the data hands over.

## Files

| file | contents |
|---|---|
| `concept_map.md` | which shift concepts are genuinely different failure modes |
| `domain_tournament.md` | 12 domains scored, execution-after-recognition weighted x3 |
| `incident_tournament.md` | 9 incidents, 3 to formal design, 2 simulated |
| `formal_designs.md` | full specification of the top three |
| `identification.md` | why the future quantity is identified without clairvoyance |
| `recognition_execution_gate.md` | **the gate G35 failed** - measured |
| `wrong_methods.md` | 15 wrong analyses with measured errors, and 3 honest non-entries |
| `valid_methods.md` | accepted routes, sampling behaviour, and an honest limitation |
| `simulation.py` / `gates.py` / `f2_repricing.py` | the measurements |
| `simulation_results.md` | all gate results including the F2 comparison |
| `correct_table_gate.md` | separation survives a perfect analysis table |
| `coherent_wrong_gate.md` | a model with R2 0.75 that is wrong by 45 sd |
| `cheap_solve_gate.md` | 12 shortcuts; best reaches 4/5 decisions |
| `falsification_design.md` | the diagnostics that separate correct from `W8`/`W9` |
| `representation_leakage.md` | necessary metadata vs answer leakage |
| `graded_fact_evidence.md` | what may and may not be graded |
| `distinctness_matrix.md` | against Task02, G05, G08, G10, G24, G31, G33, G34, G35 |
| `model_failure_predictions.md` | pre-registered, before implementation |
| `build_recommendation.md` | **the decision, the three open risks, the estimates** |

## The open risk I would flag first

The three "valid routes" measured here agree to 0.0000 because they are **algebraic rearrangements
of one estimand, not independent estimators**. The brief asks for two genuinely legitimate routes and
this phase has not demonstrated that. Implementation must build and measure a hierarchical estimator
and a regression-with-interaction form before any tolerance is fixed.
