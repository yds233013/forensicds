# Final-10 curation table

Selection criteria applied in order: (1) real distribution, (2) scientific validity, (3) meaningful
headroom, (4) coherent capability slice, (5) mechanism diversity, (6) verifier robustness,
(7) trajectory richness, (8) non-redundancy, (9) scalability to training environments.

**Selection was not by difficulty rank.** Two tasks with pass@3 = 0 were *excluded* (see below) and one
task with a pass is *included*, because mechanism coverage and verifier strength dominated.

## Included

| # | task | domain / professional workflow | scientific mechanism | dep. depth | pivots | verifier | Gemini (valid / pass) | pass@3 | RL seed | include because |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `02-renewal-risk-regression` | B2B SaaS revenue DS; renewal-risk model in production | point-in-time correctness / label leakage | 9 | 1 | re-train + re-evaluate, hidden extract | 3 / 0 | **0%** | strong | only temporal-reconstruction task; has an explicit-invariant ablation that also scored 0/3 |
| 2 | `g05-sco-rollout-gate` | Retail FP&A; capital committee tranche gate | identification under staggered adoption | 10 | 1–2 | gate figure + decision | 4 / 0 | **0%** | strong | only staggered-adoption task; decision is a capital release |
| 3 | `g10-censored-demand` | Retail demand planning; Q3 buy plan | informative censoring endogenous to the programme | 11 | 2 | multi-category baselines + decision | 3 / 0 | **0%** | **strongest** | covers the supply-chain blueprint; censoring created by the intervention being evaluated |
| 4 | `g24-recommender-ope` | Personalisation analytics; ranker selection | off-policy evaluation under a logging policy | 9 | 1 | policy value + decision | 3 / 0 | **0%** | strong | only OPE task; closest coverage of selective-label blueprint |
| 5 | `g36-tou-capacity-gate` | Regulated utility resource planning | population/exposure definition under tariff migration | 8 | 1 | scalar gate vs regulator reserve | 3 / 0 | **0%** | moderate | only regulated-utility and only capacity-constrained procurement decision |
| 6 | `p20-noshow-monitoring` | Healthcare model risk management | policy feedback + feature vintage + drift decomposition | 12 | 2 | **criterion-level**, 4 worlds | 3 / 0 | **0%** | **strongest** | only governed-decision-space task; 4-way competing-cause decomposition |
| 7 | `p22-gauge-recalibration` | Manufacturing quality engineering | measurement-system bias vs process change | 10 | 1–2 | **criterion-level**, 4 worlds | 3 / 0 | **0%** | **strongest** | only instrument-as-cause task; carries the clearest procedure-overfitting evidence in the suite |
| 8 | `p31-fill-rate-dispute` | Retail supply chain + commercial/legal | contractual metric definition reconciliation | 10 | 2 | **criterion-level**, 4 worlds | 3 / 0 | **0%** | strong | only task where the scientific object is fixed by a contract, not chosen |
| 9 | `g50-courier-boost-rollout` | Delivery marketplace experimentation | interference / unit of intervention | 12 | 2 | **criterion-level, re-executes the agent's command on 5 worlds** | see results | — | **strongest** | only interference task; only re-execution verifier; deepest pre-exposure validation |
| 10 | `g08-forecast-accuracy-vintages` | Energy trading analytics engineering | data vintage / restated actuals | 9 | 1 | accuracy pack + decision | 3 / 1 | 100% | moderate | only vintage/as-of task; mechanism lives in the temporal semantics of the evidence table |

## Excluded, with reasons

| task | valid / pass | pass@3 | why excluded |
|---|---|---|---|
| `02-renewal-risk-regression__explicit-invariant` | 3 / 0 | 0% | **Not a separate task** — same world as #1 with the invariant stated outright. Retained as an *ablation* and reported as evidence, not counted in the ten. |
| `g34-fleet-reliability-gate` | 3 / 2 | 100% | Strongest excluded candidate. Competing-risks / wrong-statistical-object is a genuinely distinct mechanism, but 2 of 3 trials passed, so it contributes little headroom, and #10 (`g08`) adds a mechanism nothing else covers while being harder. |
| `g35-dispatch-priority-gate` | 3 / 3 | 100% | Saturated. |
| `g42-contractor-safety-rate` | 3 / 3 | 100% | Saturated. |
| `g44-screening-precision` | 3 / 2 | 100% | Calibration/threshold mechanism overlaps `p20` and `g36`; 2/3 passed. |
| `g41-service-parts-rebalancing` | 3 / 1 | 100% | Inventory rebalancing overlaps `g10` and `p31` on the supply-chain surface; oracle history shows verifier instability (`g41-oracle-v2`, `-v3`, `-probe2` all recorded 0 before repair), so verifier robustness is the weakest in the pool. |
| `03-lead-score-evaluation` | 3 / 3 | 100% | Saturated. |
| `04-retention-metrics-regression` | 3 / 1 | 100% | Metric-regression mechanism overlaps `p31`; weaker decision stake. |
| `05-onboarding-experiment-readout` | 3 / 3 | 100% | Saturated. |
| `06-usage-statement-close` | 3 / 3 | 100% | Saturated. |
| `01-revenue-reconciliation` | 3 / 2 | 100% | Reconciliation overlaps `p31`; 2/3 passed. |
| `g36-tou-capacity-gate-v1.1` | 0 | — | Superseded working copy of #5; not a distinct task. |

## New tasks considered and deliberately not built

Part XI of the assignment directs that a blueprint already covered strongly must not be rebuilt. Audit
result:

| blueprint | already covered by | verdict |
|---|---|---|
| 1 — SaaS retention / policy feedback / changing observation process | `02` (point-in-time correctness) + `p20` (policy feedback) | **covered — not built** |
| 2 — supply chain / stockout-censored demand / procurement | `g10` | **covered — not built** |
| 3 — fintech / delayed + selective labels | `g24` (logging-policy selection) partially; `02` (label timing) partially | **partially covered — see below** |
| 4 — product experiment / repeated measures / unit of analysis | `g50` + `g05` | **covered — not built** |
| 5 — deployment / calibration / threshold / population shift | `p20` + `g36` + (excluded) `g44` | **covered — not built** |

The one capability **not** present anywhere in the pool is an *identification-removed* sibling world in
which the professionally correct answer is justified deferral ("not identifiable from the available
evidence"). That is a sibling-world *variant*, not a distinct task, and it cannot be added to an already
exposed task without invalidating its exposure record. It is therefore carried as the highest-priority
generation template in the 10 → 1,000 scale plan rather than built as an eleventh task competing for a
slot. Building a redundant fraud/risk task to host it would have displaced one of the ten above while
duplicating `g24`'s selective-observation mechanism.
