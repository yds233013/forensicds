# G10 build design: unconstrained demand under informative stockout censoring

- **Status:** implementation design after the research audit (`research/g10/G10_research_audit.md`) and the tolerance
  / identifiability pilot (`research/g10/pilot/`, summary in `research/g10/G10_tolerance_pilot.md`).
- **Supersedes:** `research/gen3_designs/G10_censored_demand.md`.
- **Scope:** nothing built beyond the pilot; no model run.

## 1. Incident

**Company.** Harvest Lane Markets (fictional), 16 grocery stores. Each store has one daily DC delivery:
- 10 morning-slot stores are replenished at 06:00, before opening;
- 6 afternoon-slot stores are replenished at 14:00.

**Replenishment.** Orders top shelves up to `ceil(multiplier × forecast)`, capped by shelf capacity.

**29 June 2026: two changes go live together.**
- **LEAN-26 working-capital programme.** The multiplier drops from 1.6 to 1.1 in 12 stores. Four stores, randomized
  within delivery slot, stay at 1.6 as the programme holdout.
- **Forecast v4.** Trained on 2025–26 sales, it replaces v3 for LEAN stores. v3 keeps running (production in holdout
  stores, shadow elsewhere).

**Also true in the window (6 Apr to 20 Sep 2026).**
- **Seasonality:** soups and hot beverages decline into summer; ice cream grows.
- **Promotions:** marketing halved promotional SKU-weeks from July.
- **Competitor:** a discounter opened near three LEAN stores on 20 July.
- **Store hours:** July 4 short hours and one store refit closure.

**Memo (Head of Planning).**
- The Q3 category review shows sales down in almost every category.
- The automated buy plan proposes cutting next quarter's buys in six of eight categories.
- Finance wants LEAN-26 extended to the holdout stores.
- Store managers say shelves are empty in the evenings.

The memo asks for:
1. an unconstrained demand history planning can retrain on;
2. category baseline trends and buy-plan actions;
3. the programme's lost-sales cost;
4. the production forecasts' bias against demand.

The command must run on other extracts. The memo does not name an estimator.

## 2. Estimand (oracle; stated before any method)

**Population.** Every store × SKU × date on which the store traded (store calendar), in the extract window.

For each row d:

| Quantity | Definition | Notes |
|---|---|---|
| **D_d** (demand) | units shoppers wanted to buy during trading hours: every arrival, sold or lost | generator truth |
| **expected_demand_d** | E[D_d \| observed data] | Equals `units_sold` when in stock all trading hours. On other days, sales plus expected arrivals during out-of-stock trading time. |
| **lost_units_d** | expected_demand_d − units_sold | |
| **Category baseline** (period p ∈ {pre: before go-live; post: from go-live}) | Σ over store-SKU series of the mean of expected_demand over the series' non-promotional trading days in p | |
| **baseline_change** | post / pre − 1 | |
| **action** | `reduce` if change ≤ −5%; `increase` if ≥ +5%; else `maintain` | The rule is stated in the planning process doc; it is a business rule, not a method. |
| **Programme lost sales** | Σ lost_units by period × arm (and × promo) | |
| **Forecast bias** | Σ(F − expected_demand) / Σ expected_demand for the production forecast: v3 pre (all stores); v4 post (LEAN stores) | |

**Verifier truth.**
- Every graded aggregate uses the generator's realised D (and realised non-promo daily means for baselines).
- Per-day expected demand is never compared with realised D; only aggregates over ≥ several hundred rows are graded.

## 3. Identifiability (why the estimand is recoverable)

- **A1. Traffic shape.** Arrivals for a store-SKU-day form a Poisson process with intensity λ_d·g_type(t). g depends
  only on day type (weekday / Saturday / Sunday), not on the level.
- **A2. Day level.** λ_d = μ(store, SKU, weekday, promo × category, category × week, competitor period) · ε_d, where ε_d
  ~ Gamma(α_category) has mean 1 and is independent of covariates and of the day's inventory.
- **A3. Observation.** Stockout and restock instants are exact. In-stock arrivals are single-unit sales. No phantom
  stock.
- **A4. Lost shoppers.** Shoppers arriving during a stockout are lost: no same-day return, no substitution into the
  SKU.
- **A5. Exposure.** Trading hours from the store calendar define exposure.

**Consequences.**
- Inventory is set before the day from the forecast and on-hand, so a sell-out is a stopping time of the observed
  sales process.
- The likelihood of the observed path is `λ^N Π g(t_i) exp(−λ G_in)`, where G_in is traffic-weighted in-stock
  exposure. Mixing over ε gives a negative-binomial likelihood with mean μ·G_in and shape α. Stopping does not change
  it.
- Maximum likelihood of that model, or EM over λ_d, is consistent for μ and α.
- The per-day posterior `E[λ_d | N_d] = (α + N_d)/(α/μ + G_in)` gives `expected_demand_d = N_d + E[λ_d | N_d]·(G_full − G_in)`.
- Alternative mixings and coarser covariate specifications are allowed if they meet the tolerances. Pilot: 4
  independent correct estimators.

**Informative censoring (why shortcuts fail).**
- The stockout rate rises with ε_d and with forecast under-reaction (promo, v4).
- **Drop censored days:** selects low ε.
- **Impute the mean rate:** ignores the day's revealed ε.
- **Per-day sales ÷ in-stock share:** a ratio at a stopping time, biased upward.
- **Poisson exposure model:** weights low-ε days, biased downward under overdispersion.
- **Daily censored Poisson:** misspecified tail.
- **Forecast imputation:** circular.
- **Profile from all days:** censored evenings bias the shape.
- **Uniform time:** ignores traffic.

## 4. Data-generating process (as implemented in `research/g10/pilot/g10_world.py`)

| Stage | Visible-extract parameters |
|---|---|
| Demand level | SKU base LN(ln 4, 0.7) × store scale U(0.7, 1.3) × weekday factors × category season (linear, −26% / −22% / +20% end-to-end for soups / hot beverages / ice cream; others flat) × promo lift by category (1.7–2.6) × competitor 0.88 (3 LEAN stores, from week 15) × trading-hours share |
| Day shock | Gamma(α_c), α_c ∈ {2.5 … 6} |
| Traffic shape | weekday evening peak; Saturday midday; Sunday 10:00–18:00 |
| Promotions | chain-wide SKU-weeks (Wed–Tue): 12% pre, 6% post |
| Forecasts | v3 = μ·LN(0, 0.15). v4 = μ·(1 − the series' pre-period lost share)·0.85 on promo·LN(0, 0.12). Neither knows the competitor. |
| Inventory | daily delivery at the slot to `min(cap, ceil(m × production forecast))`; leftovers carry; cap = ceil(2.6 × 1.25 × base × scale); m = 1.6 pre, 1.1 LEAN post, 1.6 holdout |
| Observation | hourly sales; out-of-stock / back-in-stock events; daily open/close on-hand and deliveries; forecasts; orders; calendar |
| Truth | per row: μ, λ, arrivals, lost |

**Visible magnitude** (5 seeds): 172k rows; censored-day share 0.29; lost share 0.12 (holdout post ≈ 0.07, LEAN post ≈
0.17).

## 5. Plausible hypotheses (≥ 3 plausible, ≥ 2 supported)

| H | Support | How analysis resolves |
|---|---|---|
| H1 customer demand fell | sales down; soups / hot beverages genuinely down; competitor near 3 stores | unconstrained baselines: soups −15%, hot beverages −13% real; others ≈ −2% (competitor), not −8 to −12% |
| H2 promo cut | promo SKU-weeks halved | baseline excludes promo days; promo cut explains total but not baseline declines |
| H3 LEAN-26 availability | stockout log up; holdout sales fell less | lost share 0.17 LEAN vs 0.07 holdout; estimated lost units |
| H4 v4 under-forecasts | model card trained on sales; v4 bias vs sales ≈ 0 | bias vs demand ≈ −6% (LEAN post) |
| H5 seasonal mix only | season plausible for all categories | only 3 categories have real season; the rest flat |

## 6. Workspace (to build)

```
/workspace
├── README.md                              repo map; `python -m demandsci review --db data/warehouse.sqlite --out out/review`
├── RELEASES.md                            demandsci releases (sales-based demand history; stockout "cleaning"), LEAN-26 note
├── demandsci/
│   ├── cli.py, warehouse.py, outputs.py
│   ├── demand.py                          deployed "demand history": sales, with stockout days excluded from baselines (faulty)
│   ├── trends.py                          category baselines + buy-plan actions from demand history (rule correct, input faulty)
│   └── impact.py                          programme lost sales (0 by construction) + forecast bias vs history
├── sql/availability_kpi.sql               in-stock rate (share of trading store-SKU-days without an out-of-stock event)
├── data/warehouse.sqlite                  stores, store_calendar, skus, promotions, sales_hourly, availability_events,
│                                           inventory_daily, replenishment_orders, forecasts, programme_assignment
├── docs/
│   ├── planning/buy_plan_process.md        baseline definition (unconstrained, non-promotional) + action thresholds
│   ├── planning/demand_definitions.md      what "unconstrained demand" means for planning (business meaning, no method)
│   ├── replenishment/order_up_to_policy.md order-up-to rule, multipliers, shelf caps, delivery slots
│   ├── programmes/lean26.md                programme design, randomized holdout
│   ├── models/v4_model_card.md             v4 trained on sales; validation vs sales
│   ├── stores/store_operations.md          trading hours, calendar, shopper behaviour at empty shelves (A4)
│   ├── stores/traffic_patterns.md          day-type traffic shapes exist, from footfall counters (no numbers usable as the profile)
│   ├── data/data_dictionary.md             tables, grains, event semantics (A3), timestamps local
│   └── outputs/review_outputs.md           output contract
├── notebooks/lost_sales_quick_estimate.ipynb   July analyst notebook: in-stock-hours scaling (attractor; wrong method)
├── reports/
│   ├── category_review_2026-09.md          sales-based trends and proposed buy cuts
│   ├── availability_weekly.csv             KPI output by arm
│   └── lean26_week8_readout.md             finance readout (sales-based, "no material sales impact vs holdout")
└── notes/
    ├── 2026-09-16_category_managers.md     conflicting positions
    └── 2026-07-22_competitor_opening.md     facts
```

## 7. Output contract (`docs/outputs/review_outputs.md`)

1. **`demand_history.csv`**
   - Columns: `store_id, sku_id, date, units_sold, expected_demand, lost_units`.
   - One row per trading store-SKU-day.
2. **`category_trends.csv`**
   - Columns: `category, baseline_pre, baseline_post, baseline_change_pct, action`.
3. **`programme_impact.json`**
   - `lost_units` and `lost_share` by period × arm;
   - `forecast_bias_pct` for v3 pre (all stores) and v4 post (LEAN stores).

## 8. Verifier (to build)

**Mechanics.**
- Warehouse digest unchanged.
- Build sandboxed (uid 65534, `/tests` 700) on visible + 3 hidden extracts.
- Deterministic rerun.
- Truth from the regenerated world (standard library).

**Checks per extract.**
1. **`demand_history` structure:**
   - exact key set;
   - `units_sold` exact;
   - `expected_demand == units_sold` (±1e-6) on rows in stock for all trading hours;
   - `lost_units` ≥ 0 and `expected_demand − units_sold` consistent.
2. **Strata** (period × arm × promo): Σ expected_demand and Σ lost_units vs realised truth within pilot tolerances.
3. **Category trends:** baseline_change within tolerance; action exact. Truth margins to ±5% ≥ 2.5 pp by construction.
4. **Programme impact:** lost_share and forecast bias within tolerance, consistent with the history.

Tolerances come from the pilot's calibration seeds (1.5× max correct error, floored) and are verified on fresh
validation seeds (§ tolerance pilot).

## 9. Hidden regimes

| Regime | Change | Wrong method it is most informative against |
|---|---|---|
| hidden_a | heavier overdispersion (α × 0.6); flatter weekday traffic; leaner LEAN (1.05); 9 afternoon-slot stores | Poisson offset; forecast imputation; per-day scaling |
| hidden_b (negative control) | weak censoring (1.8 / 1.45 / 1.8); 8 holdout stores; no promo cut; no competitor; different categories declining / growing | methods that manufacture demand; hard-coded category lists |
| hidden_c | strong evening peak; promo-heavy (20% / 15%); v4 promo under-reaction 0.7; less overdispersion | uniform-time scaling; profile from all days; no-promo models |

## 10. Mutation suite (to build)

- **Correct (must pass):**
  - oracle (NB-offset posterior, pandas);
  - EM Gamma–Poisson;
  - NB with 4-week season;
  - a fourth structurally different implementation (e.g. per-series NB using statsmodels with pooled profile).
- **Natural wrong (must fail):**
  - sales as demand;
  - drop censored days;
  - per-day traffic-share scaling;
  - uniform time scaling;
  - mean-rate imputation;
  - Poisson exposure offset;
  - daily censored Poisson;
  - forecast imputation;
  - profile from all days;
  - NB without promo;
  - holdout-store transfer.
- **Overfits (visible pass, hidden fail):**
  - hard-coded category actions;
  - hard-coded profile / α constants fitted on visible;
  - hard-coded go-live date;
  - hard-coded holdout store list.
- **Patches:** output-only patch, warehouse edit, verifier import.
