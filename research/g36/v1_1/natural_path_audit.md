# Natural-implementation-path audit (desk audit using the measured panel; independent of Gemini)

The incumbent `capacity_forecast` loops over segments, fits a stable per-segment load-vs-CDD model on
history, averages it over the target outlook and weights by **estate** shares
(`selection_transport_postmortem.md`).

| minimal plausible edit | panel analogue | reward |
|---|---|---|
| do nothing (incumbent) | M03 | 0 |
| multiply each segment by a constant pilot response (ratio of arm means) inside the existing loop | CE01 | 0 (fails hidden_c 4.99, hidden_d 2.22) |
| subtract a constant kW pilot effect per segment | CE02 | 0 (fails hidden_b, hidden_c) |
| apply one pooled pilot ratio to the headline | M07 / M18 | 0 |
| estimate a per-segment response **linear in CDD** from the pilot arms, apply it day by day inside the existing loop | V00 / V01 | 1 |
| as above, but evaluate the response once at the target mean CDD | CE03 | 1 (0.22) |
| as above, but collapse the response to one estate number by the unweighted segment mean | CE06 | **1 (0.29)** |

## Findings
1. **Selection is pre-solved by the scaffold**, as already established. The natural edit inherits
   estate weighting.
2. **The CDD-dependent transport is live.** The minimal constant-response edits (CE01, CE02, M07)
   fail, and the verifier rejects them, mostly through hidden_c and hidden_d. The task is not solved
   trivially by the minimal edit.
3. **But a nearby mis-aggregation of the response (CE06) is not rejected.** The task's discriminating
   power therefore rests almost entirely on the heat-dependence of the response, and even there a
   wrong estate aggregation of the correct heat-dependent curve passes.
