# RevOps warehouse - data dictionary

All timestamps UTC.

| Table | Grain | Columns |
|-------|-------|---------|
| `leads` | one row per inbound lead | `lead_id`, `created_at`, `source` (web_form / demo_request / content_download / webinar / partner_referral), `company_size`, `country`, `intake_status` (accepted / rejected_spam / rejected_duplicate), `campaign` |
| `lead_scores` | one row per (lead, model version) | `lead_id`, `model_version`, `scored_at`, `score` |
| `routing_events` | one row per routing decision | `routing_event_id`, `lead_id`, `routed_at`, `policy`, `queue`, `router_version`, `threshold` (intake decisions only), `score_at_routing` (intake decisions only) |
| `sdr_activities` | one row per SDR touch | `activity_id`, `lead_id`, `activity_at`, `activity_type` (call / email / meeting), `rep` |
| `conversions` | one row per closed-won opportunity sourced from a lead | `opportunity_id`, `lead_id`, `closed_won_at`, `channel` (sales_led / self_serve), `first_year_arr_usd` |
| `lead_lifecycle` | one row per accepted lead (RevOps lifecycle v2 rollup, rebuilt nightly) | `lead_id`, `created_at`, `current_queue`, `first_worked_at` (first SDR activity), `qualified` (SDR marked sales-qualified), `converted_at`, `converted_60d` (closed-won within 60 days of creation), `lifecycle_stage` |
| `router_config_log` | one row per router version | `router_version`, `effective_from`, `threshold`, `exploration_holdout_pct`, `champion_model` |

Self-serve conversions are purchases through the website checkout without SDR involvement; they are attributed
to the lead by email domain.
