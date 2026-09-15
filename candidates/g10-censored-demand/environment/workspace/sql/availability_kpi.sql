-- Store operations availability KPI: share of trading store-SKU-days with no out-of-stock during trading hours,
-- by week and LEAN-26 arm.
SELECT substr(i.date, 1, 4) || '-W' || strftime('%W', i.date) AS week,
       p.arm,
       COUNT(*) AS store_sku_days,
       1.0 - AVG(CASE WHEN i.on_hand_open = 0 OR EXISTS (
                   SELECT 1 FROM availability_events e
                   WHERE e.store_id = i.store_id AND e.sku_id = i.sku_id AND e.event_type = 'out_of_stock'
                     AND substr(e.event_time, 1, 10) = i.date
                     AND substr(e.event_time, 12, 5) >= c.open_time AND substr(e.event_time, 12, 5) < c.close_time)
                 THEN 1.0 ELSE 0.0 END) AS in_stock_rate
FROM inventory_daily i
JOIN store_calendar c ON c.store_id = i.store_id AND c.date = i.date AND c.status = 'open'
JOIN programme_assignment p ON p.store_id = i.store_id
GROUP BY week, p.arm
ORDER BY week, p.arm;
