# G02: Better AUC, worse loss ratio (negative downsampling, calibration and exposure)

Status: design only. Nothing is built and no model has been run. Numbers are generator/pipeline design targets, to be
re-measured, tuned and margin-checked at build.

## Workspace sketch

```
/workspace
  README.md                                    freqmodel repo; `python -m freqmodel run --out out/`; output formats
  CHANGELOG.md                                 v6 → v7 (more batches, sprinkler_verified feature, HGB upgrade); neutral
  config/model_v7.yaml                         features, hyper-parameters, seeds, training batches B01–B06, negative_keep_rate: 0.10
  config/model_v6.yaml                         same, batches B01–B04
  data/extracts/manifest.jsonl                 12 rows (6 batches × train/valid): source inception period, built_at, keep_rate, seed, row counts
  data/extracts/train/batch=B0x/part-0.parquet ~34 MB total, ~262k exposure records
  data/extracts/valid/batch=B0x/part-0.parquet ~9 MB, ~66k records
  data/pricing/renewal_book_2026q1.parquet     ~49k terms / ~58k exposure records to be rated (features + exposure; no claims)
  data/pricing/written_2026q1.parquet          premium written under deployed v7, engine version, rated frequency per term
  data/actuarial/severity_by_segment.csv       selected severities (actuarial, authoritative)
  data/actuarial/lr_monitor_2026-06.csv        developed loss ratio by segment × accident quarter, 2024Q1–2026Q1
  upstream/extract_builder/README.md           (Data Eng, read-only) refresh process, EXT-88 storage change
  upstream/extract_builder/sample_negatives.sql   (read-only) the sampling SQL actually used
  src/freqmodel/cli.py, data.py, features.py   load extracts, build features
  src/freqmodel/train.py                       HistGradientBoostingClassifier, unweighted
  src/freqmodel/calibrate.py                   FAULTY: Platt on valid extract, then single prior correction with config rate
  src/freqmodel/evaluate.py                    FAULTY: AUC + decile calibration on extract scale; segment O/E per policy count
  src/freqmodel/pricing_export.py              FAULTY: cell frequency = mean over records of p / exposure_years
  models/v6/metadata.json, models/v7/metadata.json   training batches, calibrator coefficients, AUCs
  reports/validation/v6_validation.json, v7_validation.json   AUC 0.768 / 0.781, "diagonal" calibration deciles, segment O/E
  docs/model_card_freq_v7.md                   target: P(≥1 reported claim in exposure record); use: pricing indicated frequency
  docs/pricing/pricing_engine_interface.md     indicated frequency per exposure-year per rating cell; expected count from probability
  docs/pricing/engine_4.2_release_notes.md     rounding change (distractor)
  docs/data/extract_dictionary.md              record grain, exposure_days, claim_count, splits, batch columns
  notes/actuarial/2026-07-08_lr_deterioration.md   contractors and food service underpriced; asks DS
  notes/ds/2026-07-20_v7_segment_auc.ipynb     segment AUCs: hospitality dips; suggests "v7 worse"
  logs/deployments.csv                         v7 pricing live 2025-10-01; engine 4.2 2025-09-29
```

Extract record schema: `record_id, policy_term_id, policy_id, batch_id, split, segment, size_band, territory, form_edition,
product (standard/seasonal), building_age, sprinkler, sprinkler_verified, revenue_band, years_in_business,
prior_claims_3y, period_start, period_end, exposure_days, claim_count`.

## 1. Research question

Can an agent see that a higher-AUC model priced worse because the *sample design* of its data varies across
extract batches? And can it repair the pipeline so that probabilities, validation tables and pricing inputs are
population-scale and exposure-based, when:

- the obvious calibration repairs make validation look perfect but leave the pricing population wrong;
- the sampling unit (policy term) differs from the modelling unit (exposure record);
- the business target is a ratio of sums over exposure, not an average over policies?

## 2. Enterprise setting

Aldermoor Mutual (fictional) writes Business Owner's Policies for small commercial risks across six segments:

- retail;
- office;
- food service, which includes a seasonal product launched mid-2024;
- contractors;
- light manufacturing;
- hospitality.

The Pricing Data Science team builds a claim-incidence classifier (`freq v7`). It predicts the probability that an
exposure record has at least one reported claim. The pricing engine converts that probability into indicated claim
frequency per exposure-year for each rating cell (segment × size band), then multiplies by actuarial severity and
loadings.

Data Engineering builds training and validation extracts in quarterly refreshes. To cut storage, it negative-downsamples
policy terms without claims.

## 3. Visible symptom

The memo comes from the Chief Actuary and Head of Pricing DS:

- `v7` beat `v6` on validation (AUC 0.781 vs 0.768) with "well-calibrated" deciles, and went live for pricing on
  2025-10-01.
- Developed loss ratio for accident quarters 2025Q4–2026Q1 is 71% against a 62% plan. Contractors (86%) and food
  service (83%) are worst.
- Candidate explanations are on the table: v7 is worse, the pricing engine 4.2 release, or mix shift from the new
  broker programme.

The memo asks for:

1. `python -m freqmodel run --out out/` must retrain and recalibrate v7 per its model card (all its batches), and write:
   - `out/validation/calibration_by_segment.csv`: for the validation population, per segment, exposure-years,
     observed claims and model-expected claims;
   - `out/pricing/indicated_frequency.csv`: per rating cell of the 2026Q1 renewal book, exposure-years and indicated
     claims per exposure-year;
   - `out/pricing/loss_ratio_review.json`: expected loss ratio of the 2026Q1 written renewal book under the premiums
     actually charged, overall and per segment, plus `segments_rate_increase_needed` (expected LR more than 8 points
     above plan).
2. Extracts, the manifest, upstream SQL and actuarial files are authoritative and must not be modified.
3. The pipeline must work on future extract refreshes. No batch ids, rates, segments or dates may be hard-coded.

The memo does not mention sampling, weights, exposure-weighting or batches.

## 4. Source distribution inspiration

- **Negative downsampling.** Standard for rare-event classifiers in large pipelines, where extract size is budgeted.
  The prior-shift (odds) correction is well known, and sampling-rate changes across data refreshes are a routine source
  of silent miscalibration.
- **Exposure-based pricing.** Insurance pricing uses frequency per exposure-year and ratio-of-sums cell estimates.
  Policy-count averages are a known actuarial mistake.
- **Discrimination vs calibration.** Discrimination improvements with calibration regressions are common in pricing
  model governance.
- **Pricing-engine releases.** Rounding and factor-table changes are routine and usually immaterial.

The literature is not cited. The prior-correction and case-control sampling literature is "to verify" if referenced
later.

## 5. Causal graph / ground truth

**Population.**
- ~95k BOP policy terms per inception year, 2022–2024; renewal book 2026Q1 ~49k terms.
- Terms split into exposure records at mid-term endorsements:
  - 18% of terms overall have 2–3 records;
  - contractors: 41% (payroll/revenue endorsements);
  - light manufacturing: 22%.
- Mid-term cancellations: 7% of terms.

**Seasonal product.** `product = 'seasonal'` launched 2024-07 for food service only (kiosks, food trucks).
- 34% of food-service terms incepting 2024H2 and 38% of the 2026 renewal book.
- Exposure 0.25–0.5 years.

**True frequency.** `log λ = β0 + β_segment + β_size + β_territory + f(building_age) − 0.25·sprinkler
+ 0.18·prior_claims_3y + 0.03·[form_edition = BOP-2024] + γ·seasonal`.
- γ = −0.45: seasonal venues have a lower annual rate but short exposure.
- `N ~ Poisson(λ · exposure_years)`; `y = 1[N ≥ 1]`; `claim_count = N`.
- Base annual frequency ≈ 0.075; food service 0.11; contractors 0.10.

**Form edition.**
- BOP-2024 is written for new business from 2024-01 and renewals from 2024-07.
- Share by batch: B01–B04 0%, B05 55%, B06 96%; the renewal book 100%.

**Mix shift.** The TradePath broker programme (2024-01) raises contractors from 12% to 21% of terms and food service
from 14% to 19%, concentrated in B05–B06.

**Extracts.**

| Batch | Inception period | Keep rate (non-claim terms, train and valid) |
|---|---|---:|
| B01 | 2022H1 | 0.10 |
| B02 | 2022H2 | 0.10 |
| B03 | 2023H1 | 0.10 |
| B04 | 2023H2 | 0.10 |
| B05 | 2024H1 | 0.10 |
| B06 | 2024H2 | **0.25** (built 2025-06 after EXT-88 raised the storage quota) |

- **Sampling unit** (`sample_negatives.sql`): a policy term is kept if any record has `claim_count > 0`. Otherwise,
  within batch × split, the non-claim terms are ordered by `hash(policy_term_id, seed)` and the first
  `round(keep_rate × count)` are kept. This is exact-count sampling. All of a term's records are kept or dropped
  together.
- **Split:** `hash(policy_id)` 80/20, before sampling.
- **Manifest:** `keep_rate`, `population_non_claim_terms` and `kept_non_claim_terms` per batch × split. Visible rates
  equal the table above, except the B03 validation split at 0.12, so per-split rates are exercised visibly.

**Faulty pipeline** (runs in the image with pinned scikit-learn):

- `train.py`: HGB (`max_iter=300, learning_rate=0.06, max_leaf_nodes=31, random_state=7`), unweighted, all
  train batches. Features include `form_edition`, `product`, segment, `log(exposure_days)` and the others.
- `calibrate.py`: Platt (logistic on logit of raw score) fit unweighted on all validation records, then
  `odds × keep_rate` with `keep_rate = 0.10` from config.
- `evaluate.py`:
  - AUC on the validation extract;
  - decile calibration comparing the **Platt output before prior correction** with the extract label rate, which is
    diagonal by construction;
  - segment O/E = mean p vs share of *policy terms* with a claim.
- `pricing_export.py`: for each cell, `mean over records(p_corrected / exposure_years)`. It uses the probability as
  the count, without `−ln(1−p)`, and averages records instead of taking a ratio of sums.

**Truth quantities** (renewal book, from generator λ):
- cell frequency `F_c = Σ λ_i e_i / Σ e_i`;
- expected LR = `Σ λ_i e_i sev_seg / Σ premium_i`.

`written_2026q1.parquet` premiums come from deployed faulty v7 frequencies × severity × 1/0.62 plan-LR loading,
rounded by engine 4.2.

**Design targets** (build must hit within ±3 points; levers are B06 rate, form/seasonal shares, segment mix):

| Quantity | Target |
|---|---|
| Deployed v7 indicated frequency error, overall | −13% |
| Contractors | −24% |
| Food service | −22% |
| Others | −4% to −9% |
| Expected LR overall | 71.5% |
| Expected LR, contractors | 84% |
| Expected LR, food service | 82% |
| Expected LR, other segments | 63%–68% |
| Engine 4.2 rounding effect | −0.2% premium |

## 6. Latent statistical/business invariant

**(a) Population scale.** Every extract record represents `w = 1/keep_rate(batch, split)` population records if its
policy term had no claims, and 1 otherwise. The weight is a *term-level* property inherited by all of the term's
records.

**(b) Training consistency.** The fitted probability must estimate `P(y = 1 | x)` in the population. The sample design
varies by batch and batches correlate with features (form edition, product, segment mix), so the fix must enter
*estimation*, not only post-hoc calibration. Valid ways:

- weighted training with `w`;
- resampling all batches to one common keep rate, followed by a single odds correction at that rate;
- an equivalent approach that removes batch-dependent prevalence before the model can absorb it.

A calibrator fit on validation, weighted or not, cannot remove a feature-dependent sampling bias learnt in training.
Neither can a per-batch correction at scoring time: the renewal book has no batch.

**(c) Validation table.**
- Weighted exposure-years `Σ w·e`.
- Weighted observed claims `Σ w·claim_count`.
- Weighted expected claims `Σ w·μ̂`, with `μ̂ = −ln(1−p̂)` per the pricing interface's Poisson relation.
- All per segment, over all validation records.

**(d) Pricing inputs.** `F̂_c = Σ μ̂_i / Σ e_i` over renewal-book records in the cell. This is a ratio of sums, not a
mean of per-record rates.

**(e) Loss ratio review.** `Σ μ̂_i·sev_seg / Σ premium` per segment and overall. `segments_rate_increase_needed` = segments
with expected LR > 70% (plan 62% + 8).

Visible truth: contractors and food service.

## 7. Grains and state variables

- **Exposure record:** the modelling unit; exposure, claim count.
- **Policy term:** the sampling unit; claim/no-claim status.
- **Policy:** the split unit.
- **Extract batch × split:** keep rate, inception period.
- **Model:** raw score scale (sample-mixed) vs population scale; `p` vs `μ = −ln(1−p)`.
- **Rating cell:** ratio-of-sums frequency.
- **Segment:** LR and decision.

Grain mistakes that matter:
- **Record-level weights** (y = 0 records ×1/s) over-weight zero records of claim terms, which bites in contractors.
- **Policy-count averaging** mis-states food service.
- **Batch-level correction at scoring** is undefined for the renewal book.

## 8. Evidence graph

N = natural path.

| Artifact | Shows | N? |
|---|---|---|
| Memo, actuarial LR note, `lr_monitor` | LR up; contractors and food service | N |
| `v7_validation.json` | AUC 0.781; diagonal deciles; segment O/E ≈ 1 by policy count | N (attractor: "calibration fine") |
| `calibrate.py`, `config/model_v7.yaml` | Platt then `keep_rate: 0.10` correction | N |
| `models/v7/metadata.json` | Training batches B01–B06 | N |
| `data/extracts/manifest.jsonl` | B06 keep rate 0.25 | N once sampling is suspected |
| `upstream/extract_builder/sample_negatives.sql` | Term-level sampling; all records of a term kept together | partly |
| `upstream/extract_builder/README.md` | EXT-88 storage change "allows larger non-claim samples from the 2025-06 refresh" | partly |
| `docs/pricing/pricing_engine_interface.md` | Indicated frequency = expected claims per exposure-year in the cell; expected claims from incidence probability via Poisson relation | N (pricing export cites it) |
| `pricing_export.py` | Mean of per-record rates; p used as count | N |
| `docs/data/extract_dictionary.md` | Record grain, endorsement splits, exposure_days | N |
| `engine_4.2_release_notes.md`, `logs/deployments.csv` | Rounding release 2 days before v7 | N (distractor) |
| `notes/ds/..._segment_auc.ipynb` | Hospitality AUC 0.70 → 0.68 | partly (distractor) |
| `written_2026q1.parquet` | `premium_unrounded` and `premium` columns (engine logs both) | partly (falsifies rounding) |

## 9. Evidence authority hierarchy

1. **Upstream SQL and manifest** govern the sampling design. `config/model_v7.yaml` `negative_keep_rate` is a pipeline
   constant copied at v6 time and is overridden.
2. **The pricing engine interface** governs the target quantity and conversion. It overrides `evaluate.py`/`pricing_export.py`
   conventions.
3. **The model card** governs training data (all batches B01–B06) and features. Dropping B06 violates it.
4. **Actuarial severity and LR monitor** are authoritative inputs. The LR monitor is realised and developed, so it is
   noisy relative to the expected LR, and it is not an answer key.
5. **Validation reports and the notebook** are derived, on extract scale, and falsifiable.

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | v7 genuinely worse★ | Hospitality AUC dip; LR worse since v7 | AUC up overall. Hospitality dip within bootstrap noise (± 0.02). Hospitality LR is fine. The worst segments have *higher* AUC |
| H2 | Pricing engine 4.2 rounding★ | Released 2 days before v7 go-live; release note | `premium_unrounded` vs `premium`: −0.2% |
| H3 | Mix shift (TradePath)★ | Contractors and food service share up; they are the bad segments | The model has segment and prices cells; mix explains the aggregate LR only if cells are mispriced. Within-cell LR is still high |
| H4 | Sampling/calibration error | Manifest B06 0.25 vs config 0.10 | The validation deciles look diagonal, which argues against it |
| H5 | Exposure / target definition error | Seasonal food service; engine interface definition | Alone explains only part of food service (≈ −7%) |

Truth: H4 with H5 interacting, the main effect concentrated through form edition, seasonal product and mix. H3 is real
but not causal for mispricing. H1 and H2 are false.

## 11. Why each wrong hypothesis is plausible

- **H1.** The "better AUC, worse business" pattern is often a real overfitting story, and the notebook supplies a
  segment dip.
- **H2.** Coincident timing plus an actual pricing-code change. Rounding errors in rating engines are a classic
  incident.
- **H3.** The worst segments are exactly the growing ones, which is a very persuasive coincidence.
- **H4 (the reason it gets dismissed).** The validation report's diagonal calibration and per-policy O/E ≈ 1 "prove"
  calibration.

## 12. Investigation path (≈40–65 actions)

1. **(1–8) Read and reproduce.** Memo, LR note, LR monitor, validation reports. Run the pipeline and reproduce the
   deployed frequencies.
2. **(9–14) Test the obvious alternatives.**
   - H2: premium unrounded vs rounded.
   - H1: segment AUC bootstrap.
   - H3: LR by cell.
3. **(15–22) Examine calibration.**
   - Notice `evaluate.py` checks calibration before the prior correction, on extract scale.
   - Manifest: B06 at 0.25.
   - **Discovery 1:** sampling rates vary by batch.
4. **(23–30) First repair** (per-batch prior correction or weighted recalibration, section 14).
   - The validation table now matches observed.
   - Renewal-book frequencies change little for contractors.
   - **Discovery 2:** B06 is feature-aligned (form edition, seasonal, TradePath). The raw model absorbed the prevalence,
     and the renewal book has no batch.
5. **(31–38) Weighted training** (or harmonised resampling). Refit and re-validate.
   - Read `sample_negatives.sql`.
   - **Discovery 3:** the sampling unit is the term. Contractors have multi-record terms with zero records.
6. **(39–48) Pricing.**
   - Interface doc: per exposure-year, expected claims.
   - `pricing_export.py` averages per-record rates.
   - **Discovery 4:** the seasonal product's short exposure makes the average differ from the ratio of sums.
7. **(49–60) Check and deliver.**
   - LR review.
   - Validate weighted sums against manifest population counts (term counts by batch).
   - Stratum checks by batch × segment.
   - Determinism.
   - Outputs.

## 13. Natural wrong implementation

The faulty pipeline is described in section 5. After an agent recognises "the sampling rate changed", the most natural
repair is **R1, per-batch prior correction**:

- In `calibrate.py`, keep Platt on the validation extract.
- Replace the constant with each record's batch rate: `odds × keep_rate[batch]`.
- For scoring the renewal book, which has no batch, pick one of:
  - the latest rate, 0.25 ("current extract design");
  - the config default, 0.10;
  - the manifest's average.

What R1 gets wrong (design targets):

- **Validation.** The per-segment weighted table looks close. Observed and expected differ by ≤ 4% on validation,
  because each record is corrected by its own batch.
- **Renewal book, latest rate (0.25).**
  - Retail, office and hospitality are over-predicted by +18–30%, because those raw scores are mostly on the 0.10
    sample scale.
  - Contractors are still −6% and food service −9%.
  - `segments_rate_increase_needed` becomes `[]`, and the LR review shows several segments under 55%.
- **Renewal book, config 0.10.** The same as faulty for contractors (−22%).
- **Average rate.** A mixture of both errors, at ±10–15% by segment.
- **Pricing export.** The ratio-of-sums error remains unless separately fixed: food service −7%.

Numerically, R1 fails the pricing cells, the segment LR and the decision list. It can pass the validation table's
observed columns if weights are also computed, and it can come close on expected.

## 14. Second-order failure modes

| ID | Repair | Why wrong | Visible effect (targets) |
|---|---|---|---|
| R2 | Single global prior correction at the extract's effective keep rate (kept/population non-claims over all batches ≈ 0.125) | Correction is feature-dependent, not scalar | Overall frequency ≈ −3% (**plausible aggregate**); contractors −15%, food service −14%, retail +6% → fails cells, segments and decision list |
| R3 | Weighted Platt/isotonic recalibration on validation with correct term weights, unweighted training | Calibrator is a function of score only; absorbed batch/form bias remains | Overall ≈ 0%; contractors −10%, food service −11%, office +5% → fails segment tolerance ±5% and cells (margin must be ≥ 2× at build) |
| R4 | Weighted training with **record-level** weights (records with y = 0 get 1/s) | Zero records of claim terms over-weighted; contractors have many | Contractors −12%, light manufacturing −6%; validation observed claims fine, exposure-years inflated → validation table fails exactly |
| R5 | Weighted training with one weight 1/0.10 for all non-claim terms | B06 still under-weighted | Contractors −9%, food service −10% |
| R6 | Correct model; pricing export mean of per-record rates | Seasonal short-exposure records over-weighted | Food service −7%; cells for food-service S/M fail |
| R7 | Correct model; `p` used as expected count | Understates by ~4% at p ≈ 0.08, more for large L-band policies (p ≈ 0.2 → 11%) | L-band cells fail; overall −5% (borderline; see section 21) |
| R8 | Drop B06 from training ("inconsistent batch") | Violates model card; seasonal product only in B06 → seasonal effect unlearnt | Food service +20% (seasonal treated as year-round) → fails |
| R9 | "Recalibrate on the validation extract" literally: refit Platt or isotonic unweighted, remove prior correction | Extract prevalence ≠ population | Frequencies ×3–5; obviously wrong, but the validation deciles are perfectly diagonal |
| R10 | Weighted everything, but exposure-years reported unweighted in the validation table | Population table definition | Validation table fails exactly |
| R11 | Attribute to mix and recommend rate increases from the realised LR monitor | Not a pipeline repair; realised LR is noisy and lagged | Required outputs wrong |

## 15. Correct repair properties

- **Weights.** Term-level, from the manifest `keep_rate` for (batch, split). Alternatively `population/kept` counts
  from the manifest, which gives the same design.
- **Estimation.** Population-consistent: weighted HGB training (`sample_weight`), or resampling every batch to a common
  rate with the matching single correction.
- **Calibration.** If kept, fit on validation *with weights*, on population-scale targets. Calibration may also be
  omitted if weighted training is already calibrated within tolerance.
- **Expected counts** via `−ln(1−p)`; cell frequencies as a ratio of sums over exposure.
- **Validation table.** Weighted exposure, observed and expected claims per segment.
- **LR review** from indicated expected claims × actuarial severity over written premium.
- **No hard-coding** of batch ids or rates; works for any number of batches and any per-split rates.
- **Preserved:** features, hyper-parameters, seeds, training batches (model card), and deterministic output.

## 16. Repair surfaces

| Surface | Why |
|---|---|
| `data.py` | Join manifest rates and derive term-level weights |
| `train.py` | Weighted fit, or harmonised resampling |
| `calibrate.py` | Remove the scalar correction; weighted calibration or none |
| `evaluate.py` | Population-scale, exposure-based validation table |
| `pricing_export.py` | Poisson conversion; ratio of sums |
| New `loss_ratio_review` | Required output |
| `config/model_v7.yaml` | Remove or ignore `negative_keep_rate`. It must not be the source of rates |

## 17. Validation requirements

- **Population reconstruction.** Σ weights of non-claim terms per batch × split vs the manifest's
  `population_non_claim_terms` (exact under the N/n design; close under 1/rate).
- **Batch × segment calibration.** Weighted O/E per batch and segment on validation, *after* training changes. R3 only
  shows up here as B06 vs B01–B05 residuals in the same segment.
- **Form edition and seasonal slices.** O/E for BOP-2024 and seasonal records separately, because the renewal book is
  100% BOP-2024.
- **Term grain check.** Contractors' claim terms: count zero records and confirm their weight is 1.
- **Exposure check.** Food-service cell frequency as a ratio of sums vs a mean of rates on the renewal book.
- **Distractor falsification.** Premium unrounded vs rounded; hospitality AUC bootstrap.

Aggregate O/E on validation, or overall LR, cannot replace these. R2 and R3 are within ±3% overall.

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface changes | Overfit / shortcut caught | Same distribution because |
|---|---|---|---|---|
| hidden_a | Rates from the manifest per batch × split | Keep rates 0.05 (B01–B03), 0.20 (B04–B05), 0.30 (B06); **validation split of B06 at 0.50**; 7 batches | Hard-coded {0.10, 0.25}; hard-coded B06; "train rate = valid rate"; R2 at a different effective rate | The manifest has per-split rows visibly. **Risk:** visible rates are equal across splits, so this tests a documented column not exercised by visible data. Mitigation: visible B03 valid at 0.12 vs train 0.10 (small but present) |
| hidden_b | Feature-dependent absorption on other axes | High-rate batches aligned with `sprinkler_verified` population (missing in early batches) and office/hospitality growth; contractors flat; seasonal product in hospitality | Segment fudge factors fitted on visible; R3 (now off in office/hospitality); decision list constant `[contractors, food_service]` | Same mechanisms (batch-feature correlation), different axis |
| hidden_c | Term grain and exposure | 35% of retail terms endorsed (multi-record), 15% mid-term cancellations in office, seasonal share 50% in food service with γ = −0.7; a single rate change | R4 (retail now fails badly), R6, R7 | Endorsements, cancellations and seasonal product exist visibly |

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` (weighted HGB, weighted Platt, Poisson conversion, ratio of sums) | 1 |
| `alt_resample_common_rate` (subsample every batch's non-claims to the min rate per split, single correction) | 1 |
| `alt_weighted_no_calibrator` (weighted HGB only) | 1 (probe; HGB calibration under weights must be within tolerance) |
| `alt_N_over_n_weights` (manifest population counts) | 1 |
| `per_batch_prior_latest` (R1) | 0 |
| `per_batch_prior_config` (R1b) | 0 |
| `global_effective_rate` (R2) | 0 |
| `weighted_recalibration_only` (R3) | 0 (margin-check) |
| `record_level_weights` (R4) | 0 |
| `single_weight_0.10` (R5) | 0 |
| `mean_of_rates_export` (R6) | 0 |
| `p_as_count` (R7) | 0 (margin-check L cells) |
| `drop_B06` (R8) | 0 |
| `unweighted_recalibration` (R9) | 0 |
| `unweighted_exposure_table` (R10) | 0 |
| **Overfit** `hardcode_rates_by_batch_id` | 1 visible, 0 hidden_a |
| **Overfit** `segment_multipliers_from_visible` | 1 visible, 0 hidden_b |
| **Overfit** `decision_list_constant` | outputs correct numbers but constant list; 0 hidden_b |
| **Cheat** `copy_truth_like_numbers` / edit manifest | 0 (digest; numbers recomputed from agent's rerun) |

## 20. Alternative valid implementations

**Model repairs.**
- Weighted training with or without a weighted calibrator.
- Harmonised resampling.
- 1/rate vs N/n weights.
- Isotonic vs Platt calibration, if weighted.

**Expected counts.** `−ln(1−p)` is required by the interface doc. A zero-truncation alternative giving the same Poisson
mean is accepted by tolerance.

**Feature-conditional calibration.** A weighted calibrator conditioned on segment × form edition is accepted if it
passes the truth tolerance. It is a legitimate population-calibration method, though expected to leave hidden_b
residuals.

**Model variance.** The verifier grades against truth with tolerances sized from the build-time spread of the
`oracle` and `alt_resample_common_rate` mutations over 5 generator seeds. The seed spread of valid methods sets the
tolerance floor.

## 21. Verifier design

1. **Integrity.** Digests of the extracts, manifest, upstream SQL, actuarial and pricing inputs. Run twice; outputs
   identical.
2. **Validation table, observed side.** Per segment, weighted exposure-years and weighted observed claims within 1e-6
   relative of the reference (deterministic under 1/rate).

   Exact-count sampling makes 1/rate and N/n weights differ only by rounding (≤ 1 term per batch × split). The check
   computes both references and passes if the agent matches either. Both designs are documented facts.
3. **Validation table, expected side.** Per segment, `Σ w·μ̂` within ±6% of truth `Σ w·λ·e` over validation records.
4. **Pricing cells.**
   - Each cell with ≥ 1,500 exposure-years: frequency within ±7% of truth. Smaller cells: ±12%.
   - Exposure-years exact.
   - Segment roll-up (verifier aggregates the agent's cells by exposure) within ±4.5%.
5. **LR review.** Overall expected LR within ±2.5 points; per segment ±4 points; `segments_rate_increase_needed` exact.
   The build asserts every segment's truth LR is ≥ 3 points from the 70% boundary.
6. **Hidden A/B/C:** checks 2–5.

**Tolerance justification** (to be measured):
- Valid methods are expected to be within ±3% at segment level across seeds.
- Each named wrong method must exceed its binding tolerance by ≥ 1.5×. That is designed for R1, R2, R4, R5, R6, R8 and
  R9.
- **R3 and R7 are the margin risks.** If R3's segment error falls below 7.5%, strengthen form/seasonal alignment with
  B06. If R7 falls below tolerance, raise L-band probabilities.

## 22. Answer-key leakage audit

| Artifact | Risk | Mitigation |
|---|---|---|
| Manifest | Exact rates per batch; realistic | The inference to weights, and the insufficiency of post-hoc correction, is the task |
| `sample_negatives.sql` | Reveals term-level sampling | A system fact. It does not say how to weight records |
| Extract builder README | Could say "downstream must reweight" | Must say only "non-claim samples reduce extract size; see manifest" |
| Pricing interface doc | Defines target per exposure-year and the Poisson conversion | Business definition; necessary. The ratio-of-sums vs mean-of-rates choice is implied by "claims per exposure-year for the cell" but not spelled out |
| `calibrate.py` | Contains a prior-correction formula (odds × s) | **Scaffolding risk:** it invites R1 and R2, which is intended (natural wrong path), but it also teaches the concept. No weights code anywhere |
| `config/model_v7.yaml` | `negative_keep_rate: 0.10` | A wrong constant, not an oracle |
| Validation reports | Extract-scale numbers | No population-scale number anywhere |
| LR monitor | Realised developed LRs close to expected truth ± noise (±4 points) | Could be used to back-fit segment multipliers (overfit mutation). Hidden fixtures carry their own LR monitors consistent with their worlds, so back-fitting to visible fails, while back-fitting per-world is not a pipeline repair: the pipeline must produce frequencies for the renewal book and cannot read realised future losses. **Remaining risk:** an agent could code "calibrate cell frequencies to the LR monitor" generically. It fails tolerance because LR monitor noise (±4 points ≈ ±6%) plus development lag exceeds cell tolerances. Measure at build |

**Cheap-solve audit.**
- **One grep** (`keep_rate`) → manifest → R1 or R2. Fails.
- **One doc** (pricing interface) → R6/R7 fixes. Partial, fails.
- **One SQL filter:** none helps.
- **One helper:** `calibrate.py`'s correction is the wrong helper.
- **One old report:** v6 validation equals the correct behaviour for v6 only, so restoring v6 is out of scope (the
  model card requires v7).
- **Restoring v6 config** (B01–B04) = R8-like. Fails.
- **Shortest correct path:** "weighted training at term grain + ratio of sums + Poisson". A textbook-aware agent could
  reach it in ~25 actions. See section 27.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| IBNR / late-reported claims | Extract dictionary: claims as reported at the extract build date are treated as complete for frequency (actuarial sign-off); the generator has no late reporting |
| Should validation use a weighted calibrator or none? | Graded against truth; both accepted |
| Train/valid split sampled separately? | SQL: sampling after split, per split rate in manifest |
| Weighted HGB: hyper-parameters unchanged? | Model card fixes them; the weight is a data-design correction, not a hyper-parameter change |
| Exposure for cancelled terms | `exposure_days` in the record is authoritative |
| Severity uncertainty | Actuarial severity is authoritative and equals generator truth severity |
| Premium loading / plan LR | Plan 62% in the actuarial note and FIN config; threshold "8 points above plan" in the memo |
| Expected LR "under premiums actually charged" | Written premium file |
| Could resampling to 0.10 be judged "throwing away data"? | Accepted if within tolerance |
| Rating cell = segment × size band only? | README output schema |

## 24. Expected trajectory length

**Estimate:** 40–65 actions. Each training run is ~40–60 s, so wall-clock time is dominated by 5–10 retrains.

**Why it is long.**
- Two repairs look finished on validation but are not.
- The pricing export and LR review are separate components.
- Distractors need quick quantitative falsification.

**Shorter than G01/G30**, because the evidence is less distributed.

## 25. Why harder than Tasks 03/05/06

- **No helper for weights.** The present helper (scalar prior correction) is on the wrong path.
- **The natural group/merge design is wrong three times:**
  - per-batch correction;
  - calibration-only;
  - mean of rates.
- **The attractor is on the path.** The diagonal decile plot and per-policy O/E ≈ 1 are exactly what an agent checks
  after its first repair.
- **A single-policy check shows nothing.** Correctness appears only at batch × segment and cell × exposure grains.

**Against Task 03.** There is no population-selection sentence. The estimand (population-scale frequency per exposure)
is a business definition, and operationalising it needs both sample-design and exposure reasoning.

## 26. Comparison with Task 02

| | Task 02 | G02 |
|---|---|---|
| Hard part | State per example × cutoff | Sample design must enter estimation; a post-hoc repair looks right |
| Aggregate non-diagnosticity | AUC 0.77 for partial fixes | Overall frequency within ±3% for R2/R3 |
| Grain trap | Entity vs example × cutoff | Record vs term (weights); record vs exposure (ratio) |
| Gradability | Exact features | Truth with tolerance (model variance) plus an exact validation-observed table |

Expected to be **somewhat easier than Task 02** for an agent with statistical training, and harder for one that follows
code scaffolding.

## 27. Benchmark risks

**Headroom: M–H, the main risk.**
- "Importance-weight the negatives" is textbook. An agent that goes straight to weighted training at term grain skips
  R1–R3.
- Remaining difficulty: term grain (R4), exposure ratio (R6), Poisson conversion (R7), per-split rates (hidden_a).
- These are individually modest. **G02 may land as a strong medium task rather than frontier-hard.**
- Strengthening options, without arbitrariness:
  - make training weights interact with the early-stopping validation fraction inside HGB (weighted
    `validation_fraction` behaviour, to be verified);
  - add a documented "claim" definition at term level that excludes $0 claims (closed without payment) for sampling but
    not for frequency, so that a policy term with only a $0 claim was sampled as non-claim.

    That creates a third weight class discoverable only by joining claim status to the SQL. It is realistic, but
    increases complexity.

**Gradability: M.** Model fit noise vs tolerances. R3 and R7 margins must be verified. Tolerances come from the seed
spread of valid methods, and every wrong method's margin is reported.

**Implementation cost: M.**
- Stdlib generator of ~330k extract records plus a renewal book is easy.
- Tuning the absorbed-bias magnitudes needs iteration with the real pipeline (sklearn in the image).
- Verifier runtime: 4 worlds × ~1 min training.

**Realism: high.**
- Batch-varying downsampling, the scalar correction inherited from an older version, exposure-based pricing and a
  concurrent engine release are all ordinary.
- Simplifications: no IBNR, and severity is exact.

**Leakage: L–M.** The manifest is necessary and factual.

**Underspecification: M.** Accepted calibrator variants; the LR-monitor back-fitting probe.

**Overlap: low** with Tasks 01–06 and the other gen-3 designs. G01 and G30 share "evaluation population" vocabulary but
not mechanics.
