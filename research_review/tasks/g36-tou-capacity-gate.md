# Task chapter — `g36-tou-capacity-gate`

**Harbor task name** `forensicds/tou-capacity-gate-g36` · **difficulty** `hard` · **agent timeout** 7200.0s · **verifier timeout** 7200.0s · **network** `public`  
**Directory** `candidates/g36-tou-capacity-gate` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**A regulated electric utility, Resource Planning Analytics.** The utility holds 1,900 MW of firm capacity
for the residential block, and the regulator requires a 10% reserve. Across 565,000 customers that caps
mean peak-window demand at **3.057 kW per customer**. A planning memo contains the arithmetic.

**The question:** Does FY27 residential peak demand breach the cap, so additional capacity must be procured?

## B. Why this is genuinely a data-science problem

Capacity procurement is a high-consequence regulated decision resting on one scalar derived from interval
(AMI) meter data. All the weight falls on how that scalar is defined and on which population.

## C. The tempting but incorrect inherited analysis

Compute mean peak-window kW over the observed customer population and compare it with 3.057. The
arithmetic in the memo is correct given its inputs.

## D. The actual scientific issue

**In everyday language.**

Customers have been moving onto time-of-use tariffs, which changes both when they use power and which
customers are on which plan. Enrolment was not random. So the 'average customer' in the data is not the
population the regulator's cap applies to.

**Technically.**

**Population and exposure definition under non-random tariff migration.** The per-customer peak figure
depends on the tariff mix during the measurement window, and migration is correlated with consumption.
The quantity the reserve applies to must be reconstructed on the specified population and window rather
than on whoever happens to appear in the extract.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **15 files** |
| generator (never in the final image) | `environment/build/`: `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_capacity.py`, `world.py` |
| reference solution | `solution/`: `capacity_forecast/__init__.py`, `capacity_forecast/__main__.py`, `capacity_forecast/__pycache__/__init__.cpython-313.pyc`, `capacity_forecast/__pycache__/estimators.cpython-313.pyc`, `capacity_forecast/__pycache__/load.cpython-313.pyc`, `capacity_forecast/cli.py`, `capacity_forecast/estimators.py`, `capacity_forecast/load.py` … |
| instruction | `instruction.md`, 31 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  capacity_forecast/__init__.py
  capacity_forecast/__main__.py
  capacity_forecast/__pycache__/__init__.cpython-313.pyc
  capacity_forecast/__pycache__/load.cpython-313.pyc
  capacity_forecast/cli.py
  capacity_forecast/incumbent.py
  capacity_forecast/load.py
  docs/extract_dictionary.md
  docs/load_research_note.md
  docs/outputs/analysis_contract.md
  docs/pilot_design_note.md
  docs/tou_programme_note.md
  reports/fy27_capacity_memo.md
  reports/peak_forecast_backtest.md
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`, `hidden_d`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (31 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `capacity_forecast/__init__.py`, `capacity_forecast/__main__.py`, `capacity_forecast/__pycache__/__init__.cpython-313.pyc`, `capacity_forecast/__pycache__/estimators.cpython-313.pyc`, `capacity_forecast/__pycache__/load.cpython-313.pyc`, `capacity_forecast/cli.py`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits a **single binary reward** only. Criterion-level attribution of its failures is therefore **UNKNOWN** — not zero. This is the dossier's main instrumentation gap.

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
| gemini | `g36-gemini3flash-baseline-1` | `g36-tou-capacity-gate__9ireeNt` | yes | 0 | [case study](../trajectories/gemini--g36-tou-capacity-gate--g36-gemini3flash-baseline-1--g36-tou-capacity-gate__9ireeNt.md) |
| gemini | `g36-gemini3flash-baseline-2` | `g36-tou-capacity-gate__gtUvxU3` | yes | 0 | [case study](../trajectories/gemini--g36-tou-capacity-gate--g36-gemini3flash-baseline-2--g36-tou-capacity-gate__gtUvxU3.md) |
| gemini | `g36-gemini3flash-baseline-3` | `g36-tou-capacity-gate__gZDvdHD` | yes | 0 | [case study](../trajectories/gemini--g36-tou-capacity-gate--g36-gemini3flash-baseline-3--g36-tou-capacity-gate__gZDvdHD.md) |
| claude | `claude-g36-tou-capacity-gate-1` | `g36-tou-capacity-gate__QpZiA8i` | yes | 0 | [case study](../trajectories/claude--g36-tou-capacity-gate--claude-g36-tou-capacity-gate-1--g36-tou-capacity-gate__QpZiA8i.md) |
| claude | `claude-g36-tou-capacity-gate-1__INVALID-credit-balance-too-low` | `g36-tou-capacity-gate__nPeAo59` | **no** | 0 | — (invalid) |
| claude | `claude-g36-tou-capacity-gate-2` | `g36-tou-capacity-gate__xZYeHd4` | yes | 0 | [case study](../trajectories/claude--g36-tou-capacity-gate--claude-g36-tou-capacity-gate-2--g36-tou-capacity-gate__xZYeHd4.md) |
| claude | `claude-g36-tou-capacity-gate-2__INVALID-credit-balance-too-low` | `g36-tou-capacity-gate__uKBELHi` | **no** | 0 | — (invalid) |
| claude | `claude-g36-tou-capacity-gate-3` | `g36-tou-capacity-gate__CKrhMnk` | yes | 0 | [case study](../trajectories/claude--g36-tou-capacity-gate--claude-g36-tou-capacity-gate-3--g36-tou-capacity-gate__CKrhMnk.md) |
| claude | `claude-g36-tou-capacity-gate-3__INVALID-credit-balance-too-low` | `g36-tou-capacity-gate__ScHsj2y` | **no** | 0 | — (invalid) |

**Gemini: 0/3 valid trials passed. Claude: 0/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Yes on difficulty, no on mechanism.** Both models 0/3. It carries four hidden worlds
(`hidden_a..d` — **VERIFIED FROM ARTIFACT**, `tests/scenarios.py`), the most of any task except `g50`, so
generalisation is tested. But it is binary-reward, so we cannot say where either model broke.

## O. What a future *separately versioned* task should change

Instrument population definition, the scalar, and the procure/do-not-procure decision; and record whether the agent ever examined the tariff-switch history.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
