# Task chapter — `p31-fill-rate-dispute`

**Harbor task name** `forensicds/fill-rate-dispute-p31` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 5400.0s · **network** `public`  
**Directory** `candidates/p31-fill-rate-dispute` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**Meridian Retail Group, demand science supporting Commercial and Legal.** The published ambient-grocery
service-level report shows a 97.7% fill rate for the quarter. The supplier's own quarterly report shows
91.5% for the same category and period. Three key accounts have logged shortfall tickets. The Commercial
Director wants the metric rebuilt, the team's bonus gate reviewed, and a position on a £1.8m claim that
turns on whether a contractual account floor was breached.

**The question:** What is the contractually correct fill rate, was the account floor breached, and does the £1.8m claim stand?

## B. Why this is genuinely a data-science problem

Reconciling two defensible computations of the same KPI, where a contract selects one of them, is ordinary
and consequential commercial analytics.

## C. The tempting but incorrect inherited analysis

Recompute the fill rate at the aggregation level the reporting code already uses and defend 97.7%. It is a
correct computation of *a* fill rate.

## D. The actual scientific issue

**In everyday language.**

There is no single definition of 'fill rate'. Whether you count at order, line or case level, whether you
use the requested or the promised date, and how you treat partial shipments and returns all change the
answer — and the contract fixes one of those choices, not the one the report used.

**Technically.**

**Metric reconciliation against a contractual definition.** The bridge between 97.7% and 91.5% decomposes
into aggregation level, denominator definition, and treatment of returns/substitutions
(`bridge_pp[aggregation]`, `bridge_pp[denominator]`, `bridge_pp[returns_treatment]` — **VERIFIED FROM
ARTIFACT**, these appear in the verifier notes). The contractual floor must then be applied at the
contractual unit, which is not the reporting unit.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **13 files** |
| generator (never in the final image) | `environment/build/`: `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_fill.py`, `tolerances.py`, `world.py` |
| reference solution | `solution/`: `service/__init__.py`, `service/__main__.py`, `service/adjudicate.py`, `service/cli.py`, `service/definitions.py`, `service/metrics.py`, `service/report.py`, `solve.sh` |
| instruction | `instruction.md`, 20 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  docs/customer_supply_agreement.md
  docs/outputs/readout_contract.md
  docs/supplier_report_methodology.md
  docs/table_dictionary.md
  notes/correspondence.md
  reports/commercial_escalation.md
  reports/demand_science_response.md
  service/__init__.py
  service/__main__.py
  service/cli.py
  service/metrics.py
  service/report.py
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (20 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `service/__init__.py`, `service/__main__.py`, `service/adjudicate.py`, `service/cli.py`, `service/definitions.py`, `service/metrics.py`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits **criterion-level rewards**: `decision`, `estimator_implementation`, `evidence_reconstruction`, `identification`, `independent_validation`, `quantitative_results`, `scientific_object`. **VERIFIED FROM ARTIFACT** (`tests/test_fill.py`).

It does **not** check reasoning, method identity, or any intermediate state the agent does not write
to disk. Legitimate alternative implementations pass as long as the graded outputs fall within
tolerance on every world.

## K. Hidden worlds and adversarial validation

Sibling worlds: `hidden_a`, `hidden_b`, `hidden_c`. The same submitted procedure is graded on each, so an analysis that encodes the mechanism it happened to
find in the visible world is distinguishable from one that recovers whichever mechanism holds.

## L. Known defects, limitations and exposure integrity

See `../09_BENCHMARK_INTEGRITY.md` for the audited defect register. Exposure: this task version is the
one both arms were graded on, and it was **not** modified after exposure.

## M. Every trial outcome

| arm | job | trial | valid | reward | case study |
|---|---|---|---|---|---|
| gemini | `p31-prospective-1` | `p31-fill-rate-dispute__GyUgp7D` | yes | 0 | [case study](../trajectories/gemini--p31-fill-rate-dispute--p31-prospective-1--p31-fill-rate-dispute__GyUgp7D.md) |
| gemini | `p31-prospective-2` | `p31-fill-rate-dispute__AjqzDN8` | yes | 0 | [case study](../trajectories/gemini--p31-fill-rate-dispute--p31-prospective-2--p31-fill-rate-dispute__AjqzDN8.md) |
| gemini | `p31-prospective-3` | `p31-fill-rate-dispute__3fnpGae` | yes | 0 | [case study](../trajectories/gemini--p31-fill-rate-dispute--p31-prospective-3--p31-fill-rate-dispute__3fnpGae.md) |
| claude | `claude-p31-fill-rate-dispute-1` | `p31-fill-rate-dispute__Xg2kwGm` | yes | 0 | [case study](../trajectories/claude--p31-fill-rate-dispute--claude-p31-fill-rate-dispute-1--p31-fill-rate-dispute__Xg2kwGm.md) |
| claude | `claude-p31-fill-rate-dispute-1__INVALID-credit-balance-too-low` | `p31-fill-rate-dispute__YKQcaym` | **no** | 0 | — (invalid) |
| claude | `claude-p31-fill-rate-dispute-2` | `p31-fill-rate-dispute__PG3jXCr` | yes | 0 | [case study](../trajectories/claude--p31-fill-rate-dispute--claude-p31-fill-rate-dispute-2--p31-fill-rate-dispute__PG3jXCr.md) |
| claude | `claude-p31-fill-rate-dispute-2__INVALID-credit-balance-too-low` | `p31-fill-rate-dispute__FsxbpBV` | **no** | 0 | — (invalid) |
| claude | `claude-p31-fill-rate-dispute-3` | `p31-fill-rate-dispute__9ojY6V5` | yes | 0 | [case study](../trajectories/claude--p31-fill-rate-dispute--claude-p31-fill-rate-dispute-3--p31-fill-rate-dispute__9ojY6V5.md) |
| claude | `claude-p31-fill-rate-dispute-3__INVALID-credit-balance-too-low` | `p31-fill-rate-dispute__Rzuodrc` | **no** | 0 | — (invalid) |

**Gemini: 0/3 valid trials passed. Claude: 0/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Yes, and it shows a *different* failure shape.** Both models 0/3. Two Gemini trials produced the right
numbers (`quantitative_results` PASS) and still failed `identification` and `decision` — the mirror image of
`p20`. One Gemini trial failed all seven criteria outright. **VERIFIED FROM ARTIFACT**
(`CRITERION_RESULTS.csv`). So the suite contains at least two distinct failure shapes, which is evidence
*against* a single-mechanism story.

## O. What a future *separately versioned* task should change

Add a world in which the published number is the contractually correct one, so that 'the report is wrong' cannot be assumed. Instrument the three bridge components individually.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
