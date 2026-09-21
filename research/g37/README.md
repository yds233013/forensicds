# G37 research — measurement-system change / errors-in-variables

**Status: RESEARCH ONLY. DECISION: DROP. No candidate directory, no Gemini, no Harbor, $0 model spend.**

## Order of work (provenance)
1. `estimand_audit.md` and `threshold_provenance.md`, written before any generator.
2. `domain_tournament.md`: 10 concepts, 6 rejected by rule, top 4 carried forward.
3. `sim/`:
   - `c1_gauge.py`, `analyze_c1.py`: C1, with window definitions pre-registered in the docstring;
   - `proto_others.py`: C2, C7, C9.
4. Gate write-ups, then `adversarial_review.md` and `recommendation.md`.

## Design log (every change, and what triggered it)
| step | change | trigger | targeted a specific wrong method? |
|---|---|---|---|
| D1 | initial C1 design: SPC-sample volumes, 5 regimes | — | — |
| fix | array-broadcast bug in the generator | crash on smoke run | no |
| D2 | realistic in-line volumes (station logs every part), manual bridge capped at 4k | D1 window 0.01; test whether volume helps | **no**: neutral |
| D3 | feasibility-frontier probe (unrealistic gauges), labelled as not a design | D2 window 0.01 | **no**: probes the frontier |
| C9 | "reference tool only" relabelled legitimate (it is unbiased under random dispatch) | a labelling error found in results | no: a correction of *my* label, disclosed |

## Files
`domain_tournament.md`, `top4_designs.md`, `estimand_audit.md`, `threshold_provenance.md`,
`identification.md`, `valid_estimators.md`, `recognition_execution.md`, `natural_path_audit.md`,
`wrong_method_panel.md`, `counterexample_search.md`, `tolerance_window.md`, `fixture_coverage.md`,
`decision_tolerance.md`, `cheap_solve.md`, `correct_table.md`, `falsification.md`,
`graded_fact_evidence.md`, `igqa.md`, `representation_leakage.md`, `distinctness.md`,
`adversarial_review.md`, `recommendation.md`.
