# G34 REDESIGN — event process and estimands

> **The original G34 design is preserved in `event_process.md`, `simulation_results.md`,
> `adversarial_review.md` and `build_recommendation.md` and remains REJECTED.** Its findings stand:
> the domain was realistic; left truncation produced only 7–10% bias; informative condition-based
> overhaul destroyed identification; the separation came from timestamp/status semantics, which is
> Task 02 / G08 ground. It must not be built. The two instrument bugs found during it (impossible
> `exit < entry` records; discrete-time bias from mid-interval censoring) are development history,
> not benchmark findings.

## Redesigned incident

> **From:** Director of Reliability & Aftermarket, industrial pump manufacturer
> **To:** Reliability Analytics
>
> Aftermarket has to commit next year's spare-assembly build and field-service headcount. Their
> planning model says 55% of the installed base will need an unplanned assembly replacement inside
> 36 months, so they want to double the spares pool. Operations says we replace most assemblies on
> the 24-month overhaul before they ever fail, and that 55% is not a number we will ever actually
> pay for. Separately, Engineering wants to know what the failure risk *would* be if we deferred
> overhauls — that is a different question and I do not want the two mixed up.

The two numbers in dispute are a **crude risk** and a **net risk** computed from the same event
history. The 55% is 1 − KM; it is the right answer to Engineering's question and the wrong answer to
Aftermarket's.

## Observational unit, origin, horizon

Unit = one installed pump with its original critical assembly. Time origin = **age since
commissioning**. Horizon **H = 36 months**.

## Event roles — the reconstruction problem

Six operational codes, four statistical roles, and the role of two of them **depends on which
question is being answered**:

| Code | Operational meaning | Role for **Q1 (crude)** | Role for **Q2 (net)** |
|---|---|---|---|
| `UNPL_FAIL` | unplanned assembly failure | **target event** | **target event** |
| `PM_OVHL` | scheduled overhaul; the assembly is replaced | **competing event** | censoring |
| `ASSET_RET` | unit permanently retired from the fleet | **competing event** | censoring |
| `SITE_XFER` | unit moved to another facility, same serial, same assembly | **not an exit** | **not an exit** |
| `TELEM_GAP` | telemetry lost; unit still running, still in the work-order system | **not an exit** | **not an exit** |
| `EXTRACT_END` | data cut-off | censoring | censoring |

No code names a statistical role. Each role is supported by an operational fact (audit in
`representation_leakage_redesign.md`).

## State machine

```
   commissioned (age 0)
          │
          ▼
    ┌── AT RISK, original assembly ──────────────────────────────┐
    │        │                                                    │
    │        ├── SITE_XFER  ─┐  same serial, same assembly ───────┤ (stays at risk)
    │        ├── TELEM_GAP  ─┘  still in the work-order system ───┤ (stays at risk)
    │        │                                                    │
    │        ├── UNPL_FAIL ───────────► TARGET EVENT              │
    │        ├── PM_OVHL   ───────────► assembly replaced         │  Q1: competing
    │        ├── ASSET_RET ───────────► unit leaves the fleet     │  Q1: competing
    │        └── EXTRACT_END ─────────► observation ends          │  censoring
    └────────────────────────────────────────────────────────────┘
```

## The two estimands, written exactly

```
Q1  crude cumulative incidence, current policy
    q1 = P( T_fail <= 36  AND  T_fail < T_overhaul  AND  T_fail < T_retire )

Q2  net risk, assemblies run to failure
    q2 = P( T_fail <= 36 )

business gate: stock the enlarged spares pool iff q1 > 0.28
```

**Counterfactual-object check.** Q1 is a directly observed current-policy probability — a
cause-specific cumulative incidence, no counterfactual. Q2 is a net probability under elimination
of the competing events; it is a hypothetical quantity and is identified **only** because the
overhaul and retirement policies are age-based and condition-independent (I2, I3). Both are graded
numerically because both are identified; verified against latent truth in
`redesign_simulation_results.md` §R1.

## Identification assumptions and their evidence

| | Assumption | Evidence available to an analyst |
|---|---|---|
| I1 | terminal event times logged at the correct date | work-order timestamps |
| I2 | overhaul is scheduled on age, not condition | maintenance SOP states the 24-month interval; checkable by regressing overhaul age on pre-overhaul condition indicators |
| I3 | retirement is driven by fleet economics, not unit condition | asset-register retirement reasons; checkable the same way |
| I4 | a transfer or telemetry gap does not end exposure | asset history shows the same serial still in service; no removal work order exists |
| I5 | extract cut-off is independent of unit state | extract metadata |

I2 and I3 are load-bearing **for Q2 only**. Q1 needs neither — it is identified from the observed
competing-risks process whatever drives the competing events. That asymmetry is itself a thing a
competent analyst should notice, and it is why Q1 is the safer number for a planning decision.
