# Courier dispatch runbook (extract)

## The dispatch pool

Couriers sign on to **one city for one service date**. The dispatcher assigns that day's orders in
that city from that pool of signed-on couriers. **Couriers are never dispatched across a city
boundary, and a courier's shift does not span service dates.** The set of orders competing for a
given courier is therefore exactly the set of orders in the same city on the same date.

Courier supply on a given day is whatever signed on. The dispatcher cannot create couriers; it can
only decide the order in which waiting orders are matched to the couriers that exist.

## How orders are matched

The dispatcher maintains a weighted queue. Each merchant's share of available courier minutes is
proportional to its order volume multiplied by its **dispatch weight**. Under the standard
configuration every merchant carries weight 1.

**Priority Dispatch** raises a merchant's dispatch weight while it is active. A merchant with a raised
weight receives a larger share of the same pool of courier minutes.

## What Priority Dispatch does and does not change

- It **does** change the order in which waiting orders are matched.
- It **does** include a revised routing heuristic that reduces courier idle time between drops.
- It **does not** add couriers, extend shifts, or change courier pay.
- It **does not** change how many orders customers place.

## Unfulfilled orders

An order that cannot be matched before the merchant's cutoff is cancelled and recorded as requested
but not delivered. `orders_requested` counts what customers placed; `orders_delivered` counts what
was completed.
