# Task chapter — `p22-gauge-recalibration`

**Harbor task name** `forensicds/man4471-yield-step-p22` · **difficulty** `hard` · **agent timeout** 5400.0s · **verifier timeout** 5400.0s · **network** `public`  
**Directory** `candidates/p22-gauge-recalibration` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**Kelvin Works, Building 2 — precision machining.** First-pass yield on the MAN-4471 bore has fallen from
97.0% to 92.8% since week 19. Purchasing has drafted a supplier nonconformance against the bar-stock
supplier and wants to escalate to a change of supplier. The supplier has declined the draft, so the claim
must be restated in the form Schedule 3 §3.2 of the supply quality agreement requires.

**The question:** Does the agreement's threshold support raising a supplier nonconformance, and how does the yield loss divide across causes?

## B. Why this is genuinely a data-science problem

Attributing a quality step across candidate causes, on a stratified population, under a contractual
definition, is the core of applied quality engineering.

## C. The tempting but incorrect inherited analysis

Compute the nonconforming rate from the CMM measurements and attribute the step to the material, because
the step coincides with new heat lots. The measurements are real, the rate step is real, the published
report is arithmetically correct.

## D. The actual scientific issue

**In everyday language.**

One of the measuring machines was re-zeroed in week 19. A gauge that reads slightly differently will fail
parts that are actually in tolerance. So some of the 'bad parts' are a measurement artefact, not a supplier
problem — and blaming the supplier would be an expensive mistake.

**Technically.**

**Measurement-system bias presenting as a process shift.** Calibration corrects instrument *bias* against a
traceable standard; Gauge R&R addresses *consistency*; a gauge can be perfectly calibrated and still fail
R&R. The conformance-referenced rate must remove the gauge offset — identifiable because the offset appears
in *reference-artefact* measurements, which the supplier's material cannot have affected — and the residual
must then be attributed across material, tooling and operator before the contractual threshold is applied.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **20 files** |
| generator (never in the final image) | `environment/build/`: `world.py` |
| verifier | `tests/`: `runtime_manifest.sha256`, `scenarios.py`, `test.sh`, `test_gauge.py`, `tolerances.py`, `world.py` |
| reference solution | `solution/`: `quality/__init__.py`, `quality/__main__.py`, `quality/__pycache__/__init__.cpython-314.pyc`, `quality/__pycache__/__main__.cpython-314.pyc`, `quality/__pycache__/attribution.cpython-314.pyc`, `quality/__pycache__/cli.cpython-314.pyc`, `quality/__pycache__/dispositions.cpython-314.pyc`, `quality/__pycache__/report.cpython-314.pyc` … |
| instruction | `instruction.md`, 19 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  README.md
  docs/QP-07_calibration.md
  docs/drawing_MAN-4471.md
  docs/outputs/readout_contract.md
  docs/supply_quality_agreement.md
  docs/table_dictionary.md
  notes/plant_notes.md
  quality/__init__.py
  quality/__main__.py
  quality/__pycache__/__init__.cpython-314.pyc
  quality/__pycache__/__main__.cpython-314.pyc
  quality/__pycache__/attribution.cpython-314.pyc
  quality/__pycache__/cli.cpython-314.pyc
  quality/__pycache__/dispositions.cpython-314.pyc
  quality/__pycache__/report.cpython-314.pyc
  quality/attribution.py
  quality/cli.py
  quality/dispositions.py
  quality/report.py
  reports/quality_report_w24.md
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (19 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `quality/__init__.py`, `quality/__main__.py`, `quality/__pycache__/__init__.cpython-314.pyc`, `quality/__pycache__/__main__.cpython-314.pyc`, `quality/__pycache__/attribution.cpython-314.pyc`, `quality/__pycache__/cli.cpython-314.pyc`.
Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).
**VERIFIED FROM ARTIFACT** for every final task.

## J. What the verifier checks

This task emits **criterion-level rewards**: `decision`, `estimator_implementation`, `evidence_reconstruction`, `identification`, `independent_validation`, `quantitative_results`, `scientific_object`. **VERIFIED FROM ARTIFACT** (`tests/test_gauge.py`).

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
| gemini | `p22-prospective-1` | `p22-gauge-recalibration__rBUvW2D` | yes | 0 | [case study](../trajectories/gemini--p22-gauge-recalibration--p22-prospective-1--p22-gauge-recalibration__rBUvW2D.md) |
| gemini | `p22-prospective-2` | `p22-gauge-recalibration__nt5YXX8` | yes | 0 | [case study](../trajectories/gemini--p22-gauge-recalibration--p22-prospective-2--p22-gauge-recalibration__nt5YXX8.md) |
| gemini | `p22-prospective-3` | `p22-gauge-recalibration__DxMjiB7` | yes | 0 | [case study](../trajectories/gemini--p22-gauge-recalibration--p22-prospective-3--p22-gauge-recalibration__DxMjiB7.md) |
| claude | `claude-p22-gauge-recalibration-1` | `p22-gauge-recalibration__j7n4ZXo` | yes | 0 | [case study](../trajectories/claude--p22-gauge-recalibration--claude-p22-gauge-recalibration-1--p22-gauge-recalibration__j7n4ZXo.md) |
| claude | `claude-p22-gauge-recalibration-2` | `p22-gauge-recalibration__2koWTjr` | yes | 1 | [case study](../trajectories/claude--p22-gauge-recalibration--claude-p22-gauge-recalibration-2--p22-gauge-recalibration__2koWTjr.md) |
| claude | `claude-p22-gauge-recalibration-2__INVALID-credit-balance-too-low` | `p22-gauge-recalibration__kuUVv69` | **no** | 0 | — (invalid) |
| claude | `claude-p22-gauge-recalibration-3` | `p22-gauge-recalibration__arKgDT2` | yes | 0 | [case study](../trajectories/claude--p22-gauge-recalibration--claude-p22-gauge-recalibration-3--p22-gauge-recalibration__arKgDT2.md) |
| claude | `claude-p22-gauge-recalibration-3__INVALID-credit-balance-too-low` | `p22-gauge-recalibration__wZe47bz` | **no** | 0 | — (invalid) |

**Gemini: 0/3 valid trials passed. Claude: 1/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Yes, and it produced the dossier's sharpest single observation.** All three Gemini trials produced
**byte-identical, correct** visible-world output (measurement_system 2.88 pp, material 1.06 pp, corrected
rate 3.81%, `no_supplier_action`) and all three scored 0, failing only the sibling world where tooling is
the true driver, reporting `attribution_pp[tooling] = 0.0` against an expected 3.083.
**VERIFIED FROM ARTIFACT** (`verifier/criteria_notes.txt`). Their attribution code had no path that could
assign the change to tooling. Claude reaches 1/3 here — so the generalisation is achievable, which means
the Gemini result is a capability observation and not a design artefact.

## O. What a future *separately versioned* task should change

Keep it as is; it is the best-designed task in the suite. If versioned, add a fourth cause (operator) as the driver in a further world, and split `quantitative_results` per cause.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
