# P20 implementation specification — no-show model deployment feedback

Authoritative source: `HANDOFF_2026-09-23.md` §16 (P20 A–Z) and §20/§23/§24/§26.

## 1. The professional incident

Halcyon Health Partners runs a no-show risk model (`noshow-v3.1`) across 38 outpatient clinics. Since the
reminder programme went live, monitoring shows AUC falling from **0.78 to 0.66** over six months. The vendor's
monitoring report attributes this to data drift, has already retrained the model, and has supplied
`noshow-v4.0` scores for every appointment. The clinical operations director wants a decision before the next
capacity plan.

## 2. The consequential decision

The model risk-management standard states two things: (a) *model performance monitoring must be computed on a
population whose outcomes are not influenced by the model's own use*; and (b) *a model may be retrained or
retired only where its discrimination on such a population falls below AUC 0.72.* The decision is one of
`retain_model`, `retrain_on_recent_data`, `replace_with_v4`, `change_reminder_policy`.

The standard does **not** say which population is policy-invariant. That has to be found.

## 3. Initially plausible explanations (5)

1. **Genuine population drift** — PSI/KS are elevated on several features (a new referral source arrived in
   month 4; this is real but is not the cause).
2. **Policy feedback / performativity** — reminded patients attend, so the model's own successes compress the
   outcome distribution at the top of the score range and destroy measured discrimination.
3. **Label leakage removed** — a pipeline fix removed a leaky feature, so the earlier AUC was inflated.
4. **Upstream feature backfill** — an ETL change recomputed `prior_no_show_count` historically (12-month
   window → all-time), so training-time and serving-time values differ for pre-change rows.
5. **Case-mix change** from the new referral source.

Mechanisms 2 and 4 are both genuinely active. 1, 3 and 5 are present as evidence but are not causes of the
measured drop.

## 4. The analytical object to reconstruct

> Model discrimination on a **policy-invariant population**, the **causal effect of the reminder programme**,
> and the share of the measured AUC change attributable to the **feature vintage** — and then the standard's
> rule applied to the first of those.

## 5. Data-generating process (generator truth; never shipped)

For appointment *i*: `eta_i = f(age_band, prior_no_shows_asof, lead_time_days, deprivation_decile,
appointment_type, distance_km)`; true no-show probability `p_i = logistic(eta_i)`.

* `noshow-v3.1` scores are a calibrated but imperfect estimate of `p_i` (a fixed coefficient vector plus
  score noise), giving AUC ≈ **0.78** on an untreated population.
* **Policy**: from week `W`, clinics call the top 20 % of scores. Ramped by clinic group over 6 weeks (the
  ramp is in the policy-engine config).
* **Treatment effect**: a reminder multiplies the no-show odds by `OR = 0.55`.
* **Holdback**: 4 of the 38 clinics were assigned to a control arm at programme start, stratified by clinic
  size, and never received score-driven reminders. This is recorded in the policy-engine configuration as an
  exclusion list with a `control_arm` stratification note — discoverable, never named in the instruction.
* **Backfill**: on date `D`, `prior_no_show_count` was recomputed for all history. The append-only
  `attendance_events` table allows the as-of-booking value to be reconstructed. The backfill inflates the
  feature for patients with long histories and costs ≈ **0.02 AUC** when the model is scored on
  current-vintage features.
* `noshow-v4.0` was trained on post-policy data **including treated outcomes**, so it partly learns "high
  score ⇒ attends". Its scores are shipped for every appointment, so its performance on any population is a
  deterministic function of the data.

## 6. Identifiable quantities

| quantity | identified by | tolerance | basis |
|---|---|---|---|
| `deployed_auc_v31` | AUC of v3.1 on reminded clinics, recent 8 weeks | ±0.01 | reproduces the vendor figure |
| `holdback_auc_v31` | AUC of v3.1 on the control-arm clinics, recent 8 weeks | ±0.015 | DeLong SE ≈0.007 at n≈9k |
| `holdback_auc_v40` | AUC of the shipped v4.0 scores on the same population | ±0.015 | as above |
| `reminder_effect_pp` | no-show rate difference in the top-20 % score band, control-arm vs reminded clinics, size-stratified | ±2.5 pp | SE ≈1.0 pp |
| `vintage_auc_delta` | AUC(v3.1, as-of features) − AUC(v3.1, current features), on the control arm | ±0.015 | paired, so SE is small |
| `decision` | the standard's 0.72 rule on `holdback_auc_v31` | exact | — |

**Not identifiable, therefore not graded:** the AUC of a model the *agent* trains (model-class dependent);
the individual-level counterfactual attendance; the causal effect outside the top-20 % band (never treated).

## 7. The correct investigation

Reproduce the vendor's curve → enumerate drift vs policy feedback vs vintage → read the policy-engine config
and discover the control arm → evaluate v3.1 there → evaluate v4.0 there and find it **worse** → reconstruct
as-of features from the event log and quantify the vintage component → estimate the reminder effect from the
control-arm contrast → apply the standard's rule → `retain_model` and fix the monitoring population.

## 8. The sophisticated incorrect investigation

PSI/KS on every feature (several exceed the usual 0.2 threshold), temporal cross-validation showing monotone
degradation, and an evaluation of `v4.0` on a recent holdout **drawn from the reminded population**, where it
scores ≈0.77. Conclusion: drift is real, retraining fixes it, adopt v4.0. Every number reconciles with the
monitoring dashboard. This is the industry-standard remedy and it makes the system worse.

## 9. Falsification opportunities (3)

| route | competing predictions | evidence |
|---|---|---|
| evaluate on the control arm | drift ⇒ AUC has fallen there too; policy feedback ⇒ AUC is unchanged there | clinic-level `control_arm` flag reachable from the policy-engine config |
| evaluate v4.0 on the control arm | genuine degradation ⇒ v4.0 better; policy-contaminated training ⇒ v4.0 **worse** | shipped v4.0 scores |
| as-of feature replay | vintage ⇒ a measurable AUC gap between vintages; not vintage ⇒ none | append-only `attendance_events` |

## 10. Deliverables and verifier strategy

`out/readout.json` with the six quantities above plus `attribution` over a neutral vocabulary
(`policy_feedback`, `feature_vintage`, `population_drift`, `label_definition`, `other`) expressed as shares of
the measured AUC change, and `decision`. `out/holdback_evaluation.csv` records the per-clinic AUC and n used,
so the population the agent evaluated on is an observable artefact rather than an assertion.

The verifier recomputes each quantity independently (its own AUC implementation, not the pipeline's) on the
visible extract and three hidden extracts. Hidden extracts vary which mechanisms are active, including one in
which the model **has** genuinely degraded on the control arm and retraining *is* the correct action — so
"never retrain" fails.
