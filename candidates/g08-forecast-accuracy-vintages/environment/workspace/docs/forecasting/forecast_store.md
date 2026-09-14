# Forecast store

Every forecast issued by every model is kept in `forecast_issues` (one row per issue) and `forecast_values` (one row
per issue, region, portfolio and delivery day).

- `issue_kind`:
  - `scheduled`: the 06:00 UK run;
  - `reissue`: a manual or data-refresh re-run;
  - `auto_reissue`: v4's automatic re-run after the 06Z weather model lands (usually shortly after midday UK).
- `scope_region`: NULL when the issue covers every region; otherwise the single region it was re-run for. An issue
  scoped to one region has values for that region only and replaces that region's earlier forecasts; the other
  regions keep theirs.
- An issue contains values for the run day's horizons (currently D+1 to D+7). Portfolios are those defined for each delivery
  day (`portfolio_membership`).
- Issues are never deleted or updated.
