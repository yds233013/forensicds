# G05: Staggered self-checkout rollout — the panel regression says roll back

Status: generation-3 detailed design. Not built. No model has been run. Numbers are design targets to be calibrated by
the generator and re-measured.

## Workspace sketch

```
/workspace
├── README.md                                 rollout_readout package; how readouts are run for store programs
├── rollout_readout/
│   ├── panel.py                              builds store × week panel from the mart (faulty: ISO weeks, planned waves,
│   │                                         eligibility = transactions > 0)
│   ├── estimate.py                           TWFE via numpy lstsq with store & week FE, cluster-robust SE by store
│   ├── event_study.py                        TWFE with binned event-time dummies (−8..+26), ref = −1
│   ├── report.py                             writes readout JSON/markdown
│   └── __main__.py                           `python -m rollout_readout --program <id> --warehouse <db> --out <dir>`
├── data/warehouse.duckdb                     read-only
│   ├── stores                  420           store_id, region, format, sqft, opened_on, lat, lon
│   ├── fiscal_calendar         ~700 days     date, fiscal_year, fiscal_week (Sunday–Saturday; FY2025 has 53 weeks)
│   ├── kpi_store_week          ~40k          store_id, fiscal_year, fiscal_week, net_merch_sales, customer_txns, sco_txn_share
│   ├── store_closures          ~5.5k         store_id, date, closure_type (remodel|install|weather|refrigeration|other), hours_closed
│   ├── program_rollout_plan    420           program_id, store_id, planned_wave, planned_go_live
│   ├── install_log             ~400          program_id, store_id, work_order, event (prewire|install|go_live), event_date
│   ├── competitor_sites        ~260          site_id, banner, lat, lon, opened_on, closed_on
│   └── trade_area_overlap      ~1.9k         store_id, site_id, overlap_share (real-estate team, 2024 refresh)
├── notebooks/
│   ├── sco2_readout_2026-09.ipynb            analyst TWFE readout (−2.3%) + event study plot
│   └── esl_readout_2025-11.ipynb             previous program readout (electronic shelf labels), same TWFE code
├── docs/
│   ├── kpi_handbook.md                       basket size definition; "comparable trading week"; fiscal calendar
│   ├── programs/sco2_program_brief.md        what SCO 2.0 changes; wave plan; installer process (prewire → install → go-live on Sunday)
│   ├── programs/readout_output_contract.md   output files and fields (estimand wording, no estimator)
│   └── real_estate/trade_area_methodology.md how overlap_share is computed; what the competitor table covers
├── notes/
│   ├── coo_2026-09-08_memo.md (the instruction)  
│   ├── store_ops/regional_manager_updates_R4.md  weekly notes; mentions ValuMart leaving town, footfall
│   └── store_ops/store_manager_survey_2026-08.csv "baskets bigger since SCO" free text + 1–5 score
└── reports/sco2_readout_2026-09-01.{json,md}  generated from faulty code: ATT −0.023 (se 0.009)
```

About 45 MB total. Runtime: Python 3.12, pandas, numpy, statsmodels, duckdb, matplotlib (pinned). Network off during
the agent run, so `pip install` of DiD packages is not possible; see §22 for why this is a deliberate choice and what
happens if it is relaxed.

---

## 1. Research question

Can an agent produce a credible causal readout of a staggered store rollout when three problems interact?

- **The house estimator is biased.** Two-way fixed effects (TWFE) is contaminated under heterogeneous, growing effects.
- **The textbook replacement is also biased as naively applied.** Not-yet-treated DiD with a `g−1` base period breaks
  on this panel: the base week is a KPI-ineligible install week, and a store-level time-varying confounder (a competitor
  closure) coincides with one wave.
- **The panel is not what it looks like.** Adoption timing and KPI eligibility must be rebuilt from operational tables
  at a different grain: daily closures to fiscal weeks, and actual go-live instead of plan.

The recognition step ("TWFE is biased under staggered adoption") is expected to be fast for a frontier model. The task
is designed so that recognition is worth little. The binding constraints are panel construction, base-period choice
and confounder adjustment, graded against simulated truth.

## 2. Enterprise setting

Meridian Foods (fictional) operates 420 grocery stores in six regions. SCO 2.0 is a self-checkout redesign: larger
bagging shelves, an integrated scale and a "big basket" lane. It went live in five waves between fiscal week 28 of
FY2025 and fiscal week 70; 24 stores are holdbacks scheduled for FY2027.

The Store Analytics team owns `rollout_readout`, a small package used for every store-program readout: ESL shelf labels
in 2025, and SCO 2.0 now. The package is re-run for each program on the warehouse. Basket size (net merchandise sales per
customer transaction, weekly) is the program's primary KPI.

## 3. Visible symptom

The COO memo (instruction) says:

- The readout says SCO 2.0 reduced basket size by 2.3% (95% CI −4.1% to −0.5%). The COO intends to stop the remaining
  holdback installs and revert the installed stores.
- Store managers' survey and regional updates say baskets got bigger.
- "Tell me what SCO 2.0 did to basket size, overall and for each wave, and whether we should keep it."

Deliverables (the memo points to `docs/programs/readout_output_contract.md`):

1. `python -m rollout_readout --program SCO2 --warehouse data/warehouse.duckdb --out out/` writes two files:
   - `out/analysis_panel.csv`: store × fiscal week, with the columns defined in the contract, including
     `kpi_comparable`, `adoption_week` and `event_week`;
   - `out/readout.json`: the causal effect estimates and the recommendation defined below.
2. The estimand, verbatim from the contract:
   - "For each wave: the average, over that wave's KPI-comparable store-weeks in event weeks 0–25, of the difference
     between log basket size and the log basket size the store would have had without SCO 2.0."
   - "Overall: the same average over all adopting stores' comparable store-weeks in event weeks 0–25."
   - "`recommendation` is `keep` if the overall effect is ≥ 0, else `rollback`."
3. The package is reused for other programs. The command will be run on other warehouses with the same schema. No
   program-, store-, region- or date-specific handling.
4. Do not modify the warehouse.

The memo does not mention TWFE, competitors, install weeks or calendar issues.

## 4. Source distribution inspiration

This mirrors a common situation in retail and multi-site analytics:

- **The initiative.** Initiatives roll out in waves for operational reasons, and the house analysis is a panel
  regression with unit and time fixed effects.
- **The estimator literature.** Modern DiD work shows that static and dynamic TWFE can be badly biased under staggered
  adoption with heterogeneous or dynamic effects. Estimators built on clean comparisons (not-yet-treated or never-treated
  controls, imputation, stacked designs) address this. These are "to verify" references, not relied on for grading:
  Goodman-Bacon decomposition; Callaway & Sant'Anna; Sun & Abraham; Borusyak, Jaravel & Spiess; de Chaisemartin &
  D'Haultfœuille.
- **Operational realities the literature does not handle for you:**
  - installation disruption right before go-live (an Ashenfelter-style dip in the base period);
  - planned vs actual go-live dates;
  - retail fiscal calendars (Sunday-start weeks, 53-week years);
  - local market shocks from competitor openings and closures, which real-estate teams track through trade-area
    overlap.

## 5. Causal graph / ground truth

```
store FE α_s, region×season, fiscal-week FE δ_t, AR(1) noise ─┐
                                                              ├─► log basket y_st
SCO effect τ_s(e) for e ≥ 0 (actual go-live) ─────────────────┤
install disruption d_st in prewire/install weeks (closures) ──┤   (and closure days themselves)
competitor closure lift c_s(t) = κ · overlap_s · ramp(t − closed_on) ─┘
wave assignment ← planning (store size, region, ValuMart proximity for W3) ⇒ W3 timing ≈ R4 closure
```

**Panel:** 420 stores × 96 fiscal weeks (FY2025 W1 = Sunday 2024-11-03 through FY2026 W43). FY2025 has 53 weeks, so the
fiscal week number resets after W53.

**Outcome:** y = α_s + δ_t + ρ_{region}(season) + τ + d + c + ε, with ε AR(1) φ = 0.5, sd 0.028.

**Waves (planned go-live week; actual go-live is always a Sunday)**

| Wave | Planned FW (continuous index) | Stores | Region mix | A_w (long-run) |
|---|---|---|---|---|
| W1 | 28 | 40 | large-format, all regions | 0.080 |
| W2 | 38 | 60 | all | 0.065 |
| W3 | 48 | 80 | 52 in R4 (50 with ValuMart overlap) | 0.050 |
| W4 | 58 | 100 | all | 0.040 |
| W5 | 70 | 116 | all | 0.030 |
| Holdback | — | 24 | all (5 in R4) | — |

**Effects**
- τ_s(e) = A_w · m_s · (1 − exp(−(e+1)/16)), where m_s ~ LogNormal(0, 0.25), correlated with sqft (ρ = 0.4).
- Effects grow for about a year (customers learn the big-basket lane). Early, larger waves have larger long-run
  effects.

**Truth estimands (targets)**
- Wave ATT over event weeks 0–25: W1 0.0417, W2 0.0339, W3 0.0261, W4 0.0208, W5 0.0156.
- Overall: 0.0244.

**Actual vs plan:** 15% of stores slipped 1–4 weeks (`install_log.go_live`). Go-live is always Sunday, so no partially
treated weeks.

**Install disruption**
- Prewire and install happen with the store closed 1–2 days (Tuesday–Wednesday), in event week −1 (70%), −2 (20%) or
  both (10%). These are recorded in `store_closures` (`closure_type = install`, `hours_closed` 10–24).
- In those weeks log basket falls by U(0.04, 0.07): express lanes only, and shoppers split trips.

**Other closures:** refrigeration refits, weather and remodels in about 5% of store-weeks, basket perturbation
N(−0.02, 0.02). Winter weather closures cluster by region.

**KPI comparability (handbook fact):** "A comparable trading week is a fiscal week in which the store traded full hours
on all seven days." Any `store_closures` row in the fiscal week makes it non-comparable.

**Competitor closures**
- `competitor_sites.closed_on` for ValuMart:
  - 14 R4 sites closed Saturday 2025-10-11. The next fiscal week is W3's planned week 48.
  - 8 R2 sites closed at FW 22.
  - 11 R6 sites closed at FW 66.
- c_s(t) = κ · overlap_share_s · min(1, (t − t_close + 1)/3), where κ = 0.05. The effect is permanent.
- `trade_area_overlap` exists for all store × site pairs with overlap > 0. It includes open competitors (irrelevant
  until they close) and closed sites whose closure was before the panel.
- Exposure in R4:
  - W3 R4 stores: 50/52 exposed, mean overlap 0.66.
  - R4 not-yet-treated and holdback stores: 12/38 exposed, mean 0.60.
  - W3 non-R4 stores: none.

**Headline numbers produced by the faulty readout (targets)**

| Estimator | Overall | Notes |
|---|---|---|
| Static TWFE, planned waves, all weeks (house) | **−0.023** (se 0.009) | forbidden comparisons with growing effects; install weeks in treated/untreated periods; lever: ramp horizon |
| TWFE with event-time dummies −8..+26, ref −1 (house `event_study.py`), averaged 0–25 | −0.006 | ref week is the install dip; cross-cohort contamination |
| True overall ATT | **+0.024** | |

Calibration lever: if the static TWFE cannot be made significantly negative with long-run effects ≤ 8%, the memo is
rewritten to "no detectable effect (+0.2%, CI spans 0); rollback because of cost". The trap structure is unchanged.
This is a stated fallback, not a hidden change.

## 6. Latent statistical/business invariant

1. **Treatment timing** is the actual go-live fiscal week (install log), not the plan. Event week = fiscal-week index
   difference on the continuous fiscal index, with 53-week years handled.
2. **Eligibility.**
   - Store-weeks with any closure day in the Sunday–Saturday fiscal week are not comparable.
   - They are excluded from the estimand *and* must not serve as a base period or as control observations.
   - Most install weeks (e = −1/−2) fall here, so any estimator anchored on `g−1` must use a comparable pre-period
     instead.
3. **Clean comparisons.** The counterfactual for a treated store-week must come from stores not yet treated (or never
   treated) at that calendar week, never from already-treated stores. Effects vary by wave and event time.
4. **Local confounding.**
   - Stores whose trade area overlapped a competitor that closed receive a permanent, overlap-proportional lift.
   - A valid counterfactual must account for that lift at store level: controls with comparable exposure, or an
     exposure covariate in the untreated-outcome model.
   - Region-level time effects are insufficient, because exposure varies within region and W3 is disproportionately
     exposed.
5. **Aggregation:** comparable store-weeks, event weeks 0–25, pooled within wave, then across all adopting stores.

## 7. Grains and state variables

| Grain | Source | Mistake if confused |
|---|---|---|
| Store × date closures | `store_closures` | ISO (Monday) weeks put Sunday closures in the wrong week (~14% of closure days) |
| Store × fiscal week (Sunday start, FY2025 53 weeks) | `fiscal_calendar` | Fixed 52-week arithmetic shifts event weeks after the year boundary |
| Store adoption (planned vs actual) | plan vs install log | Slipped stores mis-timed |
| Wave (cohort) | plan label vs actual adoption week | Cohort defined by label: slipped stores pooled with a timing they do not have |
| Store × competitor site × closure date | trade area + sites | Region-level adjustment |
| Calendar week × control set | estimator | Already-treated controls |

## 8. Evidence graph

(★ = on the natural path.)

| Artifact | Shows | Path |
|---|---|---|
| ★ `reports/sco2_readout_2026-09-01.md`, notebook | TWFE −2.3%; event-study plot with a sharp dip at −1 and a noisy positive post-period | natural |
| ★ `rollout_readout/estimate.py`, `panel.py` | TWFE; planned waves; ISO weeks; eligibility = transactions > 0 | natural |
| ★ `store_manager_survey`, R4 updates | baskets up; "since ValuMart left, Saturday baskets huge" (R4 notes, weeks 48–52) | natural (memo cites managers) |
| ★ `docs/kpi_handbook.md` | basket definition; comparable trading week; fiscal calendar | natural (KPI definition) |
| `docs/programs/sco2_program_brief.md` | installer process (prewire → install → Sunday go-live); waves; dates may move | reachable |
| `install_log` | actual go-live; prewire/install dates | reachable via brief |
| `store_closures` | daily closures with type | reachable via handbook |
| `competitor_sites`, `trade_area_overlap`, methodology doc | closures and overlap | reachable from the R4 note (names ValuMart) or from a region breakdown |
| `sco_txn_share` in the KPI mart | jumps at actual go-live (verifies timing from data) | reachable |
| `esl_readout_2025-11.ipynb` | same TWFE code on a different program ("+1.1%"); shows the package is reused | optional |

## 9. Evidence authority hierarchy

| Conflict | Governs | Why |
|---|---|---|
| Rollout plan wave dates vs install log go-live | **Install log** | The brief says the plan is a schedule and dates move; `sco_txn_share` confirms actual dates |
| `panel.py` eligibility (`txns > 0`) vs KPI handbook | **Handbook** | The KPI owner defines comparability; code is an implementation |
| ISO week in code vs fiscal calendar table | **Fiscal calendar** | Handbook: all KPIs are reported in fiscal weeks |
| TWFE readout vs store managers | Neither; **identification** governs | Managers are anecdote, and R4 managers are confounded by ValuMart. The readout is a biased estimator. |
| Region-level "competitor adjustment" vs trade-area overlap | **Store-level overlap** | Methodology doc: overlap is the pricing team's measure of competitive exposure per store; the data show jumps only where overlap > 0 |
| Estimand in contract vs whatever an estimator package reports | **Contract** | Event weeks 0–25, comparable weeks, store-week pooling |

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | SCO 2.0 lowers basket size | ★ house TWFE −2.3%, significant; event-study dip at −1 | Clean comparisons positive; dip is pre-treatment and closure-driven |
| H2 | Seasonality / calendar artefact | ★ waves near holiday periods; 53-week year | Fiscal-week FE absorbs chain seasonality; the bias persists |
| H3 | The benefit is only the ValuMart effect (SCO does nothing) | ★ R4 managers; W3 effect largest under naive CS | Non-R4 waves and unexposed W3 stores show ramps; exposed never-treated R4 stores jump without SCO |
| H4 | KPI broken by partial weeks | ★ closure weeks have odd baskets | Explains the dip, not the sign of TWFE by itself |
| H5 | Effect positive and growing, heterogeneous by wave (true) | survey; `sco_txn_share` ramps | Only visible after the panel is fixed and comparisons are cleaned |

## 11. Why each wrong hypothesis is plausible

- **H1:** it is the organisation's official method, and it is statistically significant with clustered SEs.
- **H2:** retail analysts reflexively suspect calendar effects; the fiscal calendar genuinely has a 53-week year.
- **H3:** the most vivid anecdote in the workspace is about ValuMart, and an agent who applies not-yet-treated DiD
  *without* the confounder gets W3 = +0.043, the largest wave effect. That supports "it's all ValuMart".
- **H4:** true, and it is the first panel-hygiene finding. It tempts an agent to stop after fixing only this.

## 12. Investigation path (≈ 40–70 actions)

| Phase | Actions | Discoveries |
|---|---|---|
| Reproduce | 1–8 | Run readout; notebook; `estimate.py` |
| Recognise | 9–12 | Staggered TWFE with dynamic effects → Bacon-style concern; implement not-yet-treated 2×2 comparisons by hand (numpy/pandas) |
| Textbook result | 13–18 | CS-style ATT(g,t) with base g−1: overall +0.061, W3 +0.083. "Too big" or accepted. |
| Panel hygiene | 19–32 | Event-study dip at −1 → KPI handbook → closures → fiscal weeks (Sunday) → install log → actual go-live; `sco_txn_share` check; FY2025 53 weeks |
| Re-estimate | 33–38 | Comparable-only, actual timing, comparable pre-period base → overall +0.027, W3 +0.042 (still confounded) |
| Heterogeneity check | 39–48 | W3 anomaly: step at e=0 with no ramp; R4 split; R4 not-yet-treated stores jump at FW 48 → R4 notes → ValuMart → competitor tables and overlap |
| Adjust | 49–58 | Exposure-matched controls or overlap × post-closure covariate in the untreated-outcome model; placebo on R2/R6 closures (no SCO timing) to size κ |
| Validate | 59–70 | Pre-trend placebo per wave on comparable weeks; leave-R4-out comparison; exact panel table checks (row audits for slipped stores, Sunday closures, year boundary) |

## 13. Natural wrong implementation

**First wrong implementation after recognition** (the textbook fix on the house panel):

```python
panel = rollout_readout.panel.build(program)          # planned wave week, ISO weeks, all weeks with txns>0
for g in cohorts:
    for t in weeks:
        base = g - 1
        treated = panel[(cohort==g)]
        controls = panel[(adopt_week > t) | never]    # not-yet-treated
        att[g,t] = (y[treated,t] - y[treated,base]).mean() - (y[controls,t] - y[controls,base]).mean()
overall = weighted mean of att[g, t] for t-g in 0..25
```

**What it gets wrong, numerically (targets)**
- **Base week.** For 80% of stores the base week (g−1) is an install week, depressed by about 0.055. Every ATT(g,t)
  is inflated by about 0.045 after the control-side dip is netted. Overall comes out near +0.061, W3 +0.083.
- **Contaminated controls.** Not-yet-treated stores in their own install window are depressed in some calendar weeks,
  which adds noise and a small upward bias.
- **Timing.**
  - ISO weeks misplace Sunday closures.
  - The planned wave week mis-times 15% of stores.
  - Planned-wave cohorts include slipped stores whose e=0..3 are actually untreated.
  - Each is small (≤ 0.004), but each is fatal for the exact panel table.
- **Confounder.** ValuMart is ignored: W3 is inflated by +0.017.
- **Recommendation.** `keep` is correct, but the numbers fail every tolerance.

**Second natural wrong implementation** (house `event_study.py`, "we already have an event study"):
- TWFE with event-time dummies, reference −1, on the house panel.
- Reference week = install dip. Cross-cohort contamination of the leads and lags is present.
- Overall (average 0–25) −0.006 → `rollback`.

## 14. Second-order failure modes

1. **Drop closure weeks, keep base = g−1** (now missing for most stores).
   - Packages or hand code silently drop those cohorts' stores, or fall back to the nearest available week inconsistently.
   - Wave ATTs are computed on a subset. Estimates are close for some waves, but W1 (fewest stores with e=−2
     comparable) is noisy.
   - **Also:** the population differs from the estimand, and the panel table shows stores dropped.
2. **All hygiene right, no confounder adjustment.**
   - Overall +0.0277 (truth 0.0244, tolerance ±0.003 → fail); W3 +0.042 (truth 0.026, tolerance ±0.008 → fail).
3. **Drop W3 or drop R4.**
   - Dropping W3 omits a required wave estimate → fail.
   - Dropping R4 stores: W3 is estimated from 28 non-R4 stores. Effects scale with m_s (correlated with sqft, and R4
     W3 stores are larger), so W3 is ≈ 0.020 vs truth 0.026 → fail. Other waves also lose R4 stores and their
     population changes.
   - Principled reason: the estimand is over all adopting stores.
4. **Region × week fixed effects** as the confounder adjustment.
   - Absorbs R4's average lift (12/38 controls exposed), leaving residual W3 bias ≈ +0.014 → fail.
   - Risk discussed in §27.
5. **Competitor dummy by region × post-closure.** Same as 4.
6. **Adjust with a binary "overlapped a closed site" × post indicator** instead of overlap share. Residual bias ≈ 0.002
   because treated and control exposed stores have similar mean overlap → **passes** (accepted as valid, §20).
7. **Include all closures ever** (`closed_on` before the panel). No effect, since these are constant within store and
   absorbed by store FE → passes.
8. **Event weeks 0–25 counted from planned go-live**, or 26 weeks including e=26 → panel table fails; small numeric bias.
9. **Dynamic TWFE with never-treated controls only** (24 holdbacks, all leads/lags). Still contaminated when effects are
   heterogeneous across cohorts (Sun–Abraham argument) and noisy → fail.

## 15. Correct repair properties

- **Panel.** Built on fiscal weeks from `fiscal_calendar`.
  - `adoption_week` = fiscal week (continuous index) of the actual go-live.
  - `kpi_comparable` = no closure day in that Sunday–Saturday week.
  - `event_week` computed on the continuous index.
- **Estimation.** Uses only comparable store-weeks. Counterfactual outcomes come from not-yet-treated or never-treated
  comparable store-weeks. Base periods and pre-period anchors are comparable weeks.
- **Confounder.** Adjusted at store level using overlap with closed competitor sites and closure timing:
  - exposure covariate in an untreated-outcome model;
  - or matching on exposure;
  - or controls restricted to similar exposure.
- **Aggregation** per contract; `recommendation` from the overall sign.
- **Generality:** no hard-coded program, wave list, region or ValuMart dates. Everything is read from tables.

## 16. Repair surfaces

| Surface | Why |
|---|---|
| `panel.py` | Fiscal weeks, actual adoption, comparability; the exact panel table depends on it |
| `estimate.py` (or new module) | Clean-comparison estimator with a non-`g−1` or comparable anchor and exposure adjustment |
| Confounder feature builder (new) | Store × week exposure from `trade_area_overlap` × `competitor_sites.closed_on` |
| `report.py` | Contract fields: wave and overall ATTs, recommendation |

No existing code contains a not-yet-treated comparison, an exposure builder or a fiscal-calendar join.
`event_study.py`'s binning code is TWFE-specific and does not carry over.

## 17. Validation requirements

- **Row audits of the panel:**
  - a slipped store (plan vs `install_log` vs `sco_txn_share` jump);
  - a Sunday closure;
  - a week straddling the FY2025→FY2026 boundary (53rd week);
  - a holdback store.
- **Placebo pre-trends** per wave on comparable pre-weeks with the chosen estimator: flat.
- **Confounder placebo.** Apply the estimator to the R2 (FW 22) and R6 (FW 66) closures, using *unexposed* stores as
  controls, to measure κ without SCO timing. Check that W3 exposed vs unexposed stores' estimated effects agree after
  adjustment.
- **Event-time profile** per wave: ramps, not steps. A step at e=0 flags a confound.
- **Aggregate insufficiency.** Overall ATT after hygiene but without the confounder adjustment differs from truth by
  only 0.003. Only wave-level heterogeneity checks reveal it.

## 18. Hidden fixture strategy

Each hidden warehouse is a different store program run through the same generator.

| Fixture | Invariant stressed | Surface change | Overfit caught | Same distribution because |
|---|---|---|---|---|
| `hidden_a` (program ESL2) | Confounder at store level, different wave and sign | 4 waves; a competitor *closure* coincides with wave 2 in R1; a competitor *opening* (negative lift, `opened_on`) in R5 at a non-wave date; install dip mostly at e=−2; truth overall +0.012 | Hard-coded ValuMart / R4 / W3 adjustment; exposure logic that handles closures but ignores openings | Openings are in the visible `competitor_sites.opened_on` and exercised visibly: 6 visible openings, one in-panel in R6 with a small effect |
| `hidden_b` (program SCAN&GO) | Decision computed, not assumed | **Truth overall −0.015** (effects negative and deepening); house TWFE +0.011 (flipped the other way); 30% slipped go-lives; panel starts mid-FY2025, so the 53-week boundary falls inside at a different index | `recommendation = keep` hard-coded; planned waves; fixed 52-week arithmetic | Negative effects are the same functional form with A_w < 0; slips and the fiscal calendar are visible mechanisms |
| `hidden_c` (program FRESHCASE) | Comparability correlated with timing | Winter weather closures cluster in R3 during wave-3 go-live weeks; overlap shares continuous 0.1–1.0 across 3 closure events; 40 holdbacks; stronger size-effect heterogeneity | ISO weeks; "drop weeks with closure_type = install only"; binary exposure with very different overlap distributions (bias grows) | Weather closures, continuous overlap and multiple closures are all visible (R2/R6 closures, weather rows) |

**Note on binary exposure.** In hidden_c the treated/control mean overlap differ (0.8 vs 0.35), so a binary indicator
leaves bias ≈ 0.009 on the affected wave. This rejects binary exposure there. To remain fair, the visible trade-area
methodology doc must state that overlap share scales competitive exposure. The visible extract must show this: R2's
closure lift visibly scales with overlap in a scatter.

**Named overfit pairings:**
- `hardcode_R4_W3_adjust` ↔ hidden_a.
- `keep_hardcoded` ↔ hidden_b.
- `fiscal_52_week_arith` ↔ hidden_b.
- `install_type_only_eligibility` ↔ hidden_c.
- `binary_exposure` ↔ hidden_c.

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` (house TWFE readout, house panel) | 0 |
| `oracle` (imputation estimator: untreated-outcome model with store FE, week FE, overlap×closure-ramp covariate, fit on comparable untreated store-weeks) | 1 |
| `alt_cs_notyet_exposure_matched` (independent: ATT(g,t) 2×2 comparisons; anchor = mean of comparable pre-weeks −8..−2; controls reweighted to treated exposure distribution) | 1 |
| `alt_stacked_did` (independent: stacked sub-experiments per wave with clean controls, exposure covariate, event window) | 1 |
| `twfe_static` / `twfe_event_dummies` | 0 / 0 |
| `cs_base_g_minus_1_house_panel` | 0 |
| `hygiene_no_confounder` | 0 (W3, overall) |
| `drop_w3` / `drop_r4` | 0 / 0 |
| `region_week_fe` | 0 |
| `iso_weeks` / `planned_waves` / `fiscal_52_week_arith` | 0 (panel) |
| `binary_exposure` | visible 1, hidden_c 0 |
| `hardcode_R4_W3_adjust` | visible 1, hidden_a 0 |
| `keep_hardcoded` | visible 1, hidden_b 0 |
| `install_type_only_eligibility` (drops only `closure_type = install` weeks) | 0 on the visible panel table (weather/refrigeration rows exist); hidden_c additionally fails numerically. Build must confirm the visible failure (§27). |
| `edit_warehouse`, `write_outputs_only` | 0 |

**Tolerance calibration:**
1. Run oracle and both alternatives over 30 seeds per fixture.
2. Wave tolerance = max(3 × empirical sd of the oracle error, 1.5 × max abs deviation of the alternatives). Overall
   likewise.
3. Design targets: wave ±0.008, overall ±0.003.
4. Accept the fixture only if every 0-mutation misses by ≥ 1.5× tolerance on some graded check.
5. Accept the fixture only if all three valid estimators pass on ≥ 29/30 seeds.

## 20. Alternative valid implementations

- **Estimators.** Any clean-comparison estimator:
  - imputation;
  - CS with a comparable-week anchor;
  - stacked DiD;
  - de Chaisemartin–D'Haultfœuille-style switchers;
  - synthetic-control-flavoured weighting within exposure strata;
  - never-treated-only controls. Noisier; passes the visible fixture at calibrated tolerances. If it does not pass the
    hidden fixtures, a principled reason is needed before build: hidden_c has 40 holdbacks, hidden_a 18.
- **Confounder adjustment.** Continuous overlap covariate, exposure matching, or restricting controls to the same
  exposure band. Binary exposure passes wherever it is approximately unbiased (visible).
- **Anchors.** Any comparable pre-period anchor, or none (imputation).
- **Controls.** Using or not using not-yet-treated stores beyond their own install window. Contaminated install weeks
  are non-comparable anyway, so they drop out automatically once eligibility is right.
- **Percent vs log.** The contract requires log points; an `att_pct` field, if also written, is ignored.

## 21. Verifier design

1. Warehouse digest unchanged.
2. Run the command on visible + 3 hidden warehouses as an unprivileged user; twice on visible for determinism. Numbers
   are equal within 1e-9; bootstrap SEs, if any, must be seeded.
3. **`analysis_panel.csv`**:
   - exact key set (all store × fiscal-week rows in the warehouse);
   - `kpi_comparable` exact;
   - `adoption_week` exact (null for holdbacks);
   - `event_week` exact where adoption is not null;
   - `log_basket` within 1e-9 of log(net_merch_sales / customer_txns).
4. **`readout.json`**:
   - `att_by_wave[w]` within tolerance of **generator truth** (mean τ over comparable store-weeks e ∈ 0..25 of that
     wave);
   - `att_overall` within tolerance;
   - `recommendation` equals the truth sign rule. Every fixture has |truth overall| ≥ 5 × overall tolerance.
5. Wave keys are the wave labels from `program_rollout_plan.planned_wave`: cohort *membership* by label, timing by
   actual. The contract says "wave = the store's planned wave label". Truth uses the same membership.
6. Binary reward.

Truth is additive in log space, so the realised-sample ATT equals the mean of τ exactly. No sampling noise in the
estimand itself.

## 22. Answer-key leakage audit (with cheap-solve audit)

| Artifact | Leak? |
|---|---|
| Output contract | States the estimand (causal, comparable weeks, e 0–25). It does not name an estimator or mention competitors. "Would have had without SCO 2.0" implies confounders must be handled, which is the standard definition, not a hint. **Risk: M.** The field `kpi_comparable` points at the handbook. Accepted: the panel table is a normal readout artefact, and the ESL readout (2025) had the same columns filled by the faulty code. |
| KPI handbook | Defines comparable week as a KPI fact (it is used for like-for-like sales too). It does not say "drop install weeks from the base". |
| Program brief | Installer process facts (prewire, install, Sunday go-live, dates move). Needed; it does not say "use the install log". |
| Trade-area methodology | Explains overlap share. It does not say "adjust readouts for closures". |
| R4 notes | Anecdote naming ValuMart. It gives no stores and no dates beyond "since mid-October". |
| House notebook | Wrong method |
| ESL readout | Same wrong method; no "good" old readout exists |

**Cheap-solve audit:**
- **One grep?** `grep -ri valumart` finds the R4 notes and `competitor_sites`. That localises the confounder but gives
  neither exposure nor adjustment.
- **One doc?** No doc gives the estimator or the adjustment.
- **Package?** Network is off, so no `differences`, `csdid` or `pyfixest`.
  - If the harness enables network: `differences` (CS) with default varying base `g−1` hits the install-dip trap
    unless the agent fixes the panel. Even then, without a confounder adjustment, W3 fails.
  - `pyfixest.did2s` on the house panel dilutes the install dip (imputation uses all pre-weeks, residual ≈ 0.002)
    but still fails the panel table and W3.
  - So packages remove the implementation burden of the estimator only. That is acceptable because the estimator is
    not the claimed hardness.
- **Restoring behaviour?** No prior "good" readout exists.
- **Helper?** None: no fiscal-week join utility, no install-log reader.
- **Filter?** `drop R4` fails (§14.3).
- **Residual cheap path:** hygiene + imputation + a region × week FE gets overall within tolerance but W3 out. The
  task's discrimination therefore rests mainly on W3 and the hidden fixtures' confounders. **This is the design's
  single point of failure** (§27).

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Wave membership for slipped stores | Contract: wave = planned label; timing = actual go-live |
| Event week 0 definition | Program brief: go-live on Sunday = first day of fiscal week; e=0 is that week |
| Non-comparable weeks inside e 0–25 | Excluded from the estimand (contract: "comparable store-weeks") |
| What counts as a closure | Handbook: any closure record (any `hours_closed` > 0) in the fiscal week |
| Log vs ratio basket | Contract: log(net_merch_sales / customer_txns) |
| Holdbacks as controls after the panel ends | Irrelevant (panel ends before FY2027) |
| Competitor effect functional form | Not needed exactly: store-level exposure and closure date suffice for valid adjustments; the tolerance absorbs a 3-week ramp misspecification (calibrated) |
| Anticipation beyond install weeks | None in the generator. The program brief says the redesign is invisible to shoppers until go-live. |
| Spillovers between nearby stores | None in the generator; stated as an assumption in the brief ("stores are ≥ 8 miles apart") — **simplification** |
| `recommendation` threshold | Contract rule: ≥ 0 keep. Truth far from 0 in every fixture. |
| Region × week FE rejected | Principled (store-level exposure within region) but debatable; §27 |

## 24. Expected trajectory length

45–80 tool calls. The estimator itself is 10–15 calls. Panel reconstruction and audits take 20–30, confounder
discovery and placebo 10–20, and reruns plus the contract 5–10.

## 25. Why harder than Tasks 03/05/06

| Task 06 failure | Here |
|---|---|
| Cutoff in faulty code | Faulty panel encodes the *wrong* timing and eligibility; no fiscal or install-log code |
| Summary already implemented | Estimator must be replaced; house event study is the wrong one |
| Natural design correct | Natural textbook DiD on the house panel is wrong by +0.037 overall |
| Attractor optional | TWFE readout and event-study dip are the starting point; ValuMart anecdote is in the manager evidence the memo cites |
| Traps on unchosen paths | Traps are TWFE → CS(g−1) → hygiene-without-confounder, the exact sequence a strong agent follows |
| One-row check enough | Requires panel row audits + wave-level heterogeneity + placebo |

## 26. Comparison with Task 02

- **Grain.** Task 02 required per-example × cutoff state. G05 requires per-store × fiscal-week eligibility and timing,
  which is simpler as state.
- **Statistics.** The statistical layer (clean comparisons + confounder) is harder.
- **Aggregates.** Like Task 02, the overall number after a partial repair (hygiene, no confounder) is close to truth
  (0.028 vs 0.024), exactly the near-miss pattern that defeated Task 02 agents' aggregate validation.
- **Expected difficulty.** Comparable to Task 02 for agents that know modern DiD; harder for those that do not. The
  risk is the opposite side: agents that know DiD well *and* habitually run heterogeneity checks will find W3 quickly.

## 27. Benchmark risks

- **Textbook recognition: H.** Frontier models know TWFE's staggered-adoption problem. The design accepts this and
  moves the hardness to the base period, panel and confounder. If agents routinely run wave-by-region breakdowns, W3
  is found; headroom then rests on the exact panel table and hidden fixtures.
- **Sign flip calibration: M.** Static TWFE negativity with realistic effects needs a slow ramp and few never-treated
  stores. The fallback memo (§5) keeps the task intact.
- **Region × week FE rejection: M (underspecification).** A reviewer may call region × week FE a defensible
  specification. The design makes the store-level evidence strong:
  - the methodology doc;
  - visible R2 placebo scaling with overlap;
  - W3's R4 exposure much higher than R4 controls'.

  If review disagrees, the fix is to make exposure region-wide and drop this trap. That reduces discrimination to
  "any adjustment vs none".
- **Hidden-rule drift: L–M.** Openings (hidden_a) and weather clustering (hidden_c) must be visibly exercised. The
  `install_type_only_eligibility` mutation requires the visible warehouse to contain non-install closures that also
  distort baskets (refrigeration and weather rows are present). Build must verify that mutation fails visibly, or it
  moves to the overfit list.
- **Leakage: M.** The estimand wording and panel columns are unavoidable for grading.
- **Implementation cost: M.** The panel generator is simple. Calibration of three estimators × seeds is the main cost.
- **Realism: H.** Staggered store programs, install disruption and competitor closures are routine.
- **Overlap:** low with 01–06; mild with G21/G24 (causal), but a different estimand family.
