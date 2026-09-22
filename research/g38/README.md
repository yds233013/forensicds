# G38 research — regression to the mean under threshold-triggered intervention

**Status: DROP / RESEARCH-ONLY. See `G38_FINAL_STATUS.md`.** No candidate, no Gemini, no Harbor, $0.

## Order of work (provenance)
1. `estimand.md` and `threshold_provenance.md`, written before any simulation.
2. `domain_tournament.md`: 12 concepts, 9 rejected, top 3 carried.
3. `sim/`:
   - `g38_sim.py` (DGP, 2 valid families, 3 legitimate variants, 29 wrong/ambiguous methods);
   - `analyze_g38.py` (pre-registered window definitions);
   - `aux_audits.py` (G05 ablation, trigger-window evaluation).
4. Gate documents, then `adversarial_review.md` and `recommendation.md`.

## Design log
| step | change | trigger | targeted a method? |
|---|---|---|---|
| 1 | initial design and 5 regimes | — | — |
| 2 | W13 simplified; W25 removed as a verbatim duplicate of W07 (before any scored run) | code review | no |
| 3 | historical-feature loop vectorised; W18 negative-step guard | speed / NaN | no |
| — | **no further changes.** The trigger window, sample size, tolerance and regimes were never altered after scoring | — | — |

Runs: R1 200 draws/fixture; R2 and R3 100 draws/fixture; audits 60 draws. The previous session ended
while I was polling; the detached runs finished and wrote their results intact.

## Files
`G38_FINAL_STATUS.md`, `domain_tournament.md`, `top_designs.md`, `estimand.md`,
`threshold_provenance.md`, `dgp.md`, `identification.md`, `valid_estimators.md`, `g05_overlap.md`,
`recognition_execution.md`, `natural_path.md`, `matching_audit.md`, `wrong_methods.md`,
`counterexample_search.md`, `tolerance_window.md`, `fixtures.md`, `decision_compatibility.md`,
`correct_decision_wrong_science.md`, `cheap_solve.md`, `correct_table.md`, `falsification.md`,
`graded_fact_evidence.md`, `igqa.md`, `representation_leakage.md`, `trigger_window_audit.md`,
`adversarial_review.md`, `recommendation.md`.
