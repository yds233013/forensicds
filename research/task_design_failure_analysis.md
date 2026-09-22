# Task-design failure analysis — G31, G33, G36, G37, G38 vs the survivors G05, G10, G24 (2026-09-21)

Research-only synthesis of existing records. No new evidence.

## Failure taxonomy
| code | failure class |
|---|---|
| D0 | cheap solve / proxy recovers the graded output or decision |
| D1 | semantic ambiguity of a graded quantity |
| D2 | weak identification |
| D3 | valid/wrong overlap (no tolerance window) |
| D4 | representation hands over the solution |
| D5 | natural implementation path accidentally correct |
| D6 | one-fixture dependence |
| D7 | decision/tolerance incompatibility |
| D8 | verifier implementation defect |
| D9 | insufficient execution difficulty after recognition |

## Failed designs
| | G31 fraud selective labels | G33 entity resolution | G36 TOU capacity gate | G37 measurement-system change | G38 RTM under threshold trigger |
|---|---|---|---|---|---|
| intended phenomenon | outcome unobservable because the incumbent model blocks it; censoring by dispute lag; a randomised bypass | downstream statistics depend on correct real-world entities | regime-dependent tariff response + selection transport | latent process recovery across a noisy instrument change | selection on an extreme stochastic realisation |
| why it looked promising | three interacting observation mechanisms; real business framing | ubiquitous enterprise pain | two orthogonal transports; strong K9 families | a textbook EIV problem with a large dashboard effect | classic, ubiquitous managerial error; clean G05 separation |
| stage where it failed | pre-build research | pre-build research | **post-baseline adjudication** (built, frozen, 3 trials run) | pre-build research | pre-build research |
| failure classes | **D0** (label-free top-k GTV heuristic recovers 9/9 and 15/15 decisions); **D4** (value leaks the label); **D9** (delay leg inert, selective leg zero rows: one mechanism); **D3** (W10 count-recall passes 20/20); degenerate evaluation threshold | **D0** (constant decision correct 54/60); **D3** (wrong mappings within 0.004–0.016, K12); **D7** (truth straddles the 25 % limit by seed) | **D8** (verifier graded a household-weighted response vs a load-weighted contract, F8); **D5** (scaffold pre-solved selection); **D3** (response window 0.92 vs 0.99; CE06 forecast at 0.29 × tol); D6/D7 flags (hidden_c) | **D3** (ratio 0.01); **D9** (H3 collapses to "Deming + one subtraction"); D6 partial (hidden_b) | **D3** (ratio ≈ 0.00 at 3 scales); **D7** (1.34 / 1.43 SE_REF to threshold); D0 partial (dashboard 4/5 decisions) |
| nature | statistical + representation | statistical (estimand insensitivity) | **verifier / semantic** + statistical | statistical | statistical |
| gate that caught it | independent adversarial review + a cheap-solve search | kill criteria K9 / K12 | baseline trajectories → adjudication (IGQA would have caught it pre-freeze) | pre-registered window + counterexample gate | pre-registered window gate |
| without that gate | a heuristic solver would score as a capable analyst | a constant answer would pass | a contaminated 0/3 would enter the aggregate | the verifier would either fail legitimate analyses or pass wrong ones: rewards driven by noise | same as G37, plus wrong-side decisions accepted |
| general lesson | a gate must model solvers that *never estimate anything* | the estimand must be sensitive to the phenomenon, beyond the decision margin | every graded quantity needs IGQA and a window; trace the natural edit | separability must be measured before any build effort | separability belongs to the business setting (principle 15); identifiable ≠ gradable (16) |

## Why G05, G10 and G24 survived (without overstating)
| task | what the wrong method gets wrong | measured separation | where the separation comes from |
|---|---|---|---|
| **G10** censored demand | treats censored sales as demand, or imputes from forecasts | failures **9.7–68 × tolerance** | wrong methods answer a **structurally different quantity**: sales, not demand. The gap equals the censored mass, which the business setting makes large. Valid estimators have small variance given the data |
| **G05** staggered causal ID | wrong comparison / trend structure | wrong routes rejected at **≥ 4.57 τ** vs **≤ 0.54 τ** for valid (ratio ≈ 8) | format-conditional trends are **systematic** and large relative to store-level noise; the bias does not average away |
| **G24** OPE statistical object | wrong grain / weighting / action unit | errors **0.8–4.3 τ**; some separations **thin (1.1–1.6 τ)**, and one trial landed inside tolerance on one extract | the object error is systematic, but its magnitude varies by extract. **G24 survived with thinner margins than G05/G10.** It is the survivor closest to the G37/G38 failure mode, and it should not be cited as strong evidence of separability |

**Pattern.** The survivors' wrong methods estimate a **different object**, and the business setting
makes that difference *large and systematic*. The failed statistical designs asked the verifier to
distinguish **estimator refinements of the same object** (G37 second-order EIV variants; G38
counterfactual refinements) from correct ones, against legitimate noise of the same size.

## Strategic recommendation: what TYPE of task to search for next (no selection, no simulation)
| rank | direction | scientific object | why finite-sample separation should be strong | recognition challenge | execution challenge | valid estimators | wrong methods | distinct from pool? | cheap-solve risk | semantic risk | expected gradability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **1** | **G. decision optimisation under the correct constraint set** | the optimal allocation / plan and its value under business constraints stated in the docs | near-deterministic: given the data, the optimum is unique (valid variance ≈ 0); a wrong constraint set moves the optimum by a discrete, often large amount | realising which constraints bind (capacity, contractual minimums, lead times) and which dashboard constraints are wrong | formulating and solving it (LP/MIP or exact DP), with a value derivation | LP solver; exact enumeration / DP; Lagrangian check | greedy by margin; missing constraint; wrong coupling; soft vs hard confusion | yes: no optimisation task in the pool | medium: greedy may coincide on easy fixtures → needs coverage | medium: the constraint semantics must be pinned | **high** |
| **2** | **D. unit / denominator normalisation across heterogeneous systems** | a pinned business ratio (cost per unit shipped, incidents per 1k requests) across systems with different units, grains and double counting | near-deterministic invariants (reconciliation totals); wrong normalisation errors are multiplicative and large | seeing that systems count differently | building a correct normalisation graph + deduplication | two independent reconciliation paths (bottom-up, top-down) | naive join; double count; wrong grain; currency/unit mix | partial: Task02 (as-of) and G24 (grain) are adjacent | **medium-high**: may degrade into ETL (correct-table gate essential) | medium | high |
| **3** | **B. hierarchical aggregation / Simpson with a business-defined target population** | a population-standardised KPI with target weights pinned by the business | the aggregate reversal is deterministic given the data; wrong weighting errors are large when composition shifts strongly | noticing composition shift | standardisation with pinned weights + variance | direct standardisation; model-based (g-computation) | pooled; wrong target weights; mix-of-rates | adjacent to G05 (format), G36 (estate weighting) | **high**: once named, easy (D9) | low if pinned | medium-high |
| 4 | E. partial-compliance experiment with a pinned estimand | ITT vs CACE vs per-protocol | the object difference is ×(1/compliance), large when compliance ≈ 40 % | noticing non-compliance | IV / Wald with covariates | Wald; 2SLS; principal-stratification bounds | per-protocol; as-treated; ITT reported as CACE | new | medium | medium (estimand wording) | medium: IV variance can be large (G38 risk) |
| 5 | A. sampling-frame / survey weighting failure | a population prevalence from a biased-response survey with known frame margins | large when response propensity differs several-fold by segment | differential response | raking / post-stratification | raking; MRP | unweighted; wrong frame; respondent weights | adjacent to G36 (weighting) | medium | medium | **medium: weighting variants may overlap (G36 CE06)** |
| 6 | H. revenue / ledger reconciliation with deterministic invariants | recognised revenue or deferred balance under a pinned policy | deterministic | policy nuance | schedule construction | two ledgers | cash-basis; wrong recognition timing | Task02-adjacent | medium-high (ETL) | medium | high but D9 risk |
| 7 | F. calibration under deployment shift | calibrated probability / expected loss in the deployed population | only if the shift is strong | noticing the shift | importance weighting / recalibration | reweighting; domain classifier | no reweighting; wrong weights | new | medium | medium | **low-medium: weighting noise (G37/G38 risk)** |
| 8 | C. MNAR operational data with an audit sample | full-population rate using a small audit | depends on audit size | noticing MNAR | audit-based correction | IPW on audit; pattern mixture | complete-case; wrong audit weights | adjacent to G10/G31 | medium | medium | **low: small audits recreate G37/C7** |

### Recommended next search space (not a task selection)
**Decision-analytic and deterministic-invariant tasks (ranks 1–2).** The graded object is a function
of the data with near-zero legitimate sampling variance, and plausible wrong analyses answer a
*different question* whose answer differs structurally and materially.

**Why this is more promising:**
- **G10 and G05 survived** because wrong methods estimate a different object, and the business
  setting makes the difference large.
- **G37 and G38 failed** because the verifier had to separate refinements of the *same* object from
  legitimate noise of equal size.
- With near-deterministic objects, VALID_BOUND is tiny and the window gate becomes attainable
  without tuning.

**What to avoid next:**
- estimation-precision phenomena (EIV, RTM, IV with weak first stages, small audit samples, rare
  events);
- grading intermediate quantities;
- designs whose decision a constant or a dashboard number recovers;
- weighting-variant distinctions without a large composition shift;
- any "rescue" of G37/G38.

### Pre-build gates for any future task (order matters: cheapest decisive kills first)
1. Estimand and IGQA semantics (principle 8).
2. Threshold provenance, and realistic policy and scale fixed from the domain (principle 15).
3. **Window gate, measured first** with a minimal simulation: ratio ≥ 3 with headroom (11, 16).
4. Counterexample search, combinations included (10).
5. Natural implementation path (9).
6. Cheap-solve / constant-decision / dashboard proxies (D0).
7. Recognition ≠ execution (14).
8. Fixture coverage ≥ 2 per important wrong method (12).
9. Decision/tolerance compatibility (13).
10. Correct-table, representation leakage, and a G05-type ablation where relevant.
11. Adversarial review.

G37 and G38 each spent effort on documents before the decisive window gate. **Run it first.**
