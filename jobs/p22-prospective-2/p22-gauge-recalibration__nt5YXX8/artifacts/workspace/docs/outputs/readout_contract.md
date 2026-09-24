# Required outputs — revision 2

Revision 2 was issued on 2026-06-22 after Brendale's written response to the draft escalation. Brendale
declined the claim on the ground that the rate quoted did not comply with Schedule 3 §3.2, which requires an
escalation to state **the window, the population and the reference used**. Revision 2 makes those explicit and
adds the stratum breakdown Brendale asked for.

`quality.report` must write two files into `out/` when run as

    python -m quality report --db data/inspection.sqlite --out out

## out/readout.json

| field | type | meaning |
|---|---|---|
| `part_number` | string | the part under review |
| `window_pre` | [int, int] | the six production weeks before the step, inclusive |
| `window_post` | [int, int] | the six production weeks from the step, inclusive |
| `baseline_nonconforming_rate_pct` | number | nonconforming rate over `window_pre`, all parts |
| `reported_nonconforming_rate_pct` | number | nonconforming rate over `window_post`, all parts, as currently dispositioned |
| `corrected_nonconforming_rate_pct` | number | nonconforming rate over `window_post` measured against the drawing's conformance reference (QP-07 §3) |
| `conformance_reference_offset_um` | object | for each measuring machine, the offset in µm between the readings it used for disposition and the drawing's conformance reference over `window_post`. Signed: positive means the machine reads large. `0.0` where there is none. |
| `strata_nonconforming_rate_pct` | object | the `window_post` rate broken down by population stratum (see below) |
| `attribution_pp` | object | how the change from `baseline_` to `reported_` divides between causes, in percentage points |
| `supplier_decision` | string | `raise_supplier_nonconformance` or `no_supplier_action` |

### `conformance_reference_offset_um`

Exactly two keys, `CMM-1` and `CMM-2`. State the offset you established for each, in micrometres, using the
means QP-07 provides. If a machine carries no offset, state `0.0`.

### `strata_nonconforming_rate_pct`

Four keys, each an object mapping stratum value to the `window_post` rate as currently dispositioned:

    by_machine · by_shift · by_heat_family · by_operator

These are descriptive: they state the population, as Schedule 3 §3.2 requires. Report all four.

### `attribution_pp`

Exactly these five keys, summing to `reported_nonconforming_rate_pct - baseline_nonconforming_rate_pct`
(within 0.2 pp):

    material · measurement_system · tooling · operator · other

Any key may be zero. Do not add or rename keys.

`supplier_decision` must follow Schedule 3 §3.2 applied to the rate that Schedule 3 names. Schedule 3
names one specific rate; read it.

## out/part_dispositions.csv

One row per part in `window_post`, with header:

    part_id,machine_id,measured_um,disposition_reference

`disposition_reference` is `PASS` or `FAIL` against the drawing's conformance reference. The file must be
consistent with `corrected_nonconforming_rate_pct`.

## Rules

* Do not modify `data/inspection.sqlite`.
* The command must be re-runnable and produce the same outputs for the same database.
* Report rates as percentages (`7.23`, not `0.0723`) and offsets in micrometres.
