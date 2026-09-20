# G35 graded-fact evidence audit

The G33/G34 rule: for every fact we might grade, what evidence would a real analyst have?  If only the
generator knows it, it must not be graded.

| candidate graded fact | evidence available to the analyst | verdict |
|---|---|---|
| `tau_policy` (full-rollout effect) | contrast of the 100% and 0% saturation arms, both present in the assignment log and the outcome table | **GRADE** |
| `tau_direct(0.5)` | treated vs control within the 50% arm | **GRADE** |
| `spillover(0.5)` | control merchants at 50% vs merchants at 0% | **GRADE** |
| launch decision | the 1.5-point gate is stated in the FY27 planning memo | **GRADE** |
| block = city-day dispatch pool | stated in the dispatch runbook: couriers sign on to one city for one day and are not dispatched across boundaries | **GRADE** (as the interference group) |
| assigned saturation per block | the assignment log records the drawn saturation before the day starts | **GRADE** |
| per-block order counts / merchant counts | countable in the data | **GRADE** (bookkeeping) |
| adoption flags | recorded in the feature-flag log with timestamps | **GRADE** |
| **courier capacity `S_b`** | **not observable**; the platform logs completed deliveries, not the counterfactual capacity | **DO NOT GRADE** |
| **`delta`, the routing efficiency** | a generator parameter; an analyst can only estimate its consequence, never read it | **DO NOT GRADE** |
| **`lambda`, the priority weight** | internal to the dispatch service and not exposed | **DO NOT GRADE** |
| **market tightness regime label** | a generator concept; the analyst sees fulfilment rates, not a label | **DO NOT GRADE** |
| **per-merchant potential outcomes** | not identified by any experiment | **DO NOT GRADE** |
| **effect at a saturation outside {0,.25,.5,.75,1}** | not identified by this design | **DO NOT GRADE** |
| **effect under a targeted (non-random) rollout** | the experiment randomises uniformly within block; targeted assignment is a different regime | **DO NOT GRADE** |

## Two facts the agent must infer rather than read

Both are documented, neither is handed over as a method:

1. **Couriers are the shared constraint and the pool is the city-day.**  The runbook states the
   dispatch boundary; the analyst must connect that to "my units are not independent".
2. **The deployment question is about a different saturation than the experiment's average.**  The
   planning memo asks for the effect "once every store has it"; the experiment ran at mixed
   saturation.  Nothing states "use the 100% arm" - that is the inference under test.

## The line this audit draws

The task may ask "what happens at full rollout" **only because a 100% arm exists in the design**.  If
it did not, the honest answer would be "not identified", and asking anyway would be grading generator
knowledge.  This is the single most important constraint the audit imposes on any build.
