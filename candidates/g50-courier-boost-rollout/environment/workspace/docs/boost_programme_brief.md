# Boost — programme brief

**What it is.** Boost attaches a guaranteed minimum payout to an individual delivery offer. A courier who
accepts a Boost offer is paid at least the guaranteed floor for that delivery regardless of distance or
waiting time. Unboosted offers are paid on the standard distance-and-time formula.

**Why Operations proposed it.** Couriers deliberate over marginal offers, particularly in the evening peak.
Deliberation shows up as acceptance latency, and acceptance latency is the part of the delivery clock the
platform controls. The programme hypothesis is that removing payout uncertainty from the offer shortens
acceptance latency and therefore reduces late deliveries.

**What it costs.** The guarantee only binds on offers whose standard payout would have fallen below the
floor. Realised incentive spend per boosted order is recorded in `incentive_ledger`.

**What it does not change.** Boost does not change the promise window shown to the customer, the courier
pay formula for unboosted offers, restaurant preparation, or the dispatch radius.
