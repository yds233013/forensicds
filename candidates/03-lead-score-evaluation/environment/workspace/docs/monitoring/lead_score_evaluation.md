# Lead-score evaluation (monthly)

Owner: RevOps Analytics. Implementation: `src/lead_eval`. Consumers: Sales & Marketing operating review,
router threshold reviews.

## Schedule and window

Run on the 2nd of each month with as-of date `A` = the 1st. A lead's outcome is known once its 60-day outcome
window has closed, i.e. `created_at + 60 days <= A` (00:00 UTC). The evaluation covers leads created in the 180
days up to and including the latest matured creation time: `A - 240 days <= created_at <= A - 60 days`.

## Outcome

`label = 1` if the lead became a closed-won customer within 60 days of creation
(`closed_won_at - created_at <= 60 days`), else 0.

## Score

The champion model's intake score (`lead_scores.model_version` = config `champion_model`).

## Metrics (computed from the evaluation cohort)

| Metric | Definition |
|--------|------------|
| `n_leads`, `n_converted`, `conversion_rate` | counts and mean label |
| `roc_auc` | ROC AUC of score vs label |
| score bins | `n_bins` equal-count bins after sorting by score ascending, ties by `lead_id`; when the count does not divide evenly the lower bins take the extra rows |
| `calibration` | per bin: n, min/max/mean score, conversion rate |
| `top_decile_conversion_rate`, `top_decile_lift` | conversion rate of the highest bin; divided by `conversion_rate` |
| `recommended_threshold` | walking down from the highest bin, the `min_score` of the last bin reached while every bin so far converts at >= `target_conversion_rate`; null if the highest bin is below target |
| `by_source` | n and conversion rate per lead source |

## Use in decisions

- Champion health: `roc_auc` and calibration month over month.
- Router threshold review: `recommended_threshold` (lowest score at which worked leads convert at or above the
  8% SDR-capacity break-even rate).
