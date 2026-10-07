# Task chapter — `g05-sco-rollout-gate`

**Harbor task name** `forensicds/sco-rollout-gate-g05` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 7200.0s · **network** `public`  
**Directory** `candidates/g05-sco-rollout-gate` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**A grocery/general-merchandise retailer, Decision Science in FP&A.** 'SCO 2.0' is a self-checkout
conversion programme deployed store-by-store in waves. The Capital Committee decides in October whether to
release tranche 2 (waves 5-6). The business case defines a specific 'gate figure' the decision turns on.

**The question:** Does the gate figure clear the threshold in the business case, so tranche 2 should be released?

## B. Why this is genuinely a data-science problem

Phased capital rollouts are how retailers actually deploy estate changes, and the gate number is computed
by an analyst from store-week operational data. Getting the estimator wrong here moves real capital.

## C. The tempting but incorrect inherited analysis

A before/after comparison, or a two-way fixed-effects regression across all store-weeks. Both run, both
produce a signed and precise number, and both are the conventional first thing an analyst reaches for.

## D. The actual scientific issue

**In everyday language.**

Stores did not all convert at the same time, and the early waves were chosen because they were ready, not
at random. So 'stores that have converted' and 'stores that have not' are not comparable groups, and the
usual regression quietly averages together comparisons that should not be averaged.

**Technically.**

**Identification under staggered adoption.** With treatment timing varying across units and effects varying
with exposure length, the two-way fixed-effects estimator is a weighted average of 2×2 difference-in-
differences comparisons in which *already-treated* units serve as controls for *later-treated* ones, and
some weights can be negative. The gate quantity must be built from comparisons whose control group is
genuinely not-yet-treated, on the exposure window the business case specifies.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **15 files** |
| generator (never in the final image) | `environment/build/`: `history.py`, `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_readout.py`, `world.py` |
| reference solution | `solution/`: `sco_readout/cli.py`, `sco_readout/estimate.py`, `sco_readout/panel.py`, `sco_readout/report.py`, `solve.sh` |
| instruction | `instruction.md`, 26 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  RELEASES.md
  docs/finance/glossary.md
  docs/finance/sco2_business_case.md
  docs/kpi_handbook.md
  docs/outputs/readout_contract.md
  docs/programmes/sco2_programme_brief.md
  docs/store_ops/wave_sequencing_2024-11.md
  notes/2026-09-03_tranche2_prep.md
  sco_readout/__init__.py
  sco_readout/__main__.py
  sco_readout/cli.py
  sco_readout/estimate.py
  sco_readout/panel.py
  sco_readout/report.py
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (26 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `sco_readout/cli.py`, `sco_readout/estimate.py`, `sco_readout/panel.py`, `sco_readout/report.py`, `solve.sh`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits a **single binary reward** only. Criterion-level attribution of its failures is therefore **UNKNOWN** — not zero. This is the dossier's main instrumentation gap.

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
| gemini | `g05-gemini3flash-baseline-1` | `g05-sco-rollout-gate__JnK5hsR` | yes | 0 | [case study](../trajectories/gemini--g05-sco-rollout-gate--g05-gemini3flash-baseline-1--g05-sco-rollout-gate__JnK5hsR.md) |
| gemini | `g05-gemini3flash-baseline-1` | `g05-sco-rollout-gate__MMGNYFS` | yes | 0 | [case study](../trajectories/gemini--g05-sco-rollout-gate--g05-gemini3flash-baseline-1--g05-sco-rollout-gate__MMGNYFS.md) |
| gemini | `g05-gemini3flash-baseline-1` | `g05-sco-rollout-gate__PYhR2eh` | yes | 0 | [case study](../trajectories/gemini--g05-sco-rollout-gate--g05-gemini3flash-baseline-1--g05-sco-rollout-gate__PYhR2eh.md) |
| gemini | `g05-gemini3flash-baseline-2` | `g05-sco-rollout-gate__rsDKTXQ` | yes | 0 | [case study](../trajectories/gemini--g05-sco-rollout-gate--g05-gemini3flash-baseline-2--g05-sco-rollout-gate__rsDKTXQ.md) |
| claude | `claude-g05-sco-rollout-gate-1` | `g05-sco-rollout-gate__8fewzuU` | yes | 1 | [case study](../trajectories/claude--g05-sco-rollout-gate--claude-g05-sco-rollout-gate-1--g05-sco-rollout-gate__8fewzuU.md) |
| claude | `claude-g05-sco-rollout-gate-2` | `g05-sco-rollout-gate__CQQzcMe` | yes | 1 | [case study](../trajectories/claude--g05-sco-rollout-gate--claude-g05-sco-rollout-gate-2--g05-sco-rollout-gate__CQQzcMe.md) |
| claude | `claude-g05-sco-rollout-gate-3` | `g05-sco-rollout-gate__m7DeByz` | yes | 1 | [case study](../trajectories/claude--g05-sco-rollout-gate--claude-g05-sco-rollout-gate-3--g05-sco-rollout-gate__m7DeByz.md) |

**Gemini: 0/4 valid trials passed. Claude: 3/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Partly, and differently from how we first framed it.** Claude passes 3/3 and Gemini 0/4, so the task
discriminates sharply by model capability. That makes it a good *difficulty* instrument and a poor
*mechanism* instrument: with a binary reward we cannot see whether Gemini's failures were identification
errors or arithmetic ones. **UNKNOWN.**

## O. What a future *separately versioned* task should change

Criterion-level instrumentation, plus a sibling world in which the naive estimator happens to be right, so that passing for the wrong reason becomes visible.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
