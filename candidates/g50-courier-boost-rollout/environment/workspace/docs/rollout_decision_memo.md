# Boost — rollout decision memo (Finance & Service Operations)

## The decision

The July investment committee will either approve Boost for **national rollout on every eligible order in
every market**, or decline it. There is no partial-rollout option on the table: the guarantee is a published
courier pay term and Operations will not run it in some markets and not others beyond the pilot.

## The quantity the decision is made on

The committee is deciding whether to turn Boost on for every eligible order in every enrolled market.
The number it needs is therefore:

> **The change in our estate-wide late-delivery rate — total late deliveries divided by total eligible
> deliveries across the enrolled markets — between running Boost on every eligible order and running it on
> none, under trading conditions like those of the programme period.**

Express it in percentage points, negative for an improvement.

Two points of definition, so that everyone is quoting the same number:

- **Estate-wide, not an average of markets.** A market doing ten times the volume matters ten times as much
  to the P&L and to the service-credit bill. Where a market-by-market figure has to be combined, weight each
  market by **its share of estate orders in the four weeks before the programme opened**. We fix the weights
  on the pre-programme mix on purpose: Boost could itself shift where orders land, and the weighting must not
  move with the thing being measured.
- **Trading conditions like the programme period.** This is the effect under conditions comparable to those
  we actually observed. Carrying it forward to a different season is a judgement for the committee, not part
  of the number.

## The threshold

Boost is only worth buying if the late deliveries it avoids are worth more than the incentive it pays.

- **Incentive cost.** Realised incentive spend per boosted order, from `incentive_ledger`, is £0.19.
- **Cost of a late delivery.** The service-credit schedule pays the customer £2.50. Retention analysis
  values the expected future margin lost on a late delivery at £10.20. Total **£12.70**.

Boost therefore pays for itself when it avoids more than `0.19 / 12.70` of a late delivery per order, i.e.
when the late-delivery rate falls by at least **1.4961 percentage points**.

**Decision rule.**

- `roll_out` — the estimated change is a reduction of at least the break-even figure above, **and** the 95 %
  interval on that estimate excludes zero.
- `do_not_roll_out` — otherwise.
