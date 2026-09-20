# Priority Dispatch pilot - experiment design note

**Owner:** Experimentation Platform
**Status:** closed, analysis phase

## What was randomised

Two stages, both run by the platform before each service day began.

1. **Dispatch pool saturation.** Every *dispatch pool* - one city on one service date - was
   independently assigned a target saturation drawn uniformly from
   **0%, 25%, 50%, 75%, 100%**. The draw was made the night before and written to
   `block_assignment.assigned_saturation` with the timestamp in `assigned_at`.
2. **Merchants within the pool.** Given the pool's saturation, that share of the pool's merchants was
   drawn uniformly at random without replacement and granted priority for that day. The result is in
   `merchant_assignment.assigned_priority`.

Re-randomisation happens every day: a merchant's assignment on one service date carries no information
about its assignment on another.

## Why saturation was varied

Dispatch is a shared-capacity system. Running a single 50/50 split would have told us what a priority
merchant gains **while most merchants do not have priority**. Varying saturation lets us read the
pilot at the exposure level we actually care about. The 0% and 100% pools were included specifically
so that both ends of the range are observed rather than extrapolated.

## Activation

Priority is not automatic: a merchant assigned priority must have the flag active on their store
console. `priority_activation.activated` records whether it was actually on. Activation is recorded
only for merchants that were assigned priority, and it is recorded **after** assignment. Larger
merchants activate more often - they have operations staff watching the console.

Assignment is what the platform controls. Activation is a merchant response to it.

## Balance

Assignment was independent of city, weekday, merchant size and pre-pilot fulfilment. Balance checks
are reproducible from the extract.

## Known limitations

- The pilot ran for 28 service days. Seasonality beyond that window is not covered.
- Courier supply itself was not manipulated; only the dispatch weighting was.
