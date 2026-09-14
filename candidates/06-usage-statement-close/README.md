# forensicds/usage-statement-close-06

Event time vs processing time, redeliveries, revisions and prior-period adjustments in usage billing (generation 2).

- **Agent sees:**
  - a Controller note (disputed August overage; July queries; the finance tie-out reconciles);
  - the `cobalt-metering` repository with collector deliveries, rate cards and issued statements;
  - customer terms, vendor delivery documentation, billing runbook, ADR, incident note, console export, tie-out notebook
    and dashboard export.
- **Hidden root cause:** the streaming consumer works on receipt micro-batches, with a TTL redelivery filter, receipt
  months and no adjustments.
- **Correct repair:** record identity by (event_id, rev) with the highest rev current; event-month attribution; close
  cutoff; adjustments against the issued ledger, rated with each month's rate card.
- **Verifier:** behavioural checks on the September close and three hidden extracts. The pipeline is sandboxed.

Design: `research/task06_design.md`, `research/gen2_design_review.md`. Validation: `report/task06_validation.md`.
Tooling: `tools/task06/`.
