# Analytics warehouse - data dictionary (renewal-risk sources)

The warehouse is a replica fed by connectors. Every table has `synced_at`: the UTC time the row (or
its latest version) was loaded into the warehouse. Source systems also record their own business
timestamps (`changed_at`, `opened_at`, `decided_at`, ...), which can be earlier than `synced_at`.

## Load schedules

| Source | Connector | Typical delay between source commit and `synced_at` |
|--------|-----------|------------------------------------------------------|
| Billing contracts | nightly batch | contracts exist before their start date |
| Renewal outcomes | change stream | minutes |
| Product usage | weekly rollup job | loaded Monday ~02:00 UTC for the week that closed on Sunday |
| Support tickets | change stream | minutes |
| CRM (CRM v3), direct-sales records | change stream | minutes; paused during replication incidents and replayed afterwards (see `warehouse_sync_log`, `docs/ops/`) |
| CRM (CRM v3), partner-channel records (`lead_source = partner`) | partner integration, weekly batch | up to a week (Sunday 22:00 UTC batch) |
| Customer Success platform | nightly batch | changes made on day D are loaded ~01:30 UTC on D+1 |

Rows loaded by one connector for one record are applied in the order they were committed in the source.

## Tables

### `accounts` - one row per account
`account_id`, `segment` (Enterprise / Mid-Market / SMB), `region`, `industry`, `created_date`, `synced_at`.
Static firmographics.

### `contracts` - one row per contract term
`contract_id`, `account_id`, `start_date`, `renewal_date` (term end + 1 day), `seats`, `arr_usd`, `plan`, `synced_at`.

### `renewal_outcomes` - one row per decided renewal
`contract_id`, `account_id`, `renewal_date`, `outcome` (`renewed` / `churned`), `decided_at`, `synced_at`.
Renewals not yet decided have no row.

### `usage_weekly` - one row per account per week
`account_id`, `week_start` (Monday), `active_users`, `api_calls`, `logins`, `synced_at`.

### `support_tickets` - one row per ticket (current state)
`ticket_id`, `account_id`, `opened_at`, `severity` (sev1-sev3), `category`, `closed_at` (null while open), `synced_at`.

### `crm_opportunities` - one row per CRM opportunity (CRM v3 object)
`opportunity_id`, `account_id`, `contract_id` (renewal opportunities only), `opportunity_type`
(`renewal` / `expansion`), `lead_source` (`direct` / `partner`), `owner`, `created_at`, `stage`,
`forecast_category` (Pipeline / Best Case / Commit / Omitted / Closed), `amount_usd`, `close_date`,
`competitor`, `last_modified_at`, `synced_at`.
Field values are the record's current values as of the extract. `account_id`, `contract_id`,
`opportunity_type`, `lead_source` and `created_at` never change after creation.

### `crm_opportunity_field_history` - one row per change to a tracked opportunity field
`history_id`, `opportunity_id`, `field` (`stage`, `forecast_category`, `amount_usd`, `close_date`,
`competitor`), `old_value`, `new_value` (text), `changed_at` (CRM commit time), `synced_at`, `changed_by`.
Append-only audit trail. When an opportunity is created, one row is written per tracked field (empty
`old_value`, `changed_at` = the opportunity's `created_at`); a later change from an empty value (e.g. a
first competitor) also has an empty `old_value`. The audit trail has been replicated continuously since
2019 (CRM v2 `crm_field_audit`, renamed at the CRM v3 cutover).

### `cs_account_health` - one row per account (Customer Success object)
`account_id`, `health_score` (0-100), `health_color` (Green >= 70, Yellow 50-69, Red < 50),
`nps_last` (null if the account never answered), `csm_sentiment` (Positive / Neutral / Negative),
`last_changed_at`, `synced_at`. Current values as of the extract.
Health scores are recalculated monthly; NPS surveys run quarterly; CSM sentiment is updated after
business reviews and escalations.

### `cs_account_health_history` - one row per change to a tracked health field
`history_id`, `account_id`, `field` (`health_score`, `health_color`, `nps_last`, `csm_sentiment`),
`old_value`, `new_value` (text), `changed_at`, `synced_at`, `changed_by`. Append-only. The record's
creation writes one row per field (`changed_at` = account creation); later changes from an empty value
also have an empty `old_value`.

### `warehouse_sync_log` - connector incidents and replays
`source`, `event`, `started_at`, `ended_at`, `note`.

## Decommissioned

`crm_opportunity_daily_snapshot` and `cs_health_daily_snapshot` (one row per record per day, taken at
00:00 UTC) were dropped on 2026-01-31 after the CRM v3 migration. See `docs/ops/2026-01_crm_v3_migration.md`.
