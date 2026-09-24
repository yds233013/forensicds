# P22 — world and evidence register

World: **Kelvin Works**, Building 2 machining cell (industrial OEM). Incident dated week 24 of 2026.

## A / B / C classification

Every artefact is classified by what a real professional in this seat would have. **C never reaches the agent
workspace**; it exists only in the generator and the verifier.

### A — information the professional already has

| artefact | contents |
|---|---|
| `docs/drawing_MAN-4471.md` | nominal 42.000 mm, tolerance ±30 µm, unchanged since 2019; conformance assessed against the reference QP-07 establishes |
| `docs/QP-07_calibration.md` | what the conformance reference is (§3); what `as_found`/`as_left` mean and the explicit statement that a deviation at the standard's length does **not** map to a feature offset by a fixed factor (§4); the retained-artefact programme (§5); the inspection rota's independence of heat, shift and operator (§6) |
| `docs/supply_quality_agreement.md` | Schedule 3 §3.2: escalation to a supplier change only where the rate **attributable to the supplied material**, measured against the drawing's conformance reference, exceeds 5.5 % over six weeks |
| `docs/table_dictionary.md` | the eight tables and the meaning of `measured_um` ("as read by `machine_id`") |
| `docs/outputs/readout_contract.md` | revision 2 of the output specification, issued after the supplier declined the draft claim |
| `reports/quality_report_w24.md` | the incumbent analysis and its recommendation |
| `notes/plant_notes.md` | the cell's running notes, including the metrology visit, the heat-family switch, the new night operator, and an unverified claim from the cell lead about tooling |
| `quality/` | the package that produced the report |

### B — information they would have to investigate

| artefact | what it settles | why it is not obvious |
|---|---|---|
| `reference_parts`, `reference_measurements` | the offset each machine carries on the bore feature | reachable only from QP-07 §5; 20 artefacts × 5 repeats × 2 machines × 2 dates, and the pre-adjustment round is what makes it a bridge |
| `calibration_events` | that a compensation write happened, and when | the `as_left` figure is at the standard's length and is **not** the feature offset — QP-07 §4 says so and the numbers bear it out |
| `inspection_results.machine_id` | that the step is confined to one machine's stratum | the report never stratifies by measuring machine |
| `functional_tests` | an outcome that depends on neither CMM | 8 % sample; the notes mention the rig only in passing |
| `inspection_results.tool_hours` + `tool_changes` | whether tooling contributed | the wear effect is within-week, so it is identified from variation inside each week rather than from a trend on week |
| `heats.family`, `hardness_hv` | the genuine material difference | real and significant, which is what makes the wrong route coherent |

### C — generator and verifier only

The latent per-part geometry `_true_um`; the design bias `bias_um`; the heat-family shift and spread; the
wear rate; the operator shift; `cert_scale_k`; `scenarios.py`; `truth()`, `routes()`, `latent_check()`.
`/tests` is mode 700 and the verifier refuses to grade if the pipeline user can read it.

## Trap register — every seeded contradiction

| # | trap | where it is visible | what it catches |
|---|---|---|---|
| T1 | the week-19 recalibration coincides exactly with the H2→H3 heat-family switch | `calibration_events`, `heats.first_week` | any analysis that treats coincidence in time as attribution |
| T2 | the heat-family effect on measured deviation is **real and significant** | `inspection_results` × `heats` | an ANOVA that is correct and still supports the wrong conclusion |
| T3 | the certificate's `as_left` figure is large and looks like the answer | `calibration_events` | reading a length-standard deviation as a feature offset (fails on 3 of 4 extracts) |
| T4 | the step is present only in the CMM-1 stratum | `inspection_results.machine_id` | an unstratified population |
| T5 | the insert-change interval is extended in one extract, so tooling genuinely contributes | `tool_changes.cumulative_hours`, `tool_hours` | attributing everything to the gauge |
| T6 | one extract has a genuinely bad heat family and the correct answer **is** to escalate | the data | "the gauge is always the answer" |
| T7 | an operator shift exists in one extract but only its **contrast** is identifiable | `operator_id` × window | grading, or claiming, an unidentifiable quantity |
| T8 | the cell lead's claim that tooling is unremarkable is false in one extract | `notes/plant_notes.md` vs `tool_changes` | taking a stakeholder's assertion as evidence |
| T9 | Schedule 3 names the rate attributable to **material**, not the rate against the reference | the agreement | deciding on the wrong one of two quantities the analysis produces |

## Legitimate ambiguity (retained deliberately)

Which of the two paired reference rounds to use as the baseline (the answer is the pre-adjustment one, which
QP-07 §5 dates), and whether to bridge the offset from the artefacts or from the second machine. Both routes are
accepted; the tolerance was set from their measured spread.

## Deliverables and intended routes

Deliverables: `out/readout.json`, `out/part_dispositions.csv` per the contract.
Intended route: reproduce → enumerate the five causes → QP-07 §5 → bridge → re-disposition → allocate tooling
and operator → Schedule 3 §3.2.
Unintended routes that pass: the second-machine difference-in-differences bridge; the departure of the
post-adjustment artefact readings from the NML certified values (tested as mutation M00, scores 1).
