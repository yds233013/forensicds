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

## Task status

| Task | Oracle | Nop | Mutation suite | Model runs |
|------|--------|-----|----------------|------------|
| 01 revenue reconciliation | 1.0 | 0.0 | 28/28 as expected | Gemini 3 Flash: 2/3 pass (pass@3 = 1) |
| 02 renewal-risk regression | 1.0 | 0.0 | 21/21 as expected | not yet run |

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
