-- Accuracy mart examples (Data Platform, July 2026).
-- Latest forecast issued for each run, mapped to settlement classes through the governed portfolio dimension, and
-- scored against the latest settled volume for the delivery day.
SELECT f.model,
       f.run_date,
       f.issue_id,
       f.region,
       f.portfolio,
       f.target_date,
       CAST(julianday(f.target_date) - julianday(f.run_date) AS INTEGER) AS horizon,
       f.mwh                                  AS forecast_mwh,
       SUM(s.mwh)                             AS actual_mwh,
       GROUP_CONCAT(s.run_id, ';')            AS actual_run_ids
FROM forecast_latest f
JOIN dim_portfolio p
  ON p.portfolio = f.portfolio
JOIN settled_volumes_latest s
  ON s.region = f.region
 AND s.settlement_class = p.settlement_class
 AND s.delivery_date = f.target_date
GROUP BY f.model, f.run_date, f.issue_id, f.region, f.portfolio, f.target_date, f.mwh
