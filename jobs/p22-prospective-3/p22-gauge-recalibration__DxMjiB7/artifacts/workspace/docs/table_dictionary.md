# data/inspection.sqlite — table dictionary

## inspection_results
One row per produced part, weeks 13–24.

| column | meaning |
|---|---|
| part_id | serial |
| week | production week (ISO) |
| inspected_on | date of dimensional inspection |
| heat_id | bar-stock heat the part was machined from → `heats` |
| machine_id | measuring machine that dispositioned the part (`CMM-1` or `CMM-2`), assigned by the inspection rota |
| operator_id, shift | machining operator and shift |
| tool_hours, spindle_rpm, feed_mm_min, coolant_temp_c | process parameters at the time of machining |
| measured_um | bore deviation from nominal, in µm, **as read by `machine_id`** |
| disposition | `PASS` / `FAIL`, derived from `measured_um` against the drawing tolerance |

## heats
| column | meaning |
|---|---|
| heat_id, family | heat identifier and melt-route family |
| first_week | production week the heat entered use |
| supplier_lot, hardness_hv, cert_no | supplier records from the material test certificate |

## reference_parts / reference_measurements
The retained-artefact programme of QP-07 §5. `reference_parts` carries the certified deviation per artefact;
`reference_measurements` carries each reading (artefact × machine × date × repeat).

## calibration_events
Calibration and adjustment history per machine; see QP-07 §4 for the meaning of `as_found` / `as_left`.

## functional_tests
Leak-test results on the QA-11 sample. The leak rig is a pressure test and does not use a CMM.

## tool_changes
Insert changes on the machining centre, with the reason and cumulative hours at change.

## drawing_limits
The drawing tolerance in force, with its revision and effective date.
