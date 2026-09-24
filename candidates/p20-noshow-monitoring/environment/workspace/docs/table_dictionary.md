# data/appointments.sqlite — table dictionary

## appointments
One row per booked outpatient appointment, 52 weeks. Patient and appointment attributes are as held on the
**source record**.

| column | meaning |
|---|---|
| appt_id, clinic_id, patient_id | keys |
| booked_on, appointment_on, week | booking date, appointment date, ISO production week |
| appointment_type, lead_time_days, age_band, deprivation_decile, distance_km, interpreter_required | appointment and patient attributes |
| referral_source | `GP`, or the partnership source that began referring in month 4 |
| prior_no_show_count | the no-show count held in the **current** feature table; the window it covers is in `policy_config` under `feature_store.prior_no_show_window_days` |
| attended, no_show | the realised outcome |

## feature_snapshots
What the scorer was **given** at booking, one row per appointment. This is the serving vintage.

## attendance_events
Append-only attendance history, including events that predate the extract. `appt_id` is null for events that
predate the extract.

## model_scores
`(appt_id, model_version, score)`. For `noshow-v3.1` these are the scores produced at booking. For
`noshow-v4.0` they are a batch rescore of every appointment.

## model_registry
One row per model version, with the validation figure, the feature window the model was defined on, and the
published coefficients for `noshow-v3.1`.

## reminder_calls
One row per booking selected for calling, with the call outcome.

## policy_config
Key/value configuration of the reminder programme and the feature store, with effective dates.

## monitoring_metrics
The vendor's dashboard series: weekly AUC and no-show rate on the population it monitors.

## clinics
Clinic reference data, including `size_band` and `ramp_group`.
