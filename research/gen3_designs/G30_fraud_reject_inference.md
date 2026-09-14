# G30: Challenger fraud model won the backtest, losses rose (selective labels, disputes, approve-through)

Status: design only. Nothing is built and no model has been run. Numbers are generator design targets, to be re-measured
and margin-checked at build.

## Workspace sketch

```
/workspace
  README.md                                     fraudbt repo: backtest + outcome labelling; output formats
  config/fraudbt.yaml                           warehouse path, cost-file path, default window (no rates, no code lists)
  data/payments.duckdb               ~260 MB    transactions Jan–Jul 2026 (~2.8M), decisions, scores, settlements, disputes
  data/raw/processor_webhooks/2026-*.jsonl.gz   ~40 MB  dispute lifecycle webhooks as received (source of `disputes`)
  src/fraudbt/cli.py                            `python -m fraudbt run --window 2026-01-01:2026-04-30 --out out/`
  src/fraudbt/load_disputes.py                  FAULTY: builds `disputes` table; ignores prearbitration.* events
  src/fraudbt/labels.py                         FAULTY: fraud = any Visa 10.x chargeback seen by labels_as_of
  src/fraudbt/population.py                     FAULTY: final_decision = 'approve' (all approval reasons, unweighted)
  src/fraudbt/costs.py                          FIN-212 cost function per decision/outcome (correct, generic)
  src/fraudbt/backtest.py                       applies each model's threshold to the population and sums costs
  src/fraudbt/report.py
  artifacts/backtest_2026-03-10/                fz-5 vs fz-4 backtest report + label snapshot used for go decision
  docs/model_cards/fz-4.md, fz-5.md             features, training data (approved + matured), thresholds, target
  docs/decisioning/decision_flow.md             rule engine → score → decline / approve-through / analyst override
  docs/finance/FIN-212_fraud_decision_costs.md  cost of each decision/outcome; decision criterion
  docs/payments/dispute_lifecycle.md            network timelines, reason-code families, representment and pre-arbitration
  docs/data/warehouse_dictionary.md             tables, grains, date semantics (auth vs processing), webhook loader
  reports/fraud_ops/loss_development_2026-10.csv    fraud chargebacks by auth month × age (days)
  reports/fraud_ops/weekly_kpis_2026-W42.md     chargeback rate, decline rate, approval rate
  notes/2026-03-12_fz5_go_decision.md           go decision citing backtest (−16% cost)
  notes/2026-10-14_attack_wave_postmortem_DRAFT.md  fraud ops: "June BIN attack wave explains losses"
  inbox/2025-11-03_processor_webhook_changes.eml    processor adds prearbitration.* webhook types
  logs/model_deployments.csv                    fz-5 live 2026-05-01; fz-4 shadow thereafter; fz-5 shadow Jan–Apr
```

Warehouse tables:

| Table | Grain | Rows | Key columns |
|---|---|---:|---|
| `transactions` | authorisation attempt | ~2.8M | txn_id, auth_ts, amount_usd, merchant_category, is_preorder, three_ds_result, card_network, account_age_days |
| `rule_decisions` | txn | ~2.8M | txn_id, rule_outcome (`pass`/`rule_decline`), rule_id |
| `model_scores` | txn × model | ~5.5M | txn_id, model (`fz-4`/`fz-5`), score, mode (`live`/`shadow`) |
| `decisions` | txn | ~2.8M | txn_id, live_model, initial_decision, final_decision, decision_reason (`score_approve`, `score_decline`, `approve_through`, `analyst_override`, `rule_decline`) |
| `decision_policy_log` | config change | 9 | effective_from, live_model, threshold, approve_through rates by score band × amount band |
| `settlements` | captured txn | ~2.6M | txn_id, processing_date (capture/settlement; pre-orders settle at shipment) |
| `disputes` (loaded by faulty loader) | dispute | ~9k | dispute_id, txn_id, network, reason_code, opened_at, status |
| raw webhooks | lifecycle event | ~31k | event_type, dispute_id, txn_id, reason_code, network, event_ts, payload |

## 1. Research question

Can an agent estimate the counterfactual cost of two decision policies from logs in which:

- outcomes exist only for approved transactions;
- approvals of declines are partly random with a stratified, time-varying design, and partly selected by analysts;
- outcomes mature on a network clock anchored to a date that is not the authorisation date;
- outcomes are *revised* by a multi-stage dispute process?

It must then reach the correct champion/challenger decision.

The graded quantities are an exact outcome-label table (deterministic) and policy-cost estimates checked against
generator truth.

## 2. Enterprise setting

Tessel Market (fictional) is an online marketplace acting as merchant of record for card-not-present payments. Each
authorisation goes through three stages:

1. **Rule engine.** Sanctions, velocity and blocked BINs.
2. **Fraud model score.** Decline at or above the live model's threshold.
3. **Post-decline paths.**
   - A stratified random **approve-through** programme approves a small share of score-declines to keep labels flowing
     for retraining and monitoring.
   - Fraud analysts can override declines for whitelisted or verified customers.

Cardholders dispute fraud through card-network chargebacks. Tessel's disputes team contests some of them
(representment), and issuers can escalate to pre-arbitration.

Fraud Data Science owns `fraudbt`. The champion `fz-4` was replaced by the challenger `fz-5` on 2026-05-01, after a
backtest.

## 3. Visible symptom

The memo comes from the VP Payments Risk:

- `fz-5` won the March backtest with 16% lower decision cost and went live 1 May.
- Fraud Ops now reports fraud chargeback losses at 60 days of age up about 35% for May–July cohorts.
- Ops attributes this to a June attack wave.
- Finance wants to know whether to revert.

The memo asks for:

1. A repaired `fraudbt` whose command `python -m fraudbt run --window 2026-01-01:2026-04-30 --out out/` writes:
   - `out/labels/transaction_outcomes.parquet` (or `.csv.gz`), one row per approved eligible transaction in the window;
   - `out/eval/policy_cost.json`, with each model's decline rate and expected decision cost per 1,000 eligible
     transactions under FIN-212, the difference, and `decision ∈ {keep_fz5, revert_to_fz4}`.
2. The same command must work for any window and extract.
3. Data, raw webhooks, docs and artifacts must not be modified.

The memo does not mention selection, approve-through, pre-arbitration, reason codes or processing dates.

## 4. Source distribution inspiration

This mirrors standard card-fraud and payments practice:

- **Chargeback timing and codes.** Chargebacks are filed within network time limits, counted from the transaction
  processing date, and use network-specific reason codes that are either fraud or service related.
- **Multi-stage disputes.** Representment and pre-arbitration outcomes arrive weeks later.
- **Approve-through sampling.** "Approve-through", "rejected sample" or "exploration" programmes approve a random
  fraction of declines so outcomes can be observed.
- **Credit-risk reject inference.** Methods include parceling, augmentation and extrapolation, and are known to be
  biased when declines differ from approvals on unobserved dimensions.
- **Off-policy evaluation.** Inverse-propensity weighting with known logging propensities.

Network time limits in the docs are simplified and fictionalised. Real-world specifics should be marked "to verify"
before publication, and no real processor or network rule is quoted.

## 5. Causal graph / ground truth

**Traffic.**
- 400k authorisation attempts per month, Jan–Jul 2026.
- Rule declines: 0.9%, identical across policies (the rule engine runs before the score).
- Eligible = `rule_outcome = 'pass'`.

**Latent classes per eligible transaction.**

| Class | Share | Fraud-dispute probability if approved | Recovery |
|---|---|---|---|
| Legit | 98.6% | 0 | — |
| Friendly-fraud | 0.35% | Fraud-coded dispute raised with probability 0.7 | Tessel wins representment with probability 0.75 |
| Account-takeover (ATO) | 0.55% | Disputed with probability 0.85 | — |
| BIN attack | 0.5% | Disputed with probability 0.9 | — |

- **BIN-attack traffic.** Gift cards and electronics, amount_usd $300–$1,500, new accounts, clustered BIN ranges.
- **3DS liability shift.** 3DS-authenticated true fraud (30% of ATO and 10% of BIN attack) is won on representment
  with probability 0.8, so the merchant keeps the funds.
- **Service disputes** (not fraud-coded) occur on 0.4% of legit approvals. They are not decision cost under FIN-212.

**Potential outcome if approved** (drawn for every eligible transaction, whatever the decision):
- dispute events with timestamps;
- final loss = amount + $25 fee (fraud dispute finally lost), $25 (fraud dispute finally reversed), or 0.

**Cost if declined** = 0.11 × amount_usd when the approve-outcome has no final fraud loss (FIN-212 net lost margin),
else 0.

**Scores.**
- `fz-4` separates BIN attacks well (feature `bin_velocity_24h`) and ATO moderately.
- `fz-5` dropped `bin_velocity_24h` (feature-store deprecation noted in its model card), gained device-graph features,
  and separates ATO and friendly-fraud better.
- `fz-5` uses `three_ds_result`, so it approves more authenticated risky orders (liability shifted).
- Thresholds: `fz-4` 0.62, `fz-5` 0.58, each giving ≈ 4.9% score-decline rate on Jan–Feb traffic.

**Approve-through design** (from `decision_policy_log`, applied to score-declines only):

| Live score band | Rate until 2026-02-15 | Rate from 2026-02-16 (amount ≤ $500) | Rate from 2026-02-16 (amount > $500) |
|---|---:|---:|---:|
| [thr, 0.75) | 6% | 6% | 3% |
| [0.75, 0.90) | 2% | 2% | 1% |
| ≥ 0.90 | 0.5% | 0.5% | 0.25% |

- The docs describe the programme as "about 2% of score declines", which is the realised overall average.
- The random draw is not logged per row. Only `decision_reason = 'approve_through'` is.

**Analyst overrides.**
- 7% of score-declines, selected on analyst-visible legitimacy signals.
- The fraud-class share among overrides is 0.4%, against 31% among all score-declines.

**Dates.**
- `processing_date` = auth date + 0–2 days for normal orders; for pre-orders (6% of traffic) it is the shipment date,
  auth + 7–45 days.
- Fraud disputes are opened 5–120 days after `processing_date` (gamma, median 38).
- Representment decision comes 25–50 days after opening.
- The issuer may open pre-arbitration within 30 days of a representment win: 15% of wins are escalated, and the
  merchant loses 60% of those.

**Networks and codes.**
- Visa 55%, Mastercard 35%, Amex 10%.
- Fraud-coded families are listed per network in `dispute_lifecycle.md`.

**Extract** is taken 2026-10-25.

**Window truth (Jan–Apr, champion live, design targets per 1,000 eligible):**

| Policy | Cost per 1,000 eligible |
|---|---:|
| `fz-4` | $1,080 |
| `fz-5` | $1,300 (+20%) |

Most of the difference comes from the region where `fz-4` declines and `fz-5` approves, which is BIN-attack heavy and
mostly in the [0.62, 0.90) champion band.

## 6. Latent statistical/business invariant

**(a) Outcome label per approved eligible transaction.**

- **Fraud dispute.** A dispute counts if its reason code is in the network's fraud family, per network.
- **Final state:**
  - **`fraud_loss_final`:** the dispute ended in merchant loss. That covers chargeback accepted, representment lost,
    pre-arbitration lost or accepted.
  - **`fraud_reversed_final`:** representment won, and either no pre-arbitration was opened within 30 days with
    `representment.won + 30d ≤ extract`, or pre-arbitration was won.
  - **`fraud_dispute_pending`:** anything else with an open fraud dispute.
  - **`no_fraud_final`:** no fraud dispute, and `processing_date + 120d ≤ extract`.
  - **`no_fraud_pending`:** no fraud dispute and the 120-day clock still open.
  - **Uncaptured** approved transactions (no settlement row, 0.3%): `no_fraud_final`, because they cannot be disputed.
- **Multiple fraud disputes** on one transaction do not occur. The generator guarantees at most one fraud-coded
  dispute; service disputes can co-exist.

**(b) Policy cost estimand.**

`C(π) = (1000/N) Σ_{eligible i in window} c_i(π(i))`

- `π(i)` is decline iff that model's score ≥ its threshold in `decision_policy_log`.
- `c_i` follows FIN-212 on the approve-outcome.

**(c) Identification.** Observed approve-outcomes exist for three groups.

| Group | Selection | Weight |
|---|---|---|
| `score_approve` | Deterministic, live score < live threshold | 1 |
| `approve_through` | Random, probability known from the policy log by live-score band, amount band and date | 1 / rate |
| `analyst_override` | Selected on legitimacy | Not a valid sample. Overrides must be treated as members of the score-decline stratum represented by approve-throughs, and never as a sample |

A valid estimator therefore:
- uses `score_approve` rows with weight 1;
- represents all score-declines by approve-through rows with inverse-rate weights, within each (band × amount band ×
  period) stratum;
- or uses an equivalent estimator: stratified means, self-normalised IPW within strata, or doubly robust with the IPW
  correction.

**(d) Decision.** `revert_to_fz4` iff `C(fz-5) > C(fz-4)` (FIN-212: "the lower expected decision cost wins").
Visible truth: `revert_to_fz4`.

## 7. Grains and state variables

- **Authorisation attempt:** eligibility, both scores, live decision reason.
- **Settlement:** processing_date, and whether captured.
- **Dispute lifecycle state machine per dispute:** opened → accepted | representment submitted → won | lost →
  (pre-arbitration opened → won | lost | accepted), each with a clock.
- **Network × reason code:** fraud or service family.
- **Stratum** (live model × score band × amount band × policy period): approve-through inclusion probability.
- **Policy** (model, threshold): counterfactual decision per transaction.
- **Window:** cost aggregates.

Grain mistakes that matter:
- Labelling at the dispute grain without the state machine drops pre-arbitration.
- Weighting at the global grain instead of the stratum grain.
- Treating overrides and approve-throughs as one grain of "approved declines".
- Using the auth date instead of the processing date for the clock.

## 8. Evidence graph

N = natural path.

| Artifact | Shows | N? |
|---|---|---|
| Memo, go-decision note, `artifacts/backtest_2026-03-10` | Backtest −16%; switch | N |
| `reports/fraud_ops/loss_development_2026-10.csv` | May–Jul cohorts +35% at equal age | N |
| Attack-wave postmortem draft | June BIN wave; blames external attack | N (attractor) |
| `population.py`, `labels.py`, `load_disputes.py` | Approved-only; Visa-10.x-only; label snapshot date; pre-arbitration ignored | N |
| Model cards | `fz-5` trained on approved + matured labels; `bin_velocity_24h` removed; thresholds; target "fraud loss" | N |
| `decision_flow.md` | Approve-through exists "about 2% of declines, stratified by risk band; see policy log"; overrides exist | N once selection is suspected |
| `decision_policy_log` | Exact stratified rates and dates | partly |
| `FIN-212` | Costs per decision/outcome; decision criterion; "service disputes are fulfilment cost" | N (cost code cites it) |
| `dispute_lifecycle.md` | Network code families; time limits from processing date; representment and pre-arbitration flows | partly |
| Processor webhook email + raw JSONL | Pre-arbitration event types exist since 2025-11 | no (required for exact labels) |
| `warehouse_dictionary.md` | `processing_date` semantics; pre-orders settle at shipment; `disputes` built by `load_disputes.py` from webhooks | partly |
| `weekly_kpis` | Decline rate unchanged at 4.9%; approval rate unchanged | partly (refutes "fz-5 declines less") |

## 9. Evidence authority hierarchy

1. **Raw webhooks** override the `disputes` table. The table is derived by faulty code.
2. **The policy log** overrides `decision_flow.md`'s "about 2%". The log is the system configuration; the doc gives a
   typical description.
3. **FIN-212** governs the cost definition and decision criterion. It overrides the backtest's cost code wherever they
   differ, although in this design they do not. It also overrides Ops' "losses at 60 days".
4. **`dispute_lifecycle.md`** governs code families and clocks. It overrides `labels.py`'s Visa-only list.
5. **Model cards** describe training. They are not evaluation guidance: `fz-5` was trained approved-only, which is
   itself a hint of the bias, not an authority for evaluation.
6. **Postmortem, go note, KPIs** are derived and falsifiable.

## 10. Plausible hypotheses

| # | Hypothesis | For | Against |
|---|---|---|---|
| H1 | Attack wave★ | A June BIN wave really occurred (postmortem, traffic spike) | `fz-4` shadow scores would have declined 81% of June wave attempts vs `fz-5` 34%. The loss increase is present in May cohorts, before the wave. Window Jan–Apr IPW shows the same gap |
| H2 | Label maturity makes the backtest optimistic★ | Backtest labels as of 03-10 were immature; development curve | Maturing labels (R1) keeps `fz-5` ahead by 9% |
| H3 | `fz-5` genuinely worse, invisible to approved-only evaluation (selective labels)★ | `fz-4`-declined traffic was never labelled; `bin_velocity_24h` removed | Needs approve-through reconstruction |
| H4 | Decline-rate drift (`fz-5` declines less) | Plausible after a switch | KPIs: 4.9% vs 4.9% |
| H5 | Dispute-ops changes (fewer representments won) | Win rate appears to drop in `disputes` for recent months | Artefact of pending pre-arbitration and immature disputes |

Truth: H3, with H2 as a secondary label bias. H1 is real but not causal for the policy comparison. H5 is a label-state
artefact.

## 11. Why each wrong hypothesis is plausible

- **H1.** Real, dated, with a dramatic postmortem. It "explains" the timing of losses in Ops' eyes.
- **H2.** Recognising immature labels is the first expert reflex. Fixing it moves the numbers, so it feels like
  progress, but the ranking does not flip.
- **H4.** The standard first check after a model switch.
- **H5.** The `disputes` table shows representment wins falling for recent months, which is a real-looking pattern.

## 12. Investigation path (≈50–80 actions)

1. **(1–8) Reproduce.** Memo, notes, backtest artifact, loss development. Reproduce the backtest and re-run on the
   current extract (R1): still −9%.
2. **(9–16) Test the obvious alternatives.**
   - Attack-wave hypothesis: June vs May cohorts; shadow `fz-4` on the wave.
   - Decline rate KPIs.
   - **Discovery 1:** approved-only evaluation cannot see `fz-4`-declined traffic, where `fz-5` would approve.
3. **(17–26) Find the sample.**
   - `decision_flow.md`; the `decision_reason` values; the policy log.
   - **Discovery 2:** approve-through rates are stratified and changed on 02-16.
   - **Discovery 3:** overrides look like approvals of declines but are selected. Compare the override fraud rate with
     the approve-through fraud rate.
4. **(27–38) Rebuild labels.**
   - The `labels.py` Visa-only list: code-family table.
   - **Discovery 4:** raw webhooks have `prearbitration.*`. Some "won" disputes end lost.
   - `processing_date` for pre-orders.
   - Row-audit 10–20 dispute histories.
5. **(39–52) Estimate cost.**
   - Per-stratum IPW or stratified means; check stratum sizes and weight sums against eligible score-decline counts.
   - Compare with approved-only and with a reject-inference imputation (R8) to see the sensitivity.
6. **(53–65) Finish.**
   - Bootstrap or analytic uncertainty.
   - Decision.
   - Validate the label table state counts against webhooks.
   - Determinism.
   - Test on a second window (e.g. Jan–Feb) to check the CLI generality.

## 13. Natural wrong implementation

**Faulty backtest (as shipped).**

- `population.py`: `final_decision = 'approve'`, which includes `score_approve`, `approve_through` and
  `analyst_override`, all unweighted.
- `labels.py`: fraud = any `disputes` row with `network = 'visa' AND reason_code LIKE '10.%'` opened by
  `labels_as_of`, and `status != 'won'`.
- `load_disputes.py`: keeps `chargeback.created`, `representment.won`, `representment.lost` and `chargeback.accepted`.
  It ignores `prearbitration.*`.
- `backtest.py`: for each model, decline if score ≥ its threshold; cost via `costs.py`; sums over the population.

**Natural repair R1 (after "labels immature" is recognised).** Set `labels_as_of` = extract date, and/or require
`auth_date + 120d ≤ extract`. Re-run for Jan–Apr. Some agents also fix the reason codes.

What R1 gets wrong (visible targets):

- The population is champion-approved plus approve-through plus overrides, unweighted. The region that `fz-4` declines
  (4.9% of traffic, 31% fraud class) is represented by ~1,300 rows, 70% of them analyst overrides at 0.4% fraud. It
  should represent ~78k declines.
- Estimates: `fz-4` $402, `fz-5` $366, difference −9%, decision `keep_fz5` (wrong).
- The label table still misses:
  - Mastercard and Amex fraud (~41% of fraud disputes), unless codes were fixed;
  - pre-arbitration reversals (~1.4% of fraud disputes change state);
  - pre-order clocks, marking ~2,900 pre-order transactions final too early.

## 14. Second-order failure modes

| ID | Repair | Why wrong | Visible effect (targets) |
|---|---|---|---|
| R2 | Add approve-through with weight 1/0.02 (the doc's "about 2%"), exclude overrides | Rates are stratified 0.25–6%; grey-zone rows over-weighted 3×, top band under-weighted 4× | Difference +$640 vs truth +$220 → estimate fails; decision right on visible, wrong on hidden_b |
| R3 | Correct stratified weights, but overrides included in the weighted sample (e.g. weight 1/(approve_through+override share)) or pooled with approve-throughs | Override selection on legitimacy dilutes decline-region fraud | Difference ≈ −$30 → `keep_fz5` (wrong) |
| R4 | Empirical global propensity (approve-throughs / score-declines, one number) | Ignores strata and period | Like R2 but milder (+$450) → estimate fails |
| R5 | Correct population, Visa-only fraud codes | 41% of fraud disputes missed | Both costs −30%; label table fails |
| R6 | Correct population and codes, pre-arbitration ignored | Won-then-lost disputes count as reversed | Label table fails; `fz-5` cost −$25 (it approves more 3DS orders, and 3DS wins get escalated more). Estimate may pass; hidden_c fails it |
| R7 | Clock from `auth_date` | Pre-orders marked final before the 120-day window closes | Label table fails only (estimate impact < 1%) |
| R8 | Reject inference by imputation: train a classifier on approved outcomes and impute fraud probability for all declines ("augmentation/parceling") | Extrapolation: BIN-attack patterns barely appear among approvals, so the imputer under-predicts fraud in the decline region | Difference +$60 → estimate fails (decision right on visible; hidden_b wrong) |
| R9 | Approve-through rows only (Task 03 transfer: "evaluate on the random sample") | The sample covers only score-declines; the approve region is missing | Costs meaningless (only the decline region); fails |
| R10 | Weights by the *challenger's* score band | Propensity depends on the live model (`fz-4` in the window) | Estimate fails (weights misassigned for ~40% of rows) |
| R11 | Exclude pending disputes from the population (drop rows) rather than keeping them in the denominator | Removes transactions from N; pending disputes are fraud-heavy | ~0.5% cost bias; passes tolerance (accepted, see section 23) |

## 15. Correct repair properties

- **Eligibility** from `rule_decisions`; rule declines are excluded from both policies.
- **Labels** from raw webhooks through the lifecycle state machine; fraud families per network; 120-day clock from
  `processing_date`; pre-arbitration handled.
- **Counterfactual decisions** per transaction per model, from each model's score and threshold (`decision_policy_log`,
  or model cards, which agree).
- **Estimation.**
  - `score_approve` rows are observed with weight 1.
  - Every `score_decline` of the live model, including the overridden ones, is represented by approve-through rows of
    the same stratum with weight `N_stratum / n_approve_through_stratum`, or the design `1/rate`.
  - Override outcomes are not used as a sample.
- **Pending labels.** Treated by any documented choice within tolerance; the oracle imputes pending fraud disputes as
  loss with the per-network historical reversal rate.
- **Decision** from the estimated difference.
- **No hard-coded** rates, dates, thresholds or code lists beyond `dispute_lifecycle.md`'s code families. The families
  must be encoded; they are a documented fact.

## 16. Repair surfaces

| Surface | Change |
|---|---|
| `load_disputes.py` or a new labeller over the raw webhooks | Full lifecycle, pre-arbitration, finality clocks |
| `labels.py` | Per-network fraud families; processing-date clock; five states |
| `population.py` | Eligible traffic, strata, propensities from the policy log; override handling |
| `backtest.py` | Weighted counterfactual cost for each model; decision |
| `report.py`, `cli.py` | New outputs; window argument generality |

`costs.py` stays correct. Keeping it intact is a preservation check.

## 17. Validation requirements

- **Weight sums.** Per stratum, Σ weights of approve-through rows should equal the count of live score-declines, within
  sampling noise if using `1/rate`, or exactly if using `N/n`. Only a stratum-level table exposes R2, R4 and R10.
- **Override vs approve-through outcomes.** Fraud-class rate by band. Aggregates hide it, because overrides dominate
  counts.
- **Dispute lifecycle row audit.** Pick disputes with `prearbitration.opened`, Mastercard/Amex fraud codes, and
  pre-orders disputed on day 100–120 after auth but < 120 after processing.
- **Decline-rate check.** Each model's counterfactual decline rate on eligible traffic must match
  `weekly_kpis`/model-card calibration (≈ 4.9%).
- **Sensitivity.** Approved-only vs IPW vs imputation. An expert explains why only IPW is identified.
- **Uncertainty.** Bootstrap over approve-through rows within strata. A decision within noise should be flagged, but
  visible truth is far from zero.

## 18. Hidden fixture strategy

| Fixture | Invariant tested | Surface changes | Overfit / shortcut caught | Same distribution because |
|---|---|---|---|---|
| hidden_a (window 2025-09-01:2025-12-31, extract 2026-05-10) | Stratified propensities from log; processing-date clocks | Rates 8% / 3% / 1% with band edges 0.70/0.88; no amount split but a mid-window rate change; 14% pre-orders with shipment up to 60 days; Amex share 25% | Hard-coded 6/2/0.5 rates, 02-16 date, $500 band; auth-date clock; Visa+MC-only families | Policy log and pre-orders exist visibly; only values change |
| hidden_b (window 2026-01-01:2026-03-31, different world) | Correct weights flip the decision | Truth: `fz-5` better by 11% (its blind spot is small and sits in the ≥ 0.90 band at 0.5%/0.25%); `fz-5` approves many 3DS-authenticated orders whose fraud disputes are reversed | R2 (1/0.02 under-weights top band → says `fz-5` much better; estimate fails); R6 and no-reversal variants (count reversals as loss → `revert`, wrong); "always revert" constant; R8 | Only magnitudes and which segment carries the gap change |
| hidden_c (window 2026-02-01:2026-05-31, extract 2026-09-01) | Lifecycle finality and pending handling | Pre-arbitration on 35% of representment wins (merchant loses 70%); Mastercard 60% of traffic; overrides 15% of declines at 0.2% fraud; more pending disputes (~6%) | R3 (override pooling, larger effect), R5, R6 (estimate now outside tolerance), R11 variants that drop rows (bias ~3%: check it stays inside tolerance or re-tune) | Webhook types, overrides and pending states are all present visibly |

## 19. Mutation strategy

| Mutation | Expected |
|---|---|
| `nop` | 0 |
| `oracle` (pandas; stratified `N/n` weights) | 1 |
| `alt_design_ipw` (DuckDB SQL; `1/rate` weights; pending as loss) | 1 |
| `alt_doubly_robust` (outcome model + IPW residual correction within strata) | 1 |
| `alt_self_normalised` (SNIPW per stratum) | 1 |
| `matured_approved_only` (R1) | 0 (decision visible; labels) |
| `matured_approved_only_codes_fixed` | 0 |
| `ipw_global_2pct` (R2) | 0 (estimate visible; decision hidden_b) |
| `ipw_overrides_pooled` (R3) | 0 (decision visible) |
| `ipw_empirical_global` (R4) | 0 |
| `visa_only_codes` (R5) | 0 |
| `no_prearb` (R6) | 0 (labels; hidden_c estimate) |
| `auth_date_clock` (R7) | 0 (labels) |
| `reject_inference_imputation` (R8) | 0 (estimate; hidden_b decision) |
| `approve_through_only` (R9) | 0 |
| `challenger_band_weights` (R10) | 0 |
| **Overfit** `hardcode_visible_rates_and_date` | 1 visible, 0 hidden_a |
| **Overfit** `decision_constant_revert` | 1 visible, 0 hidden_b |
| **Overfit** `stratum_weights_from_visible_counts_table` (hard-coded N/n) | 1 visible, 0 hidden |
| **Cheat** `write_truth_like_numbers` / modify webhooks | 0 (recomputed; digest) |

## 20. Alternative valid implementations

**Accepted estimators** (each within tolerance of truth on all fixtures, verified at build):
- `1/rate` IPW;
- stratum `N/n` post-stratified weights;
- self-normalised IPW;
- doubly robust with correct propensities.

**Pending fraud disputes.**
- The graded label table requires the `pending` state exactly.
- For cost, any of these stay within tolerance by construction: pending counted as loss, as reversal-rate-weighted
  loss, or excluded from the numerator but kept in N. The generator keeps pending cost share < 25% of tolerance on
  visible, hidden_a and hidden_b.

**Hybrid override use** (observed override outcomes plus approve-through for the rest) is biased, because the
approve-through draw precedes overrides. The bias is small. It is a probe mutation: if it passes, it is accepted as
near-valid and noted; if it fails, the reason is documented.

**Output format.** Parquet or `csv.gz`, with state strings exact.

## 21. Verifier design

1. **Integrity.** Digests of the DuckDB extract, raw webhooks and docs. Two runs, identical outputs.
2. **Label table.** Exact set of eligible approved transactions in the window, and exact `outcome_state`. Mismatches are
   reported by network, pre-order, pre-arbitration and state pair.
3. **Decline rates.** Each model's counterfactual decline rate on eligible window traffic within 1e-6. Deterministic,
   no labels.
4. **Costs.**
   - Each policy's `cost_per_1000` within ±6% relative of truth.
   - Difference within `max($60, 3·SE_design)`, where `SE_design` is computed by the generator from the true
     stratum-level variance of approve-outcome costs and design rates.
   - Build target: the visible SE of the difference is ≈ $38, so the tolerance is ≈ $115.
5. **Decision** equals truth. The build asserts `|truth difference| ≥ 2.5 × tolerance` on every fixture.
6. **Recomputation.** The costs in the JSON are recomputed by the verifier from the agent's label table plus its
   declared weights file (`out/eval/weights.parquet`: txn_id, weight) where provided. This catches patched numbers.

   Weights are optional. Without them, only the truth comparison applies. This keeps the method open without trusting
   free text.
7. **Hidden A/B/C:** checks 2–5.

**Tolerance honesty.**
- Design target: R2's difference error (+$420) ≈ 3.6 × tolerance.
- R8 (+$60 absolute, i.e. −$160 from truth) ≈ 1.4 × tolerance. **This is below 2×.** Either raise the BIN-attack share
  in the disagreement region, or accept that R8 is caught by hidden_b's decision flip only.
- **Data volume** is the main lever. The variance calculation in section 27 shows that an unstratified 2% sample of 4
  months at 400k per month cannot grade a ±20% difference. That is why the design uses stratified rates concentrated
  near the threshold.

## 22. Answer-key leakage audit

| Artifact | Risk | Mitigation |
|---|---|---|
| `decision_flow.md` | Could say "approve-throughs are an unbiased sample; weight by 1/rate" | States only operational facts: rates set per band in the policy log; analysts may override; purpose "keep labels flowing for model retraining" |
| `decision_policy_log` | Rates are exact propensities | This is a system fact. The inference that they are *weights*, that overrides are excluded and that strata use the live model is the task |
| `dispute_lifecycle.md` | Code families plus timelines are near-operational for labels | Accepted (facts). Finality of "won" after 30 days without pre-arbitration must be inferred from "issuer may open pre-arbitration within 30 days". No sentence defines label states |
| FIN-212 | Cost and decision rule | The rule is a business definition, and necessary |
| Model cards | `fz-5` "trained on approved transactions with matured labels" | Hints at selection but does not solve it |
| Backtest artifact | Numbers from faulty semantics | No correct number anywhere |
| `costs.py` | Correct helper | It is the cost function, not an estimator. No weights parameter. `backtest.py` has no strata code |

**Cheap-solve audit.**
- **One grep** (`approve_through`) plus `1/0.02` gives R2, which fails.
- **One doc** (`decision_flow`) plus the log gives correct rates, but overrides and live-model banding remain, so R3
  and R10 fail unless reasoned.
- **One SQL filter** (`decision_reason IN ('score_approve','approve_through')` with log-joined weights) is essentially
  the oracle population in one query.

  **This is the cheapest correct path.** Its cost is the join of stratum rates by live score band × amount × date. The
  labels must still be rebuilt from webhooks, with per-network codes, pre-arbitration and processing-date clocks.
  Estimated minimum: 6–8 correct decisions.
- **One helper:** none.
- **One old report:** the backtest artifact is the wrong answer.
- **Restoring behaviour:** reverting to `fz-4` is the decision, but the estimates and label table are still graded.

## 23. Underspecification audit

| Ambiguity | Resolution |
|---|---|
| Pending disputes in cost | Any reasonable treatment within tolerance (section 20); graded exactly only in the label table |
| Is a representment win final? | Lifecycle doc: issuer pre-arbitration allowed within 30 days of the win. State is `pending` until then. The generator avoids wins within ±1 day of the 30-day boundary at extract |
| Uncaptured approvals | Dictionary: an uncaptured authorisation expires after 7 days and cannot be charged back → `no_fraud_final` |
| Cost of service disputes | FIN-212 explicitly excludes them |
| Threshold ties (score = threshold) | Scores have 6 decimals; generator avoids exact equality |
| Which score band defines the stratum: live score at decision time or re-scored? | Only one live score per transaction exists (`mode = 'live'`) |
| Could an expert prefer imputation plus IPW (DR) with a different outcome model? | Accepted within tolerance |
| Window by auth date or processing date? | README: window selects authorisation attempts by `auth_ts` (UTC date) |
| Fee for accepted chargebacks | FIN-212: $25 for every fraud dispute, whatever the outcome |
| Explore draw before or after override | `decision_flow.md`: approve-through is decided at authorisation; analyst review happens only on declines not approved through |

## 24. Expected trajectory length

**Estimate:** 55–85 actions.

**Why it is long.**
- Four independent rebuilds: population and weights, codes, lifecycle, clock.
- A statistical estimation step with a stratum table.
- The data is large enough that agents must write aggregate queries and then drill to rows.
- The attack-wave attractor costs 5–10 actions to falsify.

## 25. Why harder than Tasks 03/05/06

- **No scaffolding.** No weights, no strata, no lifecycle, no network code table in code.
- **Wrong fixes are the natural ones.** Maturity (R1) and naive IPW (R2) are the obvious fixes, and both are wrong.
- **Attractors on the path.**
  - The backtest artifact is what the agent must reproduce.
  - The attack-wave postmortem is what Ops believes.
  - The "about 2%" doc sentence is where the approve-through is discovered.
- **Validation below the aggregate.** It needs stratum weight sums and dispute state machines; no single transaction
  demonstrates the bias.

**Against Task 03.** Task 03's population rule was "holdout, as assigned, ITT", with final and correct labels and a
rank metric (AUC).

G30 differs in four ways:
1. The random sample is **not** a sample of the evaluation population. It covers only one model's declines, so it must
   be *combined* with deterministic approvals.
2. Inclusion probabilities are stratified and time-varying, and belong to the *live* model rather than the evaluated
   one.
3. A look-alike selected group (overrides) must be excluded.
4. The estimand is a counterfactual *policy* cost for two policies, with revisable labels.

Transcribing Task 03's rule ("use the random slice") yields R9, which fails.

## 26. Comparison with Task 02

| | Task 02 | G30 |
|---|---|---|
| Failure locus | Per-example × cutoff state grain | Per-stratum propensity grain + per-dispute state machine |
| Deterministic part | Features | Label table, decline rates |
| Statistical part | None | IPW policy value with known propensities |
| Near-miss structure | Grouping key | Weight stratum, override exclusion, finality clock |

Expected to be comparable to harder. Unlike Task 02, part of the grade is tolerance-based, which admits more valid
methods but carries gradability risk.

## 27. Benchmark risks

**Gradability: M–H.** The variance arithmetic is the design constraint:
- An IPW total over a decline region of size `N_D` has SE ≈ `sd·√(N_D/p)`.
- With `N_D` ≈ 80k over 4 months, p = 2%, and per-transaction cost sd ≈ $300, the SE per 1,000 of 1.6M eligible is
  ≈ $375.
  That swamps any realistic policy difference.
- The design therefore concentrates exploration (6%) where the policies disagree and puts the disagreement near the
  threshold. The difference SE comes from the disagreement region only, ≈ 1–3k transactions.
- If build measurements miss the 2.5× margin, the levers are more traffic or higher grey-zone rates.
- The candidate's literal "2%" survives only as the doc's average.

**Implementation cost: H.**
- 2.8M-row worlds × 4, lifecycle webhooks, two score models with controlled overlap.
- Generator runtime (stdlib) is estimated at 2–4 minutes per world, so the verifier needs ~20 minutes.

**Realism: high.** Every mechanism is ordinary card-not-present fraud operations. The simplifications:
- fraudsters do not adapt to the policy;
- at most one fraud dispute per transaction;
- the approve-through draw is independent of overrides.

**Leakage: M.** The policy log is an exact propensity table. That is realistic, and it makes the cheapest correct path
~8 decisions (section 22).

**Underspecification: M.** Pending treatment and hybrid override use are probes.

**Overlap: the central risk.**

- **Task 03 (selective labels, random slice): moderate.** The concept class is the same. The operationalisation differs
  (section 25).
- **G01 (label maturity; random holdout for a score-driven treatment): moderate-high on vocabulary, lower on mechanics.**
  - G01's hard part is **source completeness** for labels and target-outcome separation for *monitoring one model*.
  - G30's hard part is **counterfactual policy value** with stratified propensities and **label revision** through a
    dispute state machine.
  - Both contain "immature labels" as a first-layer trap. That shared first layer is the overlap a benchmark reader
    will notice.
- **G24 (recommender OPE): high on estimator family.** IPW with logged-policy propensities in both.

**Should G30 survive?**
- **G30 vs G24.** G30 is the stronger of the two as a *risk* task: identified propensities, realistic label revision,
  and a binary business decision. G24 adds position bias and slate propensities, which are harder to grade.
- **G01 and G30 together** is defensible only if G01 keeps its treatment component light: holdout-based target
  estimation is fine, but not "policy value".
- **G30 and G24 together** is not recommended. Keep one, and I would keep G30 for gradability.

**Headroom.** A strong agent who knows off-policy evaluation will find IPW quickly. The residual difficulty is:
- the override look-alike;
- live-model strata;
- the label state machine.

If that proves too easy, the next lever is making approve-through rates depend on a *third* score (a pre-authorisation
risk tier) recorded only in the decision log.
