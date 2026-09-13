-- customer_quarter: lifecycle of each account in each reporting quarter.
-- Grain: one row per (quarter, account) for accounts with ARR at the start or at the end of the quarter.
DROP TABLE IF EXISTS customer_quarter;
CREATE TABLE customer_quarter AS
SELECT b.quarter,
       b.account_id,
       b.start_arr,
       b.end_arr,
       CASE
         WHEN a.created_at >= b.start_date THEN 'new'
         WHEN b.end_arr = 0 THEN 'churned'
         WHEN b.end_arr > b.start_arr THEN 'expanded'
         WHEN b.end_arr < b.start_arr THEN 'contracted'
         ELSE 'retained'
       END AS movement,
       CASE WHEN a.created_at < b.start_date THEN 1 ELSE 0 END AS in_cohort,
       CASE
         WHEN COALESCE(NULLIF(b.start_arr, 0), b.end_arr) < 25000 THEN 'SMB'
         WHEN COALESCE(NULLIF(b.start_arr, 0), b.end_arr) < 100000 THEN 'Mid-Market'
         ELSE 'Enterprise'
       END AS segment
FROM arr_boundaries b
JOIN src.crm_accounts a ON a.account_id = b.account_id
WHERE b.start_arr > 0 OR b.end_arr > 0;
