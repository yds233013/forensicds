# 04 — Architecture: how a task is built, presented, solved and graded

Every path and line number below is **VERIFIED FROM ARTIFACT**. Jargon is defined on first use.

## The vocabulary, in plain terms

- **Harbor** — the task-running framework (version `0.21.0` here). It builds a Docker image for a task,
  drops an **agent** into it, lets the agent work, then runs a **verifier** and records a **reward**.
- **Agent / scaffold** — the program that wraps a language model and gives it tools (shell, file
  read/write, search). Two were used: `gemini-cli` (wrapping `gemini-3-flash-preview`) and `claude-code`
  (wrapping `claude-opus-5-5`). The *scaffold* is not the model; it decides what the model can do and how
  much of its own reasoning gets recorded.
- **Oracle** — a built-in agent that simply runs the task's own reference solution. Used to prove a task
  is solvable. Must score 1.
- **Nop** — a built-in agent that does nothing. Used to prove the task isn't already solved on arrival.
  Must score 0.
- **Reward** — a number in `/logs/verifier/reward.txt`. 1 = pass, 0 = fail.
- **Criteria** — optional per-capability sub-scores in `/logs/verifier/criteria.json`. Four of our ten
  tasks emit them; the rest emit reward only.
- **Hidden / sibling worlds** — additional datasets generated from the same code with different seeds and
  different *mechanism parameters*. The agent never sees them. The verifier grades the agent's work
  against all of them.
- **Trajectory** — a JSON record of what the agent did: tool calls, arguments, and (scaffold permitting)
  reasoning summaries.

## End-to-end, for one task

```
AUTHORING (never seen by the agent)
  environment/build/world.py        seeded generator: makes the warehouse + operational artefacts
  tests/scenarios.py                declares hidden sibling worlds (hidden_a, hidden_b, …)
  solution/                         the reference analysis
  tests/test_*.py, tests/test.sh    the verifier

BUILD TIME  (docker build)
  ┌ FROM python:3.12-slim-bookworm@sha256:7824…   AS base        [line 1]
  │   pip install numpy pandas scipy statsmodels  (pinned)
  ├ FROM base AS extract                                          [line 15]
  │   COPY workspace/ /workspace/
  │   COPY build/ /tmp/build/
  │   RUN python /tmp/build/world.py /workspace     ← data is generated HERE
  └ FROM base                                                     [line 22]
      COPY --from=extract /workspace/ /workspace/                  [line 23]
                    ▲
         only /workspace is carried forward, so the generator is absent
         from EVERY layer of the final image

RUN TIME
  agent sees:  /workspace  +  instruction.md
  agent cannot see:  tests/ · solution/ · environment/build/ · any hidden world

GRADING  (tests/test.sh, then tests/test_*.py)
  harden the sandbox → verify runtime integrity → run the graded checks
  → write reward.txt (+ criteria.json where instrumented)
```

`candidates/g50-courier-boost-rollout/environment/Dockerfile` lines 1, 15, 22-23 are the real excerpt
above. Nine of the ten final tasks use this two-stage pattern; `02-renewal-risk-regression` does not,
which is defect **D2** in chapter 09.

## The agent's view

`instruction.md` is a short business memo — 15 to ~30 lines. It states the role, the decision, where to
start, and the output contract. It **never** names the mechanism. Example (`g50`, lines 1-4):

> Boost is the courier incentive Operations piloted this spring… The programme readout says it cuts the
> late-delivery rate by 4.0 points and recommends national rollout. The July investment committee will
> take that decision.

The workspace contains what a real analyst would have inherited: a SQLite warehouse or CSV drops, the
**incumbent analysis** as runnable Python, the published report that analysis produced, the governing
document (a contract, a model-risk standard, a decision memo), and a data dictionary.

**The incumbent analysis is the design centrepiece.** It executes, it is documented, and it is a *correct
computation of the wrong quantity*. In `g50` it computes the phase-2 arm contrast accurately, with a
narrow interval, consistent across all sixteen markets — and includes a capacity check that **cannot
fail**, because both arms draw on the same courier pool.

## Sandbox defences (`tests/test.sh`, `g50`)

Real line numbers:

| line | defence | why |
|---|---|---|
| 48-50 | `chown -R 0:0 /workspace`, `chmod 700 /tests` | the re-executed pipeline cannot read its own original workspace or the verifier |
| 54-58 | `setpriv --reuid=65534 … test -r` then `refuse` | *proves* the two directories are unreadable rather than assuming it |
| 64 | `setpriv … test -w /logs/verifier/reward.txt` → warn | detects a mode-ignoring bind mount (macOS) and says so rather than claiming protection it lacks |
| 74-77 | per-architecture runtime manifest + `sha256sum -c` → `refuse` | the interpreter, library tree and sandbox binaries must match the pinned image |
| 81 | expected-vs-actual library file list | catches files *added* to the library tree |
| 83 | `/etc/ld.so.preload` present → `refuse` | blocks the classic loader hijack |
| 90, 102 | loader drop-ins unchanged; every loaded shared object resolves to a pinned path | blocks loader redirection without breaking on `ldconfig` regeneration (this is the **D4** fix) |

`refuse` writes reward 0 **and declines to grade**. That design choice is why the `claude-code` incompatibility
(**D5**) shows up as an invalid trial rather than as a silent model failure.

## Why outputs must generalise: the re-execution verifier

`g50` is the only task whose verifier re-runs *the agent's own command*. From
`tests/test_boost.py`:

```python
RUN_ARGS = ["-m", "northline_eval", "readout",
            "--db", "data/northline.sqlite", "--out", "out"]          # line 37
SKIP_TREE = {"data", "out", "__pycache__", ".git", …}                  # line 84
...
shutil.rmtree(out, ignore_errors=True)   # no stale outputs survive into grading   line 205
proc = subprocess.run([PIPELINE_PYTHON] + RUN_ARGS, cwd=str(scratch), …)          # line 208
...
if p.stat().st_mtime < run["t0"] - 1.0:  # the file must post-date the run         line 232
```

and the scratch root is `tempfile.mkdtemp(prefix="g50-", dir="/tmp")` (line 388) with per-world
directories named `r0`…`r4`, so nothing in the agent's surroundings reveals which world it is in.

**Why this matters, concretely.** A submission that runs the correct analysis once, reads its own
`out/readout.json`, and bakes the numbers in as literals will pass the visible world and fail every
hidden one. That mutation was run during `g50`'s validation and behaved exactly so
(**REPORTED, not reverified here** — requires Docker). A static grader would have scored it 1.

The other nine tasks grade produced artefacts against per-world expectations rather than re-executing a
named command, but the generalisation property is the same: the same submitted analysis is checked against
`hidden_a`, `hidden_b`, `hidden_c` (and `hidden_d` for `g36` and `g50`).

## Why a plausible wrong solution should fail

Three independent mechanisms, and a task needs at least two of them to be sound:

1. **Cross-world conjunction.** The incumbent's mechanism-specific answer is right in the visible world
   and wrong where the mechanism differs. This is what defeated all three `p22` Gemini trials.
2. **Tolerance bands calibrated against legitimate alternatives.** `g50`'s tolerance was fixed by a stated
   rule — 1.6× the reference's own worst deviation — *before* its mutation suite ran, and deliberately not
   re-tuned afterwards. That ordering is what stops a tolerance from being fitted to the mutations.
3. **Criterion decomposition.** Where present, a wrong analysis that stumbles onto the right decision
   still loses `quantitative_results`. Chapter 08 shows this happened in 7 instrumented trials.

## How criteria are emitted

`candidates/p22-gauge-recalibration/tests/test_gauge.py` lines 50-59:

```python
@atexit.register
def _dump():
    out = Path("/logs/verifier")
    out.mkdir(parents=True, exist_ok=True)
    (out / "criteria.json").write_text(json.dumps(_state, sort_keys=True) + "\n")
    (out / "criteria_notes.txt").write_text("\n".join(_notes) + "\n")
```

`criteria_notes.txt` is the single most valuable artifact in the project for diagnosis — it records the
produced value, the expected value and the tolerance, per field per world. It is the reason chapter 08 can
say *where* an analysis was wrong.

`test.sh` then merges criteria into Harbor's `reward.json` as `criterion_*` keys alongthe headline
`reward` (`g50/tests/test.sh:144,149`; the P-series at `:99,104`).

## Freeze hashes

Each task carries an aggregate hash over path+content (`MACHINE_READABLE_INVENTORY.csv`). `g50`
additionally separates five groups — target-visible, generator, verifier, oracle, complete — so a reader
can tell *what kind* of change a digest shift represents. When `hidden_d` was added, group A
(target-visible) was unchanged and only group B moved, which is the evidence that the fifth world changed
nothing the agent sees.

## An architectural weakness worth naming

The verifier runs **inside** the container it is verifying, and checks the runtime with `sha256sum`, which
is itself a pinned binary dynamically linked against a pinned `libc`. An agent with root during the
episode that could rewrite all of them consistently would defeat the check. Pinning the `ldd` closure
raises the bar substantially; no container-internal verifier removes the circularity.
