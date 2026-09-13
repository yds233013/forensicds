-- arr_boundaries: ARR of each account at the start and at the end of each reporting quarter.
-- Grain: one row per (quarter, account) for accounts with a recurring line overlapping [start_date, end_date].
-- ARR at a date D (USD, to the cent) sums lines with start_date <= D < end_date; quarter-end ARR is ARR on end_date (first day of next quarter).
DROP TABLE IF EXISTS arr_boundaries;
CREATE TABLE arr_boundaries AS
SELECT q.quarter, q.start_date, q.end_date, l.account_id,
       ROUND(SUM(CASE WHEN l.start_date <= q.start_date AND q.start_date < l.end_date THEN l.arr_usd ELSE 0 END), 2) AS start_arr,
       ROUND(SUM(CASE WHEN l.start_date <= q.end_date AND q.end_date < l.end_date THEN l.arr_usd ELSE 0 END), 2) AS end_arr
FROM dim_quarters q
JOIN stg_recurring_lines l ON l.start_date <= q.end_date AND l.end_date > q.start_date
GROUP BY q.quarter, q.start_date, q.end_date, l.account_id;
