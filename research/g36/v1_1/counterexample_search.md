# Counterexample search — wrong MODELLING routes inside the forecast

Routes were written, and their kind ("wrong" / "alternative") fixed, **before any was scored**
(`CE` dict in `tools/g36_v11/forecast_sufficiency.py`). Each changes how the tariff response is
modelled or composed inside the forecast, not merely a reported field.

| route | kind (pre-fixed) | err/tol per fixture (vis a b c d) | max | reward |
|---|---|---|---|---|
| CE01 constant fractional response (ratio of arm means) | wrong | 0.93 0.47 0.55 4.99 2.22 | 4.99 | 0 |
| CE02 constant absolute-kW response | wrong | 0.13 0.07 1.21 4.01 0.64 | 4.01 | 0 |
| CE03 plug-in at target mean CDD (no averaging over target days) | wrong | 0.14 0.13 0.03 0.01 0.22 | 0.22 | **1** |
| CE04 response at pilot mean CDD, transported unchanged | wrong | 1.05 0.55 0.63 5.51 2.55 | 5.51 | 0 |
| CE05 household-weighted response used inside the forecast | wrong | 1.10 0.61 2.38 0.59 2.01 | 2.38 | 0 |
| **CE06 segment-unweighted response used inside the forecast** | **wrong** | **0.13 0.10 0.27 0.12 0.29** | **0.29** | **1** |
| CE07 pooled (all-segment) response curve | wrong | 2.82 1.23 5.31 1.10 1.06 | 5.31 | 0 |
| CE08 ad-hoc heat adjustment r × pilotCDD/targetCDD | wrong | 0.77 0.38 3.34 3.22 1.00 | 3.34 | 0 |
| CE09 log-linear response-vs-CDD form | alternative | 0.11 0.22 0.06 1.19 0.03 | 1.19 | 0 |
| CE10 incumbent retrained on latest window | wrong | 5.12 2.48 12.60 2.43 8.80 | 12.60 | 0 |
| CE11 latest-window stable model + correct response | alternative | 0.04 0.12 0.07 0.18 0.34 | 0.34 | 1 |
| CE12 aggregate pre/post on treated households | wrong | 8.53 5.12 8.91 9.09 11.08 | 11.08 | 0 |
| CE13 R_load composed at the mean: L0 × L1(c̄)/L0(c̄) | alternative | 0.14 0.13 0.03 0.01 0.22 | 0.22 | 1 |

## Decisive counterexample: CE06
The estate forecast is computed as the correct no-tariff estate load × (1 − the **unweighted mean of
the four segment responses** at c̄). The response is aggregated with equal weight per segment,
ignoring both estate shares and load. It is a wrong model of the estate's tariff response. It lands
at **≤ 0.29 of forecast tolerance on every graded extract**, with correct decisions and correct
bookkeeping: **reward 1**.

This is the same structural coincidence that made the response ungradable. In this DGP the
equal-segment mean of r_s falls within about 1 response-SE of R_load. Multiplied into the estate
load, that is ~0.015 kW, against forecast tolerances of 0.042–0.100 kW. **Removing response grading
does not leave a forecast that discriminates this wrong aggregation.** Nor could any response check
have done so, per the calibration.

## Secondary findings (recorded; not decisive)
- **CE03 / CE13 (plug-in at the mean CDD) pass, at 0.22.** They are wrong in principle, since
  E[f(C)] ≠ f(E[C]), but the Jensen term here (−b·r₁·Var C plus the clip) is smaller than
  estimation noise. I pre-labelled CE03 "wrong". I record it as *wrong in principle, immaterial in
  this DGP* and do **not** rely on that reclassification: CE06 alone triggers the stop.
- **CE09 (log-linear response form), pre-labelled "alternative", fails hidden_c at 1.19.** It
  extrapolates the fade exponentially to the hottest extract. Whether that is a legitimate estimator
  failing or a wrong functional form is itself an adjudication question. It is recorded, not
  resolved.
- **CE11 (latest-window stable model + correct response) passes**, as expected if the historical
  relation is genuinely stable.

## Verdict
**STOP (authorisation §9). No new verifier check is added. v1.1 → ABANDON / DEVELOPMENT-ONLY for external review.**
