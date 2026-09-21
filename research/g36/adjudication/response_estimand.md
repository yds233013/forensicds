# G36 adjudication - the response estimand from first principles

This note derives the correct definition of `estate_tou_response_at_target_cdd` from the utility's
planning problem and the contract text. **It does not use the Gemini trials as evidence.** The fact
that three trials converged on one reading is a reason to investigate, not a reason to conclude; the
conclusion must stand on domain semantics alone.

## 1. The planning problem

The utility holds firm capacity, a quantity in **MW**. It must know whether next season's **aggregate**
peak-window demand will exceed that capacity. Every quantity that matters for the decision is an
aggregate of load across customers:

```
L0 = sum_i E[ L_i(no tariff) ]      estate peak-window load without the tariff
L1 = sum_i E[ L_i(tariff)    ]      estate peak-window load with the tariff
```

Dividing by the customer count gives the per-customer means the task reports (`target_peak_kw` is
`L1 / N`). The ceiling is `firm MW / 1.10 / N`, so the decision is exactly `L1 / N >= ceiling`.

## 2. Candidate definitions

Segments `s` with estate shares `p_s`, per-segment expected no-tariff load `L_s(c)` at cooling
demand `c`, and per-segment fractional response `r_s(c)`, so that tariff load is `L_s(c)(1 - r_s(c))`.

| | definition | units | weighting |
|---|---|---|---|
| **R_load** | `(L0 - L1) / L0` at the target mean CDD `c̄` = `sum p_s L_s r_s / sum p_s L_s` | dimensionless, share of estate **load** | each customer weighted by its **load** |
| **R_household** | `sum p_s r_s(c̄)` | dimensionless, average **customer's** fractional reduction | each customer weighted **equally** |
| **R_season** | `1 - mean_d L1(d) / mean_d L0(d)` over target-season days | dimensionless, share of season-average load | load, averaged over days rather than evaluated at `c̄` |
| **R_individual** | mean over customers of each customer's own fraction | as R_household | equal. **Identical to R_household here**, because response is homogeneous within segment |
| **ΔkW** | `(L0 - L1) / N` | kW per customer | load. **Not a fraction**, so excluded by the word "fractional" |

## 3. Assessment

### Relationship to capacity planning

Capacity is consumed by **load**. A customer drawing 5 kW who cuts 20 % frees 1 kW; a customer drawing
1 kW who cuts 20 % frees 0.2 kW. `R_load` counts those correctly. `R_household` counts both as one
"20 %" and so answers a different question: *how large is the typical customer's percentage cut?*
That question matters for bill impact, customer research or programme evaluation. It does not bear on
whether the estate stays under a MW ceiling.

### Composition with the target forecast

Only a load-weighted definition composes with the headline figure:

```
L1 = L0 (1 - R_load)            holds exactly at c̄
L1 = L0 (1 - R_household)       FALSE whenever r_s and L_s covary across segments
```

A response quantity that cannot be multiplied into the forecast it sits beside is an incoherent
companion to that forecast in a capacity readout.

### When the definitions diverge

They coincide only if baseline load is identical across segments or response is uncorrelated with
load. Neither holds, and not by accident: controllable premises (smart thermostats, pool plant) both
draw more load **and** have more to shift. In this estate, household weighting understates the
estate's load reduction by about 19 % (R_load is 1.23 x R_household on every fixture):

| fixture | R_household | R_load | R_load / R_household |
|---|---|---|---|
| visible | 0.06201 | 0.07637 | 1.23 |
| hidden_a | 0.04347 | 0.05340 | 1.23 |
| hidden_b | 0.13924 | 0.17137 | 1.23 |
| hidden_c | 0.04309 | 0.05312 | 1.23 |
| hidden_d | 0.09116 | 0.11199 | 1.23 |

The ratio is stable because the load-response covariance is structural, which means the divergence is
systematic rather than a small-sample artefact.

### The contract wording

> the **estate-wide fractional reduction in peak-window load** attributable to the tariff, at the
> target season's mean cooling degree days.

- "fractional reduction in ... **load**": the numerator and denominator are load. That is `R_load`.
- "**estate-wide**": an aggregate over the estate, not an average of per-segment figures.
- "at the target season's **mean cooling degree days**": fixes the evaluation point at `c̄`. That
  selects `R_load` over `R_season`.

Nothing in the wording suggests equal weighting of customers. Had that been intended, the contract
would need to say something like "the average, across customers, of each segment's fractional
reduction" — the kind of pinning G05 does explicitly ("each store counts once, whatever its size,
because capital is committed per store").

### R_load versus R_season

`R_season` is arguably *more* coherent with the graded forecast, which is a season average. It differs
from `R_load` only where response is strongly nonlinear in CDD (`hidden_c`: 0.0531 vs 0.0711). But the
contract fixes the evaluation point explicitly, and a verifier must grade what the contract says.
`R_load` at `c̄` is the contract-faithful definition. `R_season` is noted as the stronger design
choice for any future contract (see `recommendation.md`).

## 4. Conclusion

**R_load, evaluated at the target season's mean CDD, is the scientifically correct estimand.** It is
denominated in the quantity capacity is bought against, it composes exactly with the headline forecast,
and it is what the contract's wording describes.

**The frozen verifier grades R_household. That is an F8 benchmark defect**, a verifier definition that
contradicts the contract it grades against. It is my error in specifying `_truth_values`, compounded by
using the same household-weighted helper in the oracle and all three reference estimators.

The household-weighted quantity is not meaningless. It is the wrong answer to this contract's question.
