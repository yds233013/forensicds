# G36 mutation suite and polished adversarial solutions

## Mutation suite: 27 cases, 0 mismatches, 0 ERRORs

25 generated mutations plus Oracle and Nop. Every case ran; none crashed.

| class | count | expected | observed |
|---|---|---|---|
| Oracle | 1 | 1 | **1** |
| Nop | 1 | 0 | **0** |
| legitimate routes | 2 | 1 | **1, 1** |
| wrong analyses | 23 | 0 | **all 0** |

### Hash and distinctness audit

All four rules enforced by `tools/g36/make_mutations.py`, each with a verified negative control:

| rule | enforcement | result |
|---|---|---|
| mutation differs from its source | sha256 compared to the unmutated render | pass |
| no unexpected duplicate hashes | pairwise across the suite | **caught one genuine duplicate** |
| intended change present | textual assertion on the rendered source | pass |
| **mutation actually executes** | smoke-run against a real small extract, must emit all graded quantities as numbers | pass, 25/25 |

The duplicate: `M23_seasonal_naive` rendered byte-identical to `M05_historical_mean`, because this
design's history has no multi-year seasonal structure for a seasonal-naive baseline to exploit. It
was **replaced** with `M23_control_arm_level`, a genuinely distinct wrong analysis. The rule was not
weakened. 25 distinct hashes, `source_sha256` recorded per case in `mutations_manifest.json`.

### Full results

| mutation | checks failed | what it gets wrong |
|---|---|---|
| M03_historical_model | 7 | the incumbent; no tariff response at all |
| M05_historical_mean | 4 | historical level as the forecast |
| M06_pilot_mean | 5 | the pilot's treated level as the forecast |
| M07_pilot_effect_flat | 6 | pilot ratio applied to the historical level |
| **M08_selection_fixed_only** | **3** | **reweights to the estate but evaluates at pilot weather** |
| **M09_temperature_fixed_only** | **8** | **evaluates at target weather but keeps the enrolled mix** |
| M10_pilot_population | 8 | forecasts the enrolled group, not the estate |
| M12_intercept_recalibration | 7 | level shift instead of a mechanism |
| M13_equal_segment_weights | 7 | equal rather than estate weights |
| M14_response_at_midpoint_cdd | 2 | response evaluated halfway between pilot and target weather |
| M15_target_weather_ignored | 5 | historical weather used for the target season |
| M18_aggregate_effect_uniform | 6 | one aggregate percentage applied to everything |
| M20_constant_procure | 3 | constant decision |
| M21_constant_defer | 2 | constant decision |
| M23_control_arm_level | 6 | the pilot control arm's level as the forecast |
| M24_latest_value | 4 | last season's mean |
| M26_hardcoded_households | 4 | hardcoded estate size |
| M27_hardcoded_forecast | 4 | hardcoded headline number |
| **M28_response_reported_zero** | **5** | **correct forecast, response reported as zero** |
| **M29_response_sign_flipped** | **5** | **correct forecast, response sign inverted** |
| M30_double_counted_response | 6 | response applied twice |
| M31_shares_from_pilot | 7 | enrolled shares used as estate shares |
| M32_cdd_mean_from_history | 5 | historical CDD reported as the target mean |

## Does the estate-response check earn its place? **YES**

`M28_response_reported_zero` and `M29_response_sign_flipped` both produce a **correct headline
forecast** and are caught **only** by `test_estate_tou_response` and by the response component of
the hidden extracts. Neither ever fails `test_target_peak_forecast`.

An initial automated scan reported "caught only by the response check: none". That scan was wrong -
it excluded any case failing a hidden extract, but hidden extracts grade *both* quantities, so a
response-only failure appears there too. Inspecting the failed-check lists directly settles it:
M28 and M29 fail `test_estate_tou_response` and never fail the forecast check.

**The check is retained on measured evidence**, not on the prior argument that it "isolates the
transport work". Its identifiability was already established (bias +0.0026, sd 0.0071).

## Polished adversarial solutions A-H

| | analyst | realised as | reward |
|---|---|---|---|
| **A** | incumbent-forecast analyst | `M03_historical_model` | **0** |
| **B** | pilot-headline analyst | `M06_pilot_mean` / `M07_pilot_effect_flat` | **0** |
| **C** | selection-aware but heat-naive | `M08_selection_fixed_only` | **0** |
| **D** | heat-aware but selection-naive | `M09_temperature_fixed_only` | **0** |
| **E** | latest-window / retrain analyst | `M24_latest_value` | **0** |
| **F** | decision-only analyst | `M20_constant_procure`, `M21_constant_defer` | **0** |
| **G** | coherent historical-model analyst | `M03` with the R2 0.75 backtest narrative | **0** |
| **H** | correct scientific analyst, independent route | `V00_plugin_transport`, `V01_explicit_loop`, Oracle | **1** |

A through G fail. H passes by three different routes.

**C and D are the pair that matters.** Each is written by an analyst who has correctly recognised a
real problem and fixed it, and each still fails. C reweights the pilot response to the estate and
stops; D evaluates the response at target weather and stops. Neither is a strawman - both are more
sophisticated than the incumbent, and C's write-up would read as more rigorous than the correct
answer's because it names a problem and shows its work.

## Cheap-solve panel

Carried into the packaged task via the mutation suite: historical forecast (M03), dashboard copy
(M03), last value (M24), historical mean (M05), pilot mean (M06), pilot direction (M07), constant
procure (M20), constant defer (M21), single-segment weighting (M13), aggregate pre/post (M18),
hardcoded threshold guess (M27), enrolled-share reweighting (M31), historical CDD (M32).

**No shortcut scores above 0.** The decision alone cannot earn reward: M20 and M21 reproduce some
decisions and still fail on the numeric quantities, which is the design requirement that
decision-only grading is prohibited.

## Tamper and integrity controls

| control | result |
|---|---|
| plant `/pytest.ini` | `refusing to grade`, reward 0 |
| plant `/tests/conftest.py` | `refusing to grade`, reward 0 |
| add a file to the standard library | `refusing to grade`, reward 0 |
| edit the warehouse in place | 8 checks fail, reward 0 |
| probe for `/tests` and `/solution` from the workspace | neither exists in the image, reward 0 |
