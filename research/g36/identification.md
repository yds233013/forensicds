# G36 identification

## The target quantity

```
Q = E[ peak-window load per household , next summer , EVERY household on the TOU tariff ,
        at the forecast weather for that summer ]
```

and the decision `procure` iff `Q >= 2.900 kW`.

This is a **forecast**, not an effect. It requires a causal ingredient but its value is an
operational level.

## Why it is identified from what the analyst can see

Decompose the target into a stable and an unstable part.

```
Q  =  SUM_s  p_s  *  E_d[ L_s(cdd_d) * ( 1 - r_s(cdd_d) ) ]
```

| symbol | what it is | where it comes from |
|---|---|---|
| `p_s` | population share of segment `s` | the customer master, fully observed |
| `L_s(cdd)` | flat-tariff load response to weather | **three summers of history**, all households, no tariff in force |
| `r_s(cdd)` | peak reduction under TOU | **the randomised pilot**, which assigns TOU inside the opt-in group |
| `cdd_d` | target-summer weather | the published seasonal forecast, given to the analyst |

Each ingredient is observable. Nothing requires the target summer's outcomes.

### The randomisation that makes `r_s` causal

The pilot is **voluntary to enter and randomised once inside**. Opt-in is self-selected, so the
opt-in group is not the population - but within that group, TOU and control are exchangeable.
Therefore `r_s` is identified **for each segment represented in the pilot**, which is what the
transport step then needs.

This is the honest version of a real utility trial, and it is why the task is identifiable at all:
if the pilot were observational, `r_s` would be confounded with whoever chose to enrol and the
target would not be identified.

## Assumptions, and how the analyst checks each

| | assumption | evidence available |
|---|---|---|
| **A1** | weather -> load is unchanged by the tariff | physics; testable on the pilot's *control* arm against history |
| **A2** | TOU assignment is random inside the opt-in group | the pilot enrolment log; covariate balance inside opt-in is checkable |
| **A3** | segment membership captures the effect modification | pilot heterogeneity by segment is directly estimable |
| **A4** | every population segment appears in the pilot (positivity) | countable in the enrolment log |
| **A5** | the response curve in CDD extrapolates over the observed pilot range | the pilot summer spans a range of CDD; the curve is fitted, not assumed |

## Where identification would fail

- **No control arm in the pilot.** `r_s` would be confounded by who enrolled. The design has one.
- **A segment absent from the pilot.** `r_s` unidentified there; the honest answer becomes partial.
  Positivity holds by construction and is checkable.
- **Target weather far outside the pilot's CDD range.** The curve would be extrapolated rather than
  interpolated. The pilot summer's CDD range overlaps the target's; this is a design requirement,
  not an accident, and it must be preserved in any implementation.
- **A tariff that changed the weather response itself.** Then A1 fails and nothing from history
  transports. The generator does not do this, and the task documents must say so rather than leave
  the analyst to assume it.

## The ambiguity test

Two competent analysts cannot reach different decisions because the estimand is vague: the contract
names the object in business language ("peak load next summer once every household is on the
tariff"), the gate is numeric, and the three valid routes measured in simulation agree to **0.000**
(they are algebraically identical rearrangements) with a sampling sd of 0.014 against decision
margins of 3.5-14.9 sd.
