# G34 redesign — wrong-object tournament

Pre-registered before the gate was run. Only methods natural to this business process are included;
the brief's W6/W8/W10 (transfer-as-competing, extract-end-as-competing, wrong horizon) are folded
into C1/C6 rather than listed separately.

| Code | Wrong analysis | Why a competent analyst would do it | Wrong object | Measured bias | Decision consequence |
|---|---|---|---|---|---|
| **W1** | 1 − KM for Q1, treating overhaul and retirement as censoring | This is what every survival tutorial does, and it is the *right* answer to Engineering's question | targets the **net** risk when the business needs the **crude** risk | **+36% to +188%** (32–180 sd) | right decision in `visible`, wrong in `overhaul_heavy` |
| **W2** | AJ answer used for Engineering's question | Having correctly computed the crude risk, reuse it | targets the **crude** risk when the question is **net** | **−26% to −65%** (33–118 sd) | n/a (Q2 has no gate) |
| **W3** | raw failure fraction among all units | Simple, and it is "what actually happened" | ignores that follow-up is incomplete; no risk-set reasoning | **−17% to −25%** (11–24 sd) | wrong in `visible`, right in `overhaul_heavy` |
| **W4** | failure / (failure + overhaul) | A natural "share of removals" intuition | conditions on having had a terminal event; wrong denominator | +5.7% to +19.7% (3.6–19 sd) | usually right |
| **W5** | cumulative cause-specific hazard read as a probability | Confuses Λ(t) with F(t); very common | a hazard is not a probability | **+60% to +270%** (57–171 sd) | wrong |
| **W6** | all non-failure exits competing, administrative cut-off included | "Everything that ends observation is a competing event" | administrative censoring is not an event | **−17% to −25%** (14–35 sd) | varies |
| **W7** | overhaul competing, everything else censoring (the one-liner) | The textbook recipe, applied after recognising competing risks | mis-roles retirement | **+5.7% to +37.6%** (3.6–65 sd) | right in all four regimes — an F10 case |
| **W8** | telemetry gap / transfer treated as an exit | A gap in telemetry looks like the unit disappearing | a gap is not a removal; the work-order system shows the unit still in service | **−48.5%** (51 sd) *with informative gaps* | wrong |
| **W9** | mature cohorts only (units with an observed terminal event) | "Use complete records" | conditions on the event having happened | +4.0% to +9.8% (5–9 sd) | usually right |

## The three that carry the task

- **W1** is the canonical competing-risks error and the incident's own 55%. It is *correct* for Q2
  and wrong for Q1, which is the point.
- **W7** is the analyst who has already recognised competing risks and reached for Aalen–Johansen.
  It fails only because retirement's role was not thought through — 65 sd in the regime where
  retirement is common. This is what stops the task being "use AJ".
- **W5** is the hazard/probability confusion, the largest error in the set and the one that a
  plausible-looking curve will not reveal.
