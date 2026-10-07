# Evidence index

Every substantive numeric or factual claim in the dossier, mapped to the artifact it came from.
"RERUN" = I re-executed the check in this session.

## Repository state

| claim | evidence | status |
|---|---|---|
| HEAD `7e6d4d760995c7bd3729a8cbba31e5a31a8801fe`, 106 commits, 2026-09-12 → 09-25 | `git rev-parse HEAD`, `git log`, `git rev-list --count HEAD` | RERUN |
| `submission_final10.zip` sha256 `629476cd886bd16eeb206e952c26be41370f9f79b149fa21cda0ecdf7779af7e` | `SUBMISSION_SHA256.txt`; `shasum -a 256 -c` | RERUN |
| all ten final tasks byte-identical to the ZIP | extract `samples/<task>/`, `diff -rq --exclude=__pycache__` | RERUN |
| fallback archive unchanged, `c8561aad8300df6c832921fa…` | `shasum -a 256 submission_5task_fallback.zip` | RERUN |
| `submission.zip` is a byte-identical copy of the fallback | both hash to `c8561aad8300df6c8329…` | RERUN |
| 24 task directories; 13 shipped in the ZIP | `MACHINE_READABLE_INVENTORY.csv` | RERUN |

## Results

| claim | evidence | status |
|---|---|---|
| Gemini 31 valid trials, 1 pass, 3.2%, pass@3 10% | `ALL_TRIALS.csv` ← `jobs/*/*/verifier/reward.txt`; `build_results.py` | RERUN |
| Claude 27 valid trials, 13 passes, 48.1%, pass@3 56% on 9 tasks | `ALL_TRIALS.csv` ← `crossmodel_logs/claude/*/*/verifier/reward.txt` | RERUN |
| joint subset: Gemini 1/28, Claude 13/27 | `10_CROSS_MODEL_COMPARISON.md`, computed | RERUN |
| 45 invalid attempts, 9 distinct causes | `INFRASTRUCTURE_FAILURE_REGISTER.md` | RERUN |
| Claude spend $23.0708 | sum of `final_metrics.total_cost_usd` over all Claude trajectories | RERUN |
| Claude median $0.80/trial; most expensive `g10`-1 at $3.0838, 53 steps | per-trajectory `final_metrics` | RERUN |
| Gemini cost not recorded | `gemini-cli` trajectories carry no `total_cost_usd` | VERIFIED (absence) |
| `g05` has 4 Gemini trials, not 3 | `jobs/g05-gemini3flash-baseline-1` (3 trials) + `-2` (1) | RERUN |
| `02…__explicit-invariant` ablation 0/3 | `jobs/task02-gemini3flash-explicit-invariant` | RERUN |
| `p20-v1.1` 0/3 with zero sign failures | `jobs/p20v11-gemini-{1,2,3}`; sign audit | RERUN |

## Criterion-level

| claim | evidence | status |
|---|---|---|
| exactly 5 directories emit `criteria.json` | observed in trial dirs, cross-checked against `tests/*` | RERUN |
| instrumentation sites: `g50` `tests/test_boost.py:424`, `tests/test.sh:144,149`; `p20`(+v1.1) `tests/test_monitoring.py:7,56`, `tests/test.sh:99,104`; `p22` `tests/test_gauge.py:6,55`; `p31` `tests/test_fill.py:10,59` | `grep -n criteria.json` | RERUN |
| 24 instrumented **valid** trials; 32 instrumented records incl. invalid | `CRITERION_RESULTS.csv` | RERUN |
| Gemini: evidence 14/15, object 11/15, validation 11/12, estimator 11/12, identification 5/12, decision 4/15, quantity 2/12 | `build_results.py` over `CRITERION_RESULTS.csv` | RERUN |
| Claude: evidence 9/9, object 9/9, validation 9/9, estimator 7/9, identification 4/9, decision 4/9, quantity 3/9 | same | RERUN |
| 11 distinct criterion-failure shapes | `_shapes.json`, derived in chapter 08 | RERUN |
| 7 trials pass `decision` while failing the quantity | chapter 08 computation | RERUN |
| 4 trials pass the quantity and fail `decision` | chapter 08 computation | RERUN |
| 1 full pass: `claude-p22-gauge-recalibration-2`, all 7 criteria | `verifier/criteria.json`; empty `criteria_notes.txt` | RERUN |

## Specific per-trial findings

| claim | evidence | status |
|---|---|---|
| `p22` Gemini ×3 byte-identical visible output; `attribution_pp[tooling] 0.0 vs 3.083` on `hidden_c` | `jobs/p22-prospective-{1,2,3}/*/verifier/criteria_notes.txt` | RERUN |
| `g50` Gemini ×3: `programme_effect_pp` within 0.000 pp of the arm contrast; interval 1.882 pp; `courier_hours_response_pct +0.366`; `decision roll_out` | `jobs/g50-gemini3flash-v23-1/*/verifier/test-stdout.txt` | RERUN |
| `p31` `bridge_pp[aggregation] 24.18 vs 1.831`; `incumbent_verdict` expected `not_determinable_from_available_evidence` | `jobs/p31-prospective-3/*/verifier/criteria_notes.txt` | RERUN |
| Claude `p20` ×3 sign flips, e.g. `−10.57 vs +10.849` on three worlds each | `crossmodel_logs/claude/claude-p20-noshow-monitoring-*/*/verifier/criteria_notes.txt` | RERUN |
| sign-flip totals: Claude `p20` 12, Gemini `p20` 7, `p20-v1.1` 0, `p22`/`p31` 0 both arms | field-level regex audit over all `criteria_notes.txt` | RERUN |
| no `p20` trial fails on sign alone | same audit, per-trial genuine-failure counts | RERUN |
| `g36`: Claude 13-15 steps vs Gemini 40-54 | per-trajectory step counts | RERUN |
| `g08`: the one passing Gemini trial is its most effortful (106 vs 90, 90 steps) | per-trajectory step counts | RERUN |
| `p31-prospective-1`: 4 steps, 23,987 prompt tokens, 5 tool calls, no outputs — **BORDERLINE** | `jobs/p31-prospective-1/*/agent/trajectory.json`; flagged in `ALL_TRIALS.csv` | RERUN |

## Architecture

| claim | evidence | status |
|---|---|---|
| multi-stage build keeps the generator out of every layer | `g50/environment/Dockerfile:1,15,22-23` | RERUN |
| 9 of 10 tasks multi-stage; `02` is not | `MACHINE_READABLE_INVENTORY.csv` `multistage_build` | RERUN |
| sandbox defences | `g50/tests/test.sh:48,50,54-58,64,74-77,81,83,90,102` | RERUN |
| re-execution core | `g50/tests/test_boost.py:37,84,205,208,232,388` | RERUN |
| criteria emission pattern | `p22/tests/test_gauge.py:50-59` | RERUN |
| hidden worlds per task (`hidden_a..c`, plus `hidden_d` for `g36` and `g50`) | `tests/scenarios.py` per task | RERUN |

## Integrity findings

| claim | evidence | status |
|---|---|---|
| D1 `p20` sign convention absent in v1, present in v1.1 | `grep` on both `readout_contract.md` | RERUN |
| D2 `02` single-stage leak; `pit_reference.py` 10,301 bytes exists | Dockerfile static check; `os.path.getsize` | RERUN (static) |
| D2 layer extraction and `ls /tmp/build` unreachable | prior report | **REPORTED, NOT REVERIFIED** (Docker down) |
| D3 `g50` fifth world present | `grep hidden_d tests/scenarios.py` | RERUN |
| D4 `ld.so.cache` pin removed; resolution check present | manifest grep (0 hits); `test.sh` grep (1 hit) | RERUN |
| D5 which file `claude-code` trips | `test.sh:76` discards the filename | **UNKNOWN** |
| D5 agent ran on the de-confounding attempt: 16 steps, $0.6594 | that trial's `trajectory.json` | RERUN |
| D7 drift false alarm resolved by fresh extraction | re-extracted and re-diffed | RERUN |
| `p31` implements justified deferral | `tests/scenarios.py:13`, `tests/world.py:290,294,300`, `tests/test_fill.py:285,288`, `solution/service/adjudicate.py:12,20`, `environment/workspace/docs/outputs/readout_contract.md:42` | RERUN |
| the final report denies such a world exists | `report/FINAL_REPORT.md:982`, `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md:794` | RERUN |
| original assignment text absent from the repo | `research/audit/abundant_requirements.md` opening caveat; re-ran the search | RERUN |
| README documents the superseded five-task suite | `README.md:26` | RERUN |

## Claims deliberately NOT made

| not claimed | why |
|---|---|
| behavioural rates (recognition, revision, propagation) for either arm | scaffold reasoning-text asymmetry: `gemini-cli` median 10,199 chars vs `claude-code` 1,003. RERUN measurement; the *rates* are withdrawn |
| that the two models fail for the same internal reason | identical criterion patterns do not imply identical causes |
| that the benchmark measures a general frontier gap | 5 of 9 tasks fell to one frontier model |
| statistical significance anywhere | 3 trials per task |
| process supervision from Harbor rewards | Harbor verifies final state only |
