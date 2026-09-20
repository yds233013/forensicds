# G35 identification

## Claim

`tau_policy`, `tau_direct(0.5)` and `spillover(0.5)` are all identified by the two-stage randomised
saturation design, with no extrapolation beyond the arms that exist.

## The argument

Saturation `pi_b` is assigned to blocks by an independent randomisation.  Therefore the set of blocks
with `pi_b = 1` and the set with `pi_b = 0` are exchangeable: they differ only in the treatment regime
applied to them.

```
E[ Y(1, G=1) ]  =  E[ block fulfilment | pi_b = 1 ]
E[ Y(0, G=0) ]  =  E[ block fulfilment | pi_b = 0 ]
tau_policy      =  difference of the two, demand-weighted
```

No modelling assumption is used: this is a randomisation contrast between two arms that both exist in
the data.  `tau_direct(0.5)` and `spillover(0.5)` follow the same way from the `pi_b = 0.5` arm and the
`pi_b = 0` arm.

## Assumptions, and how an analyst checks each from the workspace

| | assumption | evidence available to the analyst |
|---|---|---|
| **A1** | Saturation is randomly assigned to blocks | the assignment log records the saturation drawn for every city-day before the day started; balance on pre-period fulfilment, block size, city and weekday is directly checkable |
| **A2** | Within a block, which merchants are treated is random | the same log records the assignment seed and the drawn merchant list; covariate balance within block is checkable |
| **A3** | The dispatch pool is the city-day | stated in the dispatch runbook: couriers sign on to a city for a day and are not dispatched across city boundaries |
| **A4** | No interference *between* blocks | follows from A3; testable by looking for effects of a city's saturation on a neighbouring city's outcomes |
| **A5** | Adoption is an outcome, not an input, to assignment | the log shows assignment timestamps preceding adoption timestamps |

A1-A2 are design facts recorded in an artefact.  A3 is an operational fact stated in a document.  A4 is
implied by A3 and is separately checkable.  **None of them requires the generator.**

## Where identification would fail, and why it does not here

- If only one saturation level existed, `tau_policy` would not be identified and the honest answer
  would be "the experiment cannot answer this".  The design includes `pi = 0` and `pi = 1` arms
  precisely so the question is answerable.
- If couriers were dispatched across city boundaries, A3 fails and the interference group is larger
  than the block.  The runbook rules this out, and the task must say so explicitly rather than let the
  analyst infer it.
- If saturation were assigned to blocks by an operational rule (say, tight markets get low saturation),
  A1 fails.  The log shows the draw, and balance is checkable.

## The ambiguity test

> Could two competent analysts reach different launch calls because the task under-specifies the
> estimand?

No.  The readout contract names the object in business language - "the effect on fulfilment once every
store has it" - and the gate is stated numerically.  They may reach slightly different **numbers**: the
four valid estimator families differ by at most **0.005** fulfilment points, while the distance from the
gate is at least **0.009** in every regime and the wrong analyses miss by **0.006 to 0.51**.

One genuine ambiguity is resolved in the task text rather than by the verifier: **ITT versus effect on
adopters.**  Deployment inherits imperfect adoption, so the contract states the object is the effect of
*making the feature available*, and that the comparison is on assigned saturation.
