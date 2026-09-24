# Required outputs

`mlops.monitor` must write two files into `out/` when run as

    python -m mlops monitor --db data/appointments.sqlite --out out

## out/readout.json

| field | type | meaning |
|---|---|---|
| `model_version` | string | the model under review |
| `window_weeks` | [int, int] | the production weeks the readout covers, inclusive |
| `monitored_auc` | number | the AUC the current monitoring series reports for that window |
| `validation_auc` | number | the model registry's validation figure |
| `retention_floor_auc` | number | the floor implied by MRM-04 §4.3 |
| `evaluation_population` | object | `clinic_ids` (list) and `n_appointments` (int) for the population you evaluated on under MRM-04 §4.1 |
| `auc_by_scoring` | object | the AUC on that population under each scoring basis available (see below) |
| `feed_defect_share_pct` | number | share of scored records in the window whose served feature values disagree with the source record or the event history |
| `programme_effect_pp` | number | effect of the reminder programme on the no-show rate, in percentage points, in the score band the programme acts on, stratified by clinic size band |
| `attribution_auc` | object | how the gap between `validation_auc` and `monitored_auc` divides between causes, in AUC points |
| `decision` | string | the action MRM-04 §4.3-§4.4 requires |

### `auc_by_scoring`

Exactly these four keys:

    as_served · record_features_asof_window · feature_store_current · candidate_v4

`as_served` is the scores in `model_scores` for the model under review. `record_features_asof_window` is the
model rescored from its published coefficients over the source record and the event history, on the feature
window the registry records for it. `feature_store_current` is the model rescored over the feature store as it
now stands. `candidate_v4` is the candidate's scores.

### `attribution_auc`

Exactly these five keys, summing to `validation_auc - monitored_auc` within 0.01:

    population_drift · feature_feed_defect · feature_vintage · policy_feedback · other

Any key may be zero or negative. Do not add or rename keys.

### `decision`

One of `retain_model`, `retrain_on_recent_data`, `replace_with_v4`, `remediate_feature_pipeline`.

## out/evaluation_population.csv

Header `clinic_id,n_appointments,no_show_rate,auc_as_served`, one row per clinic in the population you
evaluated on.

## Rules

* Do not modify `data/appointments.sqlite`.
* The command must be re-runnable and produce the same outputs for the same database.
* AUCs to at least three decimals; rates and effects in percentage points.
