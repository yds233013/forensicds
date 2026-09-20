# G34 redesign — cheap-solve gate and representation leakage

## Cheap-solve panel

| Heuristic | Result |
|---|---|
| `C3` 1 − KM (one-line library default) | +36% to +188% wrong; **decision right in `visible`, wrong in `overhaul_heavy`** |
| `C2` "overhaul competing, everything else censoring" | +6% to +38% wrong; decision right in all four regimes — an F10 case, not a solve |
| `C1` all exits competing | −17% to −25% wrong |
| `C6` transfers/gaps treated as exits | −48.5% wrong (with informative gaps) |
| `C7` mature cohorts only | +4% to +10% wrong |
| `C8` raw event fraction | −17% to −25% wrong; decision wrong in `visible` |
| `C10` constant decision | best constant is right in **3 of 5 regimes**; a 2-vs-2 fixture set defeats it outright |

**Strongest shortcut: `C2`.** It gets the decision right everywhere while being 6–38% wrong on the
graded quantity. It is defeated by grading the quantities, not the decision — which is exactly what
the benchmark already does after G24 and G05.

No heuristic recovers the graded quantity. The nearest is `W9 mature-only` at 4–10%, which is
5–9 reference sd out.

## Representation-leakage audit

| Check | Result |
|---|---|
| `unit_id` vs terminal age | corr **−0.0057** |
| `unit_id` vs is-failure | corr **−0.0051** |
| event-code names | `UNPL_FAIL`, `PM_OVHL`, `ASSET_RET`, `SITE_XFER`, `TELEM_GAP`, `EXTRACT_END` — operational codes; **none names a statistical role**, none contains "competing" or "censoring" |
| terminal-code mix | failure 6401 / overhaul 8444 / retirement 3470 / still-in-service 6685 — plausible for a 24-month overhaul policy |
| events-per-unit vs is-failure | −0.030 with independent gaps; **becomes a real signal with informative gaps, by design** — it is evidence an analyst should find, not an artefact |
| **row order** | records emitted in `unit_id` order — **a build must shuffle** |
| **regime name in the observed view** | the pilot passes `spec` (including the regime name) to estimators for convenience — **a build must not ship it** |

## Graded-fact evidence audit

| Graded fact | Evidence a real analyst has |
|---|---|
| age at terminal event | work-order date − commissioning date |
| which code is the target event | event dictionary + maintenance SOP |
| overhaul is competing for Q1 | SOP: the overhaul replaces the assembly, so the original assembly can no longer fail |
| retirement is competing for Q1 | asset register: the unit leaves the fleet and generates no further demand |
| transfer is not an exit | asset history: same serial, new site, assembly unchanged |
| telemetry gap is not an exit | no removal work order exists |
| extract end is censoring | extract metadata cut-off date |
| overhaul is age-based (needed for Q2 only) | SOP states the interval; checkable by regressing overhaul age on pre-overhaul condition |

No graded fact depends on a convention only the generator knows.
