# G41 target-model baseline — google/gemini-3-flash-preview

Three sequential trials, one per job, on the frozen task (checksum `3f31849e44d9e392`, Harbor task
digest `sha256:dbf33bceb5cee6bcb50ebd3…`, identical in all three). No task file was touched during or
after the baseline. All three trials carry a full grading report, so none shows the container-teardown
signature (`research/harness_process_sweep_defect.md`).

| Trial | Reward | Cost (USD) | What it did |
|---|---|---|---|
| `g41-…__RZW9reM` | 0 | 0.1481 | reconstructed the availability rules, then solved with a hand-written "successive shortest path" that augments greedily without residual arcs |
| `g41-…__G6PJWX4` | 0 | 0.0626 | the same family: per-part greedy cheapest-lane assignment |
| `g41-…__FTzqnFz` | **1** | 0.1447 | expanded supply and demand to unit rows and solved each part with `scipy.optimize.linear_sum_assignment` under a big-M for infeasible pairs — an exact route to the same optimum |

**pass@3 = 1/3.** Total valid-baseline spend $0.3554.

## What the failures were

Both failures are **F4** (root cause found, repair incorrect), not F9 or F1. Both trials read the
availability policy and built the feasible set from it — quarantine, consignment, open allocations,
dock-to-stock, safety stock, transit against need-by — and both named minimum-cost maximum flow as the
method. Neither implemented it: the augmentation has no residual (negative-cost reverse) arcs, so it
stops at a maximal, not a maximum, flow. Both reported 68 unmet units where 46 is achievable, and
$2,224.64 where the cheapest plan achieving the true minimum costs $2,868.08.

Both got the **decision** right anyway (68 > 40, so expedite), which is the F10 pattern the suite has
seen before: the recommendation survives while every quantity under it is wrong. On this task that is
visible rather than hidden, because the contract asks for the quantities as well as the call.

## What this says about the task

The task separates recognition from execution, which is what it was designed to do (principle 15).
Recognising the constraints was not the binding step for this model — it did that in all three trials.
Constructing the optimum was: two of three produced a plausible-looking but non-optimal plan and did
not check optimality against any bound.

The single pass is a genuine solve by an independent method (unit-level assignment rather than the
oracle's LP or the generator's min-cost flow), which is evidence that the verifier grades the object
rather than the implementation.
