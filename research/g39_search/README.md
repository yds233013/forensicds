# G39 search — structural-object / decision-invariant tournament (RESEARCH ONLY)

**Decision: SEARCH AGAIN.** No concept proceeds. No candidate, no Gemini, no Harbor, $0.

## Order of work (provenance)
1. `family_A.md`, `family_B.md`, `family_C.md`: 35 concepts, targets written mathematically,
   initial cheap-solve and semantic filters. All before any code.
2. `concept_pool.md`, `top12.md`: 23 rejected, 12 carried.
3. `sim/g39_sims.py`: pre-registered statistics in its docstring; 12 concepts × 5 regimes × 60
   worlds.
4. `sim/g39_counterexamples.py`: top-3 hybrid search on the same worlds.
5. Gate write-ups, `top3_adversarial.md`, `recommendation.md`.

## Disclosures
| item | status |
|---|---|
| A1 `W03_force_x_ge_m` (pre-labelled wrong) | algebraically **valid** (relabelled) |
| A4 X03, C2 X02, C2 X03 (pre-labelled valid-alt) | confirmed identical |
| C3 `W10_relative_change_as_pp` | an **implementation error**: my re-expression made it identical by construction. It is not a meaningful wrong object |
| B4 `solar_heavy` regime | uses the same generator as "mixed" with a different seed stream; it is not a distinct regime |
| B3 p99 relative errors | huge where the truth ≈ 0 kW (a scale artefact); detection statistics unaffected |

None of these changes the verdict: each concept fails on other wrong objects too.

## Files
`README.md`, `family_A.md`, `family_B.md`, `family_C.md`, `concept_pool.md`, `top12.md`,
`minimal_simulations.md`, `valid_routes.md`, `wrong_objects.md`, `separation.md`,
`counterexamples.md`, `natural_paths.md`, `recognition_execution.md`, `decision_audit.md`,
`fixture_design.md`, `correct_table.md`, `graded_fact_evidence.md`, `igqa.md`, `invariants.md`,
`leakage.md`, `distinctness.md`, `top3_adversarial.md`, `recommendation.md`, plus `sim/`.
