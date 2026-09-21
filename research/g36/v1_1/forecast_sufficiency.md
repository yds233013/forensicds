# Forecast-only scientific sufficiency gate

Tool `tools/g36_v11/forecast_sufficiency.py` → `forecast_sufficiency.json`. It scores in-process on the five
graded extracts (full size, frozen seeds) against the **proposed** v1.1 reward: forecast within the frozen
2.5 × SE_REF, decision, exact bookkeeping, and visible reconciliation. The response is excluded
entirely. No container, no model, no saved Gemini submission.

err/tol is |forecast − truth| / forecast tolerance. The fixture order is visible, hidden_a, hidden_b,
hidden_c, hidden_d.

## Section-7 wrong analyses

| wrong analysis | case | err/tol per fixture | max | decision fails | reward |
|---|---|---|---|---|---|
| incumbent historical model | M03 | 5.04 2.53 12.61 2.43 8.83 | 12.61 | yes | **0** |
| coherent historical model (reconciles, bookkeeping right) | M03 / CE10 | as above / 5.12 2.48 12.60 2.43 8.80 | 12.6 | yes | **0** |
| historical-only mean | M05 | 2.01 0.63 8.03 0.12 2.46 | 8.03 | — | **0** |
| latest-window retrain (incumbent) | CE10 | 5.12 2.48 12.60 2.43 8.80 | 12.60 | yes | **0** |
| latest value | M24 | 2.28 0.11 9.35 0.30 2.07 | 9.35 | — | **0** |
| pilot headline | M06 | 2.94 6.23 0.52 4.94 1.07 | 6.23 | — | **0** |
| selection-corrected only (response at pilot CDD) | M08 | 1.05 0.55 0.63 5.51 2.55 | 5.51 | yes | **0** |
| heat-corrected only (enrolled mix) | M09 | 15.04 15.23 11.62 7.16 16.09 | 16.09 | yes | **0** |
| pilot population forecast | M10 | 13.24 14.12 10.43 1.81 11.45 | 14.12 | yes | **0** |
| aggregate pre/post | CE12 | 8.53 5.12 8.91 9.09 11.08 | 11.08 | yes | **0** |
| response at midpoint CDD | M14 | 0.56 0.21 0.30 2.75 1.16 | 2.75 | yes | **0** |
| constant-kW response | CE02 | 0.13 0.07 1.21 4.01 0.64 | 4.01 | yes | **0** |
| uniform treatment response | M07 / M18 | 4.05 1.94 6.04 7.44 4.44 | 7.44 | yes | **0** |
| target weather ignored | M15 | 3.19 3.19 4.05 4.85 6.90 | 6.90 | yes | **0** |
| wrong estate weighting | M13 / M31 | 7.62 5.98 6.00 3.39 8.14 / 15.04 … 16.09 | 8.14 / 16.09 | yes | **0** |
| correct decision, wrong forecast | M27 | 0.62 2.05 5.67 1.57 0.58 | 5.67 | — | **0** |
| intercept recalibration | M12 | 16.15 14.70 25.97 8.27 21.81 | 25.97 | yes | **0** |
| double-counted response | M30 | 4.90 2.13 10.36 2.42 7.33 | 10.36 | yes | **0** |
| control-arm level | M23 | 13.12 11.54 21.39 5.96 15.44 | 21.39 | — | **0** |

Every section-7 analysis is rejected, most by several extracts. Several are rejected by **one extract
only**:

| case | err/tol | only failing extract |
|---|---|---|
| M14 | 2.75 | hidden_c |
| CE02 | 4.01 | hidden_c |
| M08 | 5.51 | hidden_c |

Coverage therefore depends on hidden_c, which is the hottest extract.

## Valid routes
V00, V01 and V02 all score reward 1, with worst err/tol 0.36 (hidden_d). The frozen forecast
tolerance is reproduced exactly: the worst legitimate route is at 0.36, as recorded at the v1 freeze.

## Verdict for section 7 alone
PASS. **But section 9 (`counterexample_search.md`) fails, and that is decisive.**
