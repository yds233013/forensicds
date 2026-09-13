# Activation metrics

Owner: Product Analytics.

A **core action** is a `product_events` row with `event_type = 'core_action'` (creating and sharing a board,
running a first automation, or connecting a data source). Events carry the workspace they happened in.

| Metric | Definition | Used by |
|--------|------------|---------|
| Workspace activation (14d) | a workspace is activated if at least 3 distinct users perform a core action in that workspace within 14 days of the reference time `T`: `T <= event_at < T + 14 days` | onboarding experiments, team-growth dashboard |
| User activation (14d) | a user performs at least one core action within 14 days of `T` | growth accounting |

For experiments the reference time is defined by the experiment plan.
