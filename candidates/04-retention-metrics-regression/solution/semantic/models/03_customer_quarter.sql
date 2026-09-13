-- customer_quarter: lifecycle of each account in each reporting quarter.
-- Grain: one row per (quarter, account) for accounts with ARR at the start or at the end of the quarter.
--
-- The retention cohort of a quarter is the set of customers at the start of the quarter: accounts with ARR on
-- start_date. An account's CRM record can exist long before it becomes a customer (Sales Ops creates target and
-- prospect accounts ahead of any contract), so CRM creation dates say nothing about customer status.
-- Accounts without ARR at the start but with ARR at the end are reactivated if they held ARR on any earlier day,
-- otherwise new. Segments are assigned from starting ARR and exist only for cohort customers.
DROP TABLE IF EXISTS customer_quarter;
CREATE TABLE customer_quarter AS
SELECT b.quarter,
       b.account_id,
       b.start_arr,
       b.end_arr,
       CASE
         WHEN b.start_arr > 0 AND b.end_arr = 0 THEN 'churned'
         WHEN b.start_arr > 0 AND b.end_arr > b.start_arr THEN 'expanded'
         WHEN b.start_arr > 0 AND b.end_arr < b.start_arr THEN 'contracted'
         WHEN b.start_arr > 0 THEN 'retained'
         WHEN EXISTS (SELECT 1 FROM stg_recurring_lines l
                      WHERE l.account_id = b.account_id AND l.start_date < b.start_date) THEN 'reactivated'
         ELSE 'new'
       END AS movement,
       CASE WHEN b.start_arr > 0 THEN 1 ELSE 0 END AS in_cohort,
       CASE
         WHEN b.start_arr <= 0 THEN NULL
         WHEN b.start_arr < 25000 THEN 'SMB'
         WHEN b.start_arr < 100000 THEN 'Mid-Market'
         ELSE 'Enterprise'
       END AS segment
FROM arr_boundaries b
WHERE b.start_arr > 0 OR b.end_arr > 0;
