# G10 censored demand: Gemini 3 Flash baseline analysis

- **Task:** `candidates/g10-censored-demand`, frozen at content checksum `047195e7a12d34cd` (commits 3efed5c / ffbe949).
  The task was not modified before, during or after this analysis.
- **Job:** `jobs/g10-gemini3flash-baseline-1`.
- **Harness:** gemini-cli, `google/gemini-3-flash-preview`, Harbor 0.21.0, `-k 3 -n 3`,
  `--agent-setup-timeout-multiplier 3`.
- **Data:** per-trial data in `research/g10/g10_trials.csv`.

**Primary question.** Once Gemini recognises that sales are censored observations of latent demand, can it reason
through the consequences of *informative* censoring and carry that reasoning through a complete production repair?

**Answer: no, in 0 of 3 trials.**
- All three recognised censoring.
- Two stated explicitly that high-demand days are the ones that sell out.
- None modelled the day-level demand shock that makes censoring informative.
- None tested a modelling assumption against the data.
- All three stopped once the ice-cream trend turned positive.

## 1. Setup and validity

| Trial | Setup | Agent execution | Verifier | Model calls | Valid |
|---|---|---|---|---|---|
| LhEU3ny | 66 s | 266 s | 380 s | yes (964k input / 22k output tokens) | yes |
| cLtM9yi | 64 s | 744 s | 891 s | yes (1.07M / 24k) | yes |
| eMXZbBi | 68 s | 374 s | 448 s | yes (883k / 21k) | yes |

- Three trials, 0 exceptions, 0 infrastructure failures, no retries.
- Total cost **$0.584**.
- The G10 checksum was verified before launch and after analysis.

## 2. Results

| Trial | Reward | Tests passed | Visible lost share, LEAN post (truth 21.1%) | Holdout post (truth 6.8%) | v4 bias (truth −17.9 pp) | Visible actions correct | Worst ratio visible / a / b / c |
|---|---|---|---|---|---|---|---|
| LhEU3ny | 0 | 5/15 | 11.7% | 3.8% | −8.1 | 4/8 | 9.9 / 14.3 / 9.7 / 13.2 |
| cLtM9yi | 0 | 5/15 | 15.8% | 4.7% | −12.4 | **8/8** | 10.5 / 13.8 / 10.7 / 11.7 |
| eMXZbBi | 0 | 5/15 | 42.9% | 13.4% | −40.6 | 1/8 | 32.5 / 67.7 / 30.2 / 42.5 |

- **Success rate:** 0/3.
- **pass@3:** 0.
- **What passed in every trial:** warehouse unmodified, review runs, build time, history structure (keys, units sold,
  identity on full in-stock days, lost = expected − sold), determinism.
- **What failed in every trial:** demand strata, lost strata, category trends, programme impact, and all hidden-extract
  tests.
- **Ratios:** error/tolerance, re-graded from each agent's submitted package on the four graded extracts
  (`tools/g10/quickcheck.py`, read-only).

### Counterfactual (closest trial, one targeted patch, analysis copy only)

- **Patch.** cLtM9yi's imputation `S + (1 − W)·rate` was replaced by a Gamma-Poisson posterior
  `S + (α + S)/(α/rate + W)·(1 − W)`, with α per category fitted by NB likelihood. Everything else was kept: its pooled
  per-store-SKU-period rate, clean-day weekday weights, no promotion term, day-type-free profile, and the Sunday /
  short-day exposure bug.

  | | visible | hidden_a | hidden_b | hidden_c |
  |---|---|---|---|---|
  | Submitted | 10.5 | 13.8 | 10.7 | 11.7 |
  | + overdispersion posterior | 3.4 | 4.4 | 5.0 | 7.2 |

- **Reading.** Modelling the latent day shock removes about 70% of the error, but the trial is still far from passing.
  The remaining assumptions each bias the result:
  - the rate is estimated as a pooled Poisson ratio, so it is itself biased low by informative exposure;
  - no promotion effect;
  - a pooled traffic profile with a short-day exposure bug.

  G10 is **several** correct statistical decisions away for this model, not one.

## 3. Reasoning ladder per trajectory

| Level | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| L0 business symptom | ✓ | ✓ | ✓ (also read notes, competitor note, LEAN-26 design) |
| L1 censoring | ✓ | ✓ | ✓ |
| L2 informative censoring | ✓ explicit | ◐ stated only in the final summary; not used in design | ✓ explicit |
| L3 exposure | ✓ in-stock intervals incl. 14:00 restock | ✓ hourly integration; short-day/Sunday bug | ✓ intervals incl. pre-open events and restock |
| L4 within-day demand shape | ◐ one profile from **all** days' (censored) sales; no day types | ◐ profile from clean days; no day types | ◐ category profile from clean non-promo days; no day types; not renormalised to trading hours |
| L5 stochastic model | ✗ considered a Poisson process; implemented deterministic fill-in | ◐ Poisson exposure reasoning | ✗ per-day MLE scaling |
| L6 overdispersion / latent day shock | ✗ | ✗ | ✗ |
| L7 covariate structure | ✗ outsourced to the forecast | ◐ store×SKU×period rate + weekday; no promo; no season | ✗ |
| L8 censored-day inference | ✗ forecast imputation | ✗ plug-in at the pooled rate | ✗ per-day scaling (no pooling) |
| L9 baseline population | ✓ all non-promo days | ✓ | ✓ |
| L10 downstream propagation | ✓ | ✓ | ✓ |
| L11 scientific validation | ✗ | ✗ | ✗ |
| L12 complete repair | ✗ | ✗ | ✗ |

**First substantive failure.**
- **LhEU3ny: L4.** Its traffic profile came from censored sales pooled over day types.
  - The dominant error is L5/L8: forecast-based imputation.
- **cLtM9yi: L6 (with L2 weak).** Day-to-day heterogeneity was framed as estimator variance, never as a latent shock that
  drives both sales and sell-out.
  - It therefore concluded that observed sales carry no information about the missing hours beyond the rate (L8
    plug-in).
- **eMXZbBi: L5.** It scaled each censored day deterministically by its uptime fraction.
  - It considered smoothing, but rejected it by reading "no special-casing" as a ban on regularisation.

Levels L9–L10 were reached by all three. Reaching them is what made the wrong outputs look coherent.

## 4. Natural wrong methods

| Method | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| sales = demand | no (rejected at first read) | no | no |
| dropping stockout days | no (explicitly identified as selection bias) | no | no |
| scaling by fraction of day in stock (uniform) | considered, rejected for traffic shape | considered, rejected | considered, rejected |
| traffic-weighted scaling | no | considered (`S/W` "unbiased, high variance"; wrong: biased under stopping) | **yes** (per-day, category weights) |
| mean-rate imputation | no | **approximated** (pooled exposure rate × missing share) | fallback when uptime = 0 (clean-day mean) |
| Poisson exposure model | no | **yes** (pooled Σsales/Σexposure per store-SKU-period) | no |
| daily censored Poisson | no | no | no |
| forecast-based imputation | **yes** (production forecast × missing traffic share) | considered; rejected as circular | considered; rejected (it would zero the bias) |
| forecast as prior | no | wrote `(S + αF)/(W + α)`, then rejected for circularity | considered |
| NB plug-in imputation | n/a | Poisson plug-in (same structure) | no |
| traffic profile from all days | **yes** | no (clean days) | no (clean days) |
| NB without promotion effects | n/a (no NB) | no promo term | no promo term |
| holdout-store transfer | no | no | no |
| common-dispersion model | n/a | n/a | n/a |
| not anticipated | — | clean-day weekday weights pooled over all SKUs | "no special-casing ⇒ raw MLE" requirement misreading |

No trajectory produced a statistically defensible estimator outside the benchmark's anticipated set. No reward-0 outcome
is attributable to a reasonable alternative method (§11).

## 5. The statistical argument each agent made

| Question | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| 1. Estimand | expected units had the item been on shelf all trading hours (read correctly from docs) | same; "expected value given what was observed" | same |
| 2. Observed | hourly sales, in-stock intervals, forecasts | hourly sales, in-stock time, clean days | hourly sales, uptime intervals, clean days |
| 3. Censored | demand after sell-out until restock/close | same, via a weighted available fraction W | same, via an uptime fraction UF |
| 4. Censoring assumption | informative (high-demand days sell out), but treated as solved once the missing *time* is weighted by traffic | effectively non-informative: missing demand = rate × missing exposure | informative, handled by per-day scaling ("if something sells out early the baseline correctly goes up") |
| 5. Model | deterministic: forecast × missing traffic share | Poisson process with a pooled rate; plug-in expectation | Poisson-process per-day MLE `N/UF` |
| 6. Stockout time as evidence | yes in reasoning (step 16); not in code | no: the time of sell-out only sets W | yes (N/UF), without pooling, so noise and stopping bias explode |
| 7. Conditions on the observed portion | no (the forecast ignores the day's sales) | no (plug-in) | only on the observed portion (no prior) |
| 8. Heterogeneity across days | no | as "variance", not as a latent level | no |
| 9. Overdispersion | no | no | no |
| 10. Tests assumptions against data | no | no | no |

- **cLtM9yi came closest to the correct structure.** It wrote a shrinkage estimator with a forecast prior and
  "virtual observations", `(S + αF)/(W + α)`. Algebraically this is the Gamma-Poisson posterior mean. It abandoned the
  estimator because the forecast was a circular prior, without seeing that a model-estimated rate could serve as the
  prior mean and α could be estimated from the data.
- **eMXZbBi used the same idea in reverse.** It argued that the raw MLE was required because smoothing would be
  "special-casing".

## 6. Hypothesis search

| Hypothesis | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| Genuine seasonal decline | implicit (accepted ice cream up; soups/hot bev down "as expected"); not tested | accepted ice cream ↑ as seasonal confirmation | noted pre = Q2 / post = Q3 |
| Promotion changes | read the definition; baseline excludes promos; not tested | not tested | not tested |
| LEAN availability | **accepted** (central) | **accepted**; compared holdout vs LEAN ice-cream sales (+17.4% vs +0.3%) | **accepted** |
| Forecast degradation / v4 bias | accepted from the model card (clean-day training) | accepted | accepted from the output (−40.6%) |
| Competitor | not considered | not considered | read the note; said the per-store-SKU average handles it (justified: no graded effect) |
| Category mix | not considered | not considered | not considered |
| Invented | none | none | none |

- **Hypotheses touched:** 3 / 4 / 5.
- **Contradictions revisited:** 0 / 0 / 0.
- **Changes of working theory:** 1 / 2 / 1:
  - LhEU3ny: uniform → traffic-weighted exposure;
  - cLtM9yi: scaling → forecast prior → pooled rate;
  - eMXZbBi: clean-mean → uptime scaling.
- **No trial treated the randomised holdout as a control** for the size of the correction, although the LEAN-26 design
  doc (read by eMXZbBi) names it.

## 7. Long-horizon measurement

| Measure | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| ATIF steps | 62 | 72 | 58 |
| Tool calls (meaningful) | 44 (41) | 46 (43) | 42 (40) |
| Agent wall time | 266 s | 744 s (463 s waiting on its own 3 m 51 s review, twice) | 374 s |
| Distinct files read | 17 | 19 | 17 |
| Warehouse query calls | 9 | 15 | 5 (+2 analysis scripts) |
| Distinct intermediate analyses | ~5 (event sample, hourly profile, category profile, counts) | ~8 (schema, hourly, category, holdout vs LEAN, calendar hours, clean-day weights) | ~4 |
| Hypotheses tested | 3 | 4 | 5 |
| Material theory changes | 1 | 2 | 1 |
| Package edit calls | 8 | 4 | 7 |
| Pipeline runs | 3 (2 crashes) | 3 (1 crash) | 4 |
| Validation attempts | 0 scientific, 1 aggregate | 0 scientific, 2 output re-reads | 0 scientific, 1 aggregate |
| Row / day / SKU inspections | event sample only | event sample only | event sample; one named store-SKU-day |
| Statistical diagnostics | 0 | 0 | 0 |

**Documents never read by any trial:**
- `docs/stores/store_operations.md` (traffic shape by day type, lost shoppers);
- `docs/replenishment/order_up_to_policy.md`;
- `docs/data/data_dictionary.md` in cLtM9yi;
- model cards in eMXZbBi.

**Comparison** (same ATIF heuristics as `research/g08/g08_gemini_analysis.md` §8):

| Task | Tool calls | Distinct files | Query calls | Edits | Agent wall time |
|---|---|---|---|---|---|
| Task 02 | 51 / 49 / 57 | 23 / 24 / 22 | 7 / 8 / 7 | 10 / 3 / 10 | 278 / 195 / 267 s |
| G08 | 55 / 66 / 64 | 17 / 21 / 20 | 11 / 21 / 8 | 10 / 10 / 15 | 385 / 467 / 362 s |
| **G10** | **44 / 46 / 42** | **17 / 19 / 17** | **9 / 15 / 5** | **8 / 4 / 7** | **266 / 744* / 374 s** |

\* dominated by the agent's own slow pipeline.

**Verdict on horizon: G10 did not produce a longer scientific reasoning process.**
- Tool calls fell below both Task 02 and G08.
- Reasoning text per trial (21–24k characters) was similar.
- Each trial designed one estimator, implemented it, fixed crashes, read the aggregate and stopped.
- The workspace offered a long validation path (holdout, pre-period placebo, re-censoring, dispersion checks, day
  types) that no trial entered.

## 8. Intermediate plausible success

| Trial | What looked good enough | A. Reconstruction still wrong? | B. Further validation? | C. Stopped on plausibility? | D. Available falsifiers |
|---|---|---|---|---|---|
| LhEU3ny | Ice cream −5.3% → +10.0% (increase); LEAN lost share 11.7% vs notebook 2%; v4 bias −8% "confirming" clean-day training | yes: lost units −46% to −56%; 4/8 actions wrong | no | yes: "confirms that the Head of Planning was onto something", "the solution is robust" | 4 of 8 categories now `reduce` with no seasonal story; imputing with the forecast it had just called biased; clean-day forecast vs clean-day sales in LEAN stores; re-censoring full days |
| cLtM9yi | **All 8 actions correct**; ice cream +13.3%; lost share 15.8% "aligns with store reports" | yes: lost units −24% to −63%; bias −12.4 vs −17.9 | code-level only (go-live field, lost-units formula, runtime) | yes | holdout pre vs post lost share (4.7% both) vs LEAN pre 4.7%: plausible; but re-censoring clean days would reveal systematic under-imputation; dispersion of clean-day sales vs Poisson |
| eMXZbBi | Ice cream +25%; LEAN lost 42.9% vs holdout 13%; v4 bias −40.6% "the smoking gun" | yes: every category `increase` (+14% to +36%); lost +60% to +195% | no | yes: "incredibly excited" | pasta +36% and breakfast +28% with no seasonal reason; holdout sales −5.7% while holdout baselines rise ~20%; 13% holdout lost share with unchanged stockout rate |

Every trial reached a point that looked right on the one symptom the memo made most salient (ice cream), declared
success, and stopped. cLtM9yi is the archetype: a planner reading only the category table would accept it.

## 9. Scientific validation behaviour

| Validation | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| Identity on fully in-stock days | implemented, not checked | implemented (w = 1), not checked | implemented, not checked |
| Randomised holdout vs LEAN | no | descriptive, pre-modelling only | cited the output, not used as a test |
| Pre-period placebo | no | no | no |
| Dispersion diagnostics | no | no | no |
| Likelihood / model comparison | no | no | no |
| Artificial re-censoring | no | no | no |
| Traffic-profile stability | no | compared category shapes (to justify pooling) | compared category shapes |
| Subgroup residuals | no | no | no |

- **Code validation:** crash fixes, a warning fix, runtime, output shape, one rerun (cLtM9yi).
- **Scientific validation:** none. The only checks were whether a headline number matched the memo's narrative.

## 10. Reasoning-to-implementation gaps

| Rule | LhEU3ny | cLtM9yi | eMXZbBi |
|---|---|---|---|
| Expected demand ≠ sales on stockout days | fully implemented | fully implemented | fully implemented |
| Baselines on all non-promo days | fully implemented, propagated | fully implemented, propagated | fully implemented, propagated |
| In-stock exposure from events + restock | implemented correctly (minute resolution) | implemented, short-day bug | implemented, short-day bug |
| Traffic-weighted exposure | implemented incorrectly (profile from censored days) | implemented (pooled day types) | implemented (pooled day types) |
| Profile only from uncensored days | never recognised | fully implemented | fully implemented |
| Day-type traffic shapes | never recognised | never recognised | never recognised |
| High-demand days sell out (informative) | **correctly reasoned, omitted from implementation** | recognised late (summary only) | reasoned; implemented as unpooled scaling (misapplied) |
| Forecasts biased by censored training | **correctly reasoned, contradicted by implementation** (forecast imputation) | correctly reasoned; avoided | not examined |
| Shrinkage / prior for censored days | never recognised | **correctly reasoned (posterior form), omitted from implementation** | **reasoned ("Bayesian smoothing"), omitted after misreading a requirement** |
| Overdispersion | never recognised | never recognised | never recognised |
| Promotion effect in the rate | via the forecast | never recognised | never recognised |
| Validation against controls | never recognised | never recognised | never recognised |

The G08 pattern recurs: each trial reasoned at least one decisive rule correctly and did not implement it.

## 11. Benchmark flaw audit

| Trial | A reasoning | B implementation | C validation | D estimand | E alt. method | F tolerance | G verifier bug | H hidden dependence | I leakage | J infra |
|---|---|---|---|---|---|---|---|---|---|---|
| LhEU3ny | **primary** | secondary (no day types) | **yes** | no | no | no (worst ratio 9.7 on the best extract) | no | no (fails visible at 9.9×) | no | no |
| cLtM9yi | **primary** | secondary (short-day bug) | **yes** | no | no | no (10.5× visible; counterfactual still 3.4×) | no | no | no | no |
| eMXZbBi | **primary** | secondary | **yes** | no (read correctly) | no | no | no | no | no | no |

- **D (estimand):** all three restated the estimand correctly from `review_outputs.md`.
- **E (alternative methods):** none of the three estimators is defensible under the documented facts:
  - forecasts are documented as trained on censored sales;
  - a Poisson plug-in ignores the documented day-level variability that sell-outs select on;
  - per-day scaling is an unpooled ratio at a stopping time.
- **F/H (tolerance, hidden fixtures):** failures are ≥ 9.7× on the visible extract, so neither tolerances nor hidden
  fixtures decided any reward.
- **I (leakage):** no trial used a reports/notebook number as an answer; the notebook's 2% was explicitly rejected by
  all three.
- **Possible documentation asymmetry, not a flaw:** the day-type traffic shape is documented only in
  `docs/stores/store_operations.md`, which no trial opened. The README lists `docs/stores/`, and the data expose it
  (Sunday 10–18 hours in `store_calendar`, which cLtM9yi printed).

No benchmark flaw is counted as model weakness here, because none was found.

## 12. Reward hacking and security

| Check | Result |
|---|---|
| Warehouse modified | no (all passed `test_warehouse_unmodified`) |
| Outputs / reports hand-edited | no |
| Tests or generator probed | no reads of /tests, /logs, harbor paths |
| Special-casing | none (no hard-coded stores, dates, categories or values) |
| Stdlib / interpreter tampering | none; the verifier's integrity guard did not trigger |
| Scratch files | eMXZbBi created and deleted two analysis scripts in /workspace |

## 13. Comparison with Task 02 and G08

| | Task 02 | G08 | G10 |
|---|---|---|---|
| Reward | 0/3 | 1/3 | **0/3** |
| pass@3 | 0 | 1 | **0** |
| Failure type | semantic invariant (point-in-time) never applied | target vintage never investigated / reasoned rule not implemented | correct diagnosis; wrong statistical model (no latent shock, no validation) |
| Diagnosis reached | partly | mostly | **yes, in all three** (censoring + selection bias named correctly) |
| Intermediate plausible success | yes | yes (2 of 3) | **yes (3 of 3)**; one with all actions correct |
| Horizon (tool calls) | 49–57 | 55–66 | **42–46** |
| Cost per trial | — | $0.32 | $0.19 |

- **Task 02 fails because agents miss the invariant.**
- **G10 agents found the invariant quickly, in 1–2 minutes each,** and failed on statistical inference. This is the
  failure the task was designed to measure: "recognised censoring, implemented a plausible correction, wrong because an
  assumption was invalid".
- **In practice more than one assumption was wrong.** The counterfactual shows overdispersion alone is not sufficient.

## 14. Difficulty verdict

**FRONTIER-HARD (for Gemini 3 Flash): 0/3, pass@3 = 0.** Failures are principled and far outside tolerance (≥ 9.7× on
the visible extract), not near-misses or verifier artefacts.

Caveats:
- **The horizon was short.** Difficulty comes from statistical depth, not from long investigation; the agents never
  attempted the long validation path.
- **Only 3 trials.** A stronger model that runs a dispersion check or re-censoring validation could plausibly solve it.
  The mutation suite and nine correct specifications show the solution space is reachable and not brittle.

## 15. Does G10 belong in the final benchmark?

**Yes: recommend including it** as a frontier-hard statistical-reasoning task.
- **Rewarded failure mode:** it measures the target failure directly, and every trial exhibited it.
- **Validation depth:** a pre-registered tolerance calibration, independent reviews, and 33/33 mutation cases stand
  behind the scores.
- **Tolerance robustness:** alternative correct specifications pass at ≤ 0.68× tolerance on the graded extracts, and
  observed failures are ≥ 9.7×.
- **Headroom:** it adds headroom toward the pass@3 < 30% target, which Tasks 01, 03–06 and G08 cannot provide.
- **Pre-baseline risks still apply** (`report/g10_prebaseline_validation.md` §11): notably the thinly separated
  common-dispersion near-miss. The observed trajectories did not come close to that region.

## 16. Implications for the remaining Generation-3 candidates

1. **Statistical-inference depth beats semantic-rule tasks for headroom.** G08 (semantic vintage rules) was solved 1/3;
   G10 (inference under an invalid assumption) 0/3, with correct diagnosis. Candidates whose difficulty survives
   diagnosis are the stronger bets:
   - G24 recommender OPE (propensity and decision grain);
   - G05 staggered DiD (contamination and identification);
   - G01 label maturity.
2. **Horizon length does not follow from workspace size.** Neither G08 nor G10 lengthened trajectories: agents stop at
   the first plausible aggregate. Tasks should keep grading intermediate state (strata, row identities) rather than rely
   on long investigations.
3. **Plausible-aggregate attractors are reliable, and decision-level correctness can coexist with wrong state**
   (cLtM9yi 8/8 actions). Keep verifiers that grade below the decision level.
4. **Reasoned-but-not-implemented recurs (G08 and G10).** Designs should make the decisive rule testable at intermediate
   grain, so the gap is observable in outputs.
5. **Do not build G11 or other semantic-lock variants on the strength of G08.** Prioritise the statistical candidates
   (S2 G24, S6 G05, S8 G01), each gated by a Phase-0 tolerance pilot as G10 was.
