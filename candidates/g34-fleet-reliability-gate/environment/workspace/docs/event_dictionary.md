# Warehouse extract — table and code dictionary

## `asset_register`
One row per unit in the installed base. `commissioned_on` is the date the unit entered service.
Units appear whatever their current status; the register is not filtered to units still running.

## `work_orders`
Closed work orders only. One unit has at most one of the following, because each one ends that
unit's service life with its original assembly:

| `wo_type` | Meaning |
|---|---|
| `UNPL_FAIL` | unplanned in-service failure of the critical assembly |
| `PM_OVHL` | scheduled overhaul; the critical assembly is exchanged (see the SOP) |
| `ASSET_RET` | unit withdrawn from the fleet |

`component` names the part the order acted on where applicable.

## `telemetry_status`
Channel outage windows from the condition-monitoring platform. `gap_end` is null where the outage
was still open at the extract cut-off. **This table records data availability, not unit status.**

## `extract_meta`
`extract_cut_off` is the date the extract was taken. A unit with no work order in the extract was
still in service with its original assembly on that date.
