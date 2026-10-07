# Warehouse — data dictionary

`data/northline.sqlite`, read-only.

## markets
`market_id` · `market_name` · `region` · `launched_on` · `zone_count`

## zones
`zone_id` · `market_id` — the market this zone belongs to · `zone_name`

## orders
`order_id` · `zone_id` · `placed_at` — local platform time ·
`order_channel` — `standard`, `scheduled` or `corporate`; only `standard` orders are Boost-eligible ·
`promised_minutes` — the promise shown to the customer · `accepted_after_sec` — seconds from queue entry to courier acceptance; null for cancelled orders ·
`delivered_after_min` — minutes from `placed_at` to delivery; null for cancelled orders ·
`status` — `delivered` or `cancelled`

## experiment_assignment
`order_id` · `experiment_id` · `arm` — `boost`, `control` or `excluded`. Rows exist only for orders placed in
an enrolled market during phase 2.

## courier_shifts
`shift_id` · `courier_id` · `market_id` · `shift_date` · `hour_start` — clock hour · `online_minutes`

## experiment_config
`experiment_id` · `market_id` · `week_start` · `phase` — `pre`, `phase1_soak`, `phase2_order_randomised` ·
`randomisation_unit` — `none`, `market`, `order` · `boost_share_target` — configured share of eligible orders
carrying Boost · `status` — `not_running`, `running`, `not_enrolled`, `holdout`

## market_week_baseline
`market_id` · `week_start` · `orders` · `late_orders` · `median_delivered_min`. Pre-programme weeks only.

## incentive_ledger
`market_id` · `week_start` · `boosted_orders` · `incentive_spend_gbp`

## ops_events
`event_id` · `event_date` · `market_id` — null when platform-wide · `event_type` · `note`
