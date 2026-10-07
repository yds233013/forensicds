# Task dependency maps

One map per final task. **These are benchmark-author documentation and were never shown to any agent.**

A note on honesty: the original project materials present a twelve-node chain for several tasks. Where the
artifacts support only a shorter chain, the shorter chain is given. Depth here means *evidence-dependent
decisions*, not file count — every workspace is between 13 and 34 files.

Notation: `→` means "the later step is only motivated once the earlier evidence is in hand".

---

## `p22-gauge-recalibration` — depth 12, the fullest chain in the suite

```
D1  read the published week-24 quality report and the drafted supplier claim
 ↓
D2  reproduce 92.8% first-pass yield from the inspection database
 ↓
D3  observe the step is NOT uniform across gauges / operators / heat lots
 ↓      (a single global cause is already improbable)
D4  enumerate causes with professional motivation: material · tooling · operator · measurement
 ↙              ↓              ↓                     ↘
D5a stratify    D5b tooling-   D5c operator-level    D5d compare the two CMMs
    by heat lot     change         rate                  against the calibration log
 ↘              ↓              ↓                     ↙
D6  resolve: the step coincides with a CMM re-zero, and the offset appears in
    REFERENCE-ARTEFACT measurements — which the supplier's material cannot have affected
 ↓
D7  redefine the object: the conformance-referenced rate, gauge offset removed,
    is what Schedule 3 §3.2 requires
 ↓
D8  rebuild the population the agreement specifies (window · part · strata)
 ↓
D9  implement attribution across ALL named causes (not only the one found)
 ↓
D10 validate against the independent reference-artefact record
 ↓
D11 quantify the residual attributable to material, with the agreement's tolerance
 ↓
D12 apply the threshold → state the supplier action
```

**The load-bearing edge is D5d → D6.** The gauge offset is identifiable *only* because it appears in
reference-artefact measurements. **The load-bearing failure is D9**: all three Gemini trials completed
D1-D8 and D10-D12 correctly for the visible world, and wrote a D9 that could not express a tooling-driven
world.

---

## `p20-noshow-monitoring` — depth 12

```
D1  read the vendor monitoring review and MRM-04
 ↓
D2  reproduce the 0.77 → 0.71 AUC decline
 ↓
D3  note that several scoring bases exist in the evidence
    (as_served · record_features_asof_window · feature_store_current · candidate_v4)
 ↓
D4  four professionally motivated causes for one symptom
 ↙          ↓             ↓              ↘
D5a popu-   D5b feature-  D5c feature    D5d policy feedback
    lation      feed          vintage        (the model drives the reminder
    drift       defect                        programme that changes outcomes)
 ↘          ↓             ↓              ↙
D6  resolve the decomposition — these are not mutually exclusive and must be apportioned
 ↓
D7  fix the evaluation population to the one MRM-04 §4.1 specifies
 ↓
D8  rebuild the metric on that population under each scoring basis
 ↓
D9  compute attribution_auc across the four causes
 ↓
D10 validate (independent cohort / source)
 ↓
D11 the programme effect in the called band, size-stratified
 ↓
D12 apply MRM-04 §4.3-§4.4 → state the permitted action
```

**Observed break point: D9/D11.** Criterion data show `evidence_reconstruction`, `scientific_object`,
`estimator_implementation` and `independent_validation` passing while `quantitative_results` fails — and
in all three Claude trials `decision` (D12) passes anyway.

---

## `g50-courier-boost-rollout` — depth 12

```
D1  read the readout claiming −4.0 points and the rollout decision memo
 ↓
D2  reproduce the phase-2 arm contrast from the warehouse
 ↓
D3  read the dispatch-offer-queue note: a boosted offer pre-empts an unboosted one
 ↓
D4  recognise the arms share one market-hour courier pool
 ↓
D5  realise the incumbent capacity check CANNOT FAIL (same couriers both arms, 0.08% gap)
 ↓
D6  separate the two quantities: arm contrast ≠ effect of turning Boost on for everyone
 ↓
D7  locate the design that identifies the rollout quantity: the phase-1 market-level soak
    (the design the incumbent analyst rejected as underpowered)
 ↓
D8  rebuild the estate-weighted estimand with PRE-programme weights
 ↓
D9  estimate at the market level, pre-period adjusted
 ↓
D10 interval at the unit of assignment (market), not the order
 ↓
D11 measure the surviving channel (courier-supply response) in phase 1
 ↓
D12 apply the £0.19 / £12.70 break-even (1.4961 pp) → roll out or decline
```

**Observed break point: D6, the earliest of any task.** All three valid Gemini trials reported
`programme_effect_pp` identical to the arm contrast and never separated the two objects.

---

## `g10-censored-demand` — depth 11

```
D1  read the category review proposing cuts in all eight categories
 ↓
D2  notice the checkable absurdity: ice cream down, in summer, while sales are up
 ↓
D3  reproduce the baselines and find they use observed sales
 ↓
D4  discover LEAN-26's go-live and its availability effect
 ↓
D5  recognise sales = min(demand, availability), and that LEAN-26 CAUSED the censoring
 ↓
D6  recognise that filtering to stockout-free days selects on the outcome
 ↓
D7  reconstruct latent demand from inventory + stockout + order records
 ↓
D8  re-estimate per-category baselines on the reconstruction
 ↓
D9  validate (hold-out period or independent source)
 ↓
D10 propagate into the buy plan
 ↓
D11 decide on the LEAN-26 extension
```

**Observed:** Gemini trajectories reach D5-D7 — one recomputed ice cream from −5.3% to **+9.96%** — and
still fail. Break point **UNKNOWN** (binary reward).

---

## `p31-fill-rate-dispute` — depth 10

```
D1  read the 97.7% report, the supplier's 91.5%, and the supply agreement
 ↓
D2  reproduce 97.7% from the order/shipment tables
 ↓
D3  enumerate the definitional axes: aggregation level · denominator · returns/substitutions
 ↓
D4  build the bridge between the two numbers across those three axes
 ↓
D5  read the agreement to find which definition it fixes
 ↓
D6  recompute at the CONTRACTUAL unit (not the reporting unit)
 ↓
D7  evaluate the account-level floor per account
 ↓
D8  determine breach / no breach
 ↓
D9  position on the £1.8m claim
 ↓
D10 separately, review the bonus gate (which uses the other definition)
```

**Observed break point: D5-D8.** Two Gemini trials and one Claude trial passed
`quantitative_results` (D4/D6 correct) and failed `identification` and `decision`.

---

## `02-renewal-risk-regression` — depth 9

```
D1  read the Sales note, the monitoring, and the February evaluation
 ↓
D2  reproduce the offline/online gap
 ↓
D3  enumerate candidates: population shift · label maturity · pipeline change · leakage
 ↓
D4  inspect how health features are assembled from the store
 ↓
D5  find that feature values are read from current state, not as-of label time
 ↓
D6  repair the pipeline with a point-in-time join
 ↓
D7  retrain
 ↓
D8  re-evaluate on the corrected matrix
 ↓
D9  decide on the Q3 retrain release
```

---

## `g05-sco-rollout-gate` — depth 10

```
D1  read the business case and its gate definition
 ↓
D2  reproduce the incumbent gate figure
 ↓
D3  inspect the wave schedule → adoption is staggered and readiness-ordered
 ↓
D4  recognise the comparison group contains already-treated stores
 ↓
D5  recognise effects vary with exposure length
 ↓
D6  redefine the comparison: not-yet-treated controls only
 ↓
D7  rebuild the store-week panel on the business case's window
 ↓
D8  estimate
 ↓
D9  quantify uncertainty at the unit of adoption
 ↓
D10 apply the gate threshold → release or hold tranche 2
```

---

## `g24-recommender-ope` — depth 9

```
D1  read the offline gate and the AB-1182 readout that disagrees in sign
 ↓
D2  reproduce the gate's ranking
 ↓
D3  inspect the logs → only the deployed policy's choices are recorded
 ↓
D4  recognise the gate measures something other than online policy value
 ↓
D5  determine the evaluable population (where the logging policy had support)
 ↓
D6  estimate policy value with exposure correction
 ↓
D7  handle v7_pd, which has no online test at all
 ↓
D8  quantify uncertainty
 ↓
D9  decide which ranker serves the home row
```

---

## `g36-tou-capacity-gate` — depth 8 (genuinely shorter)

```
D1  read the planning memo and the regulator's 10% reserve
 ↓
D2  reproduce the per-customer peak figure
 ↓
D3  inspect tariff assignment history → customers have migrated onto TOU
 ↓
D4  recognise enrolment is not random and correlates with consumption
 ↓
D5  fix the population and the measurement window
 ↓
D6  recompute mean peak-window kW on that population
 ↓
D7  compare with the 3.057 kW cap
 ↓
D8  procure / do not procure
```

**This chain is short and is presented as short.** There is one pivot, not two.

---

## `g08-forecast-accuracy-vintages` — depth 9

```
D1  read the September accuracy review recommending v3's retirement
 ↓
D2  reproduce the WAPE comparison from the mart
 ↓
D3  inspect the actuals table → it is restated over time
 ↓
D4  inspect forecast origin timestamps → v3 and v4 forecast at different times
 ↓
D5  recognise that scoring against latest actuals mixes error with revision
 ↓
D6  define a consistent vintage (as-of forecast origin)
 ↓
D7  rebuild the accuracy computation on that vintage
 ↓
D8  re-rank the models
 ↓
D9  decide on v3's retirement
```

---

## Cross-task summary

| task | depth | forced pivots | observed break point | basis |
|---|---|---|---|---|
| `p22` | 12 | 1-2 | **D9** (procedure cannot express another mechanism) | criterion notes |
| `p20` | 12 | 2 | **D9/D11** (quantity), D12 passes anyway | criteria |
| `g50` | 12 | 2 | **D6** (never separated the objects) | verifier stdout |
| `g10` | 11 | 2 | UNKNOWN (reaches D5-D7) | binary reward |
| `p31` | 10 | 2 | **D5-D8** (quantity right, licence wrong) | criteria |
| `g05` | 10 | 1-2 | UNKNOWN | binary reward |
| `02` | 9 | 1 | UNKNOWN | binary reward |
| `g24` | 9 | 1 | UNKNOWN (reaches D3-D4) | binary reward |
| `g08` | 9 | 1 | UNKNOWN | binary reward |
| `g36` | 8 | 1 | UNKNOWN | binary reward |

**Six of ten break points are UNKNOWN, and that is the instrumentation gap this dossier keeps returning to.**
