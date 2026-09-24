# QP-07 — Dimensional measurement: calibration, traceability and conformance reference

Issue 6. Applies to all coordinate-measuring machines in Building 2 (CMM-1, CMM-2).

## 1. Scope

QP-07 establishes how a dimensional reading becomes a conformance decision. It covers periodic calibration,
adjustment, verification after adjustment, and the retained-artefact programme.

## 2. Traceability

All dimensional readings used for product disposition shall be traceable to the works length standard
`GB-100.000`, itself calibrated annually by a UKAS-accredited laboratory.

## 3. Conformance reference

The **conformance reference** for a feature is the deviation from nominal that would be obtained from a
measurement traceable to `GB-100.000` and free of instrument offset. Tolerances on the drawing are stated
against this reference.

Where an instrument is found to carry an offset, the conformance reference is recovered by removing that
offset from the instrument's readings. An instrument's offset is a property of the instrument, not of the
product, and does not change the drawing tolerance.

## 4. Periodic calibration and adjustment

Each CMM is calibrated on a 6-month cycle by the contracted metrology supplier. The calibration certificate
records:

* `as_found` — the deviation observed at the standard's length before any adjustment;
* `as_left` — the deviation observed at the standard's length after adjustment;
* the standard used and the certificate number.

Calibration events are recorded in `calibration_events`. An `event_type` of `PERIODIC+ADJUST` indicates that
the machine's compensation table was written to during the visit.

**Note.** The `as_found` and `as_left` figures are reported at the standard's length (100 mm) and at the
standard's geometry. A compensation write changes both offset and scale terms, so a deviation observed at the
standard's length does **not** map to the offset on a production feature by any fixed factor. The
retained-artefact programme in §5 is the means by which a feature offset is established. An escalation shall
not quote a certificate figure as a feature offset.

## 5. Verification after adjustment (retained-artefact programme)

Twenty retained reference artefacts (`REF-01` … `REF-20`) are held in the metrology room. Each carries a
certified deviation from nominal for the same feature geometry as MAN-4471, certified by NML under
`certified_by`, with a stated uncertainty.

The retained artefacts are measured **quarterly** on each machine, and additionally whenever a machine's
compensation table is written to, five repeats each, and the results recorded in `reference_measurements` with the measurement date.
Artefacts are measured on **both** machines so that the two instruments remain comparable.

The artefacts are dimensionally stable; their certified values are revalidated every three years.

## 6. Inspection rota

Production parts are routed to CMM-1 or CMM-2 by the inspection rota, which allocates on machine availability
and is independent of heat, shift and operator. Either machine may disposition any part.

## 7. Records

`reference_parts`, `reference_measurements`, `calibration_events` and `inspection_results` are retained for
seven years.
