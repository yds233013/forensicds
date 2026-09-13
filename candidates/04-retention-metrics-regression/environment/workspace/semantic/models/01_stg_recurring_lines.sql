-- stg_recurring_lines: recurring subscription lines that carry ARR.
-- Grain: one row per subscription line. One-time lines (onboarding, services) carry no ARR.
DROP TABLE IF EXISTS stg_recurring_lines;
CREATE TABLE stg_recurring_lines AS
SELECT line_id, contract_id, account_id, product, start_date, end_date, arr_usd
FROM src.subscription_lines
WHERE line_type = 'recurring' AND arr_usd > 0 AND end_date > start_date;
