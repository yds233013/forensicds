# Phase 2 — real production failure structures (operations / risk / industrial half)

Verified against primary or primary-quoting sources. Only mechanisms with a documented instance are
listed; each maps to one or more candidate incidents.

| # | mechanism | documented instance | maps to |
|---|---|---|---|
| A1 | censored demand under stockouts | FreshRetailNet-50K (Meituan, 50k series/898 stores, stockout-annotated): "Censored sales data during stockouts, where unobserved demand creates systemic policy biases"; latent-demand model reduces "systematic demand underestimation from 7.37% to near-zero bias" — arXiv:2505.16319 | G10 (existing), P28 |
| A2 | assortment substitution / walk rate | **Walmart "Project Impact"**: ~15 % of SKUs cut from 2009, comp sales fell seven consecutive quarters, ~8,500 items (~11 % of assortment) restored by April 2011 — scdigest.com/ontarget/11-04-14-2.php | P01 |
| A3 | bullwhip variance amplification | Lee, Padmanabhan & Whang, *Sloan Management Review* 38(3) 1997 / *Management Science* 43(4):546 — P&G Pampers order variance amplifying upstream | new candidate |
| A4 | optimisation on a wrong feasible set (master data) | **Target Canada**: item-master dimensions, case quantities and cost currency wrong at scale; "Store shelves sat empty, while warehouses were bursting with inventory"; ~133 stores closed 2015 | P27 |
| A6 | settlement vintages / resettlement | **ERCOT** Initial → Final (~55 d) → True-Up (~180 d); Market Notice M-B042424-06 resettles operating day 28 Feb 2024 after a price correction directed 23 Apr, invoiced 8 May — ercot.com/services/comm/mkt_notices/M-B042424-06 | G08 (existing), P04 |
| A7 | official-statistics revisions | BLS CES benchmark: preliminary −818,000 (Aug 2024) vs final −598,000 to March 2024 employment; Croushore & Stark real-time vintage dataset (*J. Econometrics* 105(1)) | P04 |
| A8 | reporting backfill / right truncation | real-time R_t underestimated because recent incidence is incomplete — PMC9931334; CDC MMWR nowcasting, measles 2025–26 | P26, P29 |
| A9 | **measurement-system change (metering)** | Leferink, Keyer & Melentjev (Univ. Twente/AUAS, IEEE EMC Mag. 2017): of nine static meters, five read up to **+582 %** and two **−30 %** vs actual; Dutch metrology institute confirmed; ≥750,000 households affected; error direction tracked sensor type | **P24**, P03 |
| A10 | measurement-system change (assay) | high-sensitivity troponin: MI incidence **18 % → 22 %** of cohort (+268 % for non-coronary injury) — PMID 23164485; **High-STEACS** stepped-wedge: 17 % of 10,360 reclassified with **no reduction in subsequent MI or CV death at 1 year** — Lancet 2018 | **P18**, P17 |
| A11 | definition change in a regulated metric | IEEE 1366 "2.5 beta" Major Event Day exclusion: reported SAIDI can improve while customer-experienced minutes worsen; the exclusion threshold is itself a five-year rolling statistic | P03, P17 |
| A12 | gauge R&R: measurement variance charged to the process | ASQ GR&R reference; practitioner statement that a poor measurement system compromises "quality gates, capability studies, control charts" | **P22**, P23 |
| A13 | **selective labels in credit** | Lakkaraju, Kleinberg, Leskovec, Ludwig & Mullainathan, **KDD 2017**: "if a defendant is denied bail, then there is no opportunity for them to commit a crime"; the algorithm "will falsely but confidently learn"; *contraction* as the evaluation method. Industry: reject inference exists for this reason (MathWorks: "Bias can result if a credit scorecard model is built only on accepts") | **P13** |
| A14 | champion/challenger without a counterfactual | payments practice: blocked transactions "have unknown true outcomes because the payment was never completed, so computing a full production precision-recall curve requires counterfactual analysis" | **P14**, P20 |
| A15 | label latency in fraud | Visa dispute window generally **120 days**, up to **540** in some fraud scenarios; VAMP thresholds computed on immature ratios | **P29**, P14 |
| A16 | **performative prediction / feedback** | Perdomo, Zrnic, Mendler-Dünner & Hardt, **ICML 2020**: "When predictions support decisions they may influence the outcome they aim to predict"; predictions "calibrated not against past outcomes, but against the future outcomes that manifest from acting on the prediction". Amazon repricer loop drove a book to **$23,698,655.93**. Google Flu Trends over-predicted ILI ~2× in Feb 2013 via "algorithm dynamics" | **P20**, P09, P13 |
| A17 | **proxy objective** | Obermeyer, Powers, Vogeli & Mullainathan, **Science 366(6464):447** — algorithm applied to ~200 M people/year predicted **cost** as a stand-in for **illness**; remedying it raises Black patients receiving extra help from **17.7 % to 46.5 %** | **P12** |
| A18 | exposure denominators + small-count noise | Hallowell et al., *Professional Safety* 66(4):28 — changes in **TRIR are 96–98 % random variation**; contractor-inclusion rules are elastic | (phase-1 G42), new candidate |
| A19 | competing risks + reporting lag in warranty | reporting-delay-adjusted warranty prediction (Kalbfleisch & Lawless lineage); "failed-but-not-reported" events; build-month × months-in-service triangles | G34 (existing), P26 |
| A20 | survivorship in fleet data | Backblaze Drive Stats: ≥**50,000 drive-days**/quarter for statistical relevance; lifetime tables drop retiring cohorts | new candidate |
| A21 | **IBNR / development-pattern break** | **Milliman 2024** commercial auto: one-year reserve development **8.0 %**, adverse for **every accident year back to 2016**; "historical data have not been representative of the higher trends observed in recent years"; ~$15.8 bn casualty adverse development in 2024, ~$62 bn cumulative 2015–24. Diagnostic: calendar-year diagonals + Berquist-Sherman | **P26** |
| A22 | risk-adjuster endogeneity (coding intensity) | MedPAC March 2025: MA coding intensity ~16 % above comparable FFS (~10 % net of the statutory adjustment); ~$22 bn of ~$76 bn higher 2026 MA payments. KFF: HRA-only diagnoses "even when there are no related services delivered" | **P19**, P18 |
| A23 | denominator/definition change in a regulated outcome | growth in **observation stays accounted for ~40 %** of the measured readmission reduction attributed to HRRP — JAMA Netw Open 2022 | **P18** |
| A24 | **verification bias** | Catalogue of Bias entry; Begg–Greenes correction; applied in IP1-PROSTAGRAM. Reference standard applied mainly to index-positives inflates sensitivity | **P21** |
| A25 | capacity at the wrong peak / correlated failure | CAISO-CPUC-CEC Aug 2020 root cause: planning targets "have not evolved to keep pace with climate change-induced extreme weather events". FERC/NERC Uri final report: ~20,000 MW firm load shed; freezing = **44 %** of unplanned outages. ERCOT **4CP** allocates transmission cost on four 15-minute coincident peaks | **P25** |
| A26 | non-linear economics | take-or-pay / minimum-volume shortfall payments; coincident-peak demand charges; VAMP penalty tiers as a step function of a ratio | **P07** |
| A27 | hierarchical reconciliation | Wickramasuriya, Athanasopoulos & Hyndman **MinT**; FPP: bottom-up omits information where "higher aggregation levels … feature a preferable signal-to-noise-ratio", top-down "necessarily introduces bias" | **P04** |
| A28 | optimal but not recoverable | **Southwest Airlines Dec 2022**: ~**16,700** cancellations in ten days; crew scheduling could not re-solve at scale; **$140 M** DOT settlement. **UK rail May 2018**: ORR inquiry found the System Operator "did not take sufficient action, especially in the critical period of autumn 2017" and "over-optimism" about recovering missed deadlines | **P27** |
| A29 | savings that never reach the ledger | NAO: of DfT's reported **£892 m**, only **43 %** fairly represented realised cash savings, **35 %** possibly overstated; Home Office 17 % with significant concerns | new candidate |
| A30 | deemed vs realised savings | Fowlie, Greenstone & Wolfram, **QJE 133(3):1597** — RCT, ~30,000 Michigan households: model-projected savings ≈**2.5×** actual; upfront costs ≈2× realised savings | new candidate |

## Wrong analyses that were internally coherent and passed the team's normal checks

These justify the design requirement that L1 coherence checks must be *passable* by the wrong route.

1. **Epic Sepsis Model.** External validation on 38,455 hospitalisations: AUC **0.63** (vendor reported
   0.76–0.83); sensitivity 33 % at the deployed threshold; **missed 1,709 of 2,552 sepsis patients (67 %)**
   while alerting on 18 % of all admissions; "would still need to evaluate 8 patients to identify a single
   patient with eventual sepsis" — JAMA Intern Med 2021. Developed on 405,000 encounters, embedded in the
   market-leading EHR, live at hundreds of sites. Nothing in the pipeline failed.
2. **JPMorgan CIO VaR model change.** A model change approved through the bank's own governance and
   disclosed in advance to the OCC dropped CIO VaR by a projected **44 %**; the Senate PSI found the bank
   "deliberately tried to lower the CIO's risk results … by manipulating the mathematical models". Losses
   at least **$6.2 bn**. Every control signed off; the number reconciled.
3. **Ofqual 2020 standardisation.** The model reproduced national and subject-level grade distributions
   *exactly* — it reconciled perfectly to the trusted aggregate — and was withdrawn because it failed at the
   unit of the decision (individual students), with small centres escaping adjustment.
4. **Target Canada.** System on-hand reconciled, replenishment released orders, DC receipts tied to POs;
   the item master was internally consistent and wrong about the physical world. Every automated check
   compares system to system; nothing compared system to shelf.
5. **Public Health England, Sept–Oct 2020.** 15,841 positive tests lost to the legacy `.xls` 65,536-row
   ceiling; rows dropped **without an error**, so dashboards received a complete-looking, internally
   consistent file that showed a *plateau*. Silence, not error, was the signature.
6. **Google Flu Trends.** Validated against CDC ILINet for multiple seasons, published in *Nature*, and
   over-predicted by ~2× once Google's own product changes altered the covariate process; a trivial
   autoregressive baseline on lagged CDC data beat it.

**The pattern in all six:** the wrong analysis tied out to a trusted figure, or to itself, and the
discriminating test was available and cheap — external validation on local patients, parallel-running the
old and new model, evaluating at the unit of decision, counting shelves, reconciling row counts, or
comparing against a naive baseline.
