# Dispatcher — offer queue

## How an order reaches a courier

When an order is ready to dispatch it enters the **offer queue** for its market and hour. The dispatcher
holds one queue per market-hour. Couriers who are online and not currently carrying a delivery are offered
the head of the queue.

Ordering within the queue: **a Boost offer is placed ahead of every unboosted offer in the same market-hour
queue.** Within the boosted group, and within the unboosted group, offers are ordered by readiness time.

A courier carries one delivery at a time. A courier who accepts an offer is unavailable until that delivery
completes, at which point they return to the front of the available pool.

`orders.accepted_after_sec` is the elapsed time from the order entering the queue to a courier accepting it.

## Dispatcher 4.11

The 4.11 release added offer-queue telemetry. It did not change queue ordering, the offer radius, or the
pay formula. See `ops_events`.
