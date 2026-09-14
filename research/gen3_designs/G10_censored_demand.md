# G10: Censored demand — a forecast that "wins" on sales while shelves go empty

Status: generation-3 detailed design. Not built. No model has been run. All numbers below are design targets that the
build must calibrate and then re-measure; they are not results.

## Workspace sketch

```
/workspace
├── README.md                                  repo purpose, how backtests and the audit job are run
├── RELEASES.md                                demandlab + replenishment release notes (v4 pilot, safety-stock change)
├── demandlab/
│   ├── config.py                              extract path, windows, model ids (no censoring constants)
│   ├── io/extract.py                          typed loaders for every extract table (no joins, no derived columns)
│   ├── features/training_frame.py             v4 training frame: target = units_sold; "stockout cleaning" step (faulty)
│   ├── evaluation/metrics.py                  mape / wape / bias on arrays (correct, generic)
│   └── evaluation/backtest.py                 backtest report: MAPE on actual>0 rows, WAPE on sales (faulty target)
├── sql/availability_kpi.sql                   Ops shelf-availability KPI: closing on-hand > 0 (attractor)
├── data/extract/                              visible extract (Parquet + CSV), read-only
│   ├── stores.csv                     16      store_id, timezone, format, delivery_slot, trading hours by weekday
│   ├── store_hours_exceptions.csv     ~40     holiday hours / closures (local)
│   ├── skus.csv                       120     sku_id, category, velocity_class, substitute_group_id (nullable)
│   ├── substitution_study.csv         34      group_id, study_window, pct_shoppers_substituting, n_oos_observations
│   ├── promo_calendar.csv             ~4.1k   store_id|ALL, sku_id, promo_start, promo_end (local dates), mechanic
│   ├── sales_daily.parquet            ~457k   store_id, sku_id, business_date, units_sold, net_sales
│   ├── inventory_events.parquet       ~2.4M   event_id, store_id, sku_id, event_type, qty, count_value,
│   │                                          effective_at_utc, posted_at_utc, corrects_event_id
│   ├── inventory_daily_close.parquet  ~457k   store_id, sku_id, business_date, on_hand_close (perpetual as posted)
│   ├── pos_gateway_status.csv         ~300    store_id, status(online|offline), from_utc, to_utc
│   ├── forecasts/v3_backtest.parquet  ~107k   day-ahead forecasts, eval window, all store-SKU-days
│   ├── forecasts/v4_backtest.parquet  ~107k   same for v4
│   └── replenishment/orders.parquet   ~300k   order_date, store_id, sku_id, forecast_model, order_qty, safety_stock
├── docs/
│   ├── planning_handbook.md                   what forecasts are for; fill rate and availability KPIs (business meaning)
│   ├── data_catalog.md                        table grains, event semantics, snapshot timing, timezone conventions
│   ├── models/v4_model_card.md                v4 target, cleaning step, backtest claim
│   ├── ops/pos_offline_mode.md                what the tills do when the gateway is down; post-recovery count procedure
│   ├── merch/substitution_study_readme.md     how the 2025 loyalty-card study measured substitution
│   └── outputs/demand_audit_contract.md       output files, columns, grains (definitions only)
├── notes/
│   ├── store_ops/2026-10-21_store_manager_feedback.md   empty shelves on promoted items, pilot stores, afternoons
│   ├── planning/2026-10-27_fill_rate_review.md          generated: availability by arm and velocity class
│   └── incidents/INC-4471_S07_pos_gateway.md            one outage write-up (facts only)
└── reports/
    ├── backtest_2026-10-26.md / .json                    generated: v4 MAPE 31.2% vs v3 34.8%
    └── shelf_availability_weekly.csv                     generated from sql/availability_kpi.sql
```

Total visible data about 70 MB compressed. Runtime: `python:3.12-slim`, pandas 2.2, numpy 2.1, pyarrow, duckdb, scipy,
statsmodels, scikit-learn (pinned). No forecasting library that ships a lost-sales estimator.

---

## 1. Research question

Can an agent recognise that the observed quantity (sales) is a censored measurement of the decision-relevant quantity
(demand), reconstruct *when* censoring happened from an intraday inventory event log with posting-time/effective-time
semantics, distinguish censoring from a measurement outage and from substitution inflation, and then produce a corrected
demand history and a corrected model comparison whose correctness can only be checked against the unobserved truth?

The capability probed is post-recognition: most strong agents will say "stockouts censor sales" within minutes. The
task is built so that the *first* operationalisations of that idea (close-of-day stockout flag, drop zero-sales days,
trailing-mean imputation, evaluate on uncensored days) each produce believable, wrong numbers.

## 2. Enterprise setting

Harvest Lane Markets (fictional) is a 16-store regional grocer in two US time zones. The demand-planning team owns
`demandlab`, which produces day-ahead store × SKU forecasts that drive automatic replenishment. Orders are forecast plus
safety stock minus projected on-hand; the DC delivers once a day in a store-specific slot (10 stores at 05:00–06:30 local,
6 stores in an afternoon slot 13:00–16:00 local).

- **v3** (production since 2025): exponential smoothing per store-SKU with promo multipliers.
- **v4** (candidate): gradient-boosted model trained on `units_sold`. Its model card describes a "stockout cleaning"
  step: drop training rows where closing on-hand is 0 and sales are 0.
- **Pilot:** from 2026-08-31, 8 stores order from v4 and 8 stay on v3. Both models also produce shadow backtest
  forecasts for all 16 stores over the 8-week evaluation window (2026-08-31 to 2026-10-25).
- **Same week:** replenishment release R-2026.08.3 lowered the safety-stock service-level z from 1.65 to 1.28 for
  velocity class C in all stores (a real change).

## 3. Visible symptom

The instruction memo (from the Director of Supply Planning) says:

- The v4 backtest shows MAPE 31.2% vs 34.8% for v3. Planning wants to roll v4 out chain-wide on 2026-11-09.
- Store operations report empty shelves on promoted items in the pilot stores. The Ops shelf-availability KPI in pilot
  stores fell from 96.4% to 92.1% (control stores 96.2% → 95.6%).
- Planning believes the safety-stock release explains the availability drop. Ops believes v4 under-orders.
- "I need to know which model actually forecasts customer demand better before we decide, and the planning team needs
  a demand history they can retrain on."

Required, stated as deliverables, not as method:

1. `python -m demandlab.audit --extract <dir> --out <dir>` writes the three files defined in
   `docs/outputs/demand_audit_contract.md`:
   - `availability_flags.csv`;
   - `demand_history.csv`;
   - `model_evaluation.json`.
   The command must work on any extract with this schema; it will be re-run on other extracts.
2. Do not modify `data/extract/`. No store-, SKU-, date- or incident-specific handling.
3. The evaluation population is every store × SKU × business date on which the store traded, in the evaluation window
   of the extract (given in `extract_manifest.json`).

The memo does not mention censoring, substitution, POS outages or the event log.

## 4. Source distribution inspiration

This mirrors ordinary retail demand-planning practice:

- **Unconstrained demand.** Replenishment forecasts are meant to estimate unconstrained demand, while point-of-sale data
  record constrained sales.
- **Lost sales.** Lost-sales estimation from on-shelf availability is standard, as is the known bias of training and
  scoring forecasts on stockout-suppressed sales.
- **Substitution.** Customers switch to an alternative when an item is unavailable, and assortment and replenishment
  analytics treat this as a recognised effect.
- **Methods.** Censored-demand estimation is a textbook topic (Tobit-style censored likelihoods, EM for censored
  Poisson demand, intraday-profile scaling). These are "to verify" as specific literature references. The design does
  not rely on any one of them.
- **Operational details.** Split between posted time and effective time in perpetual inventory systems; offline till
  modes during POS gateway outages; late cycle-count corrections. These are common operational facts, stated here
  without reference to any real company.

## 5. Causal graph / ground truth

```
promo, dow, season, store scale ──► λ(store,sku,day) ──► arrivals A ~ Poisson(λ), timed by intraday profile p(format,dow,cat)
                                                              │
forecast model (arm) ─► order ─► receipt at slot time ─► physical on-hand(t) ──┐
                                                              ▼                │
                              arrival at t: on_hand>0 → sale (depletes) ; else substitute w.p. σ_g → sibling sale ; else lost
                                                              │
                         POS gateway offline → sale happens physically, but no depletion event / no sales row
                                                              ▼
            events: pos_depletion (15-min batches), receipt, shrink, cycle_count (absolute), corrections (late posted)
            sales_daily = Σ recorded sales ; inventory_daily_close = perpetual on-hand from events *posted* by 23:59 local
```

**Demand**
- λ = base_sku × store_scale × dow_sku × season(week) × promo_lift × Gamma(8, 1/8) day noise.
- promo_lift ~ U(1.6, 3.2) by SKU. About 9% of store-SKU-days are on promo (weekly circular, Wednesday to Tuesday).
- About 30% of class-C store-SKU-days have λ < 0.5, so true zero-demand days are common for slow movers.

**Intraday profile**
- Hourly profile by format × dow × category.
- Weekday: morning shoulder and a strong 16:00–19:00 peak. The evening 4 hours carry about 38% of daily demand in
  25% of trading minutes.
- Weekend: flatter, midday peak.
- Profiles differ enough that uniform-minute scaling is biased for partial-day stockouts.

**Units per arrival:** 1 (a design choice to keep lost-demand truth exact).

**Substitution**
- When the SKU is out, the shopper buys one in-stock sibling from the same substitute group with probability σ_g.
  The sibling is chosen by base-share weights.
- σ_g ~ U(0.15, 0.60) by group. `substitution_study.csv` reports σ_g plus noise (±0.03), as measured in a 2025 study.
- Sibling *sales* include substitutes. Sibling *own demand* does not.

**Replenishment**
- Order = forecast(next day) + z·σ̂·√L − projected on-hand.
- v4 is trained on censored sales. On promo days it under-forecasts demand by about 12% relative to v3, so pilot stores
  stock out more on promo items.
- DC delivers at the store's slot, so afternoon-slot stores are routinely out mornings and back by 16:00.

**Inventory events**
- `pos_depletion`: one row per 15-minute window with recorded sales. `effective_at_utc` = window end;
  `posted_at_utc` = window end + U(1, 40) min.
- `receipt`: effective at the physical put-away time. About 6% are posted late, after the 23:59 local close snapshot,
  with effective time during the day.
- `shrink`: effective at the discovery time.
- `cycle_count`: `count_value` sets absolute on-hand at `effective_at`. About 8% of counts are *corrected* by a later
  `cycle_count` row with `corrects_event_id`, posted 1–3 days later with the same effective time. The correction
  replaces the original.
- The perpetual balance is physically accurate once all events are applied in effective-time order. Balances computed
  in posted order go transiently wrong, including negative.

**`inventory_daily_close`:** perpetual on-hand from events posted by 23:59 local, applied in posted order. This is what
Ops uses.

**POS gateway outages** (`pos_gateway_status.csv`, plus `docs/ops/pos_offline_mode.md`)
- Tills keep trading. Offline transactions for these tills are not recoverable (a fact stated in the INC note for S07).
- No depletion events and no sales rows are written for offline minutes.
- On recovery, the procedure is a full count of the store posted as `cycle_count` rows effective at recovery time.
- Visible outages: S07 on 2026-09-19, all day (08:00–22:00); S12 on 2026-06-14, 11:00–15:10.
- Generator constraint: physical on-hand never hits 0 during an offline interval. Stock state is therefore
  deterministic outside offline minutes, and "unknown" is not needed inside them.

**Timezones:** 10 stores in America/New_York, 6 in America/Chicago. Events are in UTC. Business date, trading hours
and promo dates are local. The training window contains the 2026-03-08 DST start.

**Store hours exceptions:** Labor Day (2026-09-07) short hours; S04 closed 2026-07-04 (no rows, not in population).

**Visible targets (to calibrate)**

| Quantity | Target |
|---|---|
| Store-SKU-days with any open, online stockout minutes (eval window, pilot / control) | 7.9% / 3.6% |
| Same, promo days only (pilot) | 31% |
| Stockout days that are *partial* (in stock for part of trading hours) | ~42% |
| Days with `on_hand_close = 0` that lost < 3% of demand (sold out in last 30 min) | ~1,150 |
| Cycle-count corrections that change a stockout interval | ~410 |
| Backtest MAPE (actual > 0) v3 / v4 | 34.8% / 31.2% |
| WAPE vs sales v3 / v4 | 30.9% / 29.1% |
| **True WAPE vs own demand** v3 / v4 | **27.4% / 32.1%** |
| True lost demand, eval window | ~21k units (partial 8.3k, full 11.9k, offline 0.8k) |
| Substitution inflow into siblings on days with ≥ 240 sibling-out minutes | ~16% of those siblings' own demand |

## 6. Latent statistical/business invariant

1. **Demand, not sales, is the target.** The quantity to forecast, to train on and to evaluate against is each SKU's
   own unconstrained demand: what shoppers would have bought had the SKU been on the shelf during all trading minutes.
2. **Sales equal own demand only on clean days.** A clean store-SKU-day has three properties:
   - the SKU had on-hand > 0 for every open minute, where on-hand is reconstructed in effective-time order with
     corrections replacing originals;
   - the POS was online for every open minute;
   - no sibling in its substitute group was out of stock during an open minute.

   On every other day, sales are a biased measurement:
   - stockout minutes: downward (censoring);
   - offline minutes: downward (missing measurement, *not* censoring);
   - sibling-out minutes: upward (substitution inflow).
3. **Censoring is informative.** Stockouts concentrate on high-λ days (promos, peak weekdays) and in high-intensity
   hours. Therefore:
   - an evaluation restricted to uncensored days is biased toward low-demand days;
   - imputation that ignores promo state and intraday timing is biased downward.
4. **The model comparison must be computed against demand over the full evaluation population**, with demand on
   non-clean days estimated. The preferred model is the one with lower WAPE against demand.

The invariant is statistical: no deterministic rule recovers demand on censored days. The deterministic part (flags) is
graded exactly; the estimated part is graded against generator truth with tolerances.

## 7. Grains and state variables

| Grain | Where | Mistake if confused |
|---|---|---|
| Inventory event (effective vs posted time) | `inventory_events` | Ordering by `posted_at` gives phantom stockouts and missed ones |
| Correction chain (`corrects_event_id`) | events | Applying both original and correction double-counts a count |
| Store × SKU on-hand *interval* (UTC → local) | reconstructed | Close snapshot ≠ intraday state |
| Store trading interval (regular hours ∩ exceptions, local, DST) | stores, exceptions | Overnight minutes counted as stockout minutes |
| POS gateway interval | `pos_gateway_status` | Outage read as stockout or as zero demand |
| Store × substitute group × minute | reconstructed | Sibling inflation ignored |
| Store × SKU × business date | outputs | Dropped rows (zero-sales days) |
| Stratum (promo × velocity × censor type) | estimation / grading | Pooled imputation ignores promo lift |
| Forecast origin (day-ahead) | backtests | — (fixed; not a trap) |

## 8. Evidence graph

(★ = on the natural path; an agent following the memo will open it.)

| Artifact | Shows | Path |
|---|---|---|
| ★ `reports/backtest_2026-10-26.md` | v4 wins on MAPE/WAPE vs sales | natural start |
| ★ `demandlab/evaluation/backtest.py` | MAPE excludes actual = 0 rows (full-day stockouts and outage day silently dropped); target = `units_sold` | natural |
| ★ `docs/models/v4_model_card.md` | "stockout rows removed (on-hand 0 at close and 0 sales)" — suggests censoring already handled | natural; attractor |
| ★ `sql/availability_kpi.sql`, `reports/shelf_availability_weekly.csv` | Ops definition of out-of-stock = `on_hand_close = 0` | natural; attractor |
| ★ `notes/store_ops/...feedback.md` | "gaps on promo items by mid-afternoon; delivery comes at 3" (afternoon slot) | natural; hints partial days |
| ★ `RELEASES.md`, `notes/planning/...fill_rate_review.md` | safety-stock change for class C, availability drop partly C in both arms | natural; distractor with real support |
| `docs/data_catalog.md` | effective vs posted; cycle count absolute; corrections replace; close snapshot = perpetual as posted at 23:59 local; depletion batch = 15-min window ending at `effective_at`; timestamps UTC, business dates local | must read to reconstruct |
| `inventory_events.parquet` | intraday state; partial-day stockouts; late receipts | must use |
| `pos_gateway_status.csv`, `docs/ops/pos_offline_mode.md`, INC-4471 | outages; offline transactions lost; full count on recovery | reachable from S07 zero-sales anomaly |
| `substitution_study.csv` + readme | σ_g per group (measured 2025) | reachable from `skus.substitute_group_id` |
| `promo_calendar.csv` | promo state | natural |
| `replenishment/orders.parquet` | arm per store; safety stock per order | distractor analysis |
| `docs/planning_handbook.md` | "Forecasts are an estimate of what customers want to buy, so that the shelf can meet it" + fill-rate KPI meaning | business meaning only |

## 9. Evidence authority hierarchy

| Conflict | Governs | Why |
|---|---|---|
| Ops availability KPI (close on-hand) vs event log | **Event log** (effective-time order) | The data catalog defines the snapshot as perpetual-as-posted at a moment. The KPI is a dashboard convenience; its SQL comment says "end-of-day proxy". |
| v4 model card "stockouts removed" vs data | **Data** | Card describes a filter; the events show it misses partial days and flags late sell-outs |
| Backtest report (sales) vs planning handbook | **Handbook** (demand is the target) | The report computes a metric; the handbook defines the business quantity |
| `substitution_study.csv` vs in-extract behaviour | Study is admissible evidence; either source may be used | Study σ is within ±0.03 of generator σ; estimating from data is also acceptable (§20) |
| `inventory_daily_close` = 0 on POS outage day? (it is not; perpetual stays high) vs sales = 0 | **POS gateway log + offline-mode doc** | Measurement outage, not demand and not stockout |
| Safety-stock release narrative vs arm comparison | **Data** | C-class drop is real in both arms; promo A/B-class drop is arm-specific |

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | v4 is genuinely a better forecaster; availability fell for other reasons | ★ backtest MAPE/WAPE; model card claims stockouts handled | v4 error vs reconstructed demand on promo days; arm-specific promo stockouts |
| H2 | Safety-stock release caused the availability drop | ★ release timing = pilot start; C-class availability fell in both arms | Pilot-vs-control gap is concentrated in A/B promo items, which the release did not touch |
| H3 | DC short-shipments (dairy, week of 2026-09-14) | ★ receipts < orders for dairy that week | Affects both arms equally; one week only |
| H4 | v4 learned stockout-suppressed sales and is scored on them (true) | store feedback; MAPE code drops zero actuals; training frame target | Requires event-log reconstruction to show |
| H5 | Store execution (shelves not replenished from backroom) | store feedback is about shelves | On-hand hits zero in the event log; no backroom state exists |

## 11. Why each wrong hypothesis is plausible

- **H1:** the only quantitative model evidence the organisation has says v4 wins. Its model card claims the obvious
  confound was removed.
- **H2:** it is a real change in the same week, it lowers availability, and the planning review shows a C-class drop.
  An agent that computes availability by velocity class only (not by arm × promo) sees support.
- **H3:** it is real and visible in `orders.parquet`. It creates a dip in the weekly KPI.
- **H5:** it matches the words "empty shelves". It cannot be refuted from sales alone.

## 12. Investigation path (≈ 45–80 actions)

| Phase | Actions | Discoveries |
|---|---|---|
| Orient | 1–8 | Memo; backtest report; `backtest.py` (MAPE drops zeros, target = sales); v4 card ("stockout rows removed"); availability KPI |
| Distractors | 9–16 | Safety-stock release; availability by arm × class × promo; DC shortage week |
| First censoring idea | 17–22 | Join `inventory_daily_close`; "OOS = close 0 and sales 0"; re-score → v4 still wins (natural wrong path, §13) |
| Doubt | 23–30 | Store note mentions 3 pm deliveries. Afternoon-slot stores show close on-hand > 0 but depletion stops at 11:00. Data catalog: close snapshot semantics. |
| Reconstruction | 31–45 | Replay events by effective time; apply corrections; build open intervals from hours, exceptions and timezone (DST); intersect. Discover S07 zero sales with no stockout → gateway log → offline doc. |
| Substitution | 46–52 | Sibling SKUs sell above normal while partner out; `substitute_group_id`; study table |
| Estimation | 53–65 | Intraday profile from clean days; lost demand on partial days; promo-aware model for full days and offline minutes; subtract substitution inflow from siblings |
| Evaluation | 66–72 | WAPE vs estimated demand over the full population → v3 better; sanity by stratum |
| Validation | 73–80 | Row audits of reconstructed intervals against raw events for several store-SKU-days (late receipt, correction, DST day, outage); clean-day identity; rerun determinism |

## 13. Natural wrong implementation

**Step 1 (most likely first repair).** Reuse the v4 card's rule and the Ops KPI.

```python
close = io.inventory_daily_close()
df = sales.merge(close, on=KEYS)
df["stockout"] = (df.on_hand_close <= 0) & (df.units_sold == 0)
eval_df = df[~df.stockout]                           # or: df[df.units_sold > 0]
wape(eval_df.forecast, eval_df.units_sold)
```

- **What it gets wrong.**
  - *Partial days*: about 42% of stockout days have close on-hand > 0 (afternoon delivery or late receipt), so they
    remain, scored against suppressed sales.
  - *Morning and midday sell-outs*: with the `units_sold == 0` condition, only zero-sale days are flagged, so a SKU
    that sold 14 units by 11:00 and then sat empty is scored as a 14-unit actual. Without that condition (the Ops KPI
    variant), the ~1,150 days that sold out in the last 30 minutes are flagged as full stockouts and excluded, although
    they lost < 3% of demand.
  - *Slow movers*: `units_sold > 0` removes ~30% of class-C true-zero days, which penalises neither model fairly and
    shifts the population toward high-volume days.
  - *S07 outage*: dropped by the zero filter, or kept as a zero actual.
- **Numbers (targets).**
  - Close-flag exclusion: v3 30.2%, v4 28.8%.
  - Drop zero-sales days: v3 29.9%, v4 28.6%.
  - Both still say v4.
- **Flags table.** A close-based flag misclassifies ~6,700 of ~15,900 affected visible store-SKU-days.

**Step 2 (after noticing partial days).** Replay events in `posted_at` order (the natural file order), or use
`effective_at` without applying corrections.

- Posted-order replay creates about 1,900 spurious short stockouts: depletion batches posted before a receipt posted late.
- Double-applying corrected counts shifts about 410 intervals.
- UTC business dates misassign evening minutes for all stores (UTC−4/−5 → 20:00 local onward lands on the next date).

## 14. Second-order failure modes

1. **Exclude non-clean days, evaluate on the rest.**
   - Flags correct, no estimation.
   - Result: v3 25.1%, v4 27.0%. The ordering is right but both values are outside tolerance vs truth (27.4 / 32.1).
   - This is because the censored population is the high-demand promo population where v4 fails.
   - The demand-history coverage check fails too (non-clean rows missing or null).
2. **Trailing 28-day mean for flagged days.**
   - Ignores promo lift and weekday; promo full-day stockouts are underestimated by about 38%.
   - Result: v3 28.9%, v4 30.0%, both outside ±1.0 pp.
   - The full-stockout promo stratum fails (−38% vs ±12%).
3. **Uniform-minute scaling:** `demand = sales × open_minutes / in_stock_minutes`.
   - Evening-peak censoring makes it underestimate partial-day lost demand by about 30%.
   - The ratio is undefined for full days; typical patches (cap, fallback to mean) inherit error 2.
   - The partial stratum fails (±8%).
4. **Treat the POS outage as a stockout or as zero demand.**
   - As a stockout: flags table wrong (in-stock minutes = 0 instead of offline minutes).
   - As zero demand: the offline stratum fails. In hidden_b (larger outages) both evaluation numbers move by more than
     tolerance.
5. **Ignore substitution.**
   - Sibling-exposed stratum demand overstated by about 16% (tolerance ±6%).
   - Evaluation numbers move modestly; the stratum check is what catches it.
6. **Double-correct substitution.** Subtract σ × *observed* partner shortfall using sales-based lost demand, or
   subtract from the partner as well. The sibling stratum is under by 10–20%.
7. **Estimate everything with a model, including clean days** (smoothing noise away). This fails the exact clean-day
   identity (`demand_estimate == units_sold`).
8. **Retrain a new model and report its error.** Not requested. `model_evaluation.json` must evaluate v3 and v4 as
   supplied. Extra keys are ignored.

## 15. Correct repair properties

- **On-hand state:** reconstructed per store × SKU from events in effective-time order, with each correction replacing
  its original.
- **Minutes:** trading intervals in local time (regular hours, exceptions, DST) intersected with on-hand > 0 and with
  POS-online intervals.
- **Flags:** one row per trading store-SKU-date, exact classification. Siblings' out-of-stock minutes computed per
  store × group.
- **Demand history:**
  - `demand_estimate = units_sold` on clean rows;
  - upward estimates for censored and offline minutes that use timing (intraday profile) and demand state (promo,
    weekday, level);
  - downward adjustment for substitution inflow on sibling-exposed rows;
  - no negative estimates;
  - rows for every trading store-SKU-date, including true zeros.
- **Evaluation:** WAPE (and bias) of each supplied forecast against the demand history over the full population;
  `preferred_model` = argmin WAPE.
- **Generality:** nothing specific to S07, the afternoon-slot store list, specific groups, or dates.

## 16. Repair surfaces

| Surface | Why it must change |
|---|---|
| New `demandlab/audit/` (reconstruction, flags, estimation, evaluation, CLI) | Nothing in the repo computes intraday state; the deliverable requires it |
| `demandlab/evaluation/backtest.py` (optional) | Its MAPE-on-sales target is the symptom; the verifier grades the audit outputs, not this file |
| `demandlab/features/training_frame.py` (optional) | Ideally consumes `demand_history.csv`; not graded, because retraining is out of scope |

No helper exists for any surface. Existing `metrics.wape()` is generic and correct.

## 17. Validation requirements

An agent cannot be confident from aggregates. It must check:

- **Reconstruction audits.** For a handful of store-SKU-days of each kind (afternoon-slot store, late-posted receipt,
  corrected count, DST day, holiday hours, outage day), compare the reconstructed on-hand path with raw events and
  with sales timing. A stockout should coincide with depletion batches stopping.
- **Clean-day identity** and row coverage (including zero-sales days).
- **Substitution sanity.** Sibling 15-minute sales during partner-out intervals vs the same hours on clean days.
- **Estimator sanity by stratum.**
  - Estimated lost share on partial days vs the profile share of censored hours.
  - Promo full-day estimates vs uncensored promo days of the same SKU.
  - A simulation check: artificially censor clean days, then recover them. This is the one aggregate-free check an
    expert would do.
- **Arm-level story.** The pilot/control difference in promo stockouts is consistent with the v4 bias measured
  against demand.

Aggregates cannot replace the flag audits: close-based flags produce a believable availability curve and a
believable evaluation.

## 18. Hidden fixture strategy

All three are produced by the same generator with different parameters. No hidden fixture uses a mechanism absent from
the visible extract.

| Fixture | Invariant stressed | Surface change | Overfit caught | Same distribution because |
|---|---|---|---|---|
| `hidden_a` | Partial-day censoring and intraday timing | 9 of 16 stores afternoon slot; stronger evening peak (46% in last 4 h); promo intensity 14%; σ_g range 0.35–0.70; v3 wins by 6 pp | Close-based flags; uniform-minute scaling; hard-coded afternoon store list; study σ ignored (in-data σ differs from visible) | Slots, profiles, promo rate and σ are all visible parameters |
| `hidden_b` | Outage ≠ stockout ≠ zero demand; model choice not hard-coded | Low stockout rate (v4 pilot with safety buffer); **true v4 better (v3 26.0%, v4 23.9%)**; three gateway outages, including a 3-hour one and a 2-day outage at one store; correction lag up to 5 days | `preferred_model = "v3"` hard-coded; outage as zero or as stockout; corrections assumed ≤ 3 days | Outages and correction lag are visible mechanisms with different magnitudes |
| `hidden_c` | Local-time and trading-interval semantics; true zeros | Three timezones (adds America/Denver); DST *end* inside the eval window; a store closed for 2 days (exception); 45% class-C SKUs with many zero-demand days; 50% singletons | UTC dates; fixed 2 timezones; drop zero-sales rows; group-size assumptions | Timezone, DST and exceptions are visible mechanisms (visible DST start, holiday hours, one closure) |

**Named overfit pairings:**
- `hardcode_v3_choice` ↔ hidden_b.
- `afternoon_store_list` and `uniform_minute_scale` ↔ hidden_a.
- `utc_business_date` and `drop_zero_sales` ↔ hidden_c.
- `outage_as_zero` and `correction_lag_3d_window` ↔ hidden_b.
- `study_sigma_constants_pasted` (visible σ values hard-coded rather than read) ↔ hidden_a.

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` (no audit module) | 0 |
| `oracle` (profile scaling + promo-aware multiplicative model for full days + study σ) | 1 |
| `alt_censored_poisson` (independent: censored Poisson likelihood per store-SKU with promo/dow covariates; interval censoring from minutes × profile; σ estimated from data) | 1 |
| `alt_em_intraday` (independent: EM over latent arrivals by 15-min slot) | 1 |
| `alt_duckdb_reconstruction` (flags via SQL window functions) + oracle estimator | 1 |
| `close_flag_exclude` | 0 (flags, strata, eval) |
| `drop_zero_sales` | 0 (coverage, eval) |
| `trailing_mean_impute` (correct flags) | 0 (full stratum, eval) |
| `clean_days_only_eval` | 0 (eval, coverage) |
| `uniform_minute_scale` | 0 (partial stratum) |
| `posted_order_replay` | 0 (flags) |
| `corrections_double_applied` | 0 (flags) |
| `utc_business_date` | 0 (flags) |
| `outage_as_stockout` / `outage_as_zero` | 0 / 0 |
| `ignore_substitution` / `substitution_double_count` | 0 / 0 |
| `smooth_clean_days` | 0 (clean identity) |
| `hardcode_v3_choice` | visible pass, hidden_b fail |
| `afternoon_store_list` | visible pass, hidden_a fail |
| `study_sigma_constants_pasted` | visible pass, hidden_a fail |
| `edit_extract` / `write_outputs_only` | 0 (integrity; outputs regenerated by rerun) |

**Tolerance calibration rule:**
1. Tolerances are fixed from the spread of the three independent valid estimators across 20 generator seeds: max
   absolute deviation × 1.5, floored at the Poisson noise floor of the stratum.
2. The design requires every naive mutation to miss by at least 1.5× its tolerance on at least one graded check in
   every fixture.
3. If that fails, generator parameters (promo stockout share, profile peak) are adjusted and all seeds re-run.
   Tolerances are never tightened just to reject a mutation.

## 20. Alternative valid implementations

- **Reconstruction.** Any order-correct implementation (pandas replay, DuckDB windows, interval trees) passes exact
  checks.
  - Minute accounting tolerance: ±15 minutes per row. This covers "batch window start vs end" readings of the 15-minute
    depletion convention.
  - `stockout_class` and `sibling_oos_minutes > 0` are graded exactly, except rows where the relevant interval is
    ≤ 15 minutes. The verifier skips those as boundary-ambiguous.
- **Estimation.** Any method. Graded only through stratum aggregates and the evaluation numbers against truth.
- **Substitution.** Study σ or data-estimated σ. Both land within tolerance in calibration; this is required before
  build.
- **Offline minutes.** A null `demand_estimate` is allowed on rows with any offline minutes. Non-null values count
  toward the offline stratum. The evaluation must still include those rows. An agent that nulls them must impute for
  the evaluation; the contract says WAPE is over the full population.
- **Extra columns and keys** are ignored.

## 21. Verifier design

1. Integrity: extract digest unchanged.
2. Run the command as an unprivileged user on visible + 3 hidden extracts (outputs deleted first); twice on visible
   for determinism (byte-identical CSVs, JSON numbers equal).
3. `availability_flags.csv`: exact key set (trading store-SKU-dates); exact `stockout_class`;
   `open_minutes`/`in_stock_minutes`/`pos_offline_minutes`/`sibling_oos_minutes` within ±15; boundary-ambiguous rows
   skipped (< 0.5% of rows).
4. `demand_history.csv`: exact key set; `units_sold` equals extract; clean rows exact identity; no negatives; stratum
   checks against **generator truth** (own demand):

| Stratum (by verifier truth flags) | Tolerance (relative, design target) |
|---|---|
| partial stockout, promo / non-promo | ±8% / ±8% |
| full-day stockout, promo / non-promo | ±12% / ±12% |
| sibling-exposed (≥ 240 min), in stock all day | ±6% |
| POS offline (non-null rows) | ±15% |

   Strata with < 2,000 true units are merged with their neighbour.

5. `model_evaluation.json`: WAPE per model within ±1.0 pp of truth WAPE vs own demand; bias within ±1.5 pp;
   `preferred_model` equals truth argmin. Every fixture has a truth gap ≥ 2 pp.
6. Reward = all checks pass.

**Determinism and truth.** Truth demand is stored by the generator at build time in `tests/` only. The generator is
seeded and standard-library only; the extract is written by the generator's pure-Python Parquet writer or CSV.
Parquet via pyarrow happens in a build step whose output digest is checked.

## 22. Answer-key leakage audit (with cheap-solve audit)

| Artifact | Could it be transcribed or matched? |
|---|---|
| `demand_audit_contract.md` | Defines columns. For example, `in_stock_minutes` means "trading, POS-online minutes with on-hand > 0". It states *what* a column means, not *how* to reconstruct on-hand (effective order, corrections, timezone). It mentions no estimator. **Risk: M.** Naming `sibling_oos_minutes` hints substitution. Mitigation: the column is justified as an Ops field ("minutes a substitute group had a gap"), and the adjustment itself is never mentioned. |
| `data_catalog.md` | Facts: effective vs posted, corrections replace, snapshot timing. These are system behaviours an expert needs. No sentence says "order by effective time to find stockouts". |
| `substitution_study.csv` | Gives σ, not the adjustment. Its readme says the study measured "share of shoppers who chose another item in the group when the item was missing", i.e. a behaviour. |
| v4 model card | Describes the wrong rule (attractor), no right rule |
| `sql/availability_kpi.sql` | Wrong rule for this purpose |
| Backtest report | Numbers vs sales; no truth |
| `orders.parquet` | Contains `forecast_model` and `safety_stock`, no demand |
| Old reports | No lost-sales report, no "v2 unconstrained" notebook, no `lost_units` column anywhere |

**Cheap-solve audit:**
- **One grep?** `grep -ri stockout` finds the wrong rule (card, KPI). `grep -ri censor` finds nothing.
- **One doc?** No doc states the demand-on-censored-days method or the evaluation population rule beyond "every
  trading store-SKU-date".
- **One SQL?** The close-based SQL is the attractor. A single SQL for flags needs effective-order window functions
  with correction replacement plus trading-interval intersection. That is feasible, but it is the reconstruction itself.
- **One filter?** Every filter-only approach fails (§13–14).
- **Helper?** None: no interval utilities, no profile tables, no timezone helper beyond `stores.timezone`.
- **Old report?** None contains demand.
- **Restoring behaviour?** There is no "before" to restore; v3 is not the answer (hidden_b).
- **Residual cheap path:** "pick v3" is a 50% guess. It is caught by hidden_b and by numeric checks.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Is demand own demand or sales including substitutes? | Handbook: planning forecasts "each item's own demand, as if the full range were on the shelf". The contract names the column "own demand estimate". |
| Demand during offline minutes: missing or zero? | Offline doc: tills traded but transactions are lost. Contract allows null on offline rows; evaluation must still cover them. |
| Stockout at exactly 0 vs below a presentation minimum | Contract: on-hand > 0. No presentation minimum anywhere in the generator. |
| 15-minute batch timing | Catalog: batch covers the 15 minutes ending at `effective_at`; ±15-minute tolerance and boundary skip |
| Receipt effective at put-away but posted late | Catalog: effective time is when stock became sellable |
| Store closed days | Not trading, so not in the population (contract) |
| Evaluation weights (WAPE vs MAPE) | Contract fixes WAPE = Σ\|F−D\|/ΣD and bias = Σ(F−D)/ΣD over the population |
| Sibling exposure threshold | Output is a minutes count (no threshold). Grading strata thresholds are internal to the verifier. |
| Multi-unit purchases | Generator uses 1 unit; not observable either way; no rule depends on it |
| Phantom inventory (perpetual ≠ physical) | Excluded by construction and stated in the catalog ("counts reconcile perpetual to physical; there is no known phantom stock issue in this extract") — **an acknowledged realism simplification** |
| Estimator tolerance could reject a valid but weak method | Calibrated on three independent estimators; residual risk in §27 |

## 24. Expected trajectory length

60–110 tool calls for a passing agent: reconstruction (~25), estimation (~20), row audits (~15), distractors (~10),
and orientation plus reruns. A Task 06-style "read three files, write a groupby" pass is not possible: the flags alone
require an interval engine, and the estimates require a statistical model with a self-check.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | Here |
|---|---|
| Target cutoff already in faulty code | No censoring logic exists; the existing rule (card/KPI) is the wrong one |
| Summary already implemented | Evaluation must be rebuilt against a quantity that does not exist in the data |
| Natural group/merge/subtract was correct | Natural merge with the close snapshot is wrong; natural imputation is wrong |
| Attractor evidence optional | Card and KPI are opened on the first path to "handle stockouts" |
| Traps on paths no agent chose | Traps *are* the first three repairs a competent agent writes |
| One customer's line check enough | Correctness is statistical across strata; row audits are needed for flags, and aggregate self-checks (simulated censoring) for estimates |

## 26. Comparison with Task 02

- **Grain.** Both require reconstructing state at a non-obvious grain: Task 02 per example × cutoff; here per store ×
  SKU × minute, with effective vs posted time. This is a close analogue of Task 02's `synced_at`/`changed_at`
  distinction, deliberately inverted: here *effective* time governs physical state.
- **Statistics.** G10 adds a statistical layer Task 02 lacks. Even with perfect state, the estimand is not directly
  observable, and informative censoring makes the easy estimators biased.
- **Headline metric.** Task 02 agents failed while their AUC looked plausible. Here, WAPE from close-based flags and
  from clean-days-only both look plausible, and one of them even picks the right model.
- **Expected difficulty:** harder than Task 02. The risk is the reverse: legitimate agents failing tolerances (§27).

## 27. Benchmark risks

- **Implementation cost: H.**
  - Physical inventory simulator with substitution, replenishment driven by two forecasters, and an event log with
    corrections.
  - Truth bookkeeping.
  - Three independent estimators for calibration.
  - The backtest forecasts must be produced by actual v3/v4-like models inside the generator, or by a parametric
    stand-in with the documented bias. The stand-in is acceptable if its errors are realistic (heteroscedastic,
    promo-dependent).
- **Tolerance validity: M–H.** This is the largest risk. If valid estimators disagree by more than the gap to naive
  methods, the task either rejects valid work or accepts naive work.
  - Mitigations: seeds sweep; promo stockout concentration and evening-peak strength are the levers that widen the
    naive-vs-valid gap.
  - Kill criterion: if no parameter set gives ≥ 1.5× separation on every fixture, drop estimate grading. The task then
    becomes flags + clean identity + `preferred_model` only, which is weaker.
- **Substitution identifiability: M.** Data-estimated σ may be noisy for small groups. Stratum grading pools across
  groups, and the study table exists as admissible evidence.
- **Realism simplifications:** 1 unit per purchase; no phantom inventory; perfect effective timestamps; offline
  intervals never contain a true stockout. Each is stated as a fact in docs, not hidden.
- **Leakage: L–M** (contract column names).
- **Overlap: low.** The posted/effective distinction echoes Task 02's availability theme but is secondary here.
- **Headroom risk: low.** The more likely failure is too hard or too noisy, not too easy.
- **Runtime:** reconstruction over ~2.4M events × 4 extracts in pandas is about 1–3 minutes each. Verifier budget
  30 minutes.
