# CRM v3 migration - consumer notes

Data Platform / CRM team, 2026-01-05 (updated 2026-02-02)

CRM v3 went live on **2026-01-12**. Opportunity and Customer Success health data is now served from the
v3 objects `crm_opportunities` and `cs_account_health`, which replace the v2 opportunity and health
tables.

- The daily snapshot jobs (`crm_opportunity_daily_snapshot`, `cs_health_daily_snapshot`) stop on
  2026-01-31 and the tables are dropped (storage cost was ~40% of the CRM schema). Snapshot data is
  not migrated.
- The field audit tables are renamed `crm_opportunity_field_history` and `cs_account_health_history`
  (used by RevOps forecast-change reporting); their contents are unchanged.
- All CRM v3 tables are fed by the existing connectors (see the warehouse data dictionary).
- Consumers must move off the snapshot tables before 2026-01-31. Known consumers: pipeline dashboard
  (BI-201), renewal forecast (RevOps), renewal-risk model (RA-DS-298), territory planning (SOPS-118).

Questions: #data-platform
