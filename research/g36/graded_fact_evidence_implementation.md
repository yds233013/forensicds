# G36 graded-fact evidence audit (implementation)

One row per verifier check. **Every row must read `generator-only = NO` and
`future-outcome-dependent = NO`, or the check is removed.**

| graded fact | solver-visible evidence | why a real analyst can infer it | valid methods | tolerance basis | generator-only? | future-outcome? |
|---|---|---|---|---|---|---|
| `n_households` | `customer_master` row count | countable | any | exact | **NO** | **NO** |
| `estate_segment_shares` | `customer_master.segment_code` | countable | any | exact (1e-6) | **NO** | **NO** |
| `target_cdd_mean` | `weather_forecast_2027` | the published outlook is in the extract | any | exact (1e-3) | **NO** | **NO** |
| `target_peak_kw` | flat-tariff history + randomised pilot + customer master + weather outlook | the four ingredients of the decomposition are each observable | F1, F2, F3 | 2.5 x SE_REF, measured over 30 redraws | **NO** | **NO** |
| `estate_tou_response_at_target_cdd` | pilot control arm + enrolment log + customer master + outlook | the response curve is estimable inside the pilot season and reweightable to the estate | F1, F2, F3 | 2.5 x SE_REF | **NO** | **NO** |
| `segment_target_peak_kw` (reconciliation only) | as above | per-segment forecasts weight to the headline | any | 0.02 kW, coherence only | **NO** | **NO** |
| `procurement_decision` | the ceiling is stated in the capacity memo | 3.057 kW is given, with its derivation | any | exact | **NO** | **NO** |

## Checks deliberately NOT included

| candidate | why refused |
|---|---|
| per-segment tariff response | The smallest-response segment has ~50 enrolled households. Measured: 0.003 against a true 0.031 - a 90 % relative error. Not estimable to any useful tolerance, and widening the tolerance to admit it would make the check vacuous. |
| `heat_damping` as a parameter | A generator constant. Only its consequence - the response at a stated CDD - is observable. |
| `resp0` per segment | Generator internals. |
| the regime label | A generator concept; no artefact names it. |
| actual 2027 load | **Does not exist at decision time.** Procurement lead time is nine months; the whole point is that this is decided on forecast. |
| per-household response | Not identified by any experiment. |
| response outside the pilot's observed CDD range | Extrapolation beyond support. |
| historical backtest quality | Deliberately worth nothing. The incumbent holds out at R2 0.75 and is wrong by up to 0.56 kW. |

## Explicit confirmation

**No verifier check requires generator-only truth. No verifier check requires an outcome that does
not exist at decision time.** The target forecast is graded against the generator's latent
*expectation* for the estate and the published weather outlook - a property of evidence the analyst
holds, in the same sense that G34 graded cumulative incidence and G35 graded the rollout contrast.

## On the estate-weighted response check

It is retained on identifiability grounds: measured bias +0.0026, sd 0.0071, well inside a tolerance
of 2.5 x SE_REF. Its discriminatory value beyond the headline forecast is **partial** - the two
errors correlate at r = -0.82, so roughly a third of its variance is independent. Its specific
purpose is to catch analyses that reach a plausible forecast through compensating errors in the
stable and response components, and to catch `M28_response_reported_zero` and
`M29_response_sign_flipped`, which report a defensible-looking headline with an incoherent or absent
response. Whether any wrong method is caught **only** by this check is reported in the mutation
results; if none is, the check is redundant but harmless and is kept for the compensating-error
case.
