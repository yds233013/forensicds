# INC-1874 - CRM change stream paused

Status: resolved. Severity 2. Data Platform on-call.

- **2025-11-03 00:00 UTC**: the warehouse CRM connector stopped applying the change stream after a
  schema change in CRM (new picklist value). The CRM itself kept working normally.
- **2025-11-03 - 2025-11-17**: warehouse CRM tables and field history were stale. Pipeline dashboards
  showed no movement for two weeks.
- **2025-11-18 03:10 UTC**: connector fixed and the two-week backlog replayed into the warehouse.
- Follow-ups: schema-change alerting (DATA-871). The Q4 renewal-risk retrain was skipped.
