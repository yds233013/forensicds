# G41 — weekly spare-parts rebalance (service parts rebalancing)

A field-service network decides each Monday whether next week's spare-parts shortfall crosses the
contractual expedite threshold of 40 job units. The published planner reports no shortfall at all and
recommends no expedite; the minimum achievable shortfall is 46 units, so the recommendation is wrong.

The planner's arithmetic is right and its feasible set is wrong. It nets demand against every unit the
extract shows, while the availability policy excludes QA-held and consignment stock, units reserved by
open allocations, cancelled purchase orders, receipts not yet put away, safety stock that may not be
shipped, and transfers that cannot land before the job's need-by date. Imposing those constraints
first turns the week into a genuine constrained optimisation — minimum unmet units, then minimum
transfer cost among the plans achieving it — which no longer decomposes by depot or by part.

Design, wrong-object panel and gate record: `research/g41/`.
