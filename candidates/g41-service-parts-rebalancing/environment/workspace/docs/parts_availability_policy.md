# Parts availability and rebalancing policy (Field Service Operations)

## 1. What counts as available

A unit in a depot is **available to promise (ATP)** for next week's scheduled jobs only if all of the
following hold.

1. Its stock row is `AVAILABLE`. Units on a QA hold (`QUARANTINE`) cannot be issued; units held as
   `CONSIGNMENT` belong to the customer and are not ours to plan with.
2. It is not already reserved. An allocation row with `alloc_status = 'OPEN'` reserves units for a
   work order already in flight. Cancelled allocations reserve nothing.

## 2. Inbound receipts

A confirmed purchase order becomes usable **one day after its ETA** (`dock_to_stock_days` in
`extract_meta`): goods must be received, counted and put away before they can be issued. A cancelled
PO is not coming.

## 3. Safety stock

Each depot holds a contractual minimum (`safety_stock`) per part for emergency call-outs. Safety stock
**may be used for that depot's own scheduled jobs**, but it **may not be transferred out**: the
emergency cover has to stay where the contract puts it.

The retention is on the depot's on-hand holding: of the units a depot has available to promise on the
extract date, the first `min_units` stay put. Units that arrive during the week on an inbound receipt
are next week's cover, not this week's, and may be transferred once they are usable.

## 4. Transfers

Inter-depot transfers move on the lanes in `transfer_lanes`, at `cost_per_unit`, taking
`transit_days` calendar days. A transfer dispatched on the extract date helps a job only if it arrives
**on or before** that job's `need_by_date`. Units that only become usable later (an inbound receipt)
can still be transferred, but the transit clock starts when they are usable.

## 5. What the weekly plan has to answer

Two numbers go to the Service Director every Monday:

1. **the shortfall**: the smallest number of job units that cannot be covered next week, given the
   parts we actually have and the moves we could actually make;
2. **the cost of getting there**: the cheapest transfer plan that achieves that shortfall.

## 6. Expedite rule (service contract, unchanged since FY24)

> If the week's shortfall exceeds **40 job units**, Field Service raises an expedited air-freight
> purchase with the manufacturer. At or below 40 units the gap is absorbed by rescheduling.

Expediting is expensive and is audited, so the number it is based on has to be the real one.
