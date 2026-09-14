# ADR-0012: Streaming usage consumer

Status: accepted (2026-06-18). Implemented in 2.3.0 (2026-07-06).

## Context

Usage statements were produced by the billing team's nightly batch orchestration, which read the vendor's daily
files. Statement runs regularly took hours, the orchestration is being decommissioned, and Finance wants usage in the
console within minutes instead of the next day.

## Decision

cobalt-metering consumes collector deliveries from the landing zone in offset-aligned micro-batches. A month's
statement is assembled from the micro-batches committed during the statement period, the period between the previous
statement close and this one. This keeps every statement reconciled with the collector volume Finance ties out each
month. Collector redeliveries are removed with the platform dedupe store (default retention). The usage mart is
maintained from the same micro-batches.

## Consequences

- Statements and the console no longer depend on the batch orchestration.
- Finance's monthly tie-out compares statement quantity with committed collector volume per period.
- Open item: backfill of the batch-era usage mart (low priority).
