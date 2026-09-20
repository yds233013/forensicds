# Protocol note: `harbor check` is a model run

Written 2026-09-18, after the G05 overnight handoff recorded "$0 model spend" for work that included a
`harbor check`. Established from local artifacts and `harbor check --help` (Harbor 0.21.0). **No model was run to
produce this note.**

## 1. The distinction that must be made in every instruction

| | **A. Solver / baseline model run** | **B. Validation model run (`harbor check`)** |
|---|---|---|
| Purpose | measure whether a model can solve the task | audit task quality against a rubric |
| Sees the answer? | **No** — workspace only; `/solution` and `/tests` are absent from the image | **Yes** — reads the whole task directory, including `solution/` and `tests/` |
| Produces | a reward, a trajectory, a benchmark data point | a pass/fail per rubric item with explanations |
| Contaminates the benchmark? | **Yes** for that model/task pair | **No** (§4) |
| Cost | charged to the baseline budget | charged to the validation budget, ~$0.2–0.6 per invocation |
| Default | `-a gemini-cli -m google/gemini-3-flash-preview` (explicit) | `-a claude-code -m claude-sonnet-4-6` (**implicit defaults**) |

**The failure mode this note exists to prevent:** B is easy to mistake for tooling because its model and agent are
*defaults you never type*. The command reads `harbor check <task> -c tools/task01/harbor_check_config.yaml`, which
looks like a linter invocation and is not.

**Required wording from now on.** An instruction that says "do not run any model" must say which class it means. A
report that says "$0 spend" must state the validation spend separately from the solver spend. The template:

> Solver/baseline model runs: N (model, trials, cost). Validation model runs (`harbor check`): M (cost).

## 2. What the check's model can access

From `jobs/g05-check-prebaseline/check-g05-sco-rollout-gate__2HQjq6n/agent/trajectory.json`, the evaluator read 33
distinct paths under `/app/task/`, including:

- `solution/solve.sh`, `solution/sco_readout/{panel,estimate,report,cli}.py` — **the reference answer**;
- `tests/test_readout.py`, `tests/test.sh`, `tests/scenarios.py`, `tests/world.py` — **the verifier and its frozen
  tolerances**;
- `environment/build/world.py`, `environment/build/history.py` — **the generator, i.e. ground truth**;
- the full agent-visible workspace and `task.toml`, `instruction.md`, `Dockerfile`.

It runs in a Docker container with the task mounted at `/app/task` and writes `/app/check-result.json`. It does
**not** execute the task pipeline or the verifier: `verifier/test-stdout.txt` is empty and the trial's reward (1)
records rubric completion, not a graded solution.

So: **the check agent is given the answer key by design.** That is what lets it judge `hardcoded_solution`,
`tests_or_solution_in_image` and `answer not leaked`. It is the opposite of a baseline condition.

## 3. Is the check's trajectory visible to benchmark designers?

**Yes, in full, and this is worth knowing.** Each check job writes:

- `agent/trajectory.json` (~420 KB for G05) — the complete evaluator transcript;
- `agent/claude-code.txt` (~250 KB) — the rendered session;
- `agent/sessions/projects/-app/*.jsonl` — the raw session log;
- `artifacts/check-result.json` — the 11 rubric items with written explanations.

`jobs/` is git-ignored, so none of this is in the repository; it exists only on the machine that ran the check.
Two consequences:

1. A reviewer cloning the repo gets the *reported* check outcome, not the evidence. Only the report's transcription
   survives.
2. The check transcript contains the solution and verifier verbatim. **It must never be pasted into a context that
   later evaluates a solver**, and it should not be uploaded with baseline artifacts.

## 4. Can `harbor check` contaminate a benchmark baseline?

**No, for the baselines this project runs — but the reasoning is specific, not general.**

Why it does not contaminate the Gemini baselines:

1. **Different model and vendor.** The check ran Anthropic `claude-sonnet-4-6`; the baselines run Google
   `gemini-3-flash-preview`. Nothing is shared between them at inference time.
2. **No persistence across invocations.** Each Harbor trial is a fresh container and a fresh API session. The check
   agent's context does not survive into any later run, of any model.
3. **The check never attempts a solution**, so no solution trace exists to leak into a scoring path.
4. **The baseline image excludes `/solution` and `/tests`** — verified independently by the clean-clone
   reproduction, not by the check.

Where it *could* contaminate, and what to avoid:

- **Same-model baselining.** If a Claude Sonnet 4.6 baseline is ever run on a task that model has already checked,
  the two are not independent in the way a clean baseline requires. There is no cross-session memory, so the risk is
  not mechanical leakage; the risk is that the check's transcript, rubric text, or any of it re-used in a prompt
  would carry answer-key content. **Rule: never baseline a model on a task where its own check transcript is in
  context, and treat same-model check-then-baseline as requiring an explicit note.**
- **Training-data capture.** Whether either vendor retains API traffic for training is a matter of account settings
  and terms, not something this repository can verify. **UNKNOWN from local evidence.** If a task's answer key
  passing through a provider's API is considered a contamination risk, that risk applies to `harbor check` and must
  be decided at the account level, not per task.
- **Re-using check output as design input.** The check's explanations describe the solution. Copying them into an
  instruction or a workspace doc would leak the answer key into the task. It has not been done; it is the easiest
  mistake to make.

## 5. Cost accounting

All `harbor check` jobs on this machine, from `jobs/*/result.json` (`stats.cost_usd`), model
`claude-code__claude-sonnet-4-6__adhoc` in every case:

| Task | Check jobs | Cost |
|---|---|---|
| Task 01 | `task01-check-1` (did not complete) | **UNKNOWN** — no `cost_usd` recorded |
| Task 02 | `task02-check-1` | $0.551443 |
| Task 03 | `-1`, `-2`, `-final` | $1.663657 |
| Task 04 | `-1`, `-final` (+ `-2`, no cost recorded) | $0.960256 + UNKNOWN |
| Task 05 | `task05-check-final` | $0.620244 |
| Task 06 | `task06-check-1` | $0.577774 |
| G08 | `-1`, `-2`, `-3`, `-4` | $1.789020 |
| G10 | `g10-check-prebaseline` | $0.322628 |
| G24 | `g24-check-prebaseline` | $0.594818 |
| G05 | `g05-check-prebaseline` | $0.524253 |
| G34 | `jobs/2026-09-20__01-29-33` (11/11 pass, first and only invocation) | $0.419600 |
| **Total recorded** | 17 jobs with cost | **$8.023692** |

Oracle and Nop jobs cost **$0.0000** — they run no model. Gemini baselines are accounted separately and are already
recorded per task ($0.96 G08, $0.58 G10, $0.51 G24).

**Rules going forward.**

1. Budget ~$0.5 per `harbor check` invocation, and expect several per task during iteration (G08 needed four).
2. Record the check cost in each task's validation report at the time it is run, as `report/task02_validation.md`
   already did (§6, "Evaluator cost $0.55"). That practice was correct and was lost in later reports; this note
   restores it.
3. Never write "$0 model spend" for a validation phase that includes a check.
4. Job directories are git-ignored, so the cost must be transcribed into the report or it is lost when `jobs/` is
   cleaned.

## 6. What remains UNKNOWN

- Whether provider-side retention of the check traffic poses any contamination risk (account/terms question, not
  answerable from local artifacts).
- The cost of `task01-check-1` and `task04-check-2` (no `cost_usd` in their results; task01's check did not
  complete).
- Whether the built-in rubric or evaluator prompt has changed between Harbor versions; all checks here used
  Harbor 0.21.0 defaults with only `agent_setup_timeout_multiplier: 3.0` overridden.
