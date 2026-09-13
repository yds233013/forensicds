-- retention_quarterly: board retention metrics and ARR bridge per reporting quarter.
-- Grain: one row per quarter.
DROP TABLE IF EXISTS retention_quarterly;
CREATE TABLE retention_quarterly AS
SELECT quarter,
       SUM(in_cohort) AS cohort_customers,
       SUM(CASE WHEN in_cohort = 1 THEN start_arr ELSE 0 END) AS starting_arr,
       SUM(CASE WHEN in_cohort = 1 THEN end_arr ELSE 0 END) AS cohort_ending_arr,
       SUM(CASE WHEN in_cohort = 1 THEN end_arr ELSE 0 END) / SUM(CASE WHEN in_cohort = 1 THEN start_arr ELSE 0 END) AS nrr,
       SUM(CASE WHEN in_cohort = 1 THEN MIN(start_arr, end_arr) ELSE 0 END)
         / SUM(CASE WHEN in_cohort = 1 THEN start_arr ELSE 0 END) AS grr,
       SUM(CASE WHEN in_cohort = 1 AND movement = 'churned' THEN 1 ELSE 0 END) AS churned_customers,
       1.0 * SUM(CASE WHEN in_cohort = 1 AND movement = 'churned' THEN 1 ELSE 0 END) / SUM(in_cohort) AS logo_churn_rate,
       SUM(CASE WHEN movement = 'new' THEN end_arr ELSE 0 END) AS new_arr,
       SUM(CASE WHEN movement = 'reactivated' THEN end_arr ELSE 0 END) AS reactivated_arr,
       SUM(CASE WHEN in_cohort = 1 AND end_arr > start_arr THEN end_arr - start_arr ELSE 0 END) AS expansion_arr,
       SUM(CASE WHEN in_cohort = 1 AND end_arr > 0 AND end_arr < start_arr THEN start_arr - end_arr ELSE 0 END) AS contraction_arr,
       SUM(CASE WHEN in_cohort = 1 AND end_arr = 0 THEN start_arr ELSE 0 END) AS churned_arr,
       SUM(end_arr) AS ending_arr,
       SUM(CASE WHEN movement = 'new' THEN 1 ELSE 0 END) AS new_customers,
       SUM(CASE WHEN movement = 'reactivated' THEN 1 ELSE 0 END) AS reactivated_customers
FROM customer_quarter
GROUP BY quarter;
