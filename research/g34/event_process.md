# G34 event process, estimand and identification

## Observational unit
One installed rotating-equipment unit (pump/compressor) in the fleet.

## Time origin
**Age since commissioning**, from the asset register. The monitoring feed carries calendar
timestamps only, so the age clock must be reconstructed by joining the two.

## Event-state machine

```
                 commissioned (age 0)
                        │
                        │  (not observable until the monitoring platform goes live)
                        ▼
      ┌──── monitoring go-live: DELAYED ENTRY at current age ────┐
      │                                                          │
      ▼                                                          │
   AT RISK ──── unplanned_failure ───────────► TARGET EVENT      │
      │                                                          │
      ├──────── planned_overhaul ────────────► removal (age-based policy)
      ├──────── site_decommission ───────────► removal (calendar-driven)
      ├──────── sensor_dropout ──────────────► NOT a removal; unit stays at risk
      └──────── study end ───────────────────► administrative censoring
```

The four removal reasons do **not** map one-to-one onto statistical categories, and that mapping
is the operational work: `sensor_dropout` is not an exit at all, and whether `planned_overhaul` is
censoring or a competing event depends on which estimand is being targeted (§4).

## Estimand as designed (net risk)

```
P( T_fail ≤ 30 | T_fail > 18 )        over the fleet population
gate: extend the overhaul interval 18 → 30 months iff this is below 0.30
```

Under age-based, condition-independent overhaul, planned overhaul is independent censoring, so the
net risk is identified and left-truncated Kaplan-Meier is consistent. Verified: bias +0.1% to
+0.3%, sd 2.3% at 30,000 units.

## Identification assumptions

| | Assumption | Evidence available to an analyst |
|---|---|---|
| I1 | entry age is independent of failure time given age | commissioning dates are in the asset register and unrelated to condition; checkable by comparing entry-age and failure-age distributions |
| I2 | planned overhaul is scheduled on age, not on condition | the maintenance policy document states the interval; checkable by regressing overhaul age on pre-overhaul condition indicators |
| I3 | site decommission is calendar-driven, unrelated to unit age | site closure notices carry dates and reasons |
| I4 | a sensor gap does not remove the unit from service | the work-order system shows no removal record |
| I5 | event times are logged at the correct calendar date | work-order timestamps |

**I2 is load-bearing and was tested by breaking it.** When overhaul is condition-based (pre-empting
half of impending failures), every estimator including the correct one is off by ~80%, because the
net risk stops being identified. A design that wants condition-based maintenance must abandon the
net estimand — recorded in `simulation_results.md` §1.

## Estimand variant (crude risk) — the redesign candidate

```
CIF_fail(30) = P( T_fail ≤ 30 AND T_fail < T_overhaul )
```

Cause-specific cumulative incidence under the **current** policy: the fraction of units that
actually suffer an unplanned failure before their scheduled overhaul. Identified with no extra
assumption beyond observing the competing event. Drives spares stocking and unplanned-downtime
budgeting — a different decision from interval extension, and the distinction is the point.
