# Audit 2026-09-23 — requirement-by-requirement compliance

**Caveat recorded first: the original assignment text is not in the repository.** `grep -ril
"abundant\|take-home"` over all tracked Markdown returns nothing. This audit therefore checks the
requirements as restated by the project owner in the audit brief, and flags that the wording of the
source document could not be re-read. Any requirement below marked PASS is PASS against that restatement.

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | 5–10 tasks | **PASS** | 5 tasks in `scripts/final_tasks.json`, 5 in `submission/samples/` |
| 2 | Harbor task format | **PASS** | each task has `task.toml` (schema 1.4), `instruction.md`, `environment/Dockerfile`, `tests/test.sh`, `solution/solve.sh`; all run under Harbor 0.21.0 |
| 3 | ≥3 target-model trials per task | **PASS** | 15 counted trials, 3 per task, each on a single Harbor task digest (`scripts/check_final_tasks.py`) |
| 4 | <30 % pass@3 headroom target | **PASS (1/5 = 20 %)**, with caveat | the *trial* rate is 2/15 = 13 %. Caveat: 4 of the 5 are 0/3 and one is 2/3, so the suite is bimodal rather than uniformly hard |
| 5 | Oracle = 1, Nop = 0 | **PASS** | `jobs/final-oracle-*`, `jobs/final-nop-*` for all five |
| 6 | `harbor check` (task-quality rubric) | **PASS** | `jobs/tb3-check-*` for all five, reward 1 each |
| 7 | Logs shipped | **PASS** | `submission/logs/<task>/trials/*/` with `agent/trajectory.json`, `verifier/reward.txt`, `result.json` for all 15 |
| 8 | Report | **PASS** | `report/REPORT.md`, 12 sections + 3 appendices |
| 9 | Distribution justification | **PASS WITH CAVEAT** | §1 states and defends the slice; the caveat is that the slice was named after the tasks were built, and this audit finds the shipped five span two different task architectures (§16) |
| 10 | Difficulty profile | **PASS WITH CAVEAT** | §2 tabulates traps and objects per task; declared expert-time estimates (90–300 min) are author estimates with no human-trial evidence, and this audit judges several of the *unshipped* pilot tasks materially easier than declared |
| 11 | Research awareness | **PASS** | §8 covers MLE-bench, DSBench, InfiAgent-DABench, DSAEval, DAB, DataSpace, UniDataBench, DataCross, AvalancheBench, plus method sources |
| 12 | Scale plan | **PASS** | §9: mechanism × domain skin × data regime × incumbent bug × decision rule, with the QA gate and costs |
| 13 | Failure analysis from trajectories | **PASS WITH CAVEAT** | §5–§6 are trajectory-derived; this audit revises two specific claims (F10 counting for G05; the F9 share) — see the main report |
| 14 | Automation disclosure | **PASS** | §11 states what Claude Code wrote |
| 15 | Trajectory inspection | **PASS** | per-task analyses in `research/`, re-read and partly revised by this audit |
| 16 | Tasks representative of real DS work | **PASS WITH CAVEAT** | see the realism audit; the mechanisms are real, some workspaces read as rule sheets written for a solver |
| 17 | Failures from genuine difficulty, not ambiguity/environment/verifier defects | **PASS for the shipped five** | all 13 failed final-suite trials trace to model-side defects reproducible from the agents' own submitted code; the one confirmed verifier/instruction defect (G36) was excluded before submission, and the second (Task02 explicit-invariant variant) is not in the suite |
| 18 | Piloting more candidates and curating down | **PASS** | 15 measured tasks, 5 shipped; ~20 concepts rejected pre-build with recorded gates |
