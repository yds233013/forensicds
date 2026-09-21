# G36 implementation-phase gate results

All measured on the **packaged** extract, after the final threshold and final fixtures were settled.
No model of any kind was involved.

## Final fixtures

Capacity ceiling **3.057 kW** (derivation in `threshold_provenance.md`).

| fixture | households | response character | truth (kW) | decision | margin | SE_REF | margin / SE |
|---|---|---|---|---|---|---|---|
| `visible` | 6000 | modest response, moderate heat fade | 3.0100 | defer | 0.0470 | 0.01935 | 2.4 |
| `hidden_a` | 5600 | minimal response, severe opt-in skew | 3.1209 | procure | 0.0639 | 0.02753 | 2.3 |
| `hidden_b` | 6400 | high response, flat in heat | 2.7274 | defer | 0.3296 | 0.01782 | 18.5 |
| `hidden_c` | 5800 | high response, quarters in heat | 3.1366 | procure | 0.0796 | 0.03986 | 2.0 |
| `hidden_d` | 6200 | mid response, moderate fade | 3.0047 | defer | 0.0523 | 0.01694 | 3.1 |

**3 defer / 2 procure.** Response magnitudes are an even sweep of the published time-of-use range
(maximum per-segment peak reduction 10 %, 14 %, 23 %, 30 %).

`hidden_b` and `hidden_c` are the discriminating pair: identical response magnitude, identical
history generation, identical enrolment behaviour, differing only in what heat does to the response.

### The margin caveat, stated plainly

Margins are **2.0 to 18.5 SE_REF**, and three fixtures sit near 2.0-2.4. That is materially tighter
than G35's 5.3 sd floor. `hidden_c` is the tightest because its steep response curve amplifies
extrapolation error, giving it the largest SE_REF in the set (0.0399).

What makes this gradeable rather than a coin flip: the fixtures are **frozen**, so the question is
not whether a random draw lands correctly but whether the accepted estimators do on *these* draws.
All three independent families get all five decisions right on the frozen fixtures, and across 20
fresh draws they were unanimous and correct on 20 of 20. But the headroom is real and is recorded as
the principal residual risk.

## Recognition-vs-execution (packaged artefacts)

Errors in units of the accepted estimator's sampling sd.

| insight handed over free | visible | hidden_a | hidden_b | hidden_c | hidden_d | worst | wrong decisions |
|---|---|---|---|---|---|---|---|
| **H0** nothing | 6.6 | 2.9 | 24.2 | 0.8 | 7.0 | **24.2 sd** | **3 / 5** |
| **H1** "the pilot's response does not transport" | 3.4 | 2.6 | 1.9 | 37.1 | 7.3 | **37.1 sd** | **1 / 5** |
| **H2** "the response depends on cooling demand" | 49.2 | 70.8 | 35.0 | 48.2 | 46.0 | **70.8 sd** | **3 / 5** |
| **H1 + H2** both | 0.4 | 0.7 | 0.3 | 1.3 | 1.0 | **1.3 sd** | **0 / 5** |

**PASS.** Each insight alone leaves 37-71 sd of error and at least one wrong capacity decision.
This is the gate G35 failed, and the margin here is far wider than the design phase predicted.

## Same-history / different-future

| fixture | holdout RMSE | holdout R2 | historical mean | truth | decision |
|---|---|---|---|---|---|
| visible | 0.7560 | 0.7532 | 3.1074 | 3.0100 | defer |
| hidden_a | 0.7491 | 0.7495 | 3.0774 | 3.1209 | procure |
| hidden_b | 0.7573 | 0.7496 | 3.0852 | 2.7274 | defer |
| hidden_c | 0.7528 | 0.7498 | 3.1482 | 3.1366 | procure |
| hidden_d | 0.7441 | 0.7479 | 3.1087 | 3.0047 | defer |

Backtest R2 spans 0.7479-0.7532 across every fixture - a range of 0.005. **The discriminating pair
differs by 0.0044 in holdout RMSE (0.6 %) and by 0.41 kW in truth, with opposite decisions.** No
backtest separates them; only the pilot can.

## Coherent-but-wrong: the incumbent production model

| fixture | holdout R2 | holdout bias | forecast | truth | error |
|---|---|---|---|---|---|
| visible | 0.7532 | +0.0061 | 3.2540 | 3.0100 | **+0.2441** |
| hidden_a | 0.7495 | -0.0055 | 3.2949 | 3.1209 | +0.1740 |
| hidden_b | 0.7496 | -0.0016 | 3.2893 | 2.7274 | **+0.5619** |
| hidden_c | 0.7498 | +0.0014 | 3.3783 | 3.1366 | +0.2417 |
| hidden_d | 0.7479 | -0.0008 | 3.3787 | 3.0047 | **+0.3741** |

It holds out at R2 0.75 on a genuine unseen season, calibrates to within 0.006 kW, reconciles to the
estate total, and is wrong by up to 0.56 kW - **up to 32 SE_REF** - because the mechanism it omits
did not exist during the period it was validated on.

## Negative control

The response-estimation pipeline run on a **pre-pilot flat-tariff season**, splitting enrolled
households by their eventual arm. A correct pipeline must find nothing.

| fixture | estimated response before any tariff existed |
|---|---|
| visible | +0.00127 |
| hidden_a | -0.00031 |
| hidden_b | +0.00274 |
| hidden_c | -0.00220 |
| hidden_d | -0.00257 |

All within 0.003 of zero. An unstratified version of this control reported +0.027 and -0.038 - see
`development_defect_log.md` D4.

## Representation leakage

| fixture | enrolment over-representation | corr(row order, segment) | enrolled |
|---|---|---|---|
| visible | 0.32x to 2.49x | +0.031 | 553 |
| hidden_a | 0.07x to 2.90x | -0.003 | 588 |
| hidden_b | 0.35x to 2.51x | -0.028 | 629 |
| hidden_c | 0.34x to 2.38x | -0.011 | 553 |
| hidden_d | 0.33x to 2.57x | +0.003 | 585 |

Enrolment over-representation is **necessary evidence, not leakage** - it is the selection the task
is about, the analyst must measure it, and knowing it does not give the answer. Row order carries no
segment signal. Enrolled counts overlap across fixtures.

## Tolerance calibration

| fixture | SE_REF (forecast) | tolerance | SE_REF (response) | tolerance |
|---|---|---|---|---|
| visible | 0.01935 | 0.04838 | 0.00690 | 0.01726 |
| hidden_a | 0.02753 | 0.06884 | 0.01122 | 0.02805 |
| hidden_b | 0.01782 | 0.04455 | 0.00584 | 0.01460 |
| hidden_c | 0.03986 | 0.09965 | 0.01650 | 0.04125 |
| hidden_d | 0.01694 | 0.04235 | 0.00618 | 0.01545 |

Admissible window **0.91 < multiplier < 6.88**; chosen **2.5**. Worst legitimate route at 0.36 of
tolerance; hardest wrong analysis caught at 2.75x tolerance. 30 redraws per fixture.
