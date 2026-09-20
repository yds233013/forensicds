# G36 formal designs — top three

## D1 — TOU tariff peak-load forecast  (SELECTED)

| element | specification |
|---|---|
| unit | household |
| time unit | service day within a summer peak season (60 days) |
| historical regime | three summers, flat tariff, all households |
| intervention | mandatory time-of-use tariff, effective before the target summer |
| target regime | target summer, every household on TOU |
| target population | the whole residential estate (not the pilot) |
| outcome | mean peak-window load per household (kW) |
| **forecast estimand** | `E[ load \| all households on TOU, target-summer weather ]` |
| decision threshold | procure peaking capacity iff forecast >= 2.900 kW |
| stable mechanism | weather -> load (air conditioning physics) |
| unstable mechanism | tariff -> behaviour (peak shifting) |
| evidence for the unstable part | voluntary pilot, randomised TOU vs control inside the opt-in group |
| transport problem 1 | opt-in households are more responsive than the population |
| transport problem 2 | pilot summer was mild (CDD 8.6), target is hot (CDD 12.4); response fades in heat |

## D2 — Algorithmic repricing demand forecast  (runner-up, simulated, rejected)

| element | specification |
|---|---|
| unit | store |
| time unit | week |
| historical regime | manager-set prices, endogenous to demand |
| intervention | algorithmic repricing at a published rule, deeper discounts |
| target regime | next quarter, algorithm live estate-wide |
| outcome | units index vs status quo |
| **forecast estimand** | `E[ units \| algorithm pricing, estate mix ]` |
| stable mechanism | base demand and seasonality |
| unstable mechanism | price -> demand, whose historical coefficient is confounded |
| evidence | randomised price test in volunteer stores at 10 % discount |
| transport problem 1 | test stores skew large-format |
| transport problem 2 | algorithm discounts to 18 %, beyond the tested range |

**Rejected on measurement**: accepted-estimator sd is 8 % of the quantity (vs 0.5 % for D1), one
insight alone already fixes every decision, and the accepted estimator itself gets a decision wrong.

## D3 — Scheduler change, cluster capacity  (formal design only, not simulated)

| element | specification |
|---|---|
| unit | job |
| time unit | hour |
| historical regime | legacy scheduler |
| intervention | new bin-packing scheduler |
| outcome | p95 job completion time |
| stable mechanism | job size -> service time |
| unstable mechanism | queueing, via placement |
| **the trap** | queue depth is a strong historical predictor **and a descendant of the scheduler** |
| evidence | shadow-mode output on a subset of clusters |

**Not carried forward this round**: the target quantity depends on next quarter's workload mix,
which is itself a forecast. That nests a second forecasting problem inside the first and makes the
estimand harder to state cleanly than D1's. The mediator trap is excellent and should be revisited
if D1 is ever exhausted.
