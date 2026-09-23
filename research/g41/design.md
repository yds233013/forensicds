# G41 — weekly spare-parts rebalance (constrained decision optimisation)

Coverage area 6 of the FORENSICDS-10 expansion: a task whose graded object is the optimum of a
constrained decision problem rather than an estimate. Written after the G37/G38/G40 closures, which
established that estimation-refinement designs do not separate (see
`research/task_design_failure_analysis.md`) while structural wrong-object designs do.

## 1. The business setting

Northwind Field Service plans next week's spare-parts moves across eight depots and five parts. Two
numbers go to the Service Director each Monday: the smallest number of job units that cannot be
covered, and the cheapest transfer plan that achieves that shortfall. A service contract expedites by
air freight when the shortfall exceeds 40 job units.

The published planner nets demand against every unit the extract shows in a depot and fills the
residual gap on the cheapest lanes. On the issued extract it reports **0 shortfall, 53 units moved,
$767.77, no expedite**. The truth is **46 units short, $2,868.08, expedite** — the decision is wrong,
and the depot notes describe exactly why (QA holds, open reservations, a four-day lane).

## 2. Why the published run is wrong, and why it is not stupid

Its arithmetic is correct; its feasible set is not. `docs/parts_availability_policy.md` excludes, each
for an operational reason a planner would recognise:

| Exclusion | Why the extract still shows the units |
|---|---|
| `QUARANTINE` stock | a QA hold on a supplier batch; the lot is physically there |
| `CONSIGNMENT` stock | customer-owned, held on our site |
| units under an `OPEN` allocation | reserved for work orders already in flight |
| `CANCELLED` purchase orders | still rows in `inbound_orders` |
| receipts before dock-to-stock | ETA is in the week, put-away is a day later |
| safety stock, for transfers only | may serve its own depot, may not be shipped |
| lanes that land after `need_by` | the transfer is possible, just too late |

Each exclusion is individually easy. The difficulty is that they must all be imposed *before* the
optimisation, and that what survives is no longer separable by depot or by part: one pool can serve
several jobs at several depots, subject to transit and need-by.

## 3. Identifiability (IGQA)

Three independent derivations of the graded quantities agree:

1. **Semantic** — the contract in `docs/outputs/plan_contract.md` and the policy define a
   lexicographic objective (minimum unmet units, then minimum transfer cost among the plans
   achieving it) over an explicitly stated feasible set.
2. **Min-cost max-flow** (`environment/build/world.py`, successive shortest paths with SPFA) on
   `SRC → supply → (job | shippable → job) → SNK`. All capacities are integral and the constraint
   matrix is a network matrix, so the optimum is integral.
3. **Linear program** (`solution/service_parts/network.py`, scipy HiGHS) with a big-M weight on
   unmet units, an independent formulation and an independent solver.

Routes 2 and 3 agree exactly on all four graded extracts:

| Extract | demand | shortfall | transfer units | transfer cost | decision |
|---|---|---|---|---|---|
| visible  | 680 | 46  | 144 | 2868.08 | expedite |
| hidden_a | 645 | 67  | 168 | 2984.70 | expedite |
| hidden_b | 662 | 147 | 76  | 1809.26 | expedite |
| hidden_c | 551 | 5   | 32  | 442.52  | no_expedite |

The decision is not constant across the graded extracts (3 expedite, 1 no_expedite), so the
recommendation cannot be recovered by guessing.

## 4. Pre-build wrong-object panel

Fourteen wrong objects, each a *correct* optimisation over a plausible misreading of the policy, were
labelled before any number was read (`tools/g41/panel.py`). Grading is exact on the shortfall and to
the cent on the cost, so the tolerance question that sank G37/G38/G40 does not arise: separation is
checked as a strict mismatch on the graded extracts.

All fourteen are rejected on at least three of the four extracts, eleven on all four
(`tools/g41/panel_results.json`). W14 is the important one: it reaches the *correct* shortfall by a
plan that is feasible but not cost-minimal (lanes chosen by transit time), and is rejected 4/4 on
cost — so recognising the constraints is not sufficient, the optimisation has to be done properly.

## 5. Grading

`tests/test_parts.py` regenerates each extract from the shipped generator, runs the agent's pipeline
against it unprivileged, and checks: the extract is unmodified; the run is deterministic; the
contract's schema; `demand_units`; the exact shortfall and its depot split (which must sum); the
transfer cost to the cent; `transfer_units` consistent with `plan.csv`; the expedite recommendation;
and that the submitted plan is **executable** — real lanes, arrival on or before a servable job's
need-by, and within what the origin can release.

The plan check is deliberately conservative: it flags plans that are impossible, not plans that are
merely hard to verify, and it does not require a particular optimal plan. Alternative optima with the
same cost pass — confirmed by mutation M00, which returns a different optimal vertex of the same LP
and still scores 1.

## 6. What could still make this a weak task

- The shortfall is large in three of four extracts, so a *partially* correct feasible set may still
  produce "expedite" for the wrong reason. The verifier grades the quantities, not only the decision,
  so this affects interpretation of a failure, not the reward.
- The optimisation is small enough (≈200 jobs, ≈50 pools) that a correct formulation solves in
  seconds; this task tests recognising the constraints and formulating, not scale.
