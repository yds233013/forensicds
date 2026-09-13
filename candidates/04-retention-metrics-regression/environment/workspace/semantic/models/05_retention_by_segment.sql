-- retention_by_segment: retention metrics per quarter and customer segment.
-- Grain: one row per (quarter, segment).
DROP TABLE IF EXISTS retention_by_segment;
CREATE TABLE retention_by_segment AS
SELECT quarter,
       segment,
       SUM(in_cohort) AS cohort_customers,
       SUM(CASE WHEN in_cohort = 1 THEN start_arr ELSE 0 END) AS starting_arr,
       SUM(CASE WHEN in_cohort = 1 THEN end_arr ELSE 0 END) AS cohort_ending_arr,
       SUM(CASE WHEN in_cohort = 1 THEN end_arr ELSE 0 END) / NULLIF(SUM(CASE WHEN in_cohort = 1 THEN start_arr ELSE 0 END), 0) AS nrr,
       SUM(CASE WHEN in_cohort = 1 THEN MIN(start_arr, end_arr) ELSE 0 END)
         / NULLIF(SUM(CASE WHEN in_cohort = 1 THEN start_arr ELSE 0 END), 0) AS grr,
       SUM(CASE WHEN in_cohort = 1 AND movement = 'churned' THEN 1 ELSE 0 END) AS churned_customers,
       1.0 * SUM(CASE WHEN in_cohort = 1 AND movement = 'churned' THEN 1 ELSE 0 END) / NULLIF(SUM(in_cohort), 0) AS logo_churn_rate
FROM customer_quarter
WHERE in_cohort = 1
GROUP BY quarter, segment;
