# ForensicDS

A Harbor benchmark of enterprise data-forensics tasks: an agent receives a business symptom
(e.g. "August recognized revenue is 8–9% above billing; July tied") and must reconcile,
localize, diagnose and causally repair a data pipeline whose root cause is distributed across
data, code, business semantics, configuration and operational history.

Research question and hypotheses: [`research/hypothesis.md`](research/hypothesis.md).

## Layout

| Path | Purpose |
|------|---------|
| `candidates/NN-*/` | Harbor tasks (`instruction.md`, `task.toml`, `environment/`, `tests/`, `solution/`). |
| `research/` | Hypothesis, failure taxonomy, candidate matrix, per-task design docs. |
| `tools/taskNN/` | Dev tooling: local workspace builder, reconciliation diagnostic, mutation (anti-gaming) suite. |
| `tools/make_variant.py` | Creates paired instruction variants (diagnosis vs localized) of a task. |
| `variants/` | Instruction texts for paired conditions. |
| `samples/` | Curated trajectories + failure labels (from `jobs/`). |
| `logs/` | Curated run summaries (raw Harbor `jobs/` is git-ignored). |
| `report/` | Validation reports and final write-up. |

## Final submission (see `report/REPORT.md`)

Final suite (5 tasks; `scripts/final_tasks.json`): Task02, G05, G10, G24, G34.
- gemini-3-flash-preview: 2/15 successful trials; task-level pass@3 = 1/5 (20 %).
- Full pilot pool (12 measured tasks) and all rejected designs: `report/TRIALS.md`, `research/task_design_failure_analysis.md`.
- Excluded: G36 (contaminated, F8), G37/G38 (research-only drops), G39/G40 searches (dropped at gates).

| Script | Purpose |
|--------|---------|
| `scripts/build_results.py` | `report/data/results.json` from raw `jobs/` (read-only) |
| `scripts/check_final_tasks.py` | Oracle=1 / Nop=0 / 3 valid trials on one frozen checksum, per final task |
| `scripts/run_validation.sh` | re-run Oracle + Nop for the final tasks (free, sequential) |
| `scripts/run_tb3_checks.sh` | `harbor check` with the TB3 rubric (paid evaluator) |
| `scripts/make_figures.py`, `scripts/write_appendices.py` | figures, `TRIALS.md`, `VALIDATION.md` |
| `scripts/build_submission.sh` | `submission/{samples,logs,report}` + `submission.zip` |
| `scripts/secret_scan.sh`, `scripts/final_audit.sh` | secret scan; end-to-end audit (never runs a model) |

## Common commands

```bash
# Oracle / Nop
harbor run -p candidates/01-revenue-reconciliation -a oracle -o jobs
harbor run -p candidates/01-revenue-reconciliation -a nop -o jobs

# Anti-gaming mutation suite inside the task image
docker build -t forensicds-task01:dev candidates/01-revenue-reconciliation/environment
python3 tools/task01/shortcuts.py --docker forensicds-task01:dev --report report/task01_mutations.json

# Gemini 3 Flash Preview, 3 trials (requires GEMINI_API_KEY in the environment)
harbor run -p candidates/01-revenue-reconciliation -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs
```
