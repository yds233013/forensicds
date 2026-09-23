# Weekly extract - table dictionary

## `stock_on_hand`
One row per lot in a depot. `stock_status` is one of `AVAILABLE`, `QUARANTINE` (on QA hold) or
`CONSIGNMENT` (customer-owned stock held at our depot).

## `allocations`
Reservations against stock for work orders already in flight. `alloc_status` is `OPEN` (the units are
committed and cannot be planned again) or `CANCELLED` (released; the units are free). These work
orders are **not** in `service_jobs`: they are already under way.

## `inbound_orders`
Purchase orders inbound to a depot. `eta_date` is the carrier's delivery date; `po_status` is
`CONFIRMED` or `CANCELLED`.

## `service_jobs`
Scheduled field-service jobs for the coming week, each needing `qty` units of one part at one depot by
`need_by_date`. `job_status` is `SCHEDULED` or `CANCELLED`.

## `transfer_lanes`
Directed lanes between depots, with `transit_days` (calendar days) and `cost_per_unit`.

## `safety_stock`
The contractual minimum units per depot and part (see the availability policy).

## `extract_meta`
`extract_date` is the day the extract was taken and the day any transfer would be dispatched.
`planning_horizon_days` is the length of the planning week. `dock_to_stock_days` is the put-away delay
on inbound receipts. The remaining keys list the status vocabularies.
