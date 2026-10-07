# Boost — programme readout

**Prepared by** Marketplace Analytics · **For** Service Operations and Finance

## Headline

Boost reduces the late-delivery rate by **4.0 percentage points** (95 % CI 3.6 to 4.4 pp), measured over
120,671 eligible delivered orders in the sixteen enrolled markets across the six phase-2 weeks.

Against the break-even figure of 1.50 pp in the rollout memo, Boost clears the bar by a wide margin.

**Recommendation: roll out.**

## Method

Phase 2 randomised Boost per order, so the boost and control arms are directly comparable. We take the
late-delivery rate in each arm over the metric population and difference them, with a two-proportion 95 %
interval. Reproduce with `python -m northline_eval readout`.

## Checks

| check | result |
|---|---|
| Sample ratio, realised vs configured share, 96 market-weeks | max abs z = 2.09 — no mismatch |
| Pre-programme balance, enrolled vs never-enrolled markets | 14.55 % vs 15.30 % late — comparable |
| Per-market consistency, all 16 markets | every market negative, range −3.4 to −4.6 pp |
| Courier hours available per arm | boost 9.53 h, control 9.54 h, gap −0.08 % |

The courier-hours check is the one we were asked about most. Courier supply is the obvious thing that could
differ between the arms, and it does not: the two arms draw on the same courier hours to within a tenth of a
percent. **Capacity is therefore not confounding the comparison.**

## Control arm against the never-enrolled markets

The memo requires this alongside the headline. The phase-2 control arm ran at 17.26 % late against 14.82 % in
the four never-enrolled markets, a difference of +2.44 pp.

We do not read this as evidence about Boost. The never-enrolled markets were never part of the programme;
they were not drawn against the enrolled markets and they are not a control group. A difference in level
between two groups that were never randomised against each other is not an effect, and we would not report it
as one.

## Limitations

Six weeks of phase 2. We have not modelled courier-side effects beyond the capacity check above.
