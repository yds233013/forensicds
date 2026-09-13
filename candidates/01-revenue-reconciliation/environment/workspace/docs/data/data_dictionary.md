# Data dictionary - revenue analytics

## Source extracts (`data/`) - read only

### `billing/billing.db` (Billing system extract, SQLite)

| Table | Grain (one row per) | Notes |
|-------|---------------------|-------|
| `billing_accounts` | billing account | `crm_account_id` = owning CRM account (set at creation). `status` active/closed. |
| `plans` | plan price version | list prices; `effective_from`/`effective_to`. |
| `subscriptions` | subscription | several per billing account is normal (plans, add-ons, seat blocks, usage). |
| `invoices` | invoice | `status` posted / draft / void; `replaces_invoice_id` on re-issued invoices. |
| `invoice_lines` | invoice line | `line_type` subscription / discount / usage / onboarding / tax; `service_period_start/_end` inclusive. |
| `credit_notes` | credit note | references the credited `invoice_line_id`; `amount_minor` positive. |
| `fx_rates` | (currency, rate_month) | `usd_per_unit`, monthly average. |
| `accounting_periods` | period month | `status` closed / closing / open. |

All `*_minor` amounts are integer minor units (cents) of the document currency.

### `crm/crm_accounts_export.csv` (CRM account export)

Grain: one row per (account record version, linked billing account).
The CRM keeps a history of each account record; every time an attribute or
lifecycle status changes a new `record_version` is written and the previous one
is end-dated.

| Column | Description |
|--------|-------------|
| `account_id` | CRM account id |
| `record_version` | version number of the account record (1..n) |
| `valid_from`, `valid_to` | dates the record version was in effect (inclusive); empty `valid_to` = still in effect |
| `is_current` | `true` for the latest record version of the account (an end-dated latest version means the account record is closed) |
| `account_name`, `segment`, `region`, `billing_country`, `account_owner` | attributes of that version |
| `lifecycle_status` | Active / Churned / Migrated |
| `successor_account_id` | set on Migrated versions (mirrors the migration register) |
| `billing_account_id` | a billing account shown on the account |
| `billing_link_type` | `primary`: billing account belongs to this account. `legacy`: billing account of a predecessor account, shown for account-team visibility |

### `crm/account_migrations.csv` (Billing Ops migration register)

Grain: one row per legacy account -> successor account relation.
A consolidation has one row per legacy account.

| Column | Description |
|--------|-------------|
| `migration_id`, `change_ticket` | identifiers |
| `legacy_account_id`, `successor_account_id` | CRM accounts |
| `legacy_billing_account_id`, `successor_billing_account_id` | billing accounts involved (successor empty while scheduled) |
| `migration_type` | entity_transfer / entity_consolidation |
| `cutover_mode` | `immediate`: legacy account closed on the effective date. `staged`: legacy billing account keeps invoicing existing prepaid terms and final usage until Billing Ops signs off the cutover |
| `effective_date`, `cutover_closed_date` | dates |
| `status` | scheduled / cutover_in_progress / completed |

## Warehouse (`warehouse/analytics.db`) - rebuilt on every run

### `fct_recognized_revenue`
Grain: one row per (`source_type`, `source_id`, `revenue_month`) - a recognized
invoice line or credit note in a reportable month.

| Column | Description |
|--------|-------------|
| `revenue_month` | `YYYY-MM` |
| `source_type` | `invoice_line` or `credit_note` |
| `source_id` | `invoice_line_id` or `credit_note_id` |
| `invoice_id`, `billing_account_id` | from billing |
| `account_id` | canonical customer account |
| `account_name`, `segment`, `region` | canonical account attributes |
| `currency`, `amount_local` | document currency amount recognized in the month (credit notes negative), unrounded |
| `fx_usd_per_unit`, `amount_usd` | conversion and USD amount, unrounded |

### `rpt_monthly_recognized_revenue`
Grain: one row per `revenue_month`. Columns `gross_recognized_usd` (invoice lines),
`credit_notes_usd`, `recognized_revenue_usd` (sum of both). Rounded to cents.

### `rpt_account_monthly_revenue`
Grain: one row per (`revenue_month`, `account_id`). Columns `account_name`,
`segment`, `region`, `recognized_revenue_usd`.

### `rpt_segment_monthly_revenue`
Grain: one row per (`revenue_month`, `segment`). Column `recognized_revenue_usd`.

## Dashboard extracts (`reports/exec_dashboard/`)

| File | Grain | Columns |
|------|-------|---------|
| `recognized_revenue_by_month.csv` | revenue_month | revenue_month, recognized_revenue_usd, mom_change_pct |
| `recognized_revenue_by_segment.csv` | (revenue_month, segment) | revenue_month, segment, recognized_revenue_usd |
| `top_accounts_latest_period.csv` | account (latest month, top 25) | revenue_month, account_id, account_name, segment, region, recognized_revenue_usd |
