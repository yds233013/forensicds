# G01: Collections cure model "degradation" under label maturity, contact policy and an acquired book

Status: design only. Nothing is built and no model has been run. All numbers are generator design targets. They must be
re-measured at build time and written into the validation report; they are not results.

## Workspace sketch

```
/workspace
  README.md                                   what cure_eval is, how the monthly job runs, where outputs go
  CHANGELOG.md                                cure_eval 1.4 → 2.1 (2.1.0, 2026-03: "latest vintage early read"); neutral wording
  config/cure_eval.yaml                       warehouse path, score bands, output dirs (no thresholds, no cutoffs, no latencies)
  data/warehouse.duckdb            ~110 MB    tables below; extract taken 2026-09-15 06:00 UTC
  data/raw/servicer/HPF_REMIT_2026MM.csv.gz   ~3 MB  remittance files as received from the HPF legacy servicer (Feb–Jul, June absent)
  data/raw/servicer/manifests/*.json          one manifest per delivered file: coverage_start/end, row_count, loaded_at
  src/cure_eval/cli.py                        `python -m cure_eval run --out out/`
  src/cure_eval/warehouse.py                  DuckDB readers (episodes, scores, payments)
  src/cure_eval/labels.py                     FAULTY: cure from payments by posted_at
  src/cure_eval/population.py                 FAULTY: "known outcome" population (early read)
  src/cure_eval/metrics.py                    AUC (Mann-Whitney), band cure rates; correct, generic
  src/cure_eval/report.py                     writes monitoring JSON/CSV; no status logic
  notebooks/2026-08_ptp_degradation_deepdive.ipynb   analyst notebook: PSI by feature, AUC by vintage, concludes "drift"
  docs/model_card_ptp_v3.md                   target, population, development data, development AUC 0.742
  docs/risk/MRS-4_model_performance_standard.md      assessment principles + status thresholds
  docs/data/warehouse_dictionary.md           table/column semantics incl. value_date, posted_at, hub close, manifests
  docs/collections/contact_strategy_CS-7.md   CS-7 design: threshold, day-3 call, holdout cell and its purpose
  docs/ops/hpf_boarding_runbook.md            boarding of acquired book, servicer remittance process
  docs/ops/payment_hub_PH-2_cutover.md        payment hub migration, value-date close pause
  reports/monitoring/cure_monitor_2026-{02..09}.json  8 monthly monitors produced by the faulty job at each run date
  reports/monitoring/psi_2026-08.csv          feature PSI vs development sample
  reports/strategy/cs7_uplift_readout_2026-06.md     strategy team readout: "+15.1 pp cure from early contact"
  notes/risk/2026-09-02_retire_ptp_v3_proposal.md    Credit Risk proposal to retire the model
  inbox/2026-08-21_hpf_june_remittance_hold.eml      servicer: June file held for reconciliation
  logs/job_runs.csv                           run dates, code version, row counts of each monthly run
```

Warehouse tables (visible extract):

| Table | Grain | Rows | Key columns |
|---|---|---:|---|
| `accounts` | account | ~118k | account_id, portfolio (`in_house`/`hpf`), product, boarded_at |
| `episodes` | collections episode | ~141k | episode_id, account_id, entry_date (DPD30 roll date), cure_amount, opened_at |
| `ptp_scores` | episode | ~141k | episode_id, model_version, score, scored_at |
| `strategy_assignments` | episode | ~141k | episode_id, strategy (`CS-5`/`CS-7`), cell (`bau`, `early_contact`, `holdout`), assigned_at |
| `strategy_config_log` | config change | 4 | effective_from, strategy, threshold, holdout_rate |
| `contact_attempts` | call attempt | ~610k | episode_id, attempt_ts, direction (`outbound`/`inbound`), outcome |
| `payments` | payment | ~236k | payment_id, account_id, amount, channel, value_date, posted_at, source_system (`hub`/`hpf_servicer`), file_id |
| `hub_value_date_close` | hub business day | ~620 | business_date, complete_through_value_date, published_at |
| `servicer_file_manifest` | delivered file | 6 | file_id, coverage_start, coverage_end, row_count, loaded_at, status |

## 1. Research question

Can an agent decide whether a scoring model has actually degraded when the apparent degradation comes from three
interacting label mechanisms? The mechanisms are:

- labels are observed through posting systems with source-specific completeness;
- early outcomes are informative, so partially observed windows over-represent fast curers;
- a score-driven treatment changes the outcomes the model is evaluated against.

The agent must rebuild an exact episode label table and evaluable population. It must then estimate the model's
performance against its documented target outcome (cure under the contact strategy it was developed for), which is
only partly observed after the policy change. Finally it must reach the model-risk decision that the evidence supports.

## 2. Enterprise setting

Larkfield Bank (fictional) is a consumer lender. Accounts that reach 30 days past due enter collections and
open an **episode**. At entry, `ptp_v3` scores each episode with the probability of *cure within 30 days*. Contact
strategy uses the score to prioritise outbound calls.

In December 2025 the bank acquired the Harbor Point Finance (HPF, fictional) personal-loan book. HPF accounts were
boarded into in-house collections on 2026-02-02. Their payments are still processed by the HPF legacy servicer, which
delivers monthly remittance files.

Credit Risk Analytics owns the monthly `cure_eval` job, and Model Risk decides model status under standard MRS-4.

## 3. Visible symptom

The instruction memo comes from the Head of Model Risk. It says:

- The monthly cure monitors show `ptp_v3` AUC falling from 0.74 to 0.67 over two quarters, and observed cure running
  well below prediction.
- Credit Risk has proposed retiring the model, and the analyst deep-dive attributes the fall to drift, since feature PSI
  is up.
- Collections disagrees. Its CS-7 readout says cure is *up*.

The memo asks for:

1. A repaired `cure_eval` whose command `python -m cure_eval run --out out/` writes:
   - `out/labels/episode_labels.csv`
   - `out/eval/vintage_metrics.csv`
   - `out/eval/model_assessment.json`

   in the formats in `README.md`.
2. The assessment and status must follow the model card and MRS-4.
3. The job must work on any future extract, with no special-casing of portfolios, files, dates or strategies.
4. The data, raw files, docs and historical reports must not be modified.

The memo does not mention posting, maturity, completeness, value dates or treatment effects.

Faulty monitors, computed at build from the faulty job at each historical run date (design targets):

| Monitor run | AUC | Observed / expected cure | HPF share of scored episodes |
|---|---:|---:|---:|
| 2026-02-15 | 0.741 | 1.00 | 0% |
| 2026-04-15 | 0.722 | 0.93 | 9% |
| 2026-06-15 | 0.694 | 0.87 | 18% |
| 2026-09-15 | 0.668 | 0.83 | 26% |

## 4. Source distribution inspiration

This mirrors ordinary practice in retail credit collections analytics:

- **Outcome windows and immature vintages.** Vintage analysis with outcome windows, and the rule that immature vintages
  are not performance evidence.
- **Two dates per payment.** Payments carry a value (effective) date and a later posting date. Arrears are computed at
  value date.
- **Acquired books.** An acquired book stays on a legacy servicer for months and sends batch remittance files. Those
  files are late, held for reconciliation, or delivered out of order.
- **Champion/challenger contact strategies.** Collections strategies are tested with random holdout cells, and the
  holdout is designed to measure strategy uplift, not model quality.
- **Model risk.** Model risk governance asks whether performance is measured against the model's target definition.

The statistical content is standard: informative censoring (label availability correlates with outcome), selection on
treatment, and potential outcomes with a randomized cell.

No literature is cited. The link to "selective labels / performative prediction" literature is to verify, as in the
Task 03 design.

## 5. Causal graph / ground truth

The generator is standard-library Python, seeded, and runs per world.

**Episodes.**
- In-house: 6,000 per month, 2025-01 to 2026-09-15.
- HPF: from 2026-02-02, at 900 / 1,300 / 1,700 / 2,000 / 2,200 / 2,400 / 2,500 / 2,500 for Feb–Sep.

**Score and target.**
- The score at entry is `s`.
- The true BAU cure probability is `logit(p_bau) = logit(s) + δ_portfolio`, with `δ = 0` for both portfolios in the
  visible world, so the model is calibrated and stable.
- Development AUC is 0.742.

**Potential outcomes.**
- One uniform draw `U` per episode is shared by both potential outcomes:
  - `Y_bau = 1[U < p_bau]`
  - `Y_early = 1[U < p_early]`
  with `logit(p_early) = logit(p_bau) + τ(s)`.
- `τ = 0.55` for `s ∈ [0.55, 0.75)` (≈ +12 pp) and `τ = 0.45` for `s ≥ 0.75` (≈ +6 pp).

**Cure timing.**
- For BAU cures, the cure day is drawn from a discretised gamma with median day 13.
- Under early contact the median is day 7.
- Cures are realised by 1–3 payments whose cumulative amount reaches `cure_amount` on the cure day.
- Non-cures receive partial payments that total 20–80% of `cure_amount` (the partial-payment trap).

**Contact strategy.**
- CS-5 runs until 2026-03-08: first outbound call on day 10 for everyone.
- CS-7 starts 2026-03-09:
  - `s ≥ 0.55` → cell `early_contact` (day-3 call) with probability 0.90, else `holdout` (day 10).
  - From 2026-06-01 the holdout rate is 0.05.
  - `s < 0.55` → `bau`.
- Assignment is a hash of `episode_id`, recorded in `strategy_assignments` and in `strategy_config_log`.
- **Compliance.** 85% of `early_contact` episodes are reached by day 3; the rest are called on day 9–11. The realised
  outcome for unreached episodes is `Y_bau`.
- **Inbound calls.** 12% of all episodes have an inbound customer call on day 1–4. Inbound callers have `p_bau` raised
  by +0.10 in the generator. This makes "first contact day" outcome-related, which supports the per-protocol trap.

**Payment posting.**
- `hub` source, by channel:
  - direct debit and card: posted 0–1 days after value date (62%);
  - bank transfer: 1–4 business days (30%);
  - branch/cash: 2–6 days (8%).
- After the PH-2 cutover (2026-04-20), bank transfer takes 2–7 business days.
- `hub_value_date_close` publishes nightly `complete_through_value_date`, normally business_date − 6 calendar days.
  From 2026-04-18 to 2026-05-03 it is frozen at 2026-04-14 (PH-2 pause) and then jumps.
- The generator guarantees that no hub payment is posted after the close that first covers its value date.
- `hpf_servicer`: all payments for coverage month M are posted at that file's `loaded_at`:
  - normally the 11th–14th of M+1;
  - the June 2026 file is held (`status = 'held_reconciliation'` in the inbox email, and absent from the manifest)
    and is not loaded by the extract;
  - the July file was loaded 2026-08-13;
  - the August file is not yet due.

**Visible completeness at extract (2026-09-15).**
- Hub watermark 2026-09-08, so in-house episodes are complete for entry ≤ 2026-08-09.
- HPF coverage is February–May plus July, with June missing.
  - HPF episodes are complete for entry ≤ 2026-05-01.
  - They are also complete for entry = 2026-07-01, whose window lies entirely in July (generator guarantees ≥ 40 such
    episodes).
- The *maximum* HPF coverage end is 2026-07-31.

**Distractor mechanisms (real, non-causal for degradation).**
- HPF accounts have different bureau-score and months-on-book distributions, which puts PSI at 0.28–0.34 on three
  features. In-house-only PSI is ≤ 0.05.
- PH-2 lengthens bank-transfer posting.

## 6. Latent statistical/business invariant

**(a) Label.**
- `cure_30d = 1` iff the sum of payment `amount` with `value_date ∈ [entry_date, entry_date + 30]` (inclusive) is ≥
  `cure_amount`, using every payment row present in the extract.
- The label is *determined* if it is 1, or if the episode's outcome window is complete.

**(b) Window completeness.**
- An episode is evaluated iff every value date in its window `[entry_date, entry_date + 30]` is known to be fully
  loaded for its source at extract time.
- **Hub:** every date in the window is ≤ the latest `complete_through_value_date` with `published_at ≤ extract_ts`.
- **Servicer:** every date in the window lies inside the coverage of some manifest file with `loaded_at ≤ extract_ts`.
  - This is per-window coverage, not "max coverage end", which ignores gaps.
  - It is also not "contiguous from first month", which needlessly drops windows after a gap.
- Episodes with an early cure but an incomplete window are **not evaluated**. The label table still shows
  `cure_30d = 1`.

**(c) Target performance.**
- The model's target is `Y_bau` for all scored episodes.
- **CS-5 episodes:** observed outcome = `Y_bau`.
- **CS-7 `bau` cell** (s < threshold): observed = `Y_bau`.
- **CS-7 `early_contact`:** `Y_bau` is not observed.
- **CS-7 `holdout`:** observed = `Y_bau`, for every holdout episode as assigned, whatever the actual contact.
  The holdout is a random sample of above-threshold episodes, with inclusion probability equal to the holdout rate in
  force at assignment.
- So target band cure rates for above-threshold bands must come from the holdout.
- Target AUC over a strategy period must represent the full score distribution: above-threshold holdout episodes
  weighted by the inverse holdout rate, or an equivalent stratified or outcome-model estimator.

**(d) Status.** MRS-4 thresholds are applied to the target-based estimates:
- `retire` if target AUC in any strategy period is < development AUC − 0.05;
- else `recalibrate` if any band's |target cure rate − mean score| > 0.06;
- else `stable`.

Visible truth: `stable`.

## 7. Grains and state variables

- **Episode:** entry_date, score, portfolio, strategy, cell.
- **Payment:** value_date vs posted_at; source system; file.
- **Source completeness state over time:**
  - hub: daily watermark, with a pause;
  - servicer: set of loaded coverage months, with a gap.
- **Outcome window state per episode:** determined cured / determined not cured / undetermined; complete / incomplete.
- **Strategy period × cell × band:** inclusion probability.
- **Vintage month × portfolio:** descriptive metrics.
- **Strategy period:** target AUC and band calibration; status.

Mistakes between grains matter:

- **Payment date grain.** Posting-date labels are wrong at the payment grain.
- **Watermark grain.**
  - A "max coverage" watermark is wrong at the source-state grain.
  - A global lag is wrong at the source grain.
- **Population grain.**
  - "Label determined" is wrong at the episode-state grain.
  - Treated outcomes are wrong at the cell grain.

## 8. Evidence graph

N = on the natural path (an agent reproducing the symptom will touch it).

| Artifact | Shows | N? |
|---|---|---|
| `reports/monitoring/cure_monitor_*.json` | AUC/O-E decline; HPF share rising; latest vintage O/E > 1 (early read) | N |
| `notes/risk/..._retire_proposal.md` | Retire recommendation; cites PSI and monitors | N |
| `notebooks/2026-08_ptp_degradation_deepdive.ipynb` | PSI up; AUC by vintage falls; "drift" | N |
| `src/cure_eval/labels.py`, `population.py` | Posting-date labels; early-read population | N |
| `CHANGELOG.md` | 2.1.0 early read added so the dashboard shows the latest month; HPF boarding added HPF episodes to scoring | N |
| `docs/model_card_ptp_v3.md` | Target: cure (arrears cleared) within 30 days of entry, for episodes worked under CS-5; population: all scored episodes | N |
| `docs/risk/MRS-4...md` | Assess against the documented target and population; outcomes over the full outcome window; thresholds | N |
| `docs/data/warehouse_dictionary.md` | `value_date` = date funds are effective, and arrears are computed at value date; `posted_at` = ledger posting; hub close semantics; servicer files post on load | N (read when inspecting payments) |
| `docs/collections/contact_strategy_CS-7.md` | Threshold, day-3 call, holdout cell "to measure strategy uplift", holdout rate cut | partly |
| `reports/strategy/cs7_uplift_readout_2026-06.md` | "+15.1 pp cure among treated vs holdout" (early-read labels) | partly (attractor) |
| `docs/ops/hpf_boarding_runbook.md` | Monthly remittance files; typical delivery "around the 12th"; reconciliation holds can delay a month | no |
| `inbox/2026-08-21_hpf_june_remittance_hold.eml` | June file held | no |
| `servicer_file_manifest`, `data/raw/servicer/manifests` | Coverage months loaded; June missing | N once HPF labels are examined |
| `hub_value_date_close` | Watermark, PH-2 pause | no |
| `docs/ops/payment_hub_PH-2_cutover.md` | Bank-transfer lag change; close pause | no |
| `contact_attempts` | Inbound calls, early-contact compliance | partly (per-protocol attractor) |
| `reports/monitoring/psi_2026-08.csv` | PSI 0.28–0.34 on bureau score, months on book, loan age | N |

## 9. Evidence authority hierarchy

1. **Raw data and system logs** (payments, manifests, hub close log, assignments) govern facts about what happened and
   what is loaded. Where the runbook says files arrive "around the 12th", the manifest governs: June is not loaded.
2. **The model card and MRS-4** govern *what* is measured: target outcome, population, window and thresholds.
   - They override the CS-7 readout, which measures uplift and not model quality.
   - They override the monitors, whose semantics are the faulty job's.
3. **The warehouse dictionary** governs column meaning. It overrides the faulty code's use of `posted_at`, because the
   model card's target is arrears cleared, and arrears are computed at value date.
4. **The CS-7 design doc** governs assignment mechanics: randomisation, rates, and that holdout membership is at
   assignment.
5. **Reports, notebooks, readouts and proposals** are derived evidence. Their numbers share the faulty semantics and
   must be reproduced, not trusted.

## 10. Plausible hypotheses

| # | Hypothesis | Evidence for | Evidence against |
|---|---|---|---|
| H1 | Real drift or degradation★ | PSI 0.28–0.34; AUC by vintage falls; notebook | PSI is explained by HPF composition (in-house-only PSI ≤ 0.05); CS-5 in-house vintages with complete windows keep AUC 0.735–0.748 |
| H2 | HPF data defect★ (feed "broken", acquired accounts never cure) | HPF observed cure near 5% with posting-date early labels; HPF AUC 0.55 | HPF value-dated payments exist; cures appear once files load; June file hold |
| H3 | Label maturity / early read★ | Latest vintage O/E > 1; CHANGELOG 2.1.0 | Removing the early read *worsens* the headline AUC (HPF dominates) |
| H4 | CS-7 policy effect★ | Readout +15 pp; high-band O/E > 1 after March | Policy raises cure, and the symptom is *falling* O/E; it cannot explain the headline, only mask or distort |
| H5 | PH-2 posting delay | Bank-transfer lag rose in April | Affects ~1.5% of in-house labels with posting dates, and none with value dates |

Truth: H2 is a latency artefact rather than a defect, H3 and H5 are real label mechanisms, H4 is a real confounder of
assessment, and H1 is false in the visible world. Hidden fixtures make H1 true (hidden_c) and give a real HPF calibration
shift (hidden_b).

## 11. Why each wrong hypothesis is plausible

- **H1.** PSI is the standard monitoring signal. It really is high, and the notebook's per-vintage AUC chart looks like
  textbook decay. Decomposing PSI by portfolio takes a deliberate step.
- **H2.** With posting-date labels, HPF cure is implausibly low. The obvious conclusion is a broken feed, and the
  obvious action is to exclude HPF. The email about a held file reinforces "the feed is unreliable".
- **H4.** The readout gives a large, concrete uplift number that invites a "subtract the uplift" adjustment.
- **H5.** A real migration with a documented lag change. Changing the maturity window by a few days "fixes" it
  superficially.

## 12. Investigation path (≈45–75 actions)

1. **(1–8) Read the inputs.** Memo, README, monitors, proposal, notebook. Run the job and reproduce AUC 0.668.
2. **(9–15) Read the code.** `labels.py` uses `posted_at`, and `population.py` includes cured-to-date episodes. The
   CHANGELOG explains the early read.
   - **Discovery 1:** immature cures are included. The natural repair follows (section 13).
3. **(16–22) Slice metrics.**
   - By portfolio: HPF is terrible. By vintage: still falling after the maturity filter.
   - **Discovery 2:** HPF payments post on file load, weeks after value date.
   - Read the dictionary: `value_date`. Model card: arrears cleared.
4. **(23–30) Switch to value dates.**
   - HPF recent vintages are still low. Inspect the manifest: June is missing, and HPF cure rate for May–June entries
     collapses.
   - **Discovery 3:** completeness is per source and per window's coverage. Find `hub_value_date_close` and the PH-2
     pause.
5. **(31–38) Build the watermark rule and compare evaluable sets by source.** Row-check a handful of HPF episodes whose
   cure payments sit in the July file, and hub episodes in the PH-2 pause.
6. **(39–48) Separate strategy periods.**
   - Complete CS-7 episodes above threshold have cure rate 12 pp above score → "recalibrate?".
   - Read the model card target (CS-5) and MRS-4.
   - **Discovery 4:** treated outcomes are not the target outcome.
   - Read the CS-7 doc and `strategy_config_log` (holdout rates 10% → 5%).
7. **(49–58) Estimate the target.**
   - Holdout band rates.
   - Target AUC with inverse-probability weights; notice the unweighted pool is biased.
   - Consider the per-protocol variant using `contact_attempts` and reject it.
8. **(59–68) Finish.**
   - Status.
   - Validate the label table on sampled episodes (payments listed by value date).
   - Check that CS-5 in-house metrics are unchanged by the repair.
   - Determinism re-run. Write outputs.

## 13. Natural wrong implementation

**Faulty code (as shipped).**

`labels.py`:
- `cured_by(ep, t)` sums `payments.amount` where `posted_at::date` falls between `entry_date` and `t`.
- `cure_30d = cured_by(ep, entry_date + 30) >= cure_amount`.

`population.py`:
- `known = (entry_date + 30 <= run_date) | cured_by(ep, run_date) >= cure_amount`.
- Metrics are computed over `known`.

**Natural repair R1 (after "label maturity" is recognised).** Drop the early-read OR and keep
`entry_date <= run_date - 30`, with posting-date labels unchanged. Some agents use `- 45` or `- 60` "for safety".

What R1 gets wrong (visible design targets):

- **HPF.** 71% of HPF cures post after day 30, because files load 11–45 days after value date. HPF observed cure is
  ~9% vs mean score 0.31, and headline AUC stays at 0.681.
- **Status.** R1 yields `retire`, the same wrong decision as the faulty job.
- **Label table.** It is wrong on ~7,900 episode labels:
  - ~6,300 HPF;
  - ~1,600 in-house bank-transfer and branch cures with value date ≤ day 30 and posting > day 30.
- **Evaluated set.**
  - It includes ~9,800 HPF episodes whose window is incomplete (entries 2026-05-02 to 2026-08-16).
  - It excludes nothing it should include, except with a −60 buffer, which drops ~3,700 complete in-house episodes.

## 14. Second-order failure modes

| ID | Repair | Why wrong | Visible effect (design targets) |
|---|---|---|---|
| R2 | Exclude HPF ("data defect") | Model card population includes HPF; the label table must cover HPF | AUC 0.738 in-house; but CS-7 band [.55,.75) observed − score = +0.12 → `recalibrate`; label table missing/incorrect HPF rows |
| R3 | Value-date labels + global 30-day maturity | HPF windows June–Aug incomplete (servicer files missing) | HPF May–Jul cure rates 0.10–0.14 vs 0.31; status `recalibrate` (HPF bands) |
| R4 | Value-date labels + per-source *max* coverage watermark (Jul 31) | Ignores June gap; June-window HPF episodes look uncured | ~2,100 wrongly evaluated HPF episodes; band [.2,.35) target error −0.07 → `recalibrate` |
| R5 | Value-date labels + empirical per-source lag (e.g. 99th percentile posting lag: hub 9d, HPF 45d) | Lag is not completeness; fails on the gap (visible) and on hidden late files | Visible: HPF entries up to 2026-07-02 included → R4-like error; hidden_b worse |
| R6 | Correct labels and watermarks, but "label determined" population (early cures of incomplete windows kept) | Informative censoring: fast curers over-represented | HPF May–Jul entries with cures in the July file are included, and non-cures are not; HPF band cure rates +0.09 |
| R7 | Correct labels and population, all outcomes as observed (policy ignored) | Treated outcomes ≠ target | CS-7 band 4 +0.12, band 5 +0.06 → `recalibrate`; target AUC inflated by ~0.01 |
| R8 | R7 minus readout uplift (15.1 pp) from early-contact observed rates | Readout uses early-read labels; uplift varies by band and compliance | Band 4 −0.03, band 5 −0.09 → `recalibrate` |
| R9 | Target from untreated episodes pooled unweighted (`bau` + `holdout`) | Above-threshold episodes under-represented 10–20×; AUC over-weights within-low-score pairs | Target AUC CS-7 ≈ 0.69 vs truth 0.742 (to verify at build) → risk of `retire` |
| R10 | Holdout per-protocol: drop holdout episodes with inbound or outbound contact before day 10; drop unreached early-contact | Contact timing depends on customer behaviour related to cure | Band 4 target −0.04; uplift +0.03 inflated |
| R11 | Target from CS-5 vintages only (declare CS-7 "not assessable") | Model card population includes current episodes; HPF barely exists in CS-5; MRS-4 needs both periods | Output schema requires CS-7 estimates; missing → fail |

## 15. Correct repair properties

- The label uses value dates and every payment row. No dependence on `posted_at` except through source completeness.
- Completeness comes from source state at extract time:
  - the hub close log;
  - servicer file coverage of the whole window from the manifest, never from observed payment dates or typical lags.
- The evaluated population is episodes with a complete window. No outcome-dependent inclusion.
- Target estimates use outcomes observed under the development strategy:
  - all CS-5 episodes;
  - the CS-7 `bau` cell;
  - the CS-7 holdout as assigned, with inclusion probability from `strategy_config_log` at `assigned_at`.
- The uplift estimate is ITT by cell assignment.
- Thresholds, holdout rates and strategy dates are read from data, not constants.
- Output is deterministic (sorted rows, fixed float formatting).

## 16. Repair surfaces

| Surface | Why it must change |
|---|---|
| `labels.py` | Value-date label; determined vs undetermined state |
| New completeness logic (e.g. `completeness.py` or SQL) | Per-source watermark: hub log and contiguous manifest coverage |
| `population.py` | Evaluated = complete window; remove outcome-dependent inclusion |
| New target assessment (`assessment.py`) | Strategy-period target band rates, weighted target AUC, ITT uplift, status via MRS-4 |
| `report.py` / `cli.py` | Three outputs in README formats |
| `warehouse.py` | Readers for the hub close log, manifest, assignments and config log |

Nothing in the faulty code reads the last four tables, so there is no helper to reuse.

## 17. Validation requirements

An agent needs these checks to be confident, and aggregates cannot replace them:

- **Row-level label audit.** For sampled episodes of each source and channel, list payments with `value_date`,
  `posted_at` and `file_id`, and confirm the label. HPF and bank-transfer rows are the ones that differ.
- **Completeness audit.** For HPF episodes with entry dates in 2026-05 to 2026-07:
  - which coverage months their windows need;
  - whether those months are loaded.

  The June gap is invisible in any aggregate that uses max coverage.
- **Informative censoring check.** Cure rate by entry-day within the latest months, complete vs incomplete. An
  incomplete-but-cured subset shows cure rate 1.0 and shorter cure times.
- **Cell-level check.**
  - Holdout vs early-contact cure rate by band.
  - Holdout share by assignment date: 10%, then 5%.
  - Balance of score distribution across cells (randomisation check).
- **Stability anchor.** CS-5 in-house complete vintages must be unchanged between R1 and the repair, apart from
  in-house late-posting labels. This separates label fixes from population fixes.

Headline AUC alone can land at ~0.74 for R2, R7 and the oracle, so it is non-diagnostic.

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface changes | Overfit / shortcut caught | Same distribution because |
|---|---|---|---|---|
| hidden_a (extract 2026-12-10) | Watermark from source state, not lags; cell weights from config log | Servicer files load on the 4th–6th with no gap; hub close lag 4 days; no PH-2 pause; CS-7 threshold 0.50, holdout 15% then 8%; bank transfer 45% of hub payments | Hard-coded threshold 0.55, rates 10%/5%, date 2026-06-01; lags estimated on visible (R5 now over-excludes); visible-calendar constants | Same tables and documented mechanics; only rates, calendars and threshold values in `strategy_config_log` change |
| hidden_b (extract 2026-08-20) | Per-window coverage across gaps; complete-window population; real calibration shift | Two servicer gaps (April file held, then a re-delivered May file loaded before April); hub close pause 9 days; HPF share 40%; **true δ_hpf = −0.45 logit** (HPF over-predicted ≈ −0.08) → truth `recalibrate` | R4 (max coverage), R5 (lags), R6; "always stable"; exclude HPF (R2 → `stable`, wrong) | Held files and pauses are documented and exercised visibly; δ is a model-quality change, which is exactly what is assessed |
| hidden_c (extract 2027-02-15) | Target separation under masking | From 2026-10 in-house `logit p_bau = 0.55·logit(s) + c` (score less informative): target AUC CS-7 = 0.664 → truth `retire`; early-contact τ larger (+0.18 in band 4) so observed-outcome AUC stays ≈ 0.72 | R7/R8 (say `recalibrate`), R9 (AUC direction unstable), hard-coded "stable", CS-5-only assessment (R11) | Treatment effect size and model quality are the assessed quantities; no new rule |

All three fixtures are generated by the same generator with different seeds and parameters. None introduces a table,
column, cell type or rule that is absent from the visible workspace.

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` (pandas) | 1 |
| `alt_sql_duckdb` (labels, watermarks and population in SQL; stratified-by-band target AUC estimator) | 1 |
| `alt_outcome_model` (target band rates from the holdout; AUC via weighted Mann-Whitney over a CS-7 resample) | 1 (tolerance probe) |
| `fixed_window_posting` (R1) | 0 (labels, population, status) |
| `fixed_window_posting_60` | 0 |
| `exclude_hpf` (R2) | 0 |
| `value_date_global30` (R3) | 0 |
| `max_coverage_watermark` (R4) | 0 visible |
| `empirical_lag_p99` (R5) | 0 visible and hidden_b |
| `contiguous_from_start_watermark` | 0 visible (drops the ≥ 40 July-only windows); 0 hidden_b |
| `label_determined_population` (R6) | 0 |
| `ignore_policy` (R7) | 0 (status visible; hidden_c) |
| `subtract_readout_uplift` (R8) | 0 |
| `untreated_unweighted` (R9) | 0 on target AUC (confirm margin at build; if < 2× tolerance, strengthen by lowering the holdout rate) |
| `per_protocol_holdout` (R10) | 0 on uplift or band 4 (confirm margin) |
| `cs5_only_target` (R11) | 0 |
| **Overfit** `hardcode_cs7_params` (0.55, 10%/5%, 2026-06-01) | passes visible, fails hidden_a |
| **Overfit** `hardcode_hpf_complete_through_2026-05-31` | passes visible, fails hidden_a/b |
| **Overfit** `status_constant_stable` | passes visible, fails hidden_b/c |
| **Cheat** `patch_outputs` / edit warehouse | 0 (recomputed from rerun; digest) |

## 20. Alternative valid implementations

**Target AUC.** Accepted estimators:
- inverse-probability-weighted AUC (weight `1/holdout_rate` for holdout episodes, 1 otherwise);
- stratified resampling;
- band-stratified pair counting;
- any consistent estimator within tolerance.

**Target band rates.**
- Accepted: holdout-only, or holdout weighted by period (equivalent within tolerance, because rates are constant within
  a band).
- Pooling the CS-7 `bau` cell with CS-5 for below-threshold bands is valid.

**Uplift.** Difference in means by cell, or regression with band × period, is accepted.

**Implementation language.** SQL vs pandas for labels and watermarks both work; the tables are exact, so any correct
implementation matches.

## 21. Verifier design

**Fixture setup.**
- Regenerate the visible world and compare a logical digest of the warehouse, the raw servicer files and the docs.
- Delete `out/` and run the job twice as an unprivileged user. Outputs must be byte-identical.
- For each hidden world: install it, run, restore.

**Checks** (binary reward, all must pass):

1. **Label table.**
   - Exactly one row per episode with `entry_date ≤ extract date`.
   - `cure_30d ∈ {1, 0, blank}` exactly equals the reference.
   - `evaluated` exactly equals the reference.
   - Mismatches are reported by source and by reason: label, watermark, determinism.
2. **Vintage metrics.**
   - Over `evaluated` episodes: n, cure rate, mean score, AUC per vintage × portfolio (`in_house`, `hpf`, `all`).
   - Tolerance 1e-6, recomputed from the agent's own label table and required to match the reference. This catches
     patched numbers.
3. **Target band rates.**
   - For each strategy period (`CS-5`, `CS-7`) × band, the estimate is within
     `tol = max(0.03, 3·sqrt(p(1−p)/n_obs))` of generator truth.
   - Truth = mean of `Y_bau` over *evaluated* episodes in the cell.
   - `n_obs` = episodes whose `Y_bau` is observed (holdout for above-threshold CS-7).
   - Visible band 4 CS-7: n_obs ≈ 520, tol ≈ 0.064.

   The band-4 tolerance is too wide against R7's +0.12 only if the margin shrinks; design target: R7 error ≥ 1.8×
   tol. **If the build measurement gives less, raise the visible volume or holdout rate** (see risks).
4. **Target AUC** per strategy period: within 0.025 of truth, where truth = AUC of score vs `Y_bau` over all evaluated
   episodes in the period.
5. **CS-7 uplift** per above-threshold band: within `max(0.04, 3·SE)` of the truth ITT (`Y_assigned − Y_bau`).
6. **Status** exactly equals truth. The truth status is derived from truth quantities.

   At build, the generator checks that every truth quantity sits at least 1.5 tolerances away from the MRS-4 thresholds,
   so status is not fragile. Worlds failing this are re-parameterised before freezing, never at verification time.
7. **Hidden A/B/C:** checks 1–6.

**Ground truth vs reference.**
- Checks 1–2 use an independent pure-Python reference (`tests/reference.py`), because the rule is deterministic.
- Checks 3–6 use generator truth, because the estimator is not unique.

**Build-time calibration probe.**
- On visible and hidden worlds, `oracle`, `alt_sql_duckdb` and `alt_outcome_model` must all pass 3–6.
- Each wrong mutation's error must be reported as a multiple of tolerance.

## 22. Answer-key leakage audit

| Artifact | Could it be transcribed or matched? | Mitigation |
|---|---|---|
| Model card | States target "under CS-5" and population "all scored episodes"; does not say how to observe CS-5 outcomes after CS-7 | Keep the sentence descriptive; no mention of holdout, weights or CS-7 |
| MRS-4 | "Full outcome window" pushes toward maturity, but says nothing about sources, contiguity, value date or treatment | Principles plus thresholds only. This is the biggest leakage risk (M): the phrase "documented target" is a strong hint once CS-7 is noticed |
| CS-7 doc | Describes the holdout "to measure uplift"; rates are in the config log, not the doc | Must not say "unbiased sample for model monitoring" |
| Warehouse dictionary | Defines `value_date` and "arrears computed at value date"; hub close "all hub payments with value date ≤ X have been posted"; manifest columns | Facts only. The completeness sentence for the hub is close to an answer for the hub, so leakage there is accepted; the servicer contiguity must be inferred (the manifest documents coverage per file, not a watermark) |
| Runbook, email | Delivery timing and held file | "Around the 12th" is deliberately a typical value, which the manifest overrides |
| Monitors, notebook, readout | Faulty semantics; no correct numbers | Generated by the faulty job; no correct per-vintage table exists anywhere |
| `metrics.py` | Generic AUC; no weights parameter | Must not accept `sample_weight` (avoid a nearly-correct branch) |
| `config/cure_eval.yaml` | Bands only | No thresholds, lags or dates |

**Cheap-solve audit.**
- **One grep.** `value_date` finds the dictionary. This fixes labels only (≈ R3), which fails.
- **One doc.** MRS-4 fixes the early read only (R1), which fails.
- **One SQL filter.** `cell != 'early_contact'` gives R9, which fails on target AUC *if* the build margin holds. This is
  the main residual cheap-solve risk.
- **One helper.** None exists.
- **One old report.** The pre-HPF monitor (Feb) AUC of 0.741 happens to equal truth. An agent could "restore behaviour"
  by excluding HPF (R2). That fails on the label table and gives the wrong status via the CS-7 bands.
- **Restoring prior behaviour.** Reverting to cure_eval 1.4 (pre-early-read) equals R1, which fails.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Is day 30 inclusive? | Model card: "within 30 days of entry, entry day = day 0, through day 30". The label table grades it; the generator places ~1% of cures exactly on day 30 |
| Value date vs posting date | Dictionary ("arrears computed at value date") plus model card ("arrears cleared") |
| Is a payment before `entry_date` counted? | The generator creates none; stated in the dictionary ("episodes open with arrears unpaid at roll date") |
| Hub watermark: `published_at ≤ extract` or `business_date ≤ extract`? | Extract timestamp is in `logs/job_runs.csv` and the DuckDB `extract_metadata`; the generator avoids closes published within ±1 day of extract |
| Servicer coverage gap: is data after the gap usable? | Yes. A loaded file's coverage is complete in itself (manifest `row_count` and coverage fields; runbook: "each file is the complete remittance for its coverage period"). The oracle is per-window coverage. An earlier draft of this design used "contiguous from start"; this audit judged it arbitrary, so it became a mutation. The rejection of contiguous-from-start rests on only ≥ 40 visible episodes (entry 2026-07-01), which is a residual underspecification risk: a conservative expert might defend it. Mitigation option: widen by making the July file cover 2026-06-20 to 07-31 (a mid-month re-cut after the hold), which gives ~800 such episodes |
| Holdout rate at assignment vs entry date | `assigned_at` = `entry_date` by construction |
| Episodes entering after policy start but scored before | None; score at entry |
| Target AUC tie handling | Scores are continuous with 6 decimals and no ties; Mann-Whitney standard |
| "Period" for CS-7 target estimates pooled across vintages | README output schema defines periods by `strategy` |
| Could `recalibrate` be argued when HPF is merely new? | Thresholds are explicit; truth quantities are at least 1.5 tolerances from thresholds |
| Would a model-risk expert accept "cannot assess CS-7 without more holdout"? | The instruction requires estimates; tolerance is sized to holdout n |

The coverage-gap row is the least settled item and should be resolved before build (preferred: the mid-month re-cut
option).

## 24. Expected trajectory length

**Estimate:** 50–80 actions, $1–3 for a Flash-tier agent.

**Why it is long.** Four sequential discoveries, each gated by the previous repair's residual symptom:
1. early read;
2. HPF posting;
3. servicer coverage;
4. treatment.

At each stage the agent must re-run and re-slice. Row-level payment inspection is needed for stages 2 and 3, and
cell-level inspection for stage 4.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | Here |
|---|---|
| Target cutoff already in faulty code | No watermark, no value-date logic, no manifest/close-log readers, no strategy tables read |
| Adjustment summary already implemented | Target assessment does not exist; `metrics.py` has no weights |
| Natural group/merge/subtract design correct | The natural maturity filter (R1), value-date switch (R3), exclusion (R2) and untreated pool (R9) are each wrong |
| Attractor optional | Monitors, notebook and readout are on the path; the readout number invites R8 |
| Traps target unchosen paths | R1, R2, R3 and R7 are the paths an agent takes in sequence |
| One customer check enough | Needs row audits in two sources plus cell-level checks; no single account shows the coverage gap and treatment effect together |

**Against Task 03 specifically.** Task 03's population was "the holdout, ITT", and its labels were final.

Here the holdout is necessary but not sufficient:
- it covers only above-threshold episodes;
- its rate changes;
- the target AUC needs the full score distribution;
- the labels feeding it are wrong in three independent ways before the holdout question even arises.

Task 03's one-sentence population rule does not exist here.

## 26. Comparison with Task 02

| | Task 02 | G01 |
|---|---|---|
| Core difficulty | Per-example × cutoff state | Per-episode window × source completeness state, plus treatment |
| Availability semantics | `synced_at` vs `changed_at` | `value_date` for truth vs source watermark for completeness (two different dates play two different roles) |
| Aggregate non-diagnosticity | AUC 0.77 for partial repairs | AUC ~0.74 for R2, R7 and oracle; status is the discriminator |
| Statistical layer | None | Informative censoring + randomized cell with varying inclusion probability |

Expected to be comparable to harder. The weaker point vs Task 02 is that each G01 mechanism, once seen, has a
recognisable textbook name.

## 27. Benchmark risks

- **Implementation cost: H.**
  - Generator with potential outcomes, cure timing, posting channels, the servicer file process and hub closes.
  - Three hidden worlds with margin checks.
  - Two references (exact tables, truth metrics).
- **Gradability: M.**
  - Holdout n drives tolerances. The key discriminations (R7 vs oracle on band 4; R9 on AUC) must be margin-checked
    at build.
  - If band-4 holdout n is too small, R7 might pass band checks and fail only on status. Status alone is a 1-bit
    signal, and it is robust only because truth is kept far from thresholds.
- **Underspecification: M.**
  - Coverage rule (corrected in section 23).
  - MRS-4's "documented target" may be read as "observed outcomes in the documented population".
  - The model card sentence "worked under CS-5" must be unmissable, yet not a recipe.
- **Leakage: M.** The hub close sentence is near-operational.
- **Overlap.**
  - Task 03 (randomized holdout, ITT), mitigated in section 25.
  - Task 02 (availability), a different mechanism.
  - G30 (label maturity, selective labels), see G30 section 27.

  If both G01 and G30 survive the tournament, G01 should keep its label-construction emphasis. The treatment
  component could be reduced to "CS-5 vs CS-7 period, holdout exists" to avoid G30's reject-inference core.
- **Realism: high.** Every mechanism is a recognisable collections incident. The simplification that no payments
  pre-date entry (no phantom episodes from late acquired payments) is acknowledged.
- **Headroom risk.** A strong agent may recognise "label maturity + treatment" at once. The remaining difficulty then
  rests on the servicer coverage state and the weighted target estimate. These are genuine reconstruction steps, but an
  agent that audits the manifest early passes the label half quickly.
