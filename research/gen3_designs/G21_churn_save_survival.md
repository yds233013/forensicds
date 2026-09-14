# G21 — Churn-save offer "works": targeting, self-selection, censoring, renewal-only churn, reactivation

Status: design only. Nothing built, no model run. Candidate definition: `research/gen3_candidate_pool.md` §G21.
All numbers are **generator targets**, calibrated and asserted at build time.

## Workspace sketch

```
/workspace                                           (~95 MB)
  README.md                         retention analytics repo; dashboards, readouts, KPI jobs
  warehouse/retention.duckdb        billing + product + program tables (see §7), extract as of 2026-10-01
  config/save_offer.yaml            CURRENT program config (threshold 0.50, holdout 12%, offer codes)
  docs/
    kpi/churn_definition.md         Finance-owned KPI: churn on paid core service, 30-day return rule, examples
    billing/subscription_lifecycle.md  statuses, monthly vs annual cancellation, promo plan transitions, invoices
    programs/save_offer_program.md  launch design (2025-04): eligibility at cancel intent, hash assignment, offer terms
    decisions/2025-11-24_save_offer_budget_review.md  Finance review → holdout and threshold change from 2025-12-01
    models/churn_risk_model_card.md scores at cancel intent; threshold history
    finance/offer_economics.md      break-even: offer cost ≈ 2.0 pp of 180-day retention per eligible account
  retention/
    readout/save_offer_readout.py   faulty readout (offer vs holdout 90-day churn rate, subscription grain)
    kpi/monthly_churn.sql           company churn KPI job (subscription-grain reactivation check; uses cancelled_at)
    dashboards/save_offer_kpi.sql   dashboard: takers vs non-takers, "churned in reporting quarter" (since 2026-04)
    dashboards/HISTORY.md           dashboard SQL changes (window changed 2026-04-02)
  reports/
    dashboard_export_2026-Q3.csv    takers churn 60% less than non-takers
    readouts/2026-06_save_offer_readout.md  faulty readout: "−0.4 pp, no detectable effect"
  notebooks/2026-07_holdout_integrity.ipynb  analyst: holdout share 9.3% vs configured 12% → "assignment leak?"
  notes/2026-09-18_retention_budget_thread.md  Retention lead wants 3× budget; Finance points at the readout
```

## 1. Research question

Can an agent estimate the causal effect of a retention program on survival at fixed horizons, by contract type, when
(a) the naive comparison is between self-selected takers, (b) the randomized holdout exists but its share and the
eligibility threshold changed mid-program, (c) outcomes are right-censored and churn is confirmed only 30 days after
service ends, (d) annual customers can only leave at renewal, (e) promotions and plan changes split one customer
relationship across several subscription records, and (f) the company's own KPI job implements churn at the wrong grain?

Capability: **causal survival estimation with a reconstructed outcome** — building the churn process at the grain the
KPI defines, choosing the randomized comparison and weighting it correctly across design versions, and handling
censoring that is partly administrative and partly definitional.

## 2. Enterprise setting

A small-business accounting SaaS sells monthly and annual core plans plus non-core add-ons (payroll, e-invoicing).
When a customer starts cancellation (monthly: cancel at period end; annual: turn off auto-renew), a churn-risk model
scores the account; if the score is above the program threshold the account is assigned by subscription hash to the
save offer (monthly: 50% off for three months; annual: two extra months free on renewal) or to a holdout. Retention
Marketing owns the offer; Finance owns the churn KPI; Retention Analytics owns readouts.

## 3. Visible symptom (instruction memo)

From the CFO:

> Retention wants to triple the save-offer budget: their dashboard says customers who take the offer churn 60% less.
> The analytics readout in June found no detectable effect, and someone thinks the holdout is leaking. I need the
> real effect of the program on retention at 90 and 180 days, separately for monthly and annual customers, and a
> recommendation per plan type using Finance's break-even. Also fix the churn spell table Finance uses — I want the
> readout built on it.

Required outputs:

1. `cd /workspace && python -m retention.readout.save_offer_readout --as-of 2026-10-01` writes:
   - `out/churn_spells.csv` — one row per spell of paid core service per account, per the Finance KPI definition, as
     known at the as-of date: `account_id, spell_seq, spell_start, spell_end` (empty if service has not ended),
     `churned` (1 if the spell ended in churn as known at as-of, else 0).
   - `out/save_offer_effect.csv` — rows for `plan_type ∈ {monthly, annual}` × `horizon_days ∈ {90, 180}`:
     `survival_offer, survival_holdout, difference, ci_low, ci_high`. Survival to day h = no churn on or before day h
     after the account's first eligible cancel intent in the program. The effect is that of the program as operated
     (being assigned to the offer vs the holdout), over all accounts with an eligible cancel intent since launch;
     plan type is the plan at that intent.
   - `out/recommendation.json` — `{"monthly": "continue" | "stop", "annual": "continue" | "stop"}` using
     `docs/finance/offer_economics.md` (continue only if the 180-day difference's 95% lower bound exceeds break-even).
2. Warehouse, docs and config are authoritative; do not modify. No hand-edited outputs; no special-casing accounts,
   dates or plan codes; the same command runs at future as-of dates.

The memo names neither censoring, reactivation, promotions, annual renewal nor the design change.

## 4. Source distribution inspiration

- Retention offers evaluated by takers vs non-takers (self-selection) are a common analytics error; ITT vs
  per-protocol/CACE distinctions (Angrist, Imbens & Rubin 1996 — to verify).
- Kaplan–Meier and right censoring; dependent censoring when censoring time correlates with risk (standard survival
  texts, e.g. Kalbfleisch & Prentice — to verify).
- Subscription churn definitions with grace/return windows and contract-renewal-only exits (practitioner KPI
  practice; no citation).
- Designs whose assignment probabilities change over time need stratified or inverse-probability-weighted analysis
  (Simpson's paradox in pooled arms — standard).

## 5. Causal graph / ground truth

```
account covariates (tenure, seats, usage trend, plan) ──► cancel intent (date, plan) ──► risk score
                                                               │
config version v(date) ── threshold_v, holdout_rate_v ─────────┴─► eligible? ─► arm (hash) ─► offer shown ─► accept? (self-selection on "price-sensitivity" latent)
                                                                                                   │
latent type {price-sensitive, dissatisfied, business-closed} ─► service end hazard ◄───────────────┘ (discount delays; renewal gate for annual)
                                                                   │
                                            service end ─► return within 30 days? (win-back, price-sensitive types) ─► KPI churn
billing: promo plans and plan changes create new subscription_id rows (same account, contiguous service)
```

**Program design versions** (`save_config_versions` table; also narrated in decision doc):

| Version | Effective | Score threshold | Holdout rate |
|---|---|---|---|
| v1 | 2025-04-01 | 0.60 | 5% |
| v2 | 2025-12-01 | 0.50 | 12% |

Hazards and population mix are stationary in calendar time **within** a version (§23).

**Population (first eligible intents per account).** Monthly: v1 50k (holdout 2,500), v2 80k (9,600). Annual: v1 14k
(700), v2 22k (2,640). Overall holdout share 9.3% (the notebook's "leak").

**Latent types and mechanics (monthly).** Price-sensitive (v1 35%, v2 45%): offer acceptance 70%; discount delays
service end until after the discount (≈ day 95–125) for 55% of takers and retains 25% beyond 180 days; if they leave,
30-day return probability 30% in holdout (win-back emails), 10% in offer arm. Dissatisfied: acceptance 12%, little
effect. Business-closed: acceptance 3%, no effect, no returns. Takers are overwhelmingly price-sensitive, so taker vs
non-taker contrasts compare types.

**Annual.** Service ends only at term end (intent date + time-to-renewal, uniform 1–330 days, stationary). Offer =
renewal with two free months (implemented as a new 14-month subscription, zero-due first invoice). Acceptance 22%;
small effect because most dissatisfied annual customers leave anyway at renewal; returns 9–10% in both arms.

**Billing mechanics.**
- Monthly cancel: `cancelled_at` = click date; `service_end` = current period end (up to 31 days later).
- Annual auto-renew off: `status = 'cancelled'` and `cancelled_at` set **at click**; `service_end` = term end;
  `auto_renew_on` event can reverse before term end (8% of annual intents; 15% of annual offer takers).
- Offer acceptance (monthly): current subscription ends at period end; `*_save50` subscription starts the same day
  (3 periods), then a standard monthly subscription starts. Each has its own `subscription_id`.
- Add-on subscriptions (`plans.is_core = false`) can outlive the core plan (11% of churners keep payroll ≥ 60 days).
- Invoices with `amount_due = 0` and `reason = 'promo_credit'` are paid service.

**True estimands** (generator: per unit, 400 Monte Carlo trajectories under each arm from the unit's covariates and
intent date, KPI survival computed on each; averaged over units; MC SE < 0.0001):

| Plan | h | S_offer | S_holdout | Difference | Recommendation |
|---|---:|---:|---:|---:|---|
| monthly | 90 | 0.654 | 0.560 | +0.094 | |
| monthly | 180 | 0.477 | 0.421 | +0.056 | continue (break-even 0.020) |
| annual | 90 | 0.905 | 0.902 | +0.003 | |
| annual | 180 | 0.787 | 0.781 | +0.006 | stop |

**Attractor numbers (visible).** Dashboard: takers' quarter churn 14% vs non-takers 35% ("60% less"). June readout
(offer vs holdout, 90-day churn proportion, subscription grain, `cancelled_at`, plans pooled): −0.4 pp. Notebook:
holdout 9.3% vs "configured 12%", χ² p < 1e-50.

## 6. Latent statistical/business invariant

1. **Spells.** Paid core service intervals per account from invoices on core plans (including zero-due promo
   credits), unioned across subscription records; gaps where the next core service starts ≤ 30 days after the previous
   service end are merged (KPI example: ends 03-31, returns 04-30 → not churn). `spell_end` = last paid service day;
   empty if service continues past as-of (including annual cancel-pending). `churned = 1` iff spell_end + 30 days ≤
   as-of and no core service starts within 30 days; spells that ended within the last 30 days are `churned = 0`.
2. **Unit and clock.** First eligible intent per account in the program; t0 = intent date; event time = spell_end of the
   spell containing t0, if churned; otherwise censored at as-of (service continuing) or at spell_end (unresolved).
3. **Comparison.** Arm as assigned at that intent (ITT). Not takers; not per-protocol; not CACE.
4. **Design weighting.** Arms are compared within design version; version-level survival curves are combined with
   weights proportional to eligible units per version (or equivalently inverse assignment probabilities). Pooled
   Kaplan–Meier across versions is biased twice: arm composition differs by version (5% vs 12%), and later versions
   are more censored while having different risk (dependent censoring in the pooled sample).
5. **Horizon and plan.** Separate estimates by plan type at intent, at 90 and 180 days.
6. **Decision.** Continue iff the 180-day difference's lower 95% bound > 0.020.

## 7. Grains and state variables

| Grain | Key | Mistake |
|---|---|---|
| Subscription record | `subscription_id` | promo/plan transitions counted as ends |
| Core service interval | invoice periods on core plans | add-ons keep accounts alive |
| Spell (KPI) | account × merged intervals (≤ 30-day gaps) | reactivations counted as churn |
| Spell resolution state | ended ≥ 30 days before as-of / unresolved / ongoing | unresolved counted as churn |
| Cancel intent | `intent_id` (repeated per account) | later intents as units; latest arm |
| Assignment | (intent, arm, config_version) | holdout share checked against current config |
| Design version | `config_version` | pooled arms |
| Plan type at intent | subscription plan at t0 | current plan (takers moved to promo plans) |

Tables: `accounts(account_id, created_at, segment, country)`; `plans(plan_code, plan_type, is_core, promo_of, term_months)`;
`subscriptions(subscription_id, account_id, plan_code, started_at, status, cancelled_at, service_end)`;
`subscription_events(event_id, subscription_id, event_type, event_at)`; `invoices(invoice_id, subscription_id,
period_start, period_end, amount_due, reason, paid_at)`; `cancel_intents(intent_id, account_id, subscription_id,
intent_at, risk_score)`; `save_assignments(intent_id, account_id, assigned_at, arm, config_version)`;
`save_config_versions(config_version, effective_from, score_threshold, holdout_rate)`; `save_offers(intent_id,
offer_code, shown_at, accepted, accepted_at)`. Sizes: 210k accounts, 390k subscriptions, 2.4M invoices, 260k intents,
166k assignments.

## 8. Evidence graph

(★ natural path)

| Artifact | Shows |
|---|---|
| ★ memo, dashboard export, `save_offer_kpi.sql` | taker vs non-taker, quarter window; HISTORY.md shows window change |
| ★ June readout + `save_offer_readout.py` | offer vs holdout 90-day churn proportion, `subscriptions.cancelled_at`, subscription grain, plans pooled → −0.4 pp |
| ★ notebook | holdout share 9.3% vs config 12%; "leak" |
| ★ `config/save_offer.yaml` | current values only |
| `save_config_versions`, decision doc | v1/v2 thresholds and holdout rates, effective 2025-12-01 |
| ★ `docs/kpi/churn_definition.md` | churn on paid core service; 30-day return rule with worked examples; "churn date = last day of paid service" |
| ★ `retention/kpi/monthly_churn.sql` | Finance job: `LEAD(started_at) OVER (PARTITION BY subscription_id)` for the return check (never sees a new subscription id), churn date `cancelled_at`, all plans incl. add-ons |
| `subscription_lifecycle.md` | annual cancel sets status at click; service to term end; auto_renew_on reversals; promo transitions create new subscriptions; zero-due promo invoices |
| `save_offer_program.md` | eligibility at intent, hash assignment per subscription, offer terms |
| `offer_economics.md` | break-even 2.0 pp at 180 days |
| data: accounts with several intents | re-assignments after promo transitions (new subscription id → new hash) put 6% of takers' later intents in holdout |
| data: survival by version | v2 population lower risk; v2 follow-up shorter |

## 9. Evidence authority hierarchy

1. **Finance KPI definition** — what churn is (grain, return window, churn date). Governs over every implementation,
   including Finance's own SQL job.
2. **Billing lifecycle doc + raw billing tables (invoices, subscriptions, events)** — when paid service existed.
   Invoices govern over `status`/`cancelled_at` for service timing.
3. **Program design records** — `save_config_versions` and assignment rows govern over the current YAML (which only
   holds today's values) and over the launch doc's "5%".
4. **Offer economics doc** — decision threshold.
5. **Code and outputs under review** — KPI SQL, readout, dashboard, notebook, thread.

Conflicts:
- `monthly_churn.sql` vs KPI doc: the job's return check is partitioned by subscription and uses `cancelled_at`; the
  doc's examples (a customer returning on a different plan) contradict it. Doc governs.
- Notebook "leak" vs version table: the observed 9.3% equals the eligible-weighted mix of 5% and 12%; no leak.
- `status = 'cancelled'` for annual customers still in service vs invoices: invoices govern (service continues).
- Dashboard "60% less" vs randomized assignment: takers are self-selected; the dashboard is descriptive.

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 ★ | Offer is highly effective (−60% churn) | dashboard; takers retained 3 months | taker contrast is selection; ITT effect is much smaller and fades by 180 days |
| H2 ★ | Offer has no effect | June readout −0.4 pp; notebook | readout counts promo transitions as churn in the offer arm, uses `cancelled_at`, pools plans |
| H3 ★ | Holdout is contaminated / assignment broken | share 9.3% vs 12% | version table explains the share; within-version shares are 5.0% and 12.0% (p ≈ 0.5) |
| H4 | Effect exists for monthly, not annual, and decays with horizon | holdout comparison by plan after correct spells | — (true) |
| H5 | The effect is concentrated among takers, so report per-taker effect (CACE) | acceptance 34% monthly | instruction's estimand is the program as operated; CACE also inflates 3× |

## 11. Why each wrong hypothesis is plausible

- **H1:** three-month retention of takers is real and visible in invoices; the dashboard is the organisation's number.
- **H2:** a competent-looking readout used the holdout — exactly what a careful analyst "should" do — and the notebook
  seems to explain why it might fail. An agent who re-uses `monthly_churn.sql` for outcomes reproduces "no effect".
- **H3:** a real χ² test against the only config file visible at the top of the repo; SRM reasoning is standard.
- **H5:** "per taker" matches how Retention talks about the offer.

## 12. Investigation path (≈50–80 actions)

1. (1–6) Memo, dashboard export and SQL, HISTORY, June readout, notebook, thread.
2. (7–12) Read `save_offer_readout.py` and `monthly_churn.sql`; reproduce −0.4 pp.
3. (13–18) Profile assignments: share by month → step change at 2025-12-01; find `save_config_versions` and the
   decision doc. H3 refuted; design versions recognised.
4. (19–28) KPI doc, lifecycle doc. Inspect account timelines: promo transitions, add-ons, annual cancel-pending,
   returns within 30 days on other plans. Discovery: subscription grain and `cancelled_at` are wrong.
5. (29–40) Build spells from invoices on core plans; merge ≤ 30-day gaps; resolution state at as-of. Validate against
   KPI doc examples and ~20 hand-traced accounts (promo takers, annual reversals, add-on-only survivors, boundary 30/31-day returns).
6. (41–48) Define units (first eligible intent), plan at intent, t0, event/censoring times. Check multiple intents and
   re-assignment after promo transitions.
7. (49–60) Estimate: KM per arm × plan × version, combine with eligible weights; CIs (Greenwood + delta, or seeded
   bootstrap by account). Compare with pooled KM and with naive rates to understand differences.
8. (61–70) Recommendation; sensitivity (censor at as-of − 30 for all; complete-case per version).
9. (71–80) Outputs; rerun determinism; update readout narrative.

## 13. Natural wrong implementation

**NW1 — "use the holdout properly, with survival analysis" on the existing KPI job's churn:**

```python
churn = duckdb.sql(open("retention/kpi/monthly_churn.sql").read()).df()   # subscription grain, cancelled_at
units = assignments.merge(intents).sort_values("assigned_at").drop_duplicates("account_id")
units = units.merge(churn, on="subscription_id", how="left")
units["T"] = (units.churn_date.fillna(AS_OF) - units.assigned_at).dt.days
units["E"] = units.churn_date.notna()
for plan, g in units.groupby("plan_type"):
    km_offer, km_hold = KM(g[g.arm=="offer"]), KM(g[g.arm=="holdout"])        # pooled across versions
```

Numeric consequences (visible, monthly 180 d):
- Promo transition ends the joined `subscription_id` → takers "churn" at period end: S_offer 0.30, difference −0.12.
- `cancelled_at` makes every annual intent an immediate churn: annual S ≈ 0.08 in both arms.
- If the agent notices the promo problem and joins churn by account instead but keeps the job's return check and
  `cancelled_at`: difference +0.14 (returns counted as churn, holdout returns 3× more often).
- Pooled KM across versions with correct spells: S_holdout 0.451, S_offer 0.472, difference +0.021 (−0.035 error);
  recommendation "stop" for monthly (lower bound < 0.020). This is the most likely *final* failure: every component
  looks principled.

## 14. Second-order failure modes

1. **Stratify by version, weight by holdout counts** (or by arm-specific counts): reproduces the pooled bias partly
   (+0.034).
2. **Unresolved spells as churned:** S levels −0.004 to −0.010 (inside tolerance); `churn_spells.csv` wrong on ≈ 5,900 rows.
3. **Censor everyone at as-of, unresolved treated as survivors past spell end:** S levels +0.006; table fine if flag right
   but estimate slightly off; passes values only by luck on visible, fails hidden_c (12% unresolved).
4. **Proportions without censoring** ("churned by day h among all units"): monthly 180 d S_offer 0.63 vs truth 0.48.
5. **Complete-case pooled** (units with ≥ h + 30 days follow-up, pooled): all v1 plus early v2 → v1-heavy → S levels
   −0.04.
6. **Plan at as-of** instead of at intent: takers moved to `*_save50` or annual; misclassifies 4% of monthly units into
   annual.
7. **Units = all eligible intents** (not first): 22% more units, takers' later intents re-hashed, offer arm dilution
   (difference +0.048, CI too narrow).
8. **Add-ons as service:** S +0.05 both arms.
9. **CACE** (ITT / acceptance): monthly +0.16.
10. **Gap rule `< 30`** instead of ≤ 30 days: table wrong on boundary returns (visible 212 spells).
11. **Cox model with arm × plan** pooled across versions and time-constant hazard ratio: the discount creates
    strongly non-proportional hazards; S(180) differences from the fitted model off by ≈ 0.03.

## 15. Correct repair properties

- Spell builder from invoice periods on core plans, account grain, ≤ 30-day merge, resolution at as-of.
- Units = first eligible intent per account; plan type from the subscription at intent.
- ITT arms; version-aware estimation (stratified KM with eligible weights, or IPW-KM with version holdout rates, or
  complete-case per version with eligible weights under stationarity).
- Censoring at as-of for ongoing spells and at spell_end for unresolved ones (or conservatively at as-of − 30 days for
  all — also valid).
- CIs account for version stratification; recommendation per the economics doc.

## 16. Repair surfaces

| Surface | Why |
|---|---|
| `retention/kpi/monthly_churn.sql` or a new spell builder | KPI job's grain, return check and churn date contradict the definition; the spell table must be correct for Finance |
| `retention/readout/save_offer_readout.py` | unit, clock, censoring, arms, design weighting, horizons, plan split, CIs, recommendation |
| Dashboard SQL | not graded (descriptive); agents may annotate |

## 17. Validation requirements

- **Account-level trace:** for promo takers, annual reversals, add-on survivors, 29/30/31-day returns, unresolved ends —
  compare spells with invoices by hand. Aggregate churn rates cannot distinguish subscription-grain from account-grain
  errors that partly cancel.
- **KPI doc examples** reproduced exactly.
- **Assignment balance within version** (shares 5.0% / 12.0%; covariate balance on risk score).
- **Version heterogeneity:** per-version survival curves by arm; follow-up distribution by version (shows the dependent
  censoring hazard of pooling).
- **Estimator cross-checks:** stratified KM vs IPW-KM vs per-version complete case at 90 days (should agree within ~1 SE).
- **Sanity vs attractors:** reproduce dashboard and June readout numbers with their definitions to explain the gap.

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface change | Overfit / shortcut caught | Why same distribution |
|---|---|---|---|---|
| `hidden_a` "annual_works" (as-of 2026-03-01; program 2024-09..) | plan split, renewal-only churn, decision can differ by plan | single design version (holdout 10%); annual n doubled, annual returns 25% in holdout (win-back on renewal); truth annual 180 d +0.070 → continue; monthly +0.004 → stop | hard-coded version date 2025-12-01; hard-coded recommendation; `cancelled_at` for annual | same billing lifecycle, KPI, offer terms |
| `hidden_b` "three_versions" (as-of 2026-12-01) | design weighting, boundary returns, promo grain | versions 10% / 4% / 15% with thresholds 0.60 / 0.50 / 0.70; promo codes `*_winback_q` (in `plans.promo_of`); 480 returns on exactly day 30, 350 on day 31; truth monthly +0.060 continue, annual +0.002 stop; pooled KM gives +0.105 | two-version hard-coding; plan-code lists; `< 30` gap; weights by holdout counts | version table, `promo_of`, boundary examples all exist in visible |
| `hidden_c` "delay_only" (as-of 2027-02-15) | horizon matters; resolution state | January price-increase churn wave → 12% of spells end within 30 days of as-of; offer only delays churn: monthly 90 d +0.050, 180 d −0.004 → stop; taker contrast still +0.28 | unresolved-as-churned (values and table); 90-day-based recommendation; complete-case with as-of − 30 hard-coded as 2026-09-01 | churn waves and unresolved spells exist in visible at lower rates |

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` (spells from invoices; stratified KM, eligible weights; Greenwood/delta CIs) | 1 |
| `alt_ipw_km` (weights 1/P(arm \| version), bootstrap by account, seeded) | 1 |
| `alt_complete_case_by_version` (units with ≥ h + 30 days follow-up per version, eligible weights; binomial CIs) | 1 |
| `alt_discrete_hazard` (pooled logistic on day bins with arm × version × plan × bin interactions, g-formula survival) | 1 |
| `alt_censor_asof_minus30` | 1 |
| `dashboard_takers` | 0 |
| `june_readout` | 0 |
| `kpi_sql_reuse` (subscription grain, `cancelled_at`) | 0 |
| `returns_as_churn` | 0 |
| `pooled_km` | 0 (monthly values, recommendation) |
| `holdout_count_weights` | 0 |
| `unresolved_as_churned` | 0 (table; hidden_c values) |
| `no_censoring_proportions` | 0 |
| `complete_case_pooled` | 0 |
| `plan_at_asof` | 0 (table ok; values hidden_b) |
| `all_intents_as_units` | 0 (values/CI width) |
| `addons_as_service` | 0 |
| `cace` | 0 |
| `gap_lt_30` | 0 (table) |
| `cox_ph` | 0 (values) |
| overfit `hardcode_version_boundary` | 0 (hidden_a, hidden_b) |
| overfit `hardcode_promo_codes` | 0 (hidden_b) |
| overfit `hardcode_recommendation` | 0 (hidden_a, hidden_c) |
| cheat: read `/tests` | 0 |

## 20. Alternative valid implementations

Any estimator consistent for ITT survival at h under within-version stationarity and independent administrative
censoring: stratified KM, IPW-KM, per-version complete case, discrete-time hazard with sufficient interactions.
There are no competing risks in the KPI, so no cumulative-incidence machinery is needed. Censoring either at as-of/spell_end or at
as-of − 30 for all. CIs: Greenwood, bootstrap by account (seeded), or delta method. The spell table is graded exactly;
effect rows by tolerance; recommendation exactly.

## 21. Verifier design

- **A.** Warehouse/docs unchanged; command succeeds; schemas.
- **B.** `churn_spells.csv` exact vs generator: row set on (account_id, spell_seq), dates, `churned`.
- **C.** For each of 4 rows: |S_offer − truth| ≤ τ_off; |S_holdout − truth| ≤ τ_hold; |difference − truth| ≤ τ_diff.
- **D.** CI: `ci_low ≤ difference ≤ ci_high`; width in [0.4, 3] × reference width; truth within ±2 × half-width.
- **E.** Recommendation exact. **F.** Determinism. **G.** B–E on hidden fixtures.

### Variance analysis and tolerances

Truth is exact (Monte Carlo over potential outcomes, SE < 1e-4). Estimation error comes from outcome sampling in
each arm, the version weighting, and censoring (less information in v2 at long horizons).

Visible monthly, h = 180:
- v1 holdout: n = 2,500, all followed to 210 days: SE(S) = √(0.35·0.65/2500) ≈ 0.0095.
- v2 holdout: n = 9,600, only intents before 2026-03-05 (≈ 32%) reach day 180 + 30; Greenwood at 180 with early
  times informed by all units: SE ≈ 0.0085.
- Weighted holdout: w_v1 = 50/130 = 0.385, w_v2 = 0.615 → SE ≈ √((0.385·0.0095)² + (0.615·0.0085)²) ≈ 0.0064.
- Offer arm (≈ 118k units): SE ≈ 0.0022. SE(diff) ≈ 0.0068.

Visible annual, h = 180: SE(S_holdout) ≈ 0.0106, SE(diff) ≈ 0.011. At h = 90 all SEs ≈ 0.7× the 180-day values.

The generator computes SE_ref per fixture/row by the delta method from true survival curves, the version weights and
the realised censoring distribution (deterministic, no simulation). Tolerances: τ = 3.5 × SE_ref, floor 0.010.
Visible: monthly 180 d τ_diff ≈ 0.024, τ_hold ≈ 0.022, τ_off ≈ 0.010; annual 180 d τ_diff ≈ 0.039.

Why 3.5σ: accepted estimators differ in efficiency (complete-case per version discards ≈ 50% of v2 information →
SE up to 1.4× Greenwood). Seed screening: the build accepts a seed only if all five accepted mutations are within
2.5 × their own SE of truth on every row and agree on the recommendation; 3.5 × SE_ref covers 2.5 × 1.4 × SE_ref.

Decision margins: monthly continues unless D̂ − 1.96·SE < 0.020, i.e. D̂ < 0.0333 → 3.3σ below truth 0.056
(least efficient estimator: 2.4σ; screened). Annual stops unless D̂ > 0.020 + 1.96 × 0.011 = 0.042 → 3.3σ above
truth 0.006. Hidden fixture rule: every plan's 180-day truth is ≥ 3σ from the decision boundary for the oracle and
≥ 2.3σ for the least efficient accepted estimator.

Wrong-method separation (visible, monthly 180 d difference): pooled KM −0.035 (1.5τ, plus recommendation flips);
holdout-count weights −0.022 (0.9τ; its lower bound 0.021 still gives "continue", so on visible it passes — this
mutation is caught only by hidden_b, where the 10% / 4% / 15% mix makes the error 0.045); returns as churn
+0.084; KPI SQL −0.18; takers +0.25; CACE +0.10; no-censoring levels −0.15.

## 22. Answer-key leakage audit (including cheap-solve audit)

| Artifact | Leak? | Why not an answer key |
|---|---|---|
| KPI definition | defines spells | necessary for gradability. It states *what* churn is (paid core service, 30-day return, examples) — but not invoices vs statuses, promo subscription splits, add-ons, or resolution at as-of; those come from lifecycle doc and data |
| `subscription_lifecycle.md` | promo transitions, annual status | billing facts; says nothing about churn or KPIs |
| `save_config_versions` + decision doc | holdout/threshold change | facts; neither mentions analysis |
| offer economics | threshold | decision rule only |
| `monthly_churn.sql` | wrong implementation | attractor |
| notebook | wrong conclusion | attractor |
| instruction's estimand sentence | ITT, first eligible intent, plan at intent, horizon definition | required to make grading against truth well-defined; does not mention censoring, versions or spells construction |

**Cheap-solve audit.**
- *One grep:* `grep -ri "30 days"` → KPI doc (definition) and `monthly_churn.sql` (wrong grain). `grep holdout_rate` →
  version table. None yields weighting or censoring.
- *One doc:* the KPI doc gives the spell rule's semantics; transcribing it into SQL over `subscriptions` (natural
  table) fails promo transitions and annual cancel-pending, which only invoices resolve.
- *One SQL:* the existing KPI job — wrong grain, wrong churn date.
- *Filter:* `WHERE arm = 'holdout'` vs `'offer'` proportions → −0.4 pp readout.
- *Helper:* no survival code in the repo (statsmodels is installed; `SurvfuncRight` gives KM, which is fine — it does
  not know about versions, spells or censoring semantics).
- *Old report:* June readout (wrong). No earlier correct readout exists; the launch doc's "5% holdout" is true only for v1.
- *Restoring behaviour:* restoring the dashboard's pre-2026-04 90-day window still compares takers.
- *Guessing:* "continue monthly, stop annual" is guessable from the candidate narrative on visible, but hidden_a
  (annual continue, monthly stop) and hidden_c (both stop) break a constant; values must also be within tolerance.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| ITT vs CACE vs per-protocol | instruction: effect of being assigned |
| Unit: first vs every intent | instruction: first eligible intent per account; later offers (incl. holdout accounts re-hashed after plan changes) are part of the program as operated and are in the generator truth |
| Population across design versions | instruction: all accounts with an eligible intent since launch → eligible-count weights; truth computed on that population |
| Identification of v2 180-day survival | only 32% of v2 units reach 180 + 30 days. Stationarity within version is a generator property; documented as a fact in the decision doc ("the v2 eligible population has been stable month to month; see appendix counts") — reasonable but an assumption agents must accept. Risk noted in §27 |
| "within 30 days" inclusive? | KPI doc example: ends 03-31, returns 04-30 → not churn (day 30 inclusive); second example day 31 → churn |
| Churn date | KPI doc: last day of paid service; survival "on or before day h" defined in instruction |
| Is a zero-due promo month paid service? | lifecycle doc: promo credits are paid service for KPI purposes ("service delivered under an active paid plan") |
| Unresolved spells in `churned` | instruction: "as known at as-of" → 0; KPI doc: churn is confirmed after 30 days |
| Add-ons | KPI: core service only; `plans.is_core` |
| Annual auto-renew reversal | invoices show renewal; spell continues |
| Plan type for accounts that switch plan during follow-up | instruction: plan at intent |
| Censoring convention (as-of vs as-of − 30) | both valid; tolerance covers (difference ≤ 0.004 visible, ≤ 0.009 hidden_c; screened) |
| Ties at day h | instruction's "on or before" |
| Accounts with intents before program launch | eligible intents only after launch by definition of assignments table |

## 24. Expected trajectory length

50–80 actions, 90–150 expert minutes. Three attractors with real statistics (dashboard, June readout, SRM notebook)
must be explained, not just dismissed; the spell builder needs account-level tracing across four billing mechanics;
the estimator needs a version-aware design and a censoring argument; and the recommendation depends on CIs.

## 25. Why harder than Tasks 03/05/06

- Task 03/05 documented the estimand property; here the instruction defines only the estimand *target* (ITT, first
  intent), while the operational rules (spells from invoices, version weighting, resolution censoring) are distributed
  across KPI doc, billing doc, version table and data.
- No scaffolding: the only churn implementation (`monthly_churn.sql`) is wrong at the grain; the readout has no survival
  logic; the current config hides the version change.
- The natural design after recognising "use the holdout with survival analysis" is pooled KM on reused KPI output —
  wrong twice for principled reasons (grain, dependent censoring/Simpson).
- Attractors sit on the path: the memo cites all three.
- Validation requires account-level traces; the headline difference moves plausibly (−0.4, +2.1, +5.6, +14 pp) under
  different wrong repairs.

## 26. Comparison with Task 02

Task 02's hard kernel was per-example × cutoff state. G21's analogue is the spell × as-of resolution state and the unit
× version design state; both fail silently in aggregates. G21 adds causal and survival estimation graded against truth,
and the most likely failure (pooled KM with correct spells) is a single, principled step from correct — the same shape
of near miss that failed all Task 02 trials. Expected difficulty: comparable to or harder than Task 02.

## 27. Benchmark risks

- **Identification assumption:** within-version stationarity is needed for v2 at 180 days. A cautious agent might
  refuse to extrapolate and report only units with full follow-up per version — accepted (`alt_complete_case_by_version`).
  An agent that refuses to report v2 at all (restricting population to v1) changes the estimand → fails; the
  instruction's population sentence makes that a clear miss, but it is the most defensible failure in the design.
- **Holdout-count weighting** is close to tolerance on visible; relies on hidden_b to separate. Acceptable but noted.
- **Implementation cost: medium-high.** Billing simulator with promo subscription splits, annual renewals, add-ons,
  returns, invoices; potential-outcome Monte Carlo for truth; analytic SE; five accepted estimators for screening.
- **Realism:** latent types are stylised; offer delaying churn is realistic. The hash re-assignment after plan changes
  is realistic but adds noise; kept small (6% of takers' later intents).
- **Leakage:** the KPI doc must be written carefully (definition + two examples, no mention of subscriptions or invoices).
- **Overlap:** Task 03/05 (holdout, ITT, SRM-like attractor) and Task 04 (reactivation semantics). Distinct in
  censoring, design versions, and estimation against truth.
- **Headroom:** a strong survival-analysis agent may stratify by version immediately; spells from invoices and
  resolution at as-of remain row-level hurdles graded exactly.
