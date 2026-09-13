# Experimentation platform - assignment and exposure

Owner: Experimentation Platform.

## Assignment

- Server-side, deterministic hashing of the unit id with the experiment salt. Workspace experiments assign a
  workspace when its owner first reaches the dashboard (onboarding start); user experiments assign users at signup.
- The service assigns every new unit matching the experiment's platform filter; plan-level eligibility is applied in
  analysis. For XP-231 the filter is "new workspace", so sales-assisted workspaces are assigned too.
- `xp_assignments` logs every assignment write. A unit can have several rows: SDK retries write duplicates, and
  cache incidents can write re-assignment rows (see `docs/ops/`). A unit's assignment is its first logged row;
  later rows do not change the unit's analysis arm.
- `stratum` is computed at assignment from workspace attributes and logged with the assignment.

## Exposure logging

- Exposures are logged by the web client SDK (`logExposure`) from the component that renders the experience, one
  event per user per page load that renders it, with the workspace in context.
- The SDK caches the variant for a user for the browser session; users who switch between workspaces keep the
  cached variant until they reload (XPP-44, open).
- Exposure events are for debugging and triggered analyses; they are not an assignment record.
