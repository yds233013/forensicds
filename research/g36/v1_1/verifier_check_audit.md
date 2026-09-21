# Verifier check audit (written BEFORE the v1.1 verifier edit, before any scoring run)

Every criterion in the v1 / draft-v1.1 `tests/test_capacity.py`. The binary reward is 1 only if **every**
pytest test passes (`test.sh`). So a check contributes to reward if and only if it can fail.

Categories: **A** essential scientific · **B** downstream consistency · **C** bookkeeping / schema /
integrity · **D** diagnostic only.

| # | check | quantity tested | reward-bearing in v1.1? | scientific purpose | independent information? | wrong forecast passes without it? | correct forecast fails because of it? | cat. | v1.1 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `test_warehouse_unmodified` | extract tables present, 2 arms, outlook present | yes | integrity: the agent did not destroy or rewrite the evidence | yes (integrity) | n/a | no | C | keep |
| 2 | `test_pipeline_runs` | pipeline exits 0 and writes JSON | yes | output exists | — | n/a | no | C | keep |
| 3 | `test_rerun_is_deterministic` | identical output on rerun | yes | reproducibility of the readout | yes (integrity) | n/a | no (only a nondeterministic pipeline fails) | C | keep |
| 4 | `test_output_schema` | required keys; headline numeric; decision in {procure, defer} | yes | contract shape | — | n/a | **v1: yes**, if the response key is absent. In v1.1 the response key is **removed from the required list** so reward cannot depend on the response in any way, including its presence | C | keep, response key dropped |
| 5 | `test_bookkeeping` (visible) | n_households, estate shares, target CDD mean, exact | yes | inputs the forecast is built on are read correctly from the extract; recomputed from the DB, never from truth | yes: catches hard-coded counts and wrong-table reads (M26, M31-type, M32) | M32 (CDD mean from history) is also caught by the forecast on some extracts; M26 has a correct forecast | no: these are exact counts and means, with no estimation involved | C | keep |
| 6 | `test_target_peak_forecast` (visible) | `target_peak_kw` vs latent truth, 2.5 × SE_REF | yes | **the business estimand**: E[peak kW \| whole estate on TOU, target weather] | yes: the only check on the science | — | only at the measured rate of the frozen v1 window (worst legitimate route 0.36 of tolerance) | **A** | keep, unchanged |
| 7 | `test_estate_tou_response` (visible) | response vs R_load | **no** | intermediate diagnostic | **not identifiable sharply enough to grade** (calibration: valid 0.92 SE_REF vs wrong aggregation 0.99 SE_REF) | — | yes, at any tolerance that separates wrong aggregations | **D** | **report-only**: recorded to `/logs/verifier/response_diagnostic.json`, never asserts |
| 8 | `test_segment_forecasts_reconcile` (visible) | Σ share × segment forecast = headline, within 0.02 kW | yes | internal consistency of the agent's own output; the contract's definitions make this an identity. **Uses no truth.** | integrity only (incumbent passes it while 45 SD wrong) | yes, it is not load-bearing | only if the agent's own reported fields contradict each other; a correct analysis cannot | B | keep |
| 9 | `test_procurement_decision` (visible) | decision == truth decision | yes | the business action; downstream of the forecast and the 3.057 kW ceiling | partly: blocks decision-only shortcuts from mattering, and blocks a correct forecast paired with an inverted decision | M20/M21 (constant decision) are caught by it on some extracts | **possible** in principle where tolerance exceeds the threshold margin (visible 0.048 vs margin 0.047; hidden_c 0.100 vs 0.080). Frozen v1 property; K9 families decided unanimously correctly. Recorded as a risk, not changed | B | keep, unchanged |
| 10a | `test_hidden_extract`: pipeline runs | — | yes | as #2 on unseen extracts | yes | — | no | C | keep |
| 10b | `test_hidden_extract`: forecast | `target_peak_kw` × 4 hidden | yes | as #6; stops hard-coding to the visible extract | yes | — | as #6 | **A** | keep, unchanged |
| 10c | `test_hidden_extract`: response | response × 4 hidden | **no** | — | as #7 | — | as #7 | **D** | **removed from reward**; recorded diagnostically |
| 10d | `test_hidden_extract`: bookkeeping | as #5 × 4 hidden | yes | constants from the visible extract cannot survive | yes | — | no | C | keep |
| 10e | `test_hidden_extract`: decision | as #9 × 4 hidden | yes | as #9 | as #9 | — | as #9 | B | keep, unchanged |

## Result

Reward-bearing in v1.1: **A** (forecast, 5 extracts), **B** (decision, 5 extracts; visible
reconciliation), **C** (integrity, schema, bookkeeping, determinism). **D** response: report-only.

Nothing is kept because removing it would make the task easier, and nothing is added. The only
reward-bearing change from v1 is that the response is removed from #4, #7 and #10c.
