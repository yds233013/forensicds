# Data dictionary

## Warehouse extract (`data/warehouse.db`)

| Table | Grain | Columns |
|-------|-------|---------|
| `crm_accounts` | one row per CRM account | `account_id`, `account_name`, `created_at` (CRM record creation), `source` (inbound / outbound / partner / abm_target_list), `industry`, `region` |
| `contracts` | one row per signed contract document | `contract_id`, `account_id`, `signed_at`, `contract_type` (Sales Ops category: new_business / renewal / upsell / downsell) |
| `subscription_lines` | one row per contract line | `line_id`, `contract_id`, `account_id`, `product`, `line_type` (recurring / one_time), `start_date` (inclusive), `end_date` (exclusive), `arr_usd` |
| `price_changes` | one row per price program | `program_id`, `effective_from`, `renewal_uplift` |

## Semantic layer (`analytics/analytics.db`)

| Table | Grain | Columns |
|-------|-------|---------|
| `dim_quarters` | one row per reporting quarter | `quarter` (YYYY-Qn), `start_date`, `end_date` (first day of next quarter) |
| `stg_recurring_lines` | one row per recurring line with ARR | line columns |
| `arr_boundaries` | one row per (quarter, account with a recurring line overlapping the quarter) | `quarter`, `start_date`, `end_date`, `account_id`, `start_arr`, `end_arr` |
| `customer_quarter` | one row per (quarter, account) with ARR on the quarter's start or end date | `quarter`, `account_id`, `start_arr`, `end_arr`, `movement` (new / reactivated / expanded / contracted / churned / retained), `in_cohort` (1 if the account is in the quarter's retention cohort, else 0), `segment` (SMB / Mid-Market / Enterprise for cohort accounts, else null) |
| `retention_quarterly` | one row per quarter | `quarter`, `cohort_customers`, `starting_arr`, `cohort_ending_arr`, `nrr`, `grr`, `churned_customers`, `logo_churn_rate`, `new_arr`, `reactivated_arr`, `expansion_arr`, `contraction_arr`, `churned_arr`, `ending_arr`, `new_customers`, `reactivated_customers` |
| `retention_by_segment` | one row per (quarter, segment) | `quarter`, `segment`, `cohort_customers`, `starting_arr`, `cohort_ending_arr`, `nrr`, `grr`, `churned_customers`, `logo_churn_rate` |

`nrr`, `grr` and `logo_churn_rate` are unrounded fractions (e.g. 0.9874), money columns are USD. `retention_by_segment`
has rows only for segments with at least one cohort customer in the quarter. `starting_arr` is the cohort's starting ARR (equal to all customers' ARR on S); `ending_arr` is all customers' ARR on E.
Board extracts in `reports/board/` are CSV copies of `retention_quarterly` and `retention_by_segment`.
