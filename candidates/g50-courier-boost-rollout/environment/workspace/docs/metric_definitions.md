# Metric definitions

## Late-delivery rate

An order is **late** when `delivered_after_min` exceeds `promised_minutes`. The late-delivery rate over any
set of orders is late orders divided by orders in that set.

**Population.** Only orders with `status = 'delivered'` enter the metric. Cancelled orders have no delivery
time and are excluded; they are not counted as late.

**Eligibility.** Programme reporting covers **Boost-eligible** orders only: `order_channel = 'standard'`.
Scheduled-ahead and corporate orders are never eligible for Boost, in any period, and are outside the
programme metric. `order_channel` is recorded on every order, including the weeks before the programme, so
the same population can be built for any period. This is the definition the service-level report and the
incentive ledger both use.

## Grain and calendar

The reporting grain for programme metrics is the **market-week**. Weeks start on Monday, 00:00, and are
labelled by that Monday's date — the same `week_start` convention used in `experiment_config`,
`market_week_baseline` and `incentive_ledger`. Order timestamps are local platform time with no offset
changes in the programme window.

## Market attribution

Orders carry `zone_id`, not `market_id`. A zone belongs to exactly one market for the whole programme
window; join `orders` to `zones` to attribute an order to a market.

## Courier hours

`courier_shifts` holds one row per courier per clock hour with the minutes that courier was online in that
hour. Courier hours for a market-hour are the sum of `online_minutes` over that market, date and hour,
divided by 60.
