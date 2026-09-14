# Generation 3: hardness scoring and top-15 selection

Scores are 1–5 (5 = best for a hard, valid benchmark task) and are the author's judgement from the candidate
descriptions in `research/gen3_candidate_pool.md`. They are design-time estimates, not model results.

## Rubric

| Dimension | 5 means |
|---|---|
| Realism | a senior data scientist would recognise this incident from real work |
| DS depth | requires substantive data-science reasoning, not only engineering |
| Investigation horizon | 30–80 meaningful actions are natural |
| Statistical reasoning | requires estimand, sampling, censoring or causal reasoning |
| Multi-source reconciliation | the correct rule needs several evidence sources and data |
| Repair breadth | several components must change for principled reasons |
| Natural wrong paths | the most obvious repair after recognising the failure class is wrong |
| Aggregate non-diagnosticity | several wrong repairs produce believable headline numbers |
| Verifier determinism | objectively gradable without enforcing a coding style |
| Hidden-fixture generalisability | hidden extracts can vary documented mechanisms without new rules |
| Distinctness | little overlap with Tasks 01–06 |
| Expected Gemini difficulty | expected to defeat a fast frontier agent for principled reasons |

Risk columns:
- **Leakage:** risk that an agent-facing artifact states the invariant or acts as an answer key. L / M / H.
- **Underspecification:** risk that a defensible alternative is rejected. L / M / H.
- **Implementation cost:** L / M / H.

## Composite

The composite is a weighted sum of the 12 dimensions:
- **Weight 2:** natural wrong paths, DS depth, expected difficulty.
- **Weight 1.5:** statistical reasoning, aggregate non-diagnosticity, verifier determinism.
- **Weight 1:** the others.

It then subtracts 0 / 3 / 6 for L / M / H leakage and underspecification risk. Implementation cost is reported but not
penalised.

The ranking is **not** used mechanically. It is not intended to reward complexity: a task scores high only if its wrong
paths are natural *and* it is gradable.

## Ranked table

| Rank | Candidate | Real | Depth | Horizon | Stat | Recon | Breadth | Wrong paths | Agg non-diag | Verifier | Hidden gen | Distinct | Exp. difficulty | Leakage | Underspec | Impl cost | Composite |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | G11 Multi-feature training-serving skew | 5 | 5 | 5 | 3 | 5 | 5 | 5 | 4 | 5 | 5 | 3 | 5 | L | L | H | 76.0 |
| 2 | G10 Censored demand (stockouts) | 5 | 5 | 5 | 4 | 4 | 4 | 5 | 5 | 4 | 4 | 5 | 5 | L | M | H | 73.5 |
| 3 | G01 Collections label maturity+policy+acquired book | 5 | 5 | 5 | 4 | 5 | 4 | 5 | 5 | 5 | 4 | 3 | 5 | M | M | H | 71.0 |
| 4 | G21 Churn-save survival | 5 | 5 | 5 | 5 | 4 | 4 | 5 | 5 | 4 | 4 | 4 | 5 | M | M | M | 71.0 |
| 5 | G24 Recommender feedback-loop OPE | 5 | 5 | 5 | 5 | 4 | 4 | 5 | 5 | 4 | 4 | 4 | 5 | M | M | H | 71.0 |
| 6 | G02 Better AUC worse loss ratio (sampling weights) | 5 | 4 | 4 | 5 | 4 | 3 | 5 | 5 | 5 | 4 | 5 | 4 | L | M | M | 70.5 |
| 7 | G08 Forecast backtest on revised vintages | 5 | 5 | 4 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | 3 | 4 | L | M | M | 70.0 |
| 8 | G23 Readmission episodes | 5 | 5 | 5 | 4 | 4 | 4 | 5 | 5 | 5 | 4 | 5 | 4 | M | M | M | 70.0 |
| 9 | G30 Delayed-label fraud reject inference | 5 | 5 | 5 | 5 | 4 | 4 | 5 | 5 | 4 | 4 | 2 | 5 | M | M | H | 69.0 |
| 10 | G26 Twin incident negative control | 5 | 4 | 5 | 4 | 4 | 3 | 5 | 4 | 5 | 4 | 4 | 4 | L | M | M | 67.5 |
| 11 | G05 Staggered rollout TWFE sign flip | 5 | 5 | 4 | 5 | 3 | 3 | 5 | 5 | 4 | 4 | 5 | 4 | M | M | M | 67.0 |
| 12 | G20 Telematics segmentation firmware/drift | 5 | 4 | 5 | 3 | 4 | 4 | 5 | 5 | 4 | 4 | 4 | 4 | L | M | H | 67.0 |
| 13 | G17 B2B entity resolution acquisitions/resellers | 5 | 4 | 5 | 3 | 5 | 4 | 5 | 5 | 5 | 4 | 3 | 4 | M | M | H | 65.5 |
| 14 | G25 Search judgment-pool bias | 5 | 4 | 4 | 4 | 3 | 3 | 4 | 5 | 4 | 4 | 5 | 4 | M | M | M | 61.5 |
| 15 | G03 Leaky eval via linked entities/re-opens | 5 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | M | M | M | 58.5 |
| 16 | G14 Marketplace refunds/promo allocation | 5 | 4 | 4 | 2 | 4 | 3 | 4 | 5 | 5 | 4 | 3 | 3 | M | M | M | 57.0 |
| 17 | G29 Newsvendor decision quantity | 4 | 4 | 3 | 4 | 3 | 2 | 4 | 4 | 5 | 4 | 5 | 3 | M | M | L | 56.5 |
| 18 | G07 Hierarchical forecast re-hierarchy | 4 | 4 | 4 | 3 | 3 | 3 | 4 | 4 | 2 | 3 | 5 | 3 | L | H | H | 51.5 |
| 19 | G15 Cohort LTV FX/refunds | 4 | 3 | 3 | 2 | 3 | 2 | 3 | 4 | 5 | 4 | 1 | 2 | L | L | L | 49.5 |
| 20 | G06 Holdout contamination by merges | 4 | 3 | 3 | 3 | 3 | 2 | 3 | 4 | 5 | 4 | 1 | 2 | M | L | L | 48.0 |
| 21 | G04 Switchback carryover | 4 | 4 | 3 | 4 | 3 | 3 | 4 | 4 | 3 | 3 | 2 | 3 | M | H | M | 47.5 |
| 22 | G18 Claims voids/replacements | 5 | 3 | 3 | 2 | 3 | 2 | 3 | 4 | 5 | 4 | 1 | 2 | M | L | L | 47.5 |
| 23 | G16 PSP cost allocation retro fees | 4 | 3 | 3 | 2 | 3 | 2 | 3 | 4 | 5 | 4 | 2 | 3 | M | M | M | 46.5 |
| 24 | G13 Monitoring refit bins | 4 | 3 | 2 | 3 | 2 | 2 | 3 | 3 | 5 | 3 | 3 | 2 | M | L | L | 45.5 |
| 25 | G19 Geospatial boundary vintages | 4 | 3 | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 3 | 5 | 2 | L | M | H | 45.0 |
| 26 | G22 Survey nonresponse | 4 | 3 | 3 | 4 | 2 | 2 | 3 | 4 | 3 | 3 | 5 | 3 | M | H | L | 44.5 |
| 27 | G09 DST anomaly storm | 4 | 3 | 3 | 3 | 3 | 2 | 3 | 3 | 4 | 3 | 4 | 2 | M | M | M | 44.0 |
| 28 | G12 Embedding version mismatch | 4 | 3 | 3 | 2 | 3 | 2 | 3 | 3 | 3 | 3 | 5 | 2 | M | M | M | 42.0 |
| 29 | G28 Multi-touch attribution cross-device | 4 | 3 | 3 | 2 | 3 | 2 | 3 | 4 | 4 | 3 | 2 | 3 | H | M | M | 41.0 |
| 30 | G27 Fraud drift not skew (neg control) | 4 | 3 | 3 | 3 | 3 | 1 | 3 | 3 | 3 | 3 | 4 | 3 | M | H | M | 40.5 |

## Top-15 selection

The raw top 15 by composite was G11, G10, G01, G21, G24, G02, G08, G23, G30, G26, G05, G20, G17, G25, G03. For
distribution diversity **G03 is replaced by G14** (marketplace allocation), because otherwise no financial or economic
allocation task survives.

- G03 overlaps Tasks 01 and 02 (identity, as-of labels) and G30 (label back-fill).
- G14 is the strongest "totals reconcile, attribution is wrong" candidate.

G30 is kept despite overlap with G01 (delayed labels) because it adds selective labels with an exploration sample and
label *revision* (representment) in a fraud/risk setting. The tournament must decide whether both survive.

| # | Candidate | Slice | Design file |
|---|---|---|---|
| 1 | G11 multi-feature training-serving skew | production ML / feature store | `gen3_designs/G11_training_serving_skew.md` |
| 2 | G10 censored demand from stockouts | forecasting + missing data | `gen3_designs/G10_censored_demand.md` |
| 3 | G01 collections model under label maturity, policy and acquired book | ML evaluation + censoring | `gen3_designs/G01_collections_label_maturity.md` |
| 4 | G21 churn-save offer survival analysis | survival + causal | `gen3_designs/G21_churn_save_survival.md` |
| 5 | G24 recommender feedback-loop off-policy evaluation | recommender + causal | `gen3_designs/G24_recommender_ope.md` |
| 6 | G02 better AUC, worse loss ratio | calibration / ML evaluation | `gen3_designs/G02_calibration_sampling_weights.md` |
| 7 | G08 forecast backtest on revised vintages | forecasting evaluation | `gen3_designs/G08_forecast_vintages.md` |
| 8 | G23 readmission labels on episodes | ML evaluation + grain + competing risk | `gen3_designs/G23_readmission_episodes.md` |
| 9 | G30 delayed-label fraud with reject inference | fraud / risk | `gen3_designs/G30_fraud_reject_inference.md` |
| 10 | G26 twin-incident negative control | product analytics, no-bug control | `gen3_designs/G26_twin_incident_negative_control.md` |
| 11 | G05 staggered rollout, TWFE sign flip | causal inference | `gen3_designs/G05_staggered_rollout_did.md` |
| 12 | G20 telematics trip segmentation | time-series segmentation + DQ | `gen3_designs/G20_telematics_segmentation.md` |
| 13 | G17 B2B entity resolution through acquisitions and resellers | entity resolution | `gen3_designs/G17_b2b_entity_resolution.md` |
| 14 | G25 search judgment-pool bias | ranking evaluation | `gen3_designs/G25_search_judgment_pool.md` |
| 15 | G14 marketplace refunds and promo allocation | economic allocation | `gen3_designs/G14_marketplace_allocation.md` |

**Not selected, with notable alternates:**
- **G29** (newsvendor decision quantity): a novel decision-analytics slice with low cost. It is the first alternate if a
  design fails the tournament.
- **G03** (leaky grouped evaluation).
- **G04** (switchback carryover): overlaps Task 05, and the estimator is underspecified.
- **G07** (hierarchical reconciliation): the method is underspecified.
- **G27** (second negative control): weak gradability.
