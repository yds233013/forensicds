# RA-512 - RevOps lifecycle v2

RevOps Data Engineering, 2026-06-22.

Lifecycle v1 (`lead_lifecycle_v1`, retired) only held leads that entered an SDR workflow; nurture leads had no
lifecycle row, so downstream consumers could not see outcomes for them and every consumer re-derived
conversion from `conversions` with its own logic.

Lifecycle v2 (`lead_lifecycle`) has one row per accepted lead, rebuilt nightly:

- `converted_60d` is computed centrally for every accepted lead, including nurture leads and self-serve
  purchases, using the standard 60-day definition.
- `current_queue` and `lifecycle_stage` reflect the lead's latest state.
- `first_worked_at` is the first SDR activity.

Consumers migrated: marketing attribution dashboard (MKT-88), SDR productivity report (SDR-31), lead-score
evaluation (lead_eval 2.0.0).
