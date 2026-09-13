# Feature dictionary - renewal-risk

Every feature describes the account at the example's prediction time (see the model card,
"Prediction point"). Values are written to `artifacts/features.csv` exactly as defined here; model
preprocessing (winsorization, scaling) happens inside the model pipeline.

Notation: `P` = prediction date (00:00 UTC), `R` = renewal date, `arr`, `seats` = the renewing contract's.

## Contract

| Feature | Definition | Source |
|---------|------------|--------|
| `arr_usd_log` | `ln(1 + arr)` | `contracts` |
| `seats_licensed` | seats on the renewing contract | `contracts` |
| `plan_enterprise` | 1 if plan is `Enterprise` | `contracts` |
| `tenure_months` | days from account creation date to `P`, divided by 30.4375 | `accounts` |
| `prior_renewals` | renewals of the account decided as `renewed` and loaded before `P` | `renewal_outcomes` |

## Product usage

Weekly rollups are loaded the morning after the week closes; a week is used when
`week_start + 7 days < P`.

| Feature | Definition | Default (no weeks) |
|---------|------------|--------------------|
| `active_user_ratio_4w` | mean `active_users` over the last 4 usable weeks / `seats` | 0.0 |
| `active_user_trend_12w` | least-squares slope of `active_users / seats` against week index over the last 12 usable weeks (oldest = 0); 0.0 with fewer than 3 weeks | 0.0 |
| `api_calls_4w_log` | `ln(1 + sum api_calls)` over the last 4 usable weeks | 0.0 |
| `logins_per_active_user_4w` | `sum logins / max(1, sum active_users)` over the last 4 usable weeks | 0.0 |

## Support

| Feature | Definition |
|---------|------------|
| `tickets_90d` | tickets opened before `P` and at most 90 days before `P` |
| `sev1_tickets_180d` | `sev1` tickets opened before `P` and at most 180 days before `P` |
| `open_tickets_at_prediction` | tickets opened before `P` that were not closed before `P` |

## Sales pipeline (CRM)

The renewal opportunity is the opportunity of type `renewal` on the renewing contract. When there
is no renewal opportunity for the example, the defaults apply.

| Feature | Definition | Default |
|---------|------------|---------|
| `has_renewal_opp` | 1 if there is a renewal opportunity | 0 |
| `renewal_stage_ordinal` | stage mapped Closed Lost=0, Qualification=1, Discovery=2, Proposal=3, Negotiation=4, Verbal=5, Closed Won=6 | -1 |
| `forecast_commit` | 1 if forecast category is `Commit` | 0 |
| `forecast_best_case` | 1 if forecast category is `Best Case` | 0 |
| `forecast_omitted` | 1 if forecast category is `Omitted` | 0 |
| `renewal_amount_ratio` | opportunity amount / `arr` | 1.0 |
| `days_to_opp_close` | days from `P` to the opportunity close date | 90 |
| `competitor_flagged` | 1 if a competitor is recorded on the opportunity | 0 |
| `open_expansion_opps` | expansion opportunities on the account that are not in a closed stage (`Closed Won`, `Closed Lost`) | 0 |

## Customer Success health

When the account has no health record, the defaults apply.

| Feature | Definition | Default |
|---------|------------|---------|
| `health_score` | account health score (0-100) | 50.0 |
| `health_red` | 1 if health color is `Red` | 0 |
| `nps_last` | most recent NPS response recorded on the account; missing NPS counts as the default | 0.0 |
| `csm_sentiment_negative` | 1 if the CSM sentiment is `Negative` | 0 |
