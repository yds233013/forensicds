# G43 concept screen — line capacity rollforward for a second-line decision

Coverage area 8 of FORENSICDS-10: planning under operational state. Deliberately **not** a statistical
forecast: the closed research directions (G37, G38, G40) established that estimation-refinement objects
do not separate, while deterministic objects built out of operational state do (G05, G10, G24, G41).

## Setting

A contract manufacturer runs one qualified line. Its supply agreement obliges it to accept firm
purchase orders; the customer also publishes a rolling forecast that is not binding. A capital request
to qualify a second line turns on one question:

> in the next four quarters, does committed demand exceed available line capacity in any month, and
> which month breaches first?

The published capacity plan says no month breaches. Manufacturing say they are already running
weekends.

## The object the capital decision is written on

**Available hours** per month, built from: the shift calendar (crews, shifts, plant holidays), planned
maintenance windows, and qualification runs the quality agreement requires for new part numbers.

**Committed load** per month, built from: firm purchase orders only (forecast releases outside the
firm window are not commitments), converted to hours at the routing's cycle time, **plus** changeover
time per production order, **grossed up for yield** (shipping N good units needs N / yield started),
and placed in the month the order is **due to ship** less the lead time it takes to build.

## Candidate wrong objects (labelled before any number is read)

W01 nameplate hours (24 x 7) as capacity · W02 shift calendar without plant holidays · W03 planned
maintenance ignored · W04 qualification runs ignored · W05 forecast releases counted as committed ·
W06 firm orders only inside the wrong firm window · W07 changeover time ignored · W08 yield ignored
(good units treated as started units) · W09 load placed in the ship month rather than the build month ·
W10 cycle time taken at the mature rate for parts still on the learning curve · W11 capacity and load
compared per quarter rather than per month (a breach inside a quarter disappears) · W12 scrap rework
hours double counted.

## Gate (must pass before any build)

1. the breach decision must not be constant across the graded extracts, and the *first breach month*
   must differ between extracts;
2. each wrong object must move a graded quantity on at least three of four extracts, and at least
   three must change the decision or the first breach month somewhere;
3. two independent computational routes must agree on the truth;
4. the construction must be derivable from the shop-floor documents alone.

---

## Screen result (2026-09-23): REJECTED pre-build, on principle 17

Not rejected for separation — the panel would almost certainly separate, since ignoring changeovers,
yield or maintenance moves available or required hours by 8–30 %. Rejected because **every one of those
rules is stated in the shop-floor documents the workspace would have to contain**: the shift calendar,
the maintenance schedule, the routing with its cycle times and changeover times, the yield table, the
supply agreement's firm window. That is the same shape as G42, which the target model solved 3/3 at six
cents a trial by reading two policy documents and applying them (`research/g42/baseline.md`).

A capacity rollforward can only be made hard by hiding a rule the analyst must infer, and a hidden
shop-floor rule is a puzzle rather than a realistic forensic situation. The coverage area is dropped
rather than filled with a task that measures reading speed.
