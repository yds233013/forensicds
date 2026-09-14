# G08: Load-forecast backtest on revised actuals (real-time settlement vintages)

Status: design only. Nothing built, no model run. Numbers are generator design targets, to be recalibrated at build.

## Workspace sketch

```
/workspace
├── README.md                                   repo map; CLI (`backtest`, `train`, `score`); no semantics
├── config/gbm_load_v1.yaml                     model spec (features, horizons, HGBR hyper-parameters), refit calendar, paths
├── src/loadfc/
│   ├── cli.py
│   ├── db.py                                   SQLite helpers; loads `load_actuals`, `weather_obs`, `calendar`
│   ├── features.py                             build_rows(series_df, weather_df, origins): groupby-shift lags, roll_28, calendar, weather (faulty)
│   ├── backtest/harness.py                     monthly refits, predictions, scoring vs `load_actuals` (faulty)
│   ├── backtest/report.py                      MAPE tables, relative improvement vs production v3 issued forecasts
│   ├── live/score_job.py                       production scorer: reads views v_latest_volumes / v_latest_weather_fc "now"
│   ├── live/train_job.py                       production retrain: stored feature_snapshots if they cover the window, else features.build_rows(load_actuals)
│   └── model.py                                HGBR wrapper (fit/predict), unchanged spec
├── sql/views.sql                               v_latest_volumes, v_latest_weather_fc, v_kpi_actuals (definitions used live)
├── data/energy.sqlite                          ~220 MB (tables in §5)
├── docs/
│   ├── models/gbm_load_v1_model_card.md        issue time, horizons, target, refit cadence, training rows, feature definitions
│   ├── forecasting/backtest_protocol.md        purpose of a backtest; origins; required outputs (written by team, pre-incident)
│   ├── kpi/forecast_accuracy_kpi.md            KPI = MAPE of issued forecast vs "settlement volume used for imbalance charging"
│   ├── settlement/settlement_runs_explained.md run types PRELIM/S1/S2/RF/DF, publication, withdrawal and re-run, reconciliation account
│   ├── data/data_dictionary.md                 tables, grains, timestamps (UTC), status semantics
│   ├── metering/smart_meter_programme.md       per-region migration; head-end processing schedule
│   └── weather/vendor_transition_2026.md       vendor A → B switch 2026-06-15; B hindcast delivery for onboarding
├── reports/
│   ├── backtest/gbm_v1_vs_v3_2026-06-19.md     the "−18 %" report (faulty harness output)
│   ├── kpi/monthly_forecast_accuracy_2025-07_2026-08.csv   published KPI for production (v3 until launch, then GBM; v3 shadow after)
│   └── ops/daily_accuracy_dashboard_2026-08.csv            ops view scored vs PRELIM ("first published")
├── notes/
│   ├── 2026-08-27_live_vs_backtest_thread.md   (generated) trading desk, DS, weather team positions
│   └── 2026-06-20_gbm_launch_decision.md       (generated)
└── ops/scorer_incidents.md                     2026-07-21..23 scorer ran at 10:00 after outage
```

`energy.sqlite` contents:

| Table | Rows |
|---|---|
| `settlement_runs` | 6 regions × ~1,340 dates × ~4.3 runs ≈ 35k |
| `settlement_volumes` | 35k |
| `run_status_history` | ~220 |
| `load_actuals` | 8k |
| `weather_forecasts` (vendor A + B, runs × targets) | ~330k |
| `weather_obs` | 8k |
| `calendar` | — |
| `forecasts_issued` (v3 2025-01 → 2026-08, GBM 2026-07-06 →) | ~95k |
| `feature_snapshots` (GBM live, since 2026-07-06) | 2.3k |
| `meter_programme` | — |

## 1. Research question

Can an agent turn a backtest that trains, features and scores on final revised data into a real-time backtest
that reproduces, at each forecast origin, the information set and training set that production would have had? This
requires deciding which *vintage* of each number applies to each purpose (feature, training target, KPI target). It also
requires noticing that the revision process itself changed regime mid-sample.

## 2. Enterprise setting

An electricity supplier forecasts daily energy volume for its customers in six supply regions to buy power day-ahead.

- **Issue.** The forecasting desk issues forecasts every day at 06:00 Europe/London for delivery days D+1 … D+7.
- **Settlement cost.** Imbalance cost is charged on the industry's Initial Settlement run (S1). Later reconciliation
  runs (S2, RF, dispute runs) move money through a reconciliation account that the desk is not measured on.
- **Production v3.** Regression + ETS, live for years.
- **Challenger.** A gradient-boosted model ("GBM v1"). It won a backtest by 18% and launched 2026-07-06; v3 kept running
  in shadow.

## 3. Visible symptom

Memo (Head of Trading Analytics):

> The GBM backtest showed an 18% lower MAPE than v3. Since launch the published KPI shows GBM no better than v3 — worse
> in some regions — and the ops dashboard says worse still. Weather says the vendor switch is to blame; DS says the
> summer is unusual. Before I decide whether to keep GBM I need a backtest I can believe.
>
> 1. `python -m loadfc backtest --start 2025-07-01 --end 2026-06-30` must write `out/backtest/features.csv`,
>    `training_manifest.csv`, `predictions.csv`, `scores_by_region_month.csv` and `summary.json` in the formats in
>    `docs/forecasting/backtest_protocol.md`. It will be run on other extracts and windows.
> 2. `python -m loadfc train --as-of <timestamp>` (the production retrain) must produce a model trained the same way.
> 3. Don't change the model specification in the model card. `data/energy.sqlite` is authoritative; do not modify it.
> 4. No special handling of particular regions, dates, runs or incidents.

The memo names no cause, no vintages, and no scoring target.

## 4. Source distribution inspiration

- **Real-time data sets.** Macroeconomic forecasting uses vintage data sets, and evaluating forecasts on final revised
  data overstates real-time accuracy. The Philadelphia Fed Real-Time Data Set and work by Croushore & Stark are commonly
  cited (to verify). Other work argues for estimating on real-time vintages rather than end-of-sample data (to verify).
- **Electricity settlement.** Markets settle in successive runs with estimated reads replaced by actual reads, and
  smart-meter roll-outs shrink revisions. The design keeps this generic.
- **Operational forecasting.** Common failures include issue-time cut-offs in local time and weather hindcasts
  delivered in bulk that "look like" historical forecasts.

## 5. Causal graph / ground truth

**True load.** For region r and day d: `L(r,d) = base_r × season(d) × dow × holiday × f(temp_true) × (1 + ε)`, with ε
AR(1) with σ 1.2%.

**Settlement runs** (`settlement_runs(run_id, region, delivery_date, run_type, published_at UTC, status)`,
`settlement_volumes(run_id, mwh, estimated_share)`; status transitions in `run_status_history(run_id, status,
changed_at)`):

| Run | Published | Value |
|---|---|---|
| PRELIM | d+1 at 05:25 London ± N(0,10 min). 5% late (06:10–11:00). 1% missing | feeder totals minus a loss estimate; error σ 2.5%, weather-correlated |
| S1 | 5th working day after d, 13:00–15:00 London | estimated reads for non-read meters. Estimation bias −0.7% per °C of cold anomaly × estimated share; σ 1.8% × estimated share |
| S2 | ~20th working day | estimated share falls to 1/3 of S1's |
| RF | ~60th working day | actual reads; ≈ L |
| DF (dispute) | 30–70 days after d, some after RF | re-reads for 4% of R2 dates, revision σ 3% |

- **Withdrawals:** 0.6% of runs are withdrawn 2–30 h after publication (`run_status_history`) and re-run with the same
  type. The generator never lets a withdrawal straddle a refit instant.
- **Regime change (R4 smart-meter cutover, 2026-01-19; `meter_programme`, programme doc):**
  - S1 estimated share for R4 drops from 62% to 6%, so S1→RF revision σ drops from 3.4% to 0.4%.
  - R4 PRELIM moves to the smart-meter head-end batch, published d+1 at 09:30 ± 20 min, **after** the 06:00 issue. From
    then on R4's yesterday value is not known at issue.

**`load_actuals`.** Latest value per region-date (`mwh`, `source_run`, `last_revised_at`). This is what the faulty
harness reads.

**Weather.**
- `weather_forecasts(vendor, run_ts, available_at, region, target_date, temp_c)`. Vendor A 00Z runs are available
  04:40–05:10 UTC, with 4% late (06:30–09:00 UTC). 12Z runs are also archived.
- Vendor B live from 2026-06-15. Vendor B **hindcasts** for 2023-01 → 2026-06 have real `run_ts` values but
  `available_at` = 2026-05-20 (bulk onboarding delivery). Vendor B has a +0.3 °C bias vs vendor A in R1/R5 (distractor;
  ≈0.1 pp MAPE).
- `weather_obs(region, date, temp_mean_c, loaded_at)`: observations are available at d+1 02:00 UTC.

**Production v3 issued forecasts** in `forecasts_issued` (since 2025-01). The published KPI report scores them against
S1.

**GBM live.**
- `feature_snapshots` hold the exact feature rows used at each live issue, with `issued_at`. Scorer incident: 2026-07-21
  → 07-23 issued at 10:00, and the snapshots reflect 10:00 knowledge.
- The launch model was trained by `train_job.py`'s fallback: `build_rows(load_actuals)`, i.e. final values with
  observed weather.

**Model spec** (model card + config):
- **Rows:** (region, origin o, horizon h ∈ 1..7).
- **Features:**
  - `lag_k` (k = 1..7) = volume for o−k *as known at issue*, NaN if none.
  - `roll_28` = mean of known values for o−1 … o−28, NaN if fewer than 20 known.
  - `temp_fc` = temperature for the target date from the latest forecast run available at issue.
  - `hdd_fc` = max(0, 15.5 − temp_fc).
  - `dow_target`, `holiday_target`, `horizon`, `region_code`.
- **Target:** KPI actual of the target date.
- **Refit:** first Monday of each month, 04:00 London. Training rows are origins in [R − 730 d, R) whose target KPI
  actual is available at R. Predictions for origin o use the latest refit before o's issue.
- **Estimator:** `HistGradientBoostingRegressor(loss="absolute_error", max_iter=400, learning_rate=0.05,
  max_leaf_nodes=31, min_samples_leaf=50, l2_regularization=0.5, early_stopping=False, random_state=11)`.

**Faulty harness.**
- For each refit R: `hist = load_actuals[date < R.date]`; `build_rows(hist, weather_obs, origins in [R−730, R))` builds
  one series per region, then `groupby.shift(k)` lags and `temp` = observed temperature of the **target** date; `y` =
  `hist` value of target.
- For each origin in the month: `build_rows(load_actuals[date < o], weather_obs, [o])`.
- Scoring: vs `load_actuals` (latest ≈ final). v3 issued forecasts are scored the same way.

## 6. Latent statistical/business invariant

Each backtest artifact has its own knowledge time:

| Artifact | Knowledge time | Value rule |
|---|---|---|
| Feature row (region, o, h) | issue instant `I(o)` = o 06:00 Europe/London, converted to UTC | Volume for date d: the run with max `published_at ≤ I(o)` not withdrawn as of `I(o)` (a later-withdrawn run *was* known). Weather: latest run with `available_at ≤ I(o)`. |
| Training manifest at refit R | features of each row at the row's own `I(o)` (not at R) | Row included iff the target's KPI actual was available at R; target = that value. |
| Scoring | — | KPI actual = first S1 never withdrawn, i.e. the S1 re-run if the original was withdrawn. Not PRELIM, not latest, not final. |
| Production retrain (`--as-of T`) | — | Stored snapshots where they exist (their own `issued_at`); reconstructed as-of-issue rows elsewhere. |

Consequence: the same delivery date has different values in different rows. A single per-cutoff series cannot
represent the invariant; state lives at region × delivery date × knowledge instant.

## 7. Grains and state variables

| Grain | State |
|---|---|
| region × delivery date × run | type, published_at, status history, mwh |
| region × origin × horizon | issue instant (DST-dependent UTC), features, target date |
| refit instant | training row set, targets known at R |
| region × target date | KPI actual (first valid S1), latest, PRELIM |
| weather run × target date | run_ts, available_at, vendor |
| region × month | MAPE per model on KPI basis |

## 8. Evidence graph

(★ = natural path)

| Artifact | Shows |
|---|---|
| ★ memo, ★ backtest report | −18% claim; per-region table |
| ★ `monthly_forecast_accuracy.csv` | Published KPI. v3's MAPE there (2.62%) ≠ v3's MAPE in the backtest report (2.47%) for the *same issued forecasts*, which exposes the scoring-basis mismatch. |
| ★ `daily_accuracy_dashboard` | Ops scores vs PRELIM; GBM looks worst, especially R4 (PRELIM missing → dashboard falls back to S1 later) |
| ★ `harness.py`, `features.py` | observed target-date weather (obvious leak); `load_actuals`; shift-based lags |
| ★ `live/score_job.py`, `sql/views.sql` | Live features come from "latest known now" views; v_kpi_actuals picks the first non-withdrawn S1. This is the scoring rule in SQL, a legitimate definition. |
| `live/train_job.py` | production training uses stored snapshots per origin; fallback builds from final `load_actuals` |
| `feature_snapshots` | exact as-of rows for Jul 6+ (validation), incl. 10:00-issue days |
| `kpi/forecast_accuracy_kpi.md` | KPI actual = "settlement volume on which imbalance is charged" |
| `settlement_runs_explained.md` | S1 is the charging run; re-runs replace withdrawn runs; reconciliation runs settle via reconciliation account; PRELIM "is an operational estimate, not a settlement run" |
| `smart_meter_programme.md` | R4 cutover; head-end batch "completes mid-morning" |
| `weather/vendor_transition_2026.md` | vendor switch; hindcasts delivered for onboarding "covering 2023–2026" |
| `data_dictionary.md` | UTC timestamps; `status` is current status; `run_status_history`; `available_at` vs `run_ts` |
| `model_card` | issue time local; features "as known at issue"; target "KPI actual"; refit rule |
| `backtest_protocol.md` | "reproduce, for each origin, the forecast the model would have issued in production, scored as the KPI scores it" plus output formats |
| thread note | weather team blames vendor B; DS "hot summer"; desk "R4 terrible since launch" |
| `ops/scorer_incidents.md` | 10:00 issue days |

## 9. Evidence authority hierarchy

1. **The KPI definition plus the settlement doc** govern the scoring target. The ops dashboard (PRELIM) and the backtest
   report (final) are derived views. The published KPI report corroborates S1 exactly.
2. **The model card and backtest protocol** govern issue time, horizons, training-row rule and features "as known at
   issue". The faulty harness conflicts with them, and the documents govern, because they describe production.
3. **`settlement_runs` + `run_status_history`** (system of record) govern knowledge time over `load_actuals`, which the
   dictionary calls a convenience latest-value table.
4. **`feature_snapshots`** are observations of production, but only live-period and with actual `issued_at`. They
   validate; they do not override the nominal 06:00 issue for the backtest (protocol: nominal issue).
5. **Notes and the thread** are opinion.

## 10. Plausible hypotheses

| H | For | Against |
|---|---|---|
| H1 weather vendor switch ★ | switch 3 weeks before launch; B biased +0.3 °C in two regions; weather team says so | error rise also in regions without bias; B bias worth ~0.1 pp; GBM issued forecasts with vendor-A-equivalent temps (B bias removed) still worse |
| H2 unusual summer / overfit ★ | hot July; GBM trained on final data looks overconfident | v3 shadow unaffected; R4 degradation coincides with cutover, not temperature |
| H3 the obvious leak (observed target weather) is the cause ★ | clearly in harness; fixing it cuts claimed gain from 18% to 11% | 11% still far from live |
| H4 scoring basis mismatch ★ | v3 MAPE differs between the report and the published KPI | only explains part of the gap |
| H5 vintage leakage in features + training, plus R4 regime | features shift-based on final data; R4 PRELIM after issue since Jan | — |

## 11. Why each wrong hypothesis is plausible

- **H1:** a real change at the right time, a named owner, and a measurable bias.
- **H2:** a standard post-launch story; GBMs are known to overfit.
- **H3:** a genuine leak, found first, which moves the number a lot, so it satisfies "found the bug".
- **H4:** real and half-right. An agent that rescores vs S1 but keeps final-data features gets −9%, which looks like a
  "modest but real gain", a very believable headline.

## 12. Investigation path (≈ 40–70 actions)

1. (1–8) Memo, backtest report, KPI csv, dashboard. Discovery: three different "actuals".
2. (9–14) Harness and features. Observed-weather leak; `load_actuals` latest.
3. (15–20) Data dictionary, `settlement_runs` exploration. Discovery: multiple runs per date; `load_actuals` = latest.
4. (21–26) KPI doc, settlement doc, `views.sql`. Scoring target = first valid S1; reproduce published v3 KPI exactly
   (validation key for scoring only).
5. (27–33) Implement the as-of lookup. First attempt is date-level or `last_revised_at` (§13). Compare to
   `feature_snapshots` for Jul–Aug and see mismatches on lag_5..lag_7 (S1 published at 14:00 on the origin day) and on
   R4 lag_1.
6. (34–40) Timestamp-level as-of; timezone of the issue instant (mismatch at 05:xx UTC publications in summer); 10:00
   incident days explained by `issued_at`.
7. (41–46) R4: programme doc → lag_1 NaN after cutover is *correct*; resist imputing it.
8. (47–52) Training rows: realise each training row's features must be as of its own origin; the harness's
   series-per-refit structure cannot express it; restructure to a (region, origin, horizon) feature table built once.
9. (53–57) Weather: as-of by `available_at`. Discovery: vendor B hindcasts have `run_ts` in the past.
10. (58–62) Withdrawn runs: status history.
11. (63–70) Rerun backtest; region × month scores; sanity: the backtest GBM for Jul–Aug (extended window) approximates
    the live KPI; production retrain command.

## 13. Natural wrong implementation

"As-of on date columns": after spotting revisions, keep `features.build_rows` and restrict the series at each cutoff:

```python
hist = actuals[(actuals.date < cutoff.date()) & (actuals.last_revised_at < cutoff)]   # variant A
# or
known = vol.merge(runs)[lambda x: x.published_at.dt.date <= cutoff.date()]            # variant B
series = known.sort_values(["run_type_rank"]).groupby(["region","date"]).last()
```

Also: use weather forecasts with `run_ts < cutoff`; score vs `load_actuals`, or vs S1 if the agent found the KPI doc.

What it gets wrong:

- **Variant A** drops every date revised after the cutoff. At an origin, dates o−1 … o−60 have almost all been revised
  since, so the lags are **missing, not earlier values**. `roll_28` becomes NaN for most rows (fewer than 20 known).
  The model falls back to calendar + weather. The headline is still "−6%" (plausible!).
- **Variant B:**
  - `date(published_at) ≤ o` includes S1 runs published at 14:00 on the origin day and late PRELIMs, affecting
    lag_5..7 on ~20% of rows and lag_1 on 5%.
  - It includes R4's 09:30 PRELIM for every origin after Jan 19: R4 lag_1 is never NaN, so the backtest shows R4
    *improving* after cutover while live shows it degrading.
  - Run-type rank picks RF over a later DF.
  - Status is taken as current, so withdrawn runs are excluded at origins when they were live.
- **Both variants** apply the cutoff to training rows *at the refit instant R*: one series per region per refit,
  shifted. Training features for a row with origin o use values known at R, not at I(o). Since R ≥ o + 1 month, every
  lag in training is S2/RF-level clean, while prediction lags are PRELIM/S1. This is the Task 02 grain error in
  forecasting form.
- **Weather** by `run_ts`: vendor B hindcasts (newer model, better) are used for all history.

Design-target numbers (overall GBM vs v3, KPI basis unless stated):

| Harness | Reported relative MAPE |
|---|---|
| faulty (final basis) | −18.2% |
| weather leak fixed only (final) | −11.0% |
| + score vs S1 | −8.9% |
| variant B as-of + S1 scoring + refit-grain training | −5.6% (R4 −4%) |
| variant A | −6.1% |
| oracle | −2.1% overall; R4 post-cutover **+13.5%**; R2 −0.8% |
| live Jul 6–Aug 30 (published KPI) | +3% overall; R4 +19% |

Variant B's feature table differs from reference on ~31% of rows. Its predictions differ on ~64% of rows by more
than 1e-6.

## 14. Second-order failure modes

1. **Issue instant at 06:00 UTC.** Wrong in BST for runs published 05:00–06:00 UTC (PRELIM jitter) and weather runs
   available 05:00–06:00 UTC: ~3% of summer rows.
2. **Correct features, training rows at refit** (per-refit series). The most likely final failure.
3. **Score vs PRELIM** ("first settled" read as "first published"). The settlement doc says PRELIM is not a
   settlement run.
4. **Score vs latest at extract** (≈ RF): the original faulty basis.
5. **Training target = latest known at R** instead of KPI actual. For rows near R this is PRELIM (S1 not yet
   published). Model card: target is the KPI actual; rows without one are excluded.
6. **Impute R4 lag_1** (with lag_2, or with S1 from later): "fixes" a NaN that production genuinely had.
7. **Synthetic vintages:** apply average PRELIM/S1 revision factors per region to final data. Fails at the R4 cutover
   and on weather-correlated S1 bias.
8. **Drop lag_1..lag_5** ("only use settled data"). Changes the model spec.
9. **Withdrawn runs excluded by current status.** A small row count, but exact grading catches it.
10. **Weather hindcasts via `run_ts`.**
11. **Replace backtest features with `feature_snapshots` where available.** No overlap with the backtest window, but
    the agent may extend or shift the window. Harmless if consistent; the verifier uses its own windows.

## 15. Correct repair properties

- A single (region, origin, horizon) feature table built at each row's issue instant (local → UTC), by timestamp
  as-of over runs with status reconstructed from history. Reused for both training and prediction.
- Training manifest per refit: rows with origin in the window and KPI actual published ≤ R; target = KPI actual.
- Weather as-of `available_at`.
- NaN semantics preserved (no imputation beyond the model card's `roll_28` minimum-count rule).
- Scoring target = `v_kpi_actuals` semantics, for GBM and v3 alike.
- Production retrain (`train --as-of T`) uses the same reconstruction for origins without snapshots and snapshots
  where present.
- Nothing hard-coded: regions, cutover dates, DST, publication hours and withdrawn runs are all derived from tables and
  the tz database.

## 16. Repair surfaces

| Surface | Why |
|---|---|
| `features.py` | replace series-shift with knowledge-time lookup per row; weather by `available_at` |
| `backtest/harness.py` | build feature table once per (region, origin, horizon); refit manifest rule; target = KPI actual |
| `backtest/report.py` | scoring basis for both models |
| `live/train_job.py` | fallback must reuse the reconstruction (currently final data) |
| `db.py` | load runs, status history, weather runs with `available_at` |
| unchanged | `model.py`, config spec, `views.sql` |

## 17. Validation requirements

- **Reproduce the published v3 KPI** from `forecasts_issued` using the chosen scoring basis (exact to 4 dp). This proves
  the basis. Aggregate-level, but uniquely diagnostic.
- **Row-level feature comparison vs `feature_snapshots`** for Jul 6–Aug 30 (run the builder on those origins). Explain
  every mismatch: 10:00 issue days must match when built at their `issued_at`.
- **Spot audits:**
  - one row per run type straddling the issue instant;
  - an R4 row before and after cutover;
  - a withdrawn-run row;
  - a DST-boundary row.
- **Training manifest audit:** for one refit, pick a row with origin one day before R and confirm its lag_1 is the
  PRELIM value, not the RF value.
- **Aggregate checks cannot replace these:** variants A and B and the refit-grain error all yield believable −5% to −6%
  headlines.

## 18. Hidden fixture strategy

All three are regenerated worlds with the same schema and documents. Windows passed via `--start/--end`.

| Fixture | Invariant stressed | Surface change | Overfit caught | Same distribution because |
|---|---|---|---|---|
| **hidden_a** "regime elsewhere" (window 2026-01-01 → 2026-12-31) | knowledge time from publications, not region rules | R2 cutover 2026-04-13 with head-end PRELIM 10:15; R4 no cutover; DST dates of 2026; withdrawals 3% | hard-coded R4/2026-01-19/09:30; hard-coded 2025 DST; current-status withdrawn | cutover and withdrawal mechanisms documented and present in visible |
| **hidden_b** "revision magnitude & disputes" (2025-10-01 → 2026-09-30) | latest-published (not type rank); KPI actual choice | cold winter, S1 bias 2×; DF runs for R2 and R5 at 12%, 40% after RF; S1 on 7th working day (settlement calendar shift) | run-type rank; working-day arithmetic; synthetic revision factors; scoring vs latest | DF, calendar in `settlement_runs` data |
| **hidden_c** "weather & short history" (2025-04-01 → 2026-03-31) | weather `available_at`; min-count rules; region set from data | vendor A late runs 15%; vendor B hindcasts with `run_ts` across window; new region R7 with 420 days of history; one refit where R7 has < 50 training rows | `run_ts` weather; UTC 06:00; hard-coded 6 regions; imputation for short history | hindcasts and late runs exist in visible |

## 19. Mutation strategy

| Mutation | Class | Expected |
|---|---|---|
| `nop` | control | 0 |
| `oracle` | control | 1 |
| `independent_sql` (window functions over runs + status history; Python tz) | alt | 1 |
| `publication_replay` (walk publications chronologically, maintain known-state dict per region-date, emit at issue instants) | alt | 1 |
| `weather_obs_fix_only` | partial | 0 |
| `score_vs_s1_only` | partial | 0 |
| `asof_last_revised_filter` (variant A) | natural wrong | 0 |
| `asof_date_level_runs` (variant B) | natural wrong | 0 |
| `asof_utc_0600` | second-order | 0 |
| `features_asof_refit_grain` | second-order | 0 |
| `run_type_rank` | second-order | 0 (visible DF); strongly hidden_b |
| `withdrawn_by_current_status` | second-order | 0 |
| `score_vs_prelim` / `score_vs_latest` | wrong | 0 |
| `target_latest_known_at_refit` | wrong | 0 |
| `impute_r4_lag1` | wrong | 0 |
| `synthetic_vintage_factors` | wrong | 0 |
| `drop_short_lags` | spec change | 0 |
| `weather_run_ts_asof` | wrong | 0 |
| `oracle_hardcoded_r4_cutover` | overfit | visible 1 / hidden_a 0 |
| `oracle_hardcoded_dst_2025` | overfit | visible 1 / hidden_a 0 |
| `oracle_hardcoded_regions` | overfit | visible 1 / hidden_c 0 |
| `oracle_working_day_s1` | overfit | visible 1 / hidden_b 0 |
| `oracle_changed_hyperparams` | spec | 0 |
| `patched_outputs`, `edited_db` | cheat | 0 |

Probe: oracle features + faulty scoring; oracle + train_job unchanged (fails only the retrain check).

## 20. Alternative valid implementations

- SQL window functions, event replay, or pandas `merge_asof` by (region, delivery_date) over publication-sorted runs.
  All give identical rows because publication instants are unique per (region, date) and never equal an issue instant
  or refit instant.
- **Timezone** via `zoneinfo`, pandas `tz_convert`, or `dateutil`. All agree for Europe/London.
- **`roll_28`:** mean over known values with float64. The verifier tolerance is 1e-9 relative.
- **Output layout:** CSV columns per protocol; extra columns ignored; row order ignored.
- **Retrain:** the verifier checks the model's predictions on a fixed feature file, not the pickle.

## 21. Verifier design

**A. Integrity.** DB digest; commands succeed.

**B. Visible (2025-07-01 → 2026-06-30).**
1. `features.csv` row set = reference (region × origin × horizon); every feature within 1e-9 (NaN-ness exact).
2. `training_manifest.csv` per refit: row set equal; targets exact.
3. `predictions.csv` within 1e-6 of the reference model trained on reference manifests (same image, deterministic
   HGBR).
4. `scores_by_region_month.csv`: MAPE for GBM and v3 within 1e-9; `summary.json` relative improvements consistent.
5. `train --as-of 2026-09-07T03:00Z`: the verifier scores a fixed hidden feature file with the produced model;
   predictions match the reference retrain within 1e-6. The reference retrain uses snapshots for Jul 6+ and
   reconstruction before.
6. Determinism rerun.

**C. Hidden ×3.** Checks 1–4 with each fixture's window; check 5 on hidden_b.

**Ground truth.** A deterministic reference (`tests/reference.py`, independent SQL + zoneinfo). The estimator is
uniquely implied: the model card fixes features, refit rule, target and hyper-parameters. Statistical ground truth is
not needed for grading. It is reported informationally: the oracle backtest's Jul–Aug extension approximates the live
KPI within 0.15 pp, supporting the design's claim that the correct backtest "predicts live".

**Runtime.** 12 refits × ~31k rows × HGBR 400 iters ≈ 12 × 3 s; feature build < 30 s; four extracts ≈ 5 min.

## 22. Answer-key leakage audit (with cheap-solve audit)

| Artifact | Leakage assessment |
|---|---|
| `views.sql` `v_kpi_actuals` | Gives the scoring target definition in SQL. Accepted: it is a production definition, one of ~6 required pieces, and it is not on the faulty harness path. |
| `v_latest_volumes` | "Latest non-withdrawn run *now*". Adding `published_at ≤ :issue` is tempting; it still uses current status (wrong for withdrawn), requires the issue instant in UTC, and does not fix training grain or weather. Medium risk; the most dangerous cheap path, analysed below. |
| `train_job.py` | Shows production training reads per-origin snapshots. States the grain *by behaviour*; the fallback is wrong. No TODO. |
| `feature_snapshots` | Row-level truth only for origins after the backtest window; cannot be copied into graded rows; 10:00 days mislead naive comparisons. |
| model card | "as known at issue" is a definition, not an algorithm; does not mention runs, withdrawals, DST, `available_at`. Review must avoid "use the vintage table". |
| backtest protocol | Purpose statement; formats. Must not mention vintages. |
| KPI + settlement docs | Distributed: KPI says "charging run"; settlement doc says S1 charges and PRELIM is operational. |
| smart-meter doc | Says head-end "completes mid-morning"; no link to the forecast issue. |
| published KPI csv | Exact key for *scoring basis* for v3 only; gives nothing about GBM features. |
| backtest report | Wrong semantics; matching it reproduces the faulty harness. |

**Cheap-solve audit.**

| Path | Outcome |
|---|---|
| One grep (`S1`, `published_at`) | Finds the scoring target; features, grain, weather, DST remain. Fails. |
| One doc | No doc states the knowledge-time rule for features and training. Fails. |
| One SQL (as-of `v_latest_volumes`) | Correct lag values for most rows if the issue instant is converted to UTC. Still fails withdrawn history, weather availability and training grain (unless the agent also restructures the harness), and scoring. **Main residual risk**: an agent that writes this SQL *and* builds a per-row table *and* uses `available_at` passes. That is the intended competent path, not a shortcut. |
| One filter (`last_revised_at`) | Variant A. Fails. |
| Existing helper | `build_rows` shift structure is the trap. Fails. |
| Match an old report | Backtest report: wrong. Published KPI: scoring basis only. Fails. |
| Restore previous behaviour | v3 is not the task; reverting GBM gives no backtest. Fails. |
| Copy snapshots | No overlap with graded window. Fails. |

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Real-time vs end-of-sample estimation (a legitimate methodological choice) | Pinned by production: `train_job.py` trains on per-origin stored snapshots; protocol asks for "what production would have issued". Risk M. A reviewer may argue end-of-sample training is valid research; the task's question is production-faithful backtesting. The memo must say "the backtest must tell me what GBM would have delivered live". |
| Issue instant nominal vs actual | Protocol: nominal 06:00; snapshots show actual `issued_at` for incident days (explained by incident note). |
| Withdrawn run known before withdrawal | Dictionary: `status` is current; history table gives transitions; model card "as known at issue". Risk M (pedantic); hidden_a amplifies. Option: drop withdrawals if review finds it unfair. |
| KPI actual when S1 withdrawn and re-run | Settlement doc: re-run replaces; `v_kpi_actuals` implements. |
| Training row inclusion "available at R" | Model card; generator avoids straddles and equal timestamps. |
| `roll_28` minimum count | Model card (20); faulty code has it (a feature definition, not a fix). |
| Weather fallback if no run available | Model card: NaN; generator guarantees at least a 12Z run from previous day available. |
| Holiday calendar for target | `calendar` table; unchanged code. |
| R4 lag_1 NaN correctness | Production had NaN (snapshots show it); model card NaN rule. |
| DF after RF | "latest publication known"; docs say dispute runs supersede. |
| MAPE definition (mean of daily APE per region-month) | Existing `report.py` implements; unchanged, graded. |

## 24. Expected trajectory length

45–80 actions, 30–60 minutes:
- three independent semantics (features, training grain, scoring);
- two availability subtleties (DST, withdrawals), plus weather availability and a regime change;
- restructuring the harness from series-per-cutoff to row-level knowledge time is a genuine refactor;
- validation against snapshots requires building for origins outside the backtest window.

## 25. Why harder than Tasks 03/05/06

| Task 06 flaw | G08 |
|---|---|
| Cutoff in faulty code | The harness has a *date* cutoff (`date < o`) that looks point-in-time and is the trap; no issue-instant, timezone, run or status logic exists. |
| Summary already implemented | Scoring exists but on the wrong basis; the refit manifest rule is wrong. |
| Natural design correct | Series-per-cutoff with as-of filter is the natural design and is wrong at the training grain. |
| Attractor optional | The backtest report and ops dashboard are named in the memo; the weather leak is in the first file. |
| Traps on unchosen paths | Variant A/B, UTC 06:00, refit-grain training, PRELIM scoring are each the next natural step. |
| One-entity check enough | R4 behaves differently from others; withdrawals and DST hit scattered rows; weather affects all. |

## 26. Comparison with Task 02

- **Same core:** per-example × cutoff state; availability = publication, not business date.
- **Harder:**
  - two different knowledge times in one pipeline: row origin for features, refit for inclusion;
  - a third definition for the scoring target;
  - a regime change that makes the *correct* feature missing;
  - weather availability;
  - local-time issue instants.
- **Easier:** revisions are visible as multiple rows per date, so recognising "revised data" is faster than Task 02's
  current-state tables. The live snapshots provide row-level feedback.
- **Overlap:** conceptual overlap with Task 02 is high (availability). The domain, the scoring-target subtlety and the
  regime change are distinct. If both G11 and G08 are built, three "availability" tasks exist; the tournament should
  weigh this.

## 27. Benchmark risks

- **Implementation cost: M.**
  - The generator (runs, withdrawals, DST, weather runs) is simple compared with G11.
  - Main effort: exact-equality guarantees (no ties) and HGBR runtime across 4 extracts.
- **Realism: H** for settlement runs, estimated reads, smart-meter cutover and weather hindcasts.
- **Gradability: H.** Deterministic reference; exact features.
  - HGBR determinism across identical images is reliable with `early_stopping=False`.
  - Pin threads (`OMP_NUM_THREADS=1`) to avoid float nondeterminism in histogram building. **Must verify at build.**
- **Underspecification: M.** Real-time vs end-of-sample training is the key debate; the production code and the memo
  wording must pin it. The withdrawal-history rule is the pedantic edge.
- **Headroom: M.**
  - The "as-of SQL on the live view" path is short for a strong agent.
  - Difficulty then rests on the training-grain restructure, weather `available_at`, DST and scoring basis.
  - If pilots pass easily, do not remove `train_job.py`'s snapshot branch; that is what pins the training grain, and
    removing it would under-specify the task. Instead, remove `v_latest_volumes` from `views.sql`: the live scorer then
    queries `settlement_runs` directly with `status = 'published'`, which is less copyable.
- **Leakage: L–M** (views.sql).
- **Overlap:** Task 02 moderate; G11 moderate (both "train as served").
