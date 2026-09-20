# G36 legitimate estimator families

Three routes to the same estimand, differing in where the aggregation happens.

| family | machinery | visible | hidden_a | hidden_b | hidden_c | hidden_d |
|---|---|---|---|---|---|---|
| **V1 decompose then transport** | per-segment stable curve x per-segment transported response, aggregated over the population | -0.0126 | -0.0027 | +0.0070 | +0.0105 | +0.0130 |
| **V2 segment then aggregate** | same ingredients, response applied to the segment forecast before weighting | -0.0126 | -0.0027 | +0.0070 | +0.0105 | +0.0130 |
| **V3 mixture form** | population-level base minus population-level reduction, both mixed over segments | -0.0126 | -0.0027 | +0.0070 | +0.0105 | +0.0130 |

**Maximum disagreement between valid families: 0.0000 kW.** They are algebraically identical
rearrangements of the same estimand, which is the honest description - they are not three
independent methods, they are three ways to write one.

**Sampling behaviour** (12 replications per regime, fresh draws):

| regime | bias | sd | decision margin | margin in sd |
|---|---|---|---|---|
| visible | +0.0032 | 0.0142 | 0.0976 | **6.9** |
| hidden_a_strong_selection | +0.0063 | 0.0211 | 0.0748 | **3.5** |
| hidden_b_flat_in_heat | -0.0016 | 0.0147 | 0.0798 | **5.4** |
| hidden_c_fades_in_heat | +0.0064 | 0.0118 | 0.0429 | **3.6** |
| hidden_d_high_response | +0.0045 | 0.0130 | 0.1925 | **14.9** |

Every margin is at least 3.5 sd. G34's near-threshold defect was 0.14 sd; this was checked
explicitly before any operating point was fixed.

## An honest limitation

The brief asks for **two scientifically legitimate routes**. What the simulation demonstrates is one
estimand expressed three ways, not three independent estimators. Genuinely distinct alternatives
exist in principle and should be built and measured during implementation:

- a **partial-pooling / hierarchical** estimator that shrinks thin segments toward the pooled
  response instead of estimating each independently;
- a **regression form** that fits load on CDD, segment and a TOU indicator with a CDD x TOU
  interaction, weighting to the population mix - a different estimating equation reaching the same
  target;
- a **doubly-robust** combination of the outcome model and an opt-in propensity model.

These are expected to agree, but **that expectation has not yet been measured**, and a build must
not assume it. If they materially disagree, the tolerance and the accepted set both need revisiting
(kill criterion K9).
