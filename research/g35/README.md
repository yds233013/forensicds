# G35 - marketplace / network interference in experimentation

**Status: RESEARCH COMPLETE. Recommendation A - BUILD. Not implemented. No candidate directory.**

No model of any kind was run during this turn: no Gemini, no Claude, no `harbor check`, no credits.

## The finding in one paragraph

A delivery platform randomises **dispatch priority** to merchants inside city-day blocks whose
treatment **saturation** is itself randomised.  Couriers are a fixed pool inside a block, so priority
given to one store is priority taken from another.  At full saturation every store carries the same
dispatch weight, which allocates couriers exactly as no store having priority would - so the whole
private advantage cancels and only the algorithm's genuine routing efficiency survives.  The
experiment dashboard reports a **+19.4 point** lift; the true full-rollout effect is **+4.3 points** on
the visible regime and **+0.6 points** on the sharpest hidden regime, where the naive comparison reads
**+24.0**.  The naive analysis is wrong by **4.2x to 38.7x**, and it is wrong while being an unbiased
estimate of a perfectly real quantity - just not the one the launch decision is written on.

## Why it survived where G33 and G34-v1 did not

- **G33** was dropped because the intended mechanism turned out statistically irrelevant to the final
  quantity.  Here mechanism strength was measured **first**: 4.2x-38.7x.
- **G34-v1** was rejected because the mechanism was too weak to carry the task.  Here interference is
  not a perturbation of the effect; it is most of the effect.
- **G34's baseline** showed internal coherence is not validation.  So three analyses that satisfy every
  consistency check were constructed and shown to fail - two of them flipping a launch decision.

## Files

| file | contents |
|---|---|
| `domain_tournament.md` | nine domains scored; food-delivery dispatch wins |
| `incident_tournament.md` | five incidents; two simulated |
| `formal_interference_model.md` | units, exposure mapping, potential outcomes, why the limit is exactly zero-sum |
| `estimands.md` | the three graded objects and the decision gate |
| `identification.md` | what identifies each object, and the evidence an analyst has |
| `wrong_methods.md` | 12 pre-registered wrong analyses, with measured errors, including two honest negatives |
| `valid_methods.md` | four valid families, agreement to 0.0048 |
| `simulation.py` | design, counterfactual truth, estimator panel |
| `gates.py` | coherent-but-wrong and cheap-solve gates |
| `simulation_results.md` | all measured gate results |
| `correct_table_gate.md` | separation survives a perfect analysis table |
| `cheap_solve_gate.md` | shortcut panel, with two entries reclassified as legitimate |
| `coherent_wrong_gate.md` | the G34 carry-forward |
| `constant_decision_and_regimes.md` | four regimes, 2/2 split, the discriminating pair |
| `representation_leakage.md` | leakage probes and build requirements |
| `graded_fact_evidence.md` | what may and may not be graded |
| `mutation_hash_design.md` | rules derived from G34's phantom-mutation defect |
| `adversarial_review.md` | ten attacks; two landed and were fixed, one partially stands |
| `cross_task_matrix.md` | distinctness from Task02, G05, G08, G10, G24, G31, G33, G34 |
| `build_recommendation.md` | **the decision, the risks, and the cost estimate** |

## Honest headline risk

**K17 partially lands.**  Marketplace interference is a famous idea, and once an analyst recognises
that assigned saturation is the operative variable, several different analyses land close to the truth.
The difficulty is concentrated in one recognition step.  That is the same shape as G34, which scored
2/3.  A similar band is likely and is predicted here **before** any baseline.
