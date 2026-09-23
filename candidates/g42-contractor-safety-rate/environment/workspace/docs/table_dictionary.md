# Table dictionary - safety warehouse

| Table | Grain | Notes |
|---|---|---|
| `sites` | one row per site | `region`, `client` (the operator whose access requirement applies) |
| `workers` | one row per worker | `worker_type` is `EMPLOYEE` or `AGENCY`; `home_site_id` is the assignment of record, not where every shift is worked; `left_on` is null for current workers |
| `shift_entries` | one row per worker, day and site | `hours` is time booked; `hour_type` says whether it was worked; `scheduled_hours` is the roster figure |
| `incident_cases` | one row per injured person per event | `event_id` groups cases from one event; `occurred_on` and `recorded_on` differ; `site_id` is where the incident happened |
| `contract_terms` | key/value | reporting window, rate basis, rate limit, and the permitted values of the coded columns |
