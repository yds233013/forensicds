# logs/ — Harbor output for every counted trial

One directory per task (named as in `samples/`):

| path | contents |
|---|---|
| `<task>/trials/<trial>/` | Harbor output of each of the 3 counted `gemini-cli` / `google/gemini-3-flash-preview` trials (see below) |
| `<task>/trials/job_<job>_*.json/.log` | job-level `config.json`, `result.json` and `job.log` |
| `<task>/invalid/` | infrastructure-invalid runs, kept for transparency; **not counted** (G05 only) |
| `<task>/validation/` | final Oracle and Nop runs on the frozen task checksum, plus `harbor check` reports |

Each trial directory contains:
- `agent/trajectory.json`: the ATIF trajectory;
- the native gemini-cli transcript;
- `verifier/`: `reward.txt`, test stdout, `ctrf.json`;
- `result.json`, `config.json` and `trial.log`;
- `artifacts/`: the agent's final `/workspace` snapshot.

**Artifact size limit.** To keep the archive a reasonable size, `artifacts/` keeps only files of **1 MB or
less**. That covers all of the agent's code and its outputs. Large data files (warehouse extracts,
multi-MB CSVs) are dropped; they are regenerated deterministically by each task's environment build.

The trials, rewards, costs and checksums are tabulated in `report/TRIALS.md`, generated from these
`result.json` files by `scripts/build_results.py` and `scripts/write_appendices.py`.
