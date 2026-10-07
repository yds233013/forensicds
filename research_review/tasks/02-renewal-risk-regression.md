# Task chapter — `02-renewal-risk-regression`

**Harbor task name** `forensicds/renewal-risk-regression-02` · **difficulty** `hard` · **agent timeout** 3600.0s · **verifier timeout** 2700.0s · **network** `public`  
**Directory** `candidates/02-renewal-risk-regression` — verified byte-identical to `submission_final10.zip`. **VERIFIED FROM ARTIFACT.**

## A. The company story and business question

**Northwind-style B2B SaaS, Revenue Data Science.** A model called `renewal-risk v2.4` predicts which
customer accounts will fail to renew. It was trained in February, scored far better offline than the
previous `v2.3`, and has been scoring live renewals since March. Sales and Customer Success now say the
scores are unusable, and the monitoring dashboards do not resemble the model that was approved. The Q3
retrain is frozen pending an explanation.

**The question:** Is `v2.4` fit to keep scoring renewals, and can the Q3 retrain be released?

## B. Why this is genuinely a data-science problem

Churn/renewal risk scoring is one of the highest-volume applications of applied ML in B2B software. The
work here — rebuild the training pipeline, re-derive the evaluation, explain an offline/online gap — is
the daily job of a revenue data scientist, not a puzzle.

## C. The tempting but incorrect inherited analysis

The inherited pipeline computes account 'health' features as **time-windowed aggregates** read from the
current state of the warehouse, then joins them to renewal outcomes. Offline AUC looks excellent. The
analysis is internally coherent and the code runs.

## D. The actual scientific issue

**In everyday language.**

Some of the features are computed from data that did not exist yet when the prediction would have been
made. The model is effectively being told part of the answer. Offline it looks brilliant; in production,
where the future is genuinely unavailable, it does not.

**Technically.**

**Point-in-time correctness.** A training row for account *a* with label observed at time *t* must carry
feature values **as of** *t*, i.e. the most recent value with timestamp ≤ *t*. The inherited pipeline reads
feature values from a mutable store whose rows are overwritten, so a feature for a row labelled in January
can reflect a March value. This is *label leakage via non-point-in-time features*. It inflates offline
metrics and vanishes in production, where the serving path has no future data. The fix is a temporal
('as-of') join, and the evaluation must be recomputed on the corrected matrix.

## E. Map of task files

| area | contents |
|---|---|
| agent-visible workspace | **34 files** |
| generator (never in the final image) | `environment/build/`: `history_artifacts.py`, `pit_reference.py`, `world.py` |
| verifier | `tests/`: `reference.py`, `reference_model.py`, `scenarios.py`, `test.sh`, `test_renewal_risk.py`, `world.py` |
| reference solution | `solution/`: `audit_point_in_time.py`, `renewal_risk/features/health.py`, `renewal_risk/features/pipeline_signals.py`, `renewal_risk/sources/history.py`, `renewal_risk/sources/warehouse.py`, `solve.sh` |
| instruction | `instruction.md`, 17 lines |
| provenance | `REAL_DISTRIBUTION_PROVENANCE.md` present |

Agent-visible workspace inventory:

```
  CHANGELOG.md
  README.md
  config/pipeline.toml
  docs/data/warehouse_data_dictionary.md
  docs/feature_dictionary.md
  docs/model_card_renewal_risk.md
  docs/ops/2025-11_inc1874_crm_replication.md
  docs/ops/2026-01_crm_v3_migration.md
  docs/process/model_retraining_runbook.md
  logs/deployments.csv
  logs/scheduler/training_runs.csv
  requirements.lock
  src/renewal_risk/__init__.py
  src/renewal_risk/__main__.py
  src/renewal_risk/cli.py
  src/renewal_risk/config.py
  src/renewal_risk/examples.py
  src/renewal_risk/features/__init__.py
  src/renewal_risk/features/build.py
  src/renewal_risk/features/contract.py
  src/renewal_risk/features/health.py
  src/renewal_risk/features/pipeline_signals.py
  src/renewal_risk/features/registry.py
  src/renewal_risk/features/support.py
  src/renewal_risk/features/usage.py
  src/renewal_risk/model/__init__.py
  src/renewal_risk/model/evaluate.py
  src/renewal_risk/model/train.py
  src/renewal_risk/model/transforms.py
  src/renewal_risk/pipeline.py
  src/renewal_risk/reporting.py
  src/renewal_risk/scoring.py
  src/renewal_risk/sources/__init__.py
  src/renewal_risk/sources/warehouse.py
```

## F. How the data was generated

**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**
in a stage whose layers are not copied into the final image, so the data-generating process is absent
from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: **`hidden_a`, `hidden_b`, `hidden_c`**. **VERIFIED FROM ARTIFACT.**

What is synthetic: the company, the people, every row of data, and all generator parameters. What is
preserved from real practice: the artefact surface, the governing document, and the fact that the
inherited analysis is a correct computation of the wrong quantity.

## G. The agent's tools and instructions

The agent receives `instruction.md` (17 lines) and a populated `/workspace`. It has
the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the
mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the
hidden worlds.

## H. Dependency map

See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts
support; where a task is genuinely short this is said rather than padded.

## I. The reference solution

`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the
pipeline. Reference modules: `audit_point_in_time.py`, `renewal_risk/features/health.py`, `renewal_risk/features/pipeline_signals.py`, `renewal_risk/sources/history.py`, `renewal_risk/sources/warehouse.py`, `solve.sh`.
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
| gemini | `task02-gemini3flash-diagnosis` | `02-renewal-risk-regression__JctTpSi` | yes | 0 | [case study](../trajectories/gemini--02-renewal-risk-regression--task02-gemini3flash-diagnosis--02-renewal-risk-regression__JctTpSi.md) |
| gemini | `task02-gemini3flash-diagnosis` | `02-renewal-risk-regression__nXXMdDm` | yes | 0 | [case study](../trajectories/gemini--02-renewal-risk-regression--task02-gemini3flash-diagnosis--02-renewal-risk-regression__nXXMdDm.md) |
| gemini | `task02-gemini3flash-diagnosis` | `02-renewal-risk-regression__pf9zaPc` | yes | 0 | [case study](../trajectories/gemini--02-renewal-risk-regression--task02-gemini3flash-diagnosis--02-renewal-risk-regression__pf9zaPc.md) |
| claude | `claude-02-renewal-risk-regression-1` | `02-renewal-risk-regression__Q6Cwv6g` | yes | 1 | [case study](../trajectories/claude--02-renewal-risk-regression--claude-02-renewal-risk-regression-1--02-renewal-risk-regression__Q6Cwv6g.md) |
| claude | `claude-02-renewal-risk-regression-2` | `02-renewal-risk-regression__TFChTfx` | yes | 1 | [case study](../trajectories/claude--02-renewal-risk-regression--claude-02-renewal-risk-regression-2--02-renewal-risk-regression__TFChTfx.md) |
| claude | `claude-02-renewal-risk-regression-3` | `02-renewal-risk-regression__gJgbpBV` | yes | 1 | [case study](../trajectories/claude--02-renewal-risk-regression--claude-02-renewal-risk-regression-3--02-renewal-risk-regression__gJgbpBV.md) |

**Gemini: 0/3 valid trials passed. Claude: 3/3 valid trials passed.** Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.

## N. Does this task isolate the proposed failure mode?

**Partially.** It tests evidence reconstruction and estimand/population repair, and the fix must survive
sibling worlds. It does *not* isolate the 'recognises-but-cannot-quantify' phenomenon, because the task's
reward is binary: a trial that diagnosed leakage but mis-measured the corrected AUC is indistinguishable
from one that never diagnosed it. **UNKNOWN** which of those happened in the Gemini failures.

## O. What a future *separately versioned* task should change

Instrument it. A v2 should emit separate criteria for (i) metric population rebuilt as-of, (ii) leaked
features identified, (iii) corrected offline metric within tolerance, (iv) decision. That single change
would let this task contribute to the central failure-mode question instead of only to the pass rate.

---

*The frozen original is never edited. Every improvement above belongs in a new version with its own
exposure record.*
