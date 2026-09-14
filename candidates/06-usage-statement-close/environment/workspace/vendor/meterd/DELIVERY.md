# meterd: record delivery

*Vendor documentation excerpt, meterd 4.x edge collector (retrieved 2026-06-10).*

## Usage windows

Meters report usage per customer and meter for consecutive 4-hour windows aligned to 00:00, 04:00, …, 20:00 UTC. A
window covers `[window_start, window_end)`. Each window has one `event_id`.

## Records and revisions

A record carries the metered `quantity` for its window. The first record for a window has `rev` 1. When meterd's
reconciliation corrects a window, for example after late meter readings, it emits the record again with `rev`
incremented. The record with the highest `rev` is the current one. A window that should not have been metered is
voided by a revision with `quantity` `"0.000"`.

Corrections are typically emitted within 12 days of the window; corrections after longer periods occur.

## Delivery

Delivery to the landing service is at-least-once: a record may be delivered more than once. Deliveries of the same
record revision carry identical records. Most records are delivered within minutes of the end of their window. Records
that cannot be sent, for example during connectivity loss at the edge, are buffered on the collector and delivered
when sending resumes, which can be hours or days later.
