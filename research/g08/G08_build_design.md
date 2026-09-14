# G08 build design (revised before implementation)

Status: implementation design. It supersedes `research/gen3_designs/G08_forecast_vintages.md` for the build. Nothing
here has been run against a model. Section 17 records the revisions made after the pre-baseline adversarial review;
where §§1–16 and §17 differ, §17 is what is built.

Build directory:
- `candidates/g08-forecast-accuracy-vintages/`
- `tools/g08/`

## 0. Audit of the original G08 design

### 0.1 Tournament criticism (treated as binding)

| Tournament finding (R2 + §3 #13) | Status in this design |
|---|---|
| `v_latest_volumes` is one filter from correct | **Removed.** No view or helper computes "latest known" for any type or status. The only view the faulty mart uses (`settled_volumes_latest`) is current-state and any-type. Making it correct needs status history reconstruction per evaluation instant, not a filter. |
| `feature_snapshots` allow row-by-row unit tests | **Removed.** No row-level record of the correct target exists. The Billing charge-basis snapshots that once held it are retired and absent from the extract; only month-level packs remain (1 dp WAPE, counts). |
| Published KPI CSV is an exact scoring key | **Replaced.** Historical packs are aggregates (portfolio × month, 1 dp) and cover only months before the migration. The two post-migration packs were produced by the faulty mart. Every grade is at example level, and hidden extracts have no packs. |
| Variants A/B were strawmen | **Replaced.** Natural wrong paths come from reading the data model and the docs (§9), not from odd filters. Each is implemented as a mutation that must fail on the *visible* extract. |
| Vendor precedence / "latest run" ordering underspecified | No weather vendors. Run ordering is by `published_at`; the generator makes publication instants unique per (region, class, delivery date) and never equal to a close or gate instant. The charge-basis run at any instant is unique by construction (§5.3). |
| HGBR column-order sensitivity | **No model is trained.** Forecasts are stored issued values; grading uses deterministic tables. |
| A hidden mechanism absent from the snapshot window | No snapshots. Each hidden extract stresses a documented situation that is rare in the visible extract (§12). |

### 0.2 The user's pivot (binding)

The original G08 core was *feature* availability at forecast issue, which is Task 02 in forecasting form. This build
moves the core to the **target**:

> Which version of the actual should each historical forecast example be evaluated against, given settlement runs,
> late publication, withdrawals, data corrections, reconciliation, portfolio re-definition and a monthly evaluation
> close?

Feature construction and model training are out of scope. The forecast side contributes one principled vintage
question: which issued forecast was in force.

## 1. Incident

- **Company:** "Harbourline Energy", a fictional electricity supplier.
- **Forecasts:** the forecasting desk issues daily volume forecasts per supply region × customer portfolio, for
  delivery days D+1 … D+7.
- **KPI:** each month the desk publishes a **forecast accuracy KPI** (WAPE by model, portfolio, horizon) in an
  accuracy pack. The pack feeds the desk scorecard.
- **Models:**
  - Champion **v3** throughout.
  - Challenger **v4**: shadow from January 2026, production from 6 April 2026. v3 continues in shadow.
- **Before July 2026:** a notebook produced each pack at KPI close. It joined Billing's month-end *charge-basis
  snapshot* to the trading system's *locked forecast extract*.
- **2026 retirements:** both feeds were retired (Billing platform consolidation; trading system upgrade).
- **July 2026:** the Data Platform team replaced the notebook with an **accuracy mart** (`fcaccuracy`) reading the new
  warehouse. Their migration made five "improvements", each defensible on its face:
  1. score against `settled_volumes_latest`, "the most accurate settled volume available, including reconciliation";
  2. use `forecast_latest`, "the most recent forecast issued for each run";
  3. map portfolios with the current `dim_portfolio`;
  4. assign KPI months by forecast run month, "aligned with model runs";
  5. compare models over "each model's own production period".

**Visible symptom.** The mart's July and August packs, and the restated history in the September accuracy review,
show v4 about 30% better than v3. Several signed-off months also changed materially. The packs signed off before the
migration showed v4 about 9% better in shadow. Trading does not see the claimed improvement in imbalance costs, and a
model decision is due.

## 2. Research question

Can an agent reconstruct, for every historical forecast example, the evaluation state the KPI defines?

- **Forecast in force:** the issued forecast locked at that run day's gate closure, per forecast unit.
- **Target:** the settlement volume on which the day's imbalance charge was calculated, *as it stood at the KPI close*
  of the delivery month.
- **Grain:** the portfolio definition in effect for the delivery day.

The agent then rebuilds the example table, the monthly KPI and the head-to-head comparison. It must reject several
tempting "better data" repairs:
- latest reconciliation;
- current charge basis;
- first publication;
- latest run at close;
- current mapping.

## 3. Clocks (each has a semantic purpose)

| Clock | Where | Purpose |
|---|---|---|
| Forecast run date | `forecast_issues.run_date` | Defines horizon = delivery date − run date and the gate that locks the set |
| Forecast issue time | `forecast_issues.issued_at` (UTC) | Which issue was in force at the gate |
| Gate closure | 11:00 UK local time on the run date (trading doc) | The DST-dependent instant that locks forecasts; re-issues after it are informational |
| Delivery (target) date | `forecast_values.target_date`, `settlement_runs.delivery_date` | Portfolio definition in effect; KPI month |
| Run publication time | `settlement_runs.published_at` | When a settlement value became known |
| Status change time | `run_status_history.changed_at` | When a run stopped being valid (withdrawn/superseded) |
| KPI close | `kpi_close_log.closed_at` (actual, can slip) | The evaluation instant for each delivery month |
| Extract / as-of | `--as-of` | Which months are closed; current state is the attractor |

Present but **without** knowledge-time meaning (distractors that exist in real warehouses):
- `settlement_volumes.loaded_at`: warehouse load time; history before July was backfilled at migration.
- `settlement_runs.status_updated_at`: time of the *current* status.

## 4. Generator (ground truth)

Deterministic, stdlib only, seeded. Parameters below are for the visible extract.

### 4.1 Calendar

- Delivery dates from 2025-05-20 to the extract instant 2026-09-22 06:00Z.
- Forecast run dates from 2025-06-01.
- UK working days: weekdays minus England and Wales bank holidays 2025–2027.

### 4.2 Physical volume

- **Regions (6):** NORTH, MIDLANDS, EAST, SOUTH, WEST, LONDON.
- **Settlement classes (5):** DOM (domestic, non-half-hourly), SME_NHH, SME_HH (elective half-hourly), IC_HH, UMS
  (unmetered supplies; added at calibration, see §17).
- **Model:** `V(r,c,d) = base(r,c) · season(d) · dow(c,d) · (1 + γ_c · anom(r,d)) · (1 + AR(1) noise, σ 1.2%)`.
  - `anom` is an AR(1) temperature anomaly in °C.
  - γ_c is negative (cold means more volume): DOM −2.2%/°C, SME_NHH −1.4%, SME_HH −0.9%, IC_HH −0.4%.

### 4.3 Settlement runs (per region × class × delivery date)

| Run | Publication | Value |
|---|---|---|
| `EST` | d+1, 04:30–05:30 UK | `V·(1+N(0, 2.5%))` operational estimate |
| `IS` initial settlement | 7 working days after d, 10:00–16:00 UK | `V·(1 + s_IS(c)·κ·anom + N(0, 1.2%·s_IS))`: profile estimates under-react to temperature (κ = +1.8%/°C; s_IS = estimated share: DOM 0.55, SME_NHH 0.45, SME_HH 0.05, IC_HH 0.02) |
| `R1` | 24 WD | same with s × 0.5 |
| `R2` | 80 WD | s × 0.2 |
| `RF` | 270 WD | s × 0.03 |
| `DF` dispute | 30–90 days after RF or R2 (0.3% of dates) | re-read σ 2% |

**Perturbations:**

- **Late IS.** 1.2% of IS publications are delayed 3–12 WD.
- **Settlement-agent outage.** MIDLANDS, all classes, delivery 2026-01-19 → 01-30: IS delayed to 2026-02-19 (after the
  January close).
- **Withdrawal.**
  - 1.0% of runs of any type are withdrawn 2–40 h after publication.
  - A `withdrawal_rerun` of the same type is published 1–6 WD after the withdrawal.
  - The withdrawn value carried a gross error of ±6–12%; the re-run carries the normal value.
- **Data correction.**
  - 2.5% of IS runs, and 2.0% of R1 runs, contain a data-load error δ of ±3–9%.
  - A `data_correction` re-run of the same type, without δ, is published 2–40 calendar days after the flawed run.
  - The flawed run's status becomes `superseded` at the correction's `published_at`.
  - Corrections come in batches: region × class × a 3–10-day delivery range, sharing one publication instant.
- **Forced visible boundary cases** (so no graded rule is hidden-only): at least one each of
  - an IS withdrawn after the close of its month;
  - a close falling between an IS withdrawal and its re-run;
  - an IS data correction published within 48 h *after* a close;
  - an IS data correction published before a close;
  - an R1 data correction published before a close;
  - an IS published after close (outage plus random late).
- **No ties.** No `published_at` or `changed_at` within 120 s of any `closed_at`.

**Invariant guaranteed by construction:** at any instant at most one IS-type run per (region, class, date) has
status `published`.

### 4.4 KPI close

- Nominal: 12th UK working day of month m+1 at 17:00 UK.
- Slips: December 2025 +2 WD, April 2026 +1 WD.
- `kpi_close_log` stores the actual `closed_at` (UTC).

### 4.5 Portfolios (by delivery date; SCD2 table `portfolio_membership`)

| Effective delivery dates | RESI | BUSINESS | SME | IC |
|---|---|---|---|---|
| → 2026-03-01 | DOM | SME_NHH, SME_HH, IC_HH | — | — |
| 2026-03-02 → 2026-05-31 | DOM | — | SME_NHH, SME_HH | IC_HH |
| 2026-06-01 → | DOM | — | SME_NHH | SME_HH, IC_HH |

- The forecasting system issues each target date for the portfolios effective on that target date. A forecast issued
  2026-05-28 for 2026-06-02 is an SME forecast under the June definition.
- `dim_portfolio` holds the current definition only.

### 4.6 Forecasts

**Models** (`models` table):

| Model | Run dates | Role |
|---|---|---|
| v3 | 2025-06-01 → | production until 2026-04-05, shadow after |
| v4 | 2026-01-05 → | shadow until 2026-04-05, production after |

**Issue pattern per model × run date** (all times UK local; stored UTC):

| Issue | When | Share of run dates |
|---|---|---|
| `scheduled` | 06:00 + U(0, 9) min | fails on 1.2% of days; the first issue is then a pre-gate `reissue` at 07:10–10:40. On 0.25% there is no pre-gate issue at all, so no forecast is in force. |
| Pre-gate partial `reissue` (scope = one region) | 07:30–10:50 | 3% |
| Gate-miss `reissue` (scope = all regions or one region) | 11:02–11:58 | 3% |
| v4 `auto_reissue` after the 06Z weather update (all regions) | 12:25–12:55 | 80% (from shadow start) |
| v3 `reissue` for incident reviews | 14:00–18:00 | 1.5% |

**Forecast value** for (model m, run date o, region r, portfolio p, target t, horizon h = t − o):

- `F = Σ_{c ∈ p(t)} E_IS(r,c,t) · (1 + ε)`, where `E_IS = V_det·(1 + s_IS·κ·anom_det)`. Forecasts target the charge
  basis; the model learned the profile bias.
- `ε = a_m·w + u`, with:
  - `w ~ N(0, σ_w(h))` a weather-forecast error shared by the models;
  - `u ~ N(0, σ_m(h))` model-specific;
  - σ_w(h) = 1.6% + 0.25%·h; σ_v3(h) = 2.9% + 0.2%·h; σ_v4(h) = 2.5% + 0.18%·h.
- **Re-issues:**
  - pre-gate: `w' = 0.9w`, `u' = 0.95u + N(0, 0.3%)`;
  - gate-miss: `w' = 0.75w`;
  - auto re-issue (06Z weather): `w' = 0.5w`, `u' = 0.9u`.

## 5. Oracle invariant (verifier truth)

Given `--as-of A`:

### 5.1 Closed months

Delivery months m with a `kpi_close_log` row and `closed_at(m) ≤ A`. `C(m) = closed_at(m)`.

### 5.2 Examples

For each model, run date o, region r, portfolio p and target date t, with t in a closed month:

1. **Gate.** `G(o)` = o 11:00 Europe/London, converted to UTC.
2. **Forecast in force.** Consider the issues of that model with `run_date = o` and `issued_at < G(o)` whose scope
   covers r (all regions or r). Among those, take the one with the latest `issued_at` that has a value for (r, p, t).
   If none exists, there is no example.
3. **Horizon.** h = (t − o) in days.
4. **KPI month.** The month of t.
5. **Portfolio classes.** `K(p,t)` = classes with `effective_from ≤ t ≤ effective_to` (NULL = open).
6. **Charge basis at close, per class c ∈ K.**
   - `IS(r,c,t)` = runs with `run_type = 'IS'`.
   - Known at close: `published_at ≤ C(month(t))`.
   - Status at close: the latest `run_status_history` row with `changed_at ≤ C`.
   - The basis run is the unique IS run whose status at close is `published`.
7. **Status.**
   - If every class has a basis run: `scored`, `actual_mwh = Σ mwh`, `actual_run_ids` = sorted run ids joined by `;`,
     `abs_error_mwh = |F − actual|`.
   - Otherwise: `unsettled`, with actual fields empty.

### 5.3 Why "the basis run" is well defined

- An IS publication makes that run the charge basis.
- A withdrawal ends it; the withdrawal re-run restores a basis.
- A data correction supersedes the flawed run at the correction's publication instant.
- The generator never overlaps two published IS runs, so the basis run at any instant is either unique or absent.

### 5.4 Monthly KPI

Rows for each model × KPI month × portfolio × horizon with at least one example:
- `n_examples`, `n_scored`;
- `abs_error_mwh`, `actual_mwh` (sums over scored examples);
- `wape = abs_error_mwh / actual_mwh` (empty if `n_scored = 0`).

### 5.5 Head-to-head

For each unordered pair of models (a < b), pool the (region, portfolio, target date, horizon) keys where both models
have a scored example in closed months. Report:
- `n_pairs`, `first_month`, `last_month`;
- `wape_a`, `wape_b`, `relative_change = wape_b / wape_a − 1`.

## 6. Evidence graph (★ = on the natural path)

| Artifact | What it shows | Why it is not an answer key |
|---|---|---|
| ★ `instruction.md` (memo) | Symptom, numbers, required command and outputs, no special-casing | Names no cause, vintage, close or run |
| ★ `README.md` | Repo map, CLI, where docs are | No semantics |
| ★ `fcaccuracy/` + `sql/accuracy_mart.sql` | Faulty mart: `settled_volumes_latest`, `forecast_latest`, `dim_portfolio`, run-month KPI, unpaired comparison. Month selection from `kpi_close_log` (so the close log is on path). | Contains no status-history, gate, membership-history or close-knowledge logic |
| ★ `RELEASES.md` | Migration notes: the five "improvements" and the retired feeds, in the Platform team's voice (attractor) | Presents the wrong choices as improvements |
| ★ `reports/accuracy_review_2026-09.md` | Mart-based executive review: v4 −30%, restated history table vs signed-off packs (attractor) | Numbers from the faulty mart |
| ★ `reports/kpi_packs/pack_history.csv` + `reports/kpi_packs/2026-01.md`, `2026-05.md`, `2026-08.md` | Signed-off WAPE (1 dp) and scored counts per model × portfolio × month; footnotes (January MIDLANDS not settled at close; August produced by the mart) | Aggregates at 1 dp, pre-migration months only; wrong post-migration |
| ★ `notebooks/kpi_pack_legacy.ipynb` | Old pack: joins `billing.charge_basis_snapshot` to `trading.locked_forecasts` by (region, portfolio, date), pairing both models; header "run at KPI close". Tables no longer exist. | Contains none of the reconstruction; can't be run |
| `docs/kpi/forecast_accuracy_kpi.md` | KPI = accuracy of the forecast locked for trading vs the settled volume on which the day's imbalance charge is calculated; monthly by delivery month; published at KPI close; WAPE definition; horizons | A definition; says nothing about runs, status or knowledge time |
| `docs/finance/scorecard_policy.md` | Scorecard figures are final when signed off at close; no restatement | Governance fact |
| `docs/finance/billing_feed_retirement_2026.md` | Billing's month-end charge-basis snapshot (the volumes imbalance charges were calculated on) is retired; warehouse settlement tables replace it; "Billing no longer produces it" | Describes a retired artifact, not how to rebuild it |
| `docs/settlement/settlement_process.md` | Runs EST/IS/R1/R2/RF/DF; charges calculated on IS; withdrawal and re-run; data correction re-runs re-issue the charge; reconciliation via reconciliation account; EST is not a settlement run; publication timetable | Process facts; no evaluation rule |
| `docs/trading/day_ahead_process.md` | Forecast issued 06:00 UK; gate closure 11:00 UK on run day locks the D+1…D+7 set; shadow models issued and locked the same way; re-issues after gate are informational | Operational fact; no timezone conversion or table logic |
| `docs/forecasting/forecast_store.md` | Issues, scopes (single-region re-issues supersede that region only), auto re-issue in v4 | System behaviour |
| `docs/data/data_dictionary.md` | Tables, UTC timestamps, `status` = current, `run_status_history`, `loaded_at` = warehouse load (backfilled at migration), `status_updated_at`, SCD2 `portfolio_membership` effective by delivery date, `dim_portfolio` = current | Schema facts |
| `docs/portfolio/portfolio_restructure_2026.md` | March and June restructures (business reasons) | Facts |
| `docs/models/v4_release_note.md` | v4 features; auto re-issue after 06Z weather "improves short horizons" (attractor: model looks genuinely better) | Model facts |
| `docs/mart/accuracy_mart.md` | Output schema for the three outputs (pre-migration requirements + Platform additions) | Formats; statuses `scored`/`unsettled` described as "settled volume available / not available" |
| `reports/ops/daily_accuracy_dashboard_2026-08.csv` | Ops view scored vs EST (attractor for "first published actual") | Wrong basis |
| `notes/2026-09-18_accuracy_thread.md` | Platform: reconciliation is "the truth"; Trading: v4 doesn't show in costs; Finance: signed months must not move; DS: v4 is genuinely better | Opinions; conflicting |
| `ops/settlement_incidents.md` | January MIDLANDS agent outage; withdrawn runs are routine | Facts |

## 7. Authority hierarchy

1. **KPI definition + scorecard policy.** They govern *what* is measured (locked forecast; charge-basis volume;
   delivery month; published at close; final at sign-off).
2. **Settlement process doc + `settlement_runs` / `run_status_history`.** They govern *which run was the charge basis
   when*.
3. **Trading day-ahead process + `forecast_issues`.** They govern which forecast was locked.
4. **Data dictionary + `portfolio_membership`.** They govern grain. `dim_portfolio` is explicitly current-only.
5. **Packs (pre-migration).** Corroborating aggregates.
6. **Mart release notes, accuracy review, ops dashboard, thread.** Derived views and opinions; lowest authority.

**Conflicts and resolutions:**

- **Platform's "reconciliation is more accurate"** is true about physical volume but irrelevant to a KPI defined on
  the charge basis.
- **"Latest forecast"** conflicts with the lock at gate.
- **Current mapping** conflicts with effective dating.
- **Restated history** conflicts with the scorecard policy.

## 8. Plausible hypotheses

| H | For | Against |
|---|---|---|
| H1 v4 is genuinely ~30% better (new features, auto re-issue) | Release note; v4 better on every mart cut | Pre-migration shadow packs show ~9%; trading costs; improvement concentrated in horizons 1–3 and in post-gate issues |
| H2 Pre-migration packs were wrong (the notebook used stale estimates; the mart uses better data) | Platform thread; IS contains estimated reads, R2/RF are closer to physical volume | KPI defines charge basis; restatement changes both models, not only v4; finance policy |
| H3 Restructure broke the mart (BUSINESS missing, SME/IC odd in spring) | Visible in mart output | Explains portfolio gaps, not the model gap |
| H4 Evaluation-state defects in actual vintage, forecast vintage, grain, month and comparison population | All evidence | — |
| H5 Seasonality / spring 2026 easier to forecast (v4 live in easier months) | Restated history shows lower error recently | Pairing on the same examples removes it; packs don't show it |

## 9. Natural wrong implementations (all must fail the visible extract)

Each is written as a mutation. "Near-correct" rows keep every other component correct.

| # | Wrong repair | Why tempting | What it gets wrong |
|---|---|---|---|
| W1 | Actual = `settled_volumes_latest` (today's latest, any type) | It is what the mart does and what Platform argues | Reconciliation values for old months; restated history |
| W2 | Actual = first published (EST) | "First actual after delivery"; ops dashboard | Not a settlement run |
| W3 | Actual = IS with current status `published` | Finds "charged on IS" and filters status | Post-close corrections included; runs withdrawn/superseded after close lost; late IS included |
| W4 | Actual = IS `reason = 'scheduled'` (dedupe by picking the scheduled run) | Classic dedupe of multiple runs | Ignores withdrawal re-runs and data corrections; uses withdrawn values |
| W5 | Actual = latest run of any type published ≤ close with status as of close | Gets the as-of-close insight but not the charge basis | R1 (and data-corrected R1) for early-month days |
| W6 | Actual = IS as of close, but corrections of any run type overlay | "Data corrections supersede" read type-blind | R1/R2 corrections applied |
| W7 | IS known at close by `published_at ≤ C`, with current status | Common as-of filter | Superseded/withdrawn-after-close runs dropped (unsettled), and runs withdrawn before close but re-published miscounted |
| W8 | Knowledge time = `status_updated_at` or `loaded_at` | Timestamp columns named "updated/loaded" | Backfill and current-status times, not availability |
| W9 | One global cutoff: IS as of `--as-of` for all months | "Point-in-time as of the run" | Same as W3 plus the late-IS and gap cases |
| W10 | Forecast = latest issue before 11:00 **UTC** | Timestamps are UTC | BST gate-miss re-issues included |
| W11 | Forecast = latest issue per (model, run date) | Issue-level dedupe | Partial re-issues drop other regions' examples or use superseded ones |
| W12 | Forecast = latest issue overall (`forecast_latest`) | Mart | Post-gate auto re-issues (v4's inflated gain) |
| W13 | Forecast = scheduled issue only | "The 06:00 forecast" | Pre-gate re-issues ignored; days with a failed schedule dropped |
| W14 | Mapping = current `dim_portfolio` | Mart | BUSINESS dropped; SME/IC misassigned before June |
| W15 | Mapping by run date instead of target date | "Definition when the forecast was made" | Examples crossing a restructure |
| W16 | KPI month by run date | Mart | Month-boundary examples |
| W17 | Unsettled examples dropped or scored with a fallback (EST/R1) | Inner join habit | Status and counts |
| W18 | Freeze targets at forecast creation | "Point-in-time" over-applied | Nothing settled; all unsettled |
| W19 | Head-to-head unpaired (each model's own period) | Mart | Different populations |
| W20 | Metric-only patch (recompute WAPE from packs or scale) | Matching packs | Example table wrong |

**Expected plausible aggregates** (calibrated at build; §15 of the validation report records actuals):
- W3, W5, W7 and W10 each give pooled head-to-head numbers within about ±1–2 pp of the truth.
- W1 and W12 give the "−30%" story.

## 10. Investigation path (≈ 45–80 actions)

1. **(1–8)** Memo, README, run the mart, open the review and pack history. Discovery: restated months; v4 −30% vs
   pre-migration ~9%.
2. **(9–16)** Read mart code and SQL; RELEASES. Discovery: five changed choices and two retired feeds.
3. **(17–22)** Legacy notebook: what the packs were built from (retired snapshot, locked forecasts, "run at close").
4. **(23–32)** KPI doc, scorecard policy, billing retirement note, settlement process doc. Explore `settlement_runs`:
   types, reasons, statuses, multiple runs per date. Discovery: charge basis = IS family; corrections re-issue charges;
   reconciliation doesn't.
5. **(33–40)** `run_status_history`, the close log, packs' January footnote. Discovery: evaluation state is at close;
   withdrawn and superseded runs had a history; late IS explains the January counts.
6. **(41–48)** Forecast issues: multiple issues per run date, scopes, times. Trading doc gate in UK time. Discovery:
   v4's post-gate auto re-issues; partial re-issues; BST conversion.
7. **(49–54)** Portfolio restructures; SCD2 membership by delivery date; mart output missing BUSINESS.
8. **(55–66)** Implement example construction, KPI, pairing.
9. **(67–80)** Validation:
   - reproduce pre-migration pack WAPEs at 1 dp and scored counts;
   - explain residual differences;
   - row-level spot checks: late IS after close, correction after close, withdrawal gap, R1 before close, BST re-issue,
     partial re-issue, restructure boundary;
   - rerun for another `--as-of`.

## 11. Repair breadth

| Surface | Required change |
|---|---|
| Actual reconstruction | Charge-basis run per (region, class, date) at an arbitrary instant from runs + status history |
| Forecast selection | Lock at UK-local gate at forecast-unit grain |
| Grain | Membership effective by target date |
| Example construction | KPI month by target; per-month close; unsettled status |
| KPI + comparison | Unsettled excluded from WAPE; pairwise head-to-head over common scored keys; all model pairs from data |

The faulty code spreads these across `sql/accuracy_mart.sql`, `fcaccuracy/mart.py` and `fcaccuracy/kpi.py`. A correct
repair necessarily touches the actual logic, forecast logic, mapping and aggregation.

## 12. Hidden extracts

All are regenerated worlds with the same schema, documents and rules.

| Fixture | Semantic situation | Plausible overfit caught |
|---|---|---|
| **hidden_a "close boundaries"** | Earlier calendar (2024-11 → 2026-02). Settlement-agent outages in 2 regions push IS past close. 4× withdrawals, many straddling closes (gap at close; withdrawn after close). Correction batches clustered 0–3 days after closes. December and February closes slip, February by 4 WD. `--as-of` falls after February's *nominal* close but before its actual close. | W3/W7/W9 global or current state; close computed by a working-day rule; hard-coded visible close timestamps; hard-coded as-of; fallback for unsettled |
| **hidden_b "portfolio & issuing"** | Different restructures: a class moves mid-month (SME_HH → IC on the 15th); new portfolio EV (class EV_HH) from a mid-window date; horizons 1…10. 3× partial and gate-miss re-issues, in BST and GMT. v4 auto re-issues sometimes *before* the gate (10:20–10:55 UK). Different DST year. | W10 UTC gate; W11 issue grain; W13 scheduled-only; W14/W15 mapping; hard-coded portfolio sets and dates; hard-coded horizons 1–7; hard-coded "auto_reissue = post-gate" |
| **hidden_c "revision regime & models"** | Three models (v3, v4, v5). R1 at 9 WD, so R1 is known at close for most days. Frequent R1/R2 data corrections; IS correction chains (a correction of a correction); a withdrawn correction followed by a re-run; DF runs. No auto re-issues. | W5 latest-at-close any type; W6 type-blind corrections; "latest correction wins" by reason; hard-coded v3/v4 pair; logic keyed to v4 re-issue behaviour |

## 13. Mutation suite (`tools/g08/shortcuts.py`)

- **Controls:** `nop` 0; `oracle` 1; `alt_sqlite_windows` 1; `alt_event_replay` 1.
- **Natural wrong repairs** (all expected 0, all on the visible extract): W1–W19, as named mutations.
- **Partial repairs** (expected 0):
  - actual only (forecast, mapping and month unfixed);
  - actual + forecast (mapping unfixed);
  - everything but pairing.
- **Patches and cheats** (expected 0): `output_only_patch`, `metric_only_patch`, `db_edit`, `import_verifier_reference`.
- **Overfits** (visible 1, hidden 0, expected 0 overall):
  - `hardcoded_close_timestamps` (hidden_a);
  - `hardcoded_portfolio_membership` (hidden_b);
  - `hardcoded_model_pair` (hidden_c);
  - `hardcoded_horizons_1_7` (hidden_b);
  - `hardcoded_as_of` (hidden_a).

## 14. Alternative correct implementations

- **Oracle:** pandas repair of the workspace modules (`solution/`).
- **`alt_sqlite_windows`:** a single SQLite script with window functions; Python handles the London conversion via
  `zoneinfo` and writes the output.
- **`alt_event_replay`:** pure Python; replays status events chronologically and snapshots state at each close; forecast
  lock by scanning issues.
- **Verifier reference (`tests/reference.py`):** stdlib only, and structurally different again. It resolves status at
  an instant per run, and computes the DST rule arithmetically (last Sunday of March/October at 01:00 UTC).

The verifier ignores row order, extra columns and float formatting.

## 15. Verifier

1. The warehouse DB matches a pristine regeneration (digest).
2. `python -m fcaccuracy build --as-of <visible as-of>` succeeds, with outputs deleted first and the pipeline sandboxed
   as uid 65534 (Task 03–06 pattern).
3. **Examples:**
   - key set (model, region, portfolio, target_date, horizon) equal;
   - `run_date`, `issue_id`, `forecast_mwh` (±1e-6);
   - `kpi_month`;
   - `status`;
   - `actual_run_ids` exact;
   - `actual_mwh`, `abs_error_mwh` (±1e-6).
4. **Monthly KPI:** row set; counts exact; sums ±1e-6; WAPE ±1e-9 absolute.
5. **Head-to-head:** pairs, counts and months exact; WAPEs ±1e-9.
6. Determinism (byte-identical rerun).
7. **Hidden ×3:** checks 3–5.

The reference computes from the DB. It shares no code with the generator. A dev-only consistency test also checks the
reference against the generator's own bookkeeping (it knows which run it intended to be the basis at each close).

## 16. Answer-key and cheap-solve audit (pre-build)

| Cheap path | Result |
|---|---|
| Read one document | KPI doc gives the definition; settlement doc gives run semantics; neither gives the close-state, lock or grain. Fails. |
| One timestamp helper | None exists. Fails. |
| Copy one cutoff rule | No global cutoff is correct (W9). Fails. |
| Change one WHERE clause | `settled_volumes_latest` with `run_type = 'IS'` gives W3. Fails. |
| Match a historical metric | Packs are 1 dp aggregates of pre-migration months only; example-level grading and hidden extracts. Fails. |
| Restore old behaviour | Notebook's tables are retired. Fails. |
| One obvious notebook | Contains only joins to retired tables. Fails. |
| Final actuals everywhere | W1. Fails. |

**Residual risk.** A strong agent that reads the settlement doc, KPI doc and scorecard policy may hypothesise "IS as at
close" early. The remaining difficulty is:
- operationalising status at an instant (withdrawn/superseded history);
- the lock at a UK-time gate at forecast-unit grain;
- effective-dated grain;
- unsettled handling;
- pairing;
- validating row states that aggregates do not reveal.

That is comparable to Task 02's per-example × cutoff reconstruction across feature families.

## 17. Revisions after calibration and the pre-baseline adversarial review (as built)

### 17.1 Calibration

- **Portfolio classes.** Moving SME_HH (450 MWh/day base) in June made the current-dimension mapping so wrong (WAPE ≈ 9%)
  that the mart showed v4 *worse*, which contradicted the incident. A small unmetered-supplies class (UMS, 70
  MWh/day) now moves:
  - BUSINESS = {SME_NHH, SME_HH, IC_HH, UMS} until 2026-03-01;
  - SME = {SME_NHH, SME_HH, UMS}, IC = {IC_HH} from 2026-03-02;
  - UMS moves to IC from 2026-06-01.
- **Resulting headlines** (visible extract):

  | Source | v4 vs v3 |
  |---|---|
  | Deployed mart | −29.7% |
  | Truth | −13.6% on 26,999 common forecasts |
  | Pre-migration packs, per month | −11% to −15% |

- **Ties.** The generator guarantees strictly increasing issue times per model and run day (tie-breaking would
  otherwise differ between implementations).

### 17.2 Review findings and fixes

The independent review found grading sound. The oracle passed all 4 extracts, and every natural wrong path failed at
example level. It found five material problems.

| Finding | Severity | Fix |
|---|---|---|
| Easier than Task 02 on paper. The natural clocks (`published_at`, `changed_at`) were the correct ones. Every run had at most 2 status events, so `status='published' OR status_updated_at > C` matched the reference. Exact scored counts in `pack_history.csv` let an agent hill-climb every actual-rule error. | high (headroom) | **(a) Effective vs recorded status clock** (Task-02-style trap on the core path): `run_status_history(run_id, status, effective_from, recorded_at)`. A withdrawal takes effect from the run's own publication (void from the start) but is recorded when the notice arrives; a supersession takes effect and is recorded at the correction's publication (as built after the second review, §17.4). Withdrawal notices arrive 2–40 h (55%) or 3–45 days (45%) after publication; withdrawal share 1.5%. The charge basis at close depends on `recorded_at` (settlement doc: a charge stands until the notice is received). `settlement_runs.status_effective_from` replaces `status_updated_at`, so the current-status shortcut is also wrong. On the visible extract, status reconstructed on `effective_from` differs from truth on 467 examples (head-to-head −13.70% vs −13.60%); current status differs on 3,294. **(b) Coarser packs:** `pack_history.csv` and pack markdowns carry WAPE only (1 dp); the counts were removed. The January coverage note stays. |
| Timeout budget: the memo allowed a 10-minute build, while the verifier runs 6 builds + 4 world builds within 2400 s. | high | The redundant final restore build was removed (5 builds). After harbor check flagged that a stated time limit was untested, the memo says 10 minutes and a verifier test enforces it (`test_build_time`, 600 s); each build times out at 660 s; verifier timeout 4800 s. |
| WAPE tolerance 1e-9 with no "unrounded" requirement. | medium | Spec says numbers are written unrounded; WAPE tolerance 1e-7, relative change 1e-6. |
| Generator bug (hidden_a): an outage-delayed IS received a correction published before it. | medium | Close-boundary correction templates skip keys whose IS is published later than C − 50 h. `validate_runs` asserts at build time: first event is publication; events recorded after publication and strictly increasing; replacement published after the replaced run; at most one published IS per key at every recorded instant. |
| Untracked task; `test.sh` mode 644. | must-fix | `test.sh` and `solve.sh` set to 755; committed with the validation artifacts. |
| `RELEASES.md` listed exactly the five defects. | should-fix | Mixed with four correct, retained decisions (closed-month scope, WAPE pooling, horizon, all models). |
| Timeline contradictions (thread dated before the review's run; feeds retired before the June pack; notebook used locked forecasts after their retirement). | should-fix | Thread dated 22 Sep; mart 1.0.0 on 2026-07-27; Billing retirement effective 1 Aug 2026 with June the last snapshot; trading cut-over 20 Jul 2026. |
| "In force from July 2025" vs hidden_a months before July 2025. | low | Sentence removed; months come from `kpi_close_log`. |
| Memo "12%–16%" range. | nice | Memo cites the January shadow pack: −15.2%. |
| Pipeline inherits `PYTEST_CURRENT_TEST`. | low | `PYTEST*` variables stripped from the pipeline environment. |

### 17.3 Mutations affected

- `actual_status_updated_at_as_knowledge_time` is replaced by:
  - `actual_status_effective_from_shortcut` (current status or status taking effect after the close);
  - `actual_status_by_effective_time` (full history replay on `effective_from`).
- Strawman-ish paths kept only as cheap controls, and not counted as trap coverage: W2 (EST), W6 (type-blind
  corrections, 21 examples), W9 (identical to W3 on the visible extract; differs on hidden_a), W18 (at forecast
  creation), `loaded_at`.

### 17.4 Second review (after the fixes above)

No blocking issues. Oracle equals reference on all 4 extracts; generator invariants hold; no status-reconstruction
shortcut passes any extract.

| Finding | Fix |
|---|---|
| `effective_from` equalled `published_at` for every status row (supersessions were also back-dated), so an effective-time replay equalled "published by close + current status" (W7): three mutations were one function. | Supersessions take effect at the correction's publication; withdrawals stay void from publication. The effective-time replay is now a distinct, subtler wrong path (467 examples vs W7's 2,601). The redundant shortcut mutation was replaced by the reviewer's most likely near-miss, `actual_latest_is_published_by_close` (status ignored: 126 examples; head-to-head within 0.01 pp; 1 pack cell). |
| `ops/settlement_incidents.md` still said withdrawals are notified within two days. | Rewritten: most notices within two days, later-check faults notified weeks after publication. |
| Pack markdown head-to-heads carried WAPE to 2 dp, the strongest remaining signal for choosing between rules. | 1 dp WAPE (relative change stays 1 dp; the memo cites −15.2%). |
| The notebook still computed forecast counts. | Removed from the notebook's pack output. |

**Reviewer verdict:** on paper, roughly on par with Task 02. There are six independent components, every shortcut
fails, and the most likely failures for a strong agent are:
1. latest IS by close without the withdrawal-notice check;
2. effective/current-status clock without pack validation;
3. UTC gate or scheduled-only forecast lock (invisible in pack cells).

Cheapest successful path: ~30–40 actions.
