# Task chapter — `g50-courier-boost-rollout`

**Harbor task name** `forensicds/courier-boost-rollout-g50` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 5400.0s · **network** `public`  
**Directory** `candidates/g50-courier-boost-rollout` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**Northline, an on-demand delivery marketplace.** 'Boost' is a guaranteed minimum courier payout attached
to an individual delivery offer, piloted in spring. The programme readout says it cuts late deliveries by
4.0 points across 120,671 orders and recommends national rollout. The July investment committee decides.
The Finance director wants the recommendation re-derived from the warehouse.

**The question:** Should Boost be rolled out nationally, given £0.19 incentive per boosted order and £12.70 per late delivery — a 1.4961 pp break-even?

## B. Why this is genuinely a data-science problem

Re-deriving an experiment readout before a capital decision, where the experiment was run correctly but
answers a different question, is exactly the marketplace-experimentation problem.

## C. The tempting but incorrect inherited analysis

Report the phase-2 arm contrast. It is the **correct** estimate of the arm contrast: assignment is clean,
realised share tracks the configured target in every market-week, arms were balanced pre-programme, the
effect appears in all sixteen markets, and the interval is four tenths of a point wide. Its capacity check
compares courier hours available to each arm and finds them identical to within 0.08%.

## D. The actual scientific issue

**In everyday language.**

A boosted offer jumps the queue ahead of an unboosted one, and the same couriers serve both. So the
measured gain is mostly one order winning at another's expense. Turn Boost on for everyone and there is no
queue position left to win. The capacity check cannot fail, because both arms share the same couriers —
that is the trap.

**Technically.**

**Interference / unit of intervention.** Phase-2 randomises per order, violating SUTVA through a shared
market-hour courier queue. Because the priority reordering is **mean-preserving** within a market-hour, the
arm contrast is largely redistribution and collapses at full rollout. The rollout estimand is
`τ = Σ_m w_m [r_m(1) − r_m(0)]` with `w_m` the pre-programme share of estate orders; it is identified by
the market-level phase-1 soak — the design the incumbent analyst rejected as underpowered.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **18 files** |
| generator (never in the final image) | `environment/build/`: `world.py` |
| verifier | `tests/`: `runtime_manifest.aarch64.sha256`, `runtime_manifest.x86_64.sha256`, `scenarios.py`, `test.sh`, `test_boost.py`, `world.py` |
| reference solution | `solution/`: `northline_eval/effects.py`, `northline_eval/report.py`, `solve.sh` |
| instruction | `instruction.md`, 24 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  docs/boost_programme_brief.md
  docs/courier_supply_note.md
  docs/data_dictionary.md
  docs/dispatch_offer_queue.md
  docs/experiment_plan.md
  docs/metric_definitions.md
  docs/outputs/readout_contract.md
  docs/rollout_decision_memo.md
  northline_eval/__init__.py
  northline_eval/__main__.py
  northline_eval/cli.py
  northline_eval/effects.py
  northline_eval/panel.py
  northline_eval/report.py
  northline_eval/warehouse.py
  notebooks/analyst_note.md
  reports/boost_readout_2026-06.md
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`, `hidden_d`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (24 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `northline_eval/effects.py`, `northline_eval/report.py`, `solve.sh`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits **criterion-level rewards**: `courier_supply_response`, `decision`, `evidence_reconstruction`, `quantitative_result`, `scientific_object`, `uncertainty`. **VERIFIED FROM ARTIFACT** (`tests/test_boost.py`).

It does **not** check reasoning, method identity, or any intermediate state the agent does not write
to disk. Legitimate alternative implementations pass as long as the graded outputs fall within
tolerance on every world.

## K. Hidden worlds and adversarial validation

Sibling worlds: `hidden_a`, `hidden_b`, `hidden_c`, `hidden_d`. The same submitted procedure is graded on each, so an analysis that encodes the mechanism it happened to
find in the visible world is distinguishable from one that recovers whichever mechanism holds.

## L. Known defects, limitations and exposure integrity

See `../09_BENCHMARK_INTEGRITY.md` for the audited defect register. Exposure: this task version is the
one both arms were graded on, and it was **not** modified after exposure.

## M. Every trial outcome

| arm | job | trial | valid | reward | case study |
|---|---|---|---|---|---|
| gemini | `g50-gemini3flash-baseline-1__INVALID-verifier-refused-ldsocache` | `g50-courier-boost-rollout__oi5LLwQ` | **no** | 0 | — (invalid) |
| gemini | `g50-gemini3flash-baseline-2__INVALID-verifier-refused-ldsocache` | `g50-courier-boost-rollout__5zpVc4k` | **no** | 0 | — (invalid) |
| gemini | `g50-gemini3flash-baseline-3__INVALID-verifier-refused-ldsocache` | `g50-courier-boost-rollout__BNSAPAD` | **no** | 0 | — (invalid) |
| gemini | `g50-gemini3flash-v23-1` | `g50-courier-boost-rollout__po8qqPB` | yes | 0 | [case study](../trajectories/gemini--g50-courier-boost-rollout--g50-gemini3flash-v23-1--g50-courier-boost-rollout__po8qqPB.md) |
| gemini | `g50-gemini3flash-v23-2` | `g50-courier-boost-rollout__omjdhqN` | yes | 0 | [case study](../trajectories/gemini--g50-courier-boost-rollout--g50-gemini3flash-v23-2--g50-courier-boost-rollout__omjdhqN.md) |
| gemini | `g50-gemini3flash-v23-3` | `g50-courier-boost-rollout__ZYZkxqK` | yes | 0 | [case study](../trajectories/gemini--g50-courier-boost-rollout--g50-gemini3flash-v23-3--g50-courier-boost-rollout__ZYZkxqK.md) |
| claude | `claude-g50-courier-boost-rollout-1__INVALID-credit-balance-too-low` | `g50-courier-boost-rollout__GfQTCRY` | **no** | 0 | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-1__INVALID-verifier-refused-agent-did-run` | `g50-courier-boost-rollout__6pHEtw7` | **no** | 0 | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-1__INVALID-verifier-refused` | `claude-g50-courier-boost-rollout-1` | **no** | — | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-1__INVALID-verifier-refused` | `g50-courier-boost-rollout__A5bPR5U` | **no** | 0 | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-2__INVALID-credit-balance-too-low` | `g50-courier-boost-rollout__oDoYNbL` | **no** | 0 | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-2__INVALID-verifier-refused` | `claude-g50-courier-boost-rollout-2` | **no** | — | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-2__INVALID-verifier-refused` | `g50-courier-boost-rollout__qGycs8G` | **no** | 0 | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-3__INVALID-credit-balance-too-low` | `g50-courier-boost-rollout__2HZJVRL` | **no** | 0 | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-3__INVALID-verifier-refused` | `claude-g50-courier-boost-rollout-3` | **no** | — | — (invalid) |
| claude | `claude-g50-courier-boost-rollout-3__INVALID-verifier-refused` | `g50-courier-boost-rollout__tgY6hWE` | **no** | 0 | — (invalid) |

**Gemini: 0/3 valid trials passed. Claude: 0/0 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**For Gemini, yes — decisively. For Claude, not measured.** All three valid Gemini trials reported
`programme_effect_pp` **identical to the arm contrast** (within 0.000 pp), an order-level interval 1.882 pp
wide, `courier_hours_response_pct` +0.366 (the zero-power identity check), and `decision: roll_out` — the
expensive wrong answer. **VERIFIED FROM ARTIFACT** (`verifier/test-stdout.txt`). This is failure at the
*estimand* step, a different location from `p22` and `p20`. Claude received **no valid grade** (chapter 09).

## O. What a future *separately versioned* task should change

The verifier's runtime hash-pin must be replaced by the resolution check already prototyped, so that a
scaffolded agent can be graded at all. That is a **verifier** fix in a new version, never in the frozen
original. Also retire or narrow the three documented blind spots (`H_post`, `R2`, `M_holdout_as_control`).

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
