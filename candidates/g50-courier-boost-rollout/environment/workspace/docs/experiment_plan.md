# Boost experiment plan (EXP-BOOST-01)

## Phase 1 — soak

Boost was enabled for **every eligible order** in the phase-1 "on" markets for four weeks. Sixteen markets
were enrolled in the programme; the phase-1 on/off split was drawn by coin flip over the enrolled markets
before the phase opened, eight on and eight off. Four further markets were never enrolled in the programme
at any phase.

Phase 1 was scheduled to confirm that the guarantee did not create payout or fraud incidents. It closed on
schedule with no incidents raised (`ops_events`).

## Phase 2 — order-randomised

From the phase-2 start date the dispatcher attached Boost to an individual eligible order with the
configured probability, drawn independently per order. `experiment_config.boost_share_target` records the
configured probability for each market-week; `experiment_assignment.arm` records what each order actually
got. The probability was raised once, after the earnings-volatility review, on the date in `ops_events`.

The four never-enrolled markets remained off Boost throughout phase 2 and carry no assignment rows.

## Eligibility and exclusions

Scheduled-ahead and corporate-account orders are not eligible for Boost. They carry
`order_channel` other than `standard`, and in phase 2 they are also recorded with `arm = 'excluded'`.

## Balance

`market_week_baseline` holds market-week orders, late orders and median delivery time for the four weeks
before phase 1. Markets differ persistently in their delivery performance for reasons that predate the
programme — road network, restaurant density, courier mix — so these weeks are the reference for what each
market looked like before anything changed.
