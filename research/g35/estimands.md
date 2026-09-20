# G35 estimands

Defined before any wrong method was written.

## The business incident

> **From:** VP Marketplace Operations
> **To:** Experimentation
> **Re:** FY27 commitment on Priority Dispatch
>
> The Priority Dispatch pilot readout says treated stores fulfil **+19.4 points** more of their demand.
> Merchant Growth want to ship it to the whole estate and have written the FY27 plan on that number.
> Courier Ops do not accept it: we have a fixed number of couriers signed on in a city on a given day,
> and they think we have simply moved couriers from the stores that were not in the test to the stores
> that were. If they are right, shipping it to everyone changes nothing.
> I need the expected effect **after full rollout**, and the launch call that follows.

The gate: **launch iff the full-rollout effect on fulfilment is at least +1.5 points.**

## The graded quantities

Three statistical objects, all computable from the same experiment, all scientifically distinct.

### Q1 - policy effect at full rollout  (the decision object)

```
tau_policy = E[ Y_i(1, G=1) ] - E[ Y_i(0, G=0) ]          demand-weighted over all merchants
```

The contrast between a world where the feature is available to everybody and the status quo.  This is
an **ITT** contrast: adoption is imperfect and deployment would inherit exactly that imperfection, so
"offered to all" is the right treatment, not "used by all".

### Q2 - direct effect at 50% saturation  (the dashboard object)

```
tau_direct(0.5) = E[ Y_i(1, G~0.5) | i treated ] - E[ Y_i(0, G~0.5) | i control ]
```

What a within-experiment treated-versus-control comparison measures in the half-saturated blocks.  It
is a real quantity, correctly estimated by the naive comparison, and **it is not the deployment
effect**.

### Q3 - spillover on untreated merchants at 50% saturation

```
spillover(0.5) = E[ Y_i(0, G~0.5) ] - E[ Y_i(0, G=0) ]
```

How much untreated merchants are harmed by their neighbours' treatment.  Negative whenever couriers
are scarce.  This is the quantity that makes the interference visible rather than merely asserted.

### Q4 - the decision

`launch` iff `tau_policy >= 0.015`, else `hold`.

## Measured magnitudes (simulation, fulfilment-rate points)

| regime | Q1 tau_policy | Q2 direct(0.5) | Q3 spillover(0.5) | Q4 |
|---|---|---|---|---|
| visible | **0.0434** | 0.3329 | -0.1422 | launch |
| hidden_a_tight_hollow | **0.0062** | 0.5056 | -0.2444 | hold |
| hidden_b_slack | **0.0063** | 0.0193 | -0.0061 | hold |
| hidden_c_tight_real | **0.0585** | 0.4499 | -0.1913 | launch |

The three objects differ by up to **two orders of magnitude** inside one regime (`hidden_a`: 0.006 vs
0.506 vs -0.244).  An analysis that confuses them does not miss by a little.

## Why three objects and not just the decision

G34's baseline settled this.  Its failing trial produced probabilities summing to exactly 1.0 and a
confident narrative while using the wrong risk set; only the numeric comparisons caught it.  Grading
Q1 alone would let an agent reach the right launch call from the wrong effect size - the brief's
own failure mode 16, and observed in G34 trial 2.  Grading Q2 and Q3 as well forces the agent to keep
the objects apart, which is the actual capability under test.

## Deliberately NOT graded

- **Any effect at a saturation outside `{0, .25, .5, .75, 1}`.**  The design does not identify it.
- **The effect under a *targeted* rollout** (e.g. "the largest 40% of merchants").  The experiment
  randomises uniformly within block, so it identifies effects of *random* saturation only.  Asking for
  a targeted-rollout effect would require an unidentified extrapolation, which the brief forbids.
- **Per-merchant treatment effects.**  Not identified and not needed.
