# XP-231 - Onboarding checklist (pre-registration)

Owner: Growth (onboarding squad). Analyst: Product Analytics. Approved 2026-07-01.

## Hypothesis

A setup checklist on the dashboard of new workspaces helps teams get going: more new workspaces reach team
activation within their first two weeks.

## Design

- **Randomization unit:** workspace. The checklist is a workspace setting; every member of a workspace gets the
  same experience.
- **Assignment:** by the experimentation platform at onboarding start (the first time the workspace owner reaches
  the dashboard), 50/50, stratified by the platform's `stratum` for workspace experiments.
- **Eligible population:** workspaces created through self-serve signup. Sales-assisted workspaces get a guided
  onboarding and never see the checklist; internal test workspaces are excluded.
- **Primary metric:** workspace activation (14d) from the assignment time (`docs/metrics/activation.md`).
- **Guardrails:** none for this readout.
- **Power:** about 3,400 analyzable workspaces by 2026-09-01 at ~8% baseline activation; minimum detectable effect
  about 2.6 percentage points (80% power, two-sided 5%).

## Analysis

- Units are analyzed in the arm they were assigned to, whether or not their members saw the checklist.
- Readouts include every eligible workspace whose 14-day activation window has closed by the analysis date:
  `assigned_at + 14 days <= analysis date 00:00 UTC`.
- Estimator: stratified difference in activation rates, strata weighted by their share of analyzed workspaces,
  Neyman variance; 95% confidence interval (z = 1.96).
- Decision: **ship** if the CI lower bound is above 0, **rollback** if the upper bound is below 0, otherwise
  **inconclusive** (keep running or stop at the owner's discretion).
- Sample ratio check on analyzed units against the 50/50 allocation.

## Instrumentation

- Control: exposure logged by the dashboard when it loads.
- Treatment: exposure logged by the checklist component when it mounts.
- Readout runs weekly on Mondays from 2026-08-03; decision readout on 2026-09-01.
