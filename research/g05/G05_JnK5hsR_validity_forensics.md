# Forensic adjudication: was G05 trial `JnK5hsR` a valid agent trial?

Written 2026-09-18. **Forensics only.** No model was run, no replacement trial launched, no API spend, and nothing
in `candidates/g05-sco-rollout-gate/` was read-modified — only read. G05 checksum unchanged at `77a6e432d9d2cba2`.

**The scientific quality of Gemini's output plays no part in this adjudication.** Validity here is about execution
integrity only.

**Conclusion: (B) INVALID INFRASTRUCTURE FAILURE, confidence MEDIUM.**

---

## 1. Execution timeline comparison

Harbor phase records (`result.json`, UTC):

| Trial | Agent exec end | Gap | Verifier start | Verifier duration | Verifier end | Post-verifier |
|---|---|---|---|---|---|---|
| `JnK5hsR` | 10:00:17.247 | 14.86 s | 10:00:32.105 | **2.18 s** | 10:00:34.285 | 14.17 s |
| `MMGNYFS` | 10:00:55.149 | 6.87 s | 10:01:02.020 | 176.52 s | 10:03:58.543 | 27.55 s |
| `PYhR2eh` | 10:01:28.596 | 4.60 s | 10:01:33.195 | 220.13 s | 10:05:13.322 | 22.42 s |

Docker daemon log (`~/Library/Containers/com.docker.docker/Data/log/vm/01-docker.log.{3,2}`), container→trial
association established from adjacent compose-project filters (`…project=g05-sco-rollout-gate__<trial>__env`):

| Trial | container | exec calls around the verifier phase |
|---|---|---|
| `JnK5hsR` | `e98479a85481` | 10:00:30.97, **10:00:33.34**, 10:00:33.95, 10:00:35.65, **stop 10:00:37.34** |
| other-A (`MMGNYFS`) | `0d280434d807` | …10:01:00.14, **10:01:03.36**, 10:01:04.02, *(silence 175 s)*, 10:03:58.91, 10:03:59.42, 10:04:00.44, **stop 10:04:01.60** |
| other-B (`PYhR2eh`) | `dbc9a983c594` | …10:01:31.88, **10:01:34.52**, 10:01:35.15, *(silence 218 s)*, 10:05:13.98, 10:05:14.66, 10:05:15.44, **stop 10:05:16.19** |

**The structural signature is identical in all three.** Each verifier phase issues an exec pair at roughly +1.2 s and
+1.9 s after `verifier.started_at`. In the two successful trials that pair is followed by a long silence — test.sh
running — of 175 s and 218 s. In `JnK5hsR` there is **no silence**: the next exec arrives 0.6 s later and the phase
ends.

### Reconstructed stage sequence

| Stage | `JnK5hsR` | `MMGNYFS` / `PYhR2eh` |
|---|---|---|
| Agent end | 10:00:17.247 | 10:00:55.149 / 10:01:28.596 |
| Artifact collection (exec burst) | 10:00:16.39–10:00:20.50 | 10:00:54.15–10:01:00.14 / 10:01:27.70–10:01:31.88 |
| Verifier phase start | 10:00:32.105 | 10:01:02.020 / 10:01:33.195 |
| test.sh exec issued | **10:00:33.34 (+1.24 s)** | 10:01:03.36 (+1.34 s) / 10:01:34.52 (+1.33 s) |
| test.sh reaches line 11 (`echo 0 > reward.txt`) | **CONFIRMED** (§2) | yes |
| Stray-process sweep | **UNKNOWN** | assumed yes |
| venv create + pip install from wheels | **NO** (no time, no output) | yes (~25–30 s) |
| pytest invocation | **NO** | yes |
| Test collection (14 items) | **NO** | yes |
| ctrf.json generation | **NO** | yes |
| Verifier termination | 10:00:34.285 | 10:03:58.543 / 10:05:13.322 |
| Container stopped | 10:00:37.34 (3.1 s later, clean) | 10:04:01.60 / 10:05:16.19 (clean) |

---

## 2. Exact `JnK5hsR` verifier evidence

### How Harbor runs the verifier (read from the installed Harbor 0.21.0 source)

`harbor/verifier/verifier.py:185-202` builds the command with
`harbor/utils/scripts.py:122-160`, which produces:

```
(/tests/test.sh) > /logs/verifier/test-stdout.txt 2>&1
```

Two consequences that make the evidence unusually sharp:

1. **stderr is merged into `test-stdout.txt`.** Any refusal line, bash diagnostic, traceback or error message
   produced by test.sh would be in that file. It is **0 bytes**.
2. **Harbor does not pre-create `reward.txt`** in the Docker path. `verifier.py:227-236` raises
   `RewardFileNotFoundError` when no reward file exists, and `_parse_reward_text` (`verifier.py:66-79`) raises when
   the file is empty. Harbor parsed reward `0.0` with no exception, so a non-empty `reward.txt` existed **inside the
   container**. The only writer of that file is `tests/test.sh`.

### Findings

| Question | Answer | Status |
|---|---|---|
| Did `test.sh` start? | **Yes.** `reward.txt` = `0` can only have been written by `test.sh` line 11 | **CONFIRMED** |
| Earliest confirmed executed line | line 11, `echo 0 > /logs/verifier/reward.txt` (line 10 `mkdir -p` implied) | **CONFIRMED** |
| Did the stray-process sweep execute? | no direct record; it is the next block after line 11 | **UNKNOWN** |
| Did pytest start? | **No** — pytest `-rA` always prints a session header, and stdout+stderr are empty | **CONFIRMED** |
| Did pytest collect anything? | No | **CONFIRMED** |
| Was the ctrf plugin invoked / `ctrf.json` created? | No; file absent | **CONFIRMED** |
| Was the venv created / wheels installed? | No — 2.18 s is far below the ~25–30 s the sibling trials needed, and both failure paths call `refuse` (which prints) | **SUPPORTED BUT NOT PROVEN** |
| Did any `refuse` path fire? | **No** — every `refuse` echoes to stdout, which is merged and empty | **CONFIRMED** |
| exit code of the test.sh exec | not recorded by Harbor or the daemon log | **UNKNOWN** |
| signal | not recorded | **UNKNOWN** |
| container exit status | container removed (`delete: true`); no retained event | **UNKNOWN** |
| OOMKilled flag | container removed; docker event ring buffer no longer covers 10:00 (healthcheck traffic from unrelated stacks flushed it) | **UNKNOWN** |
| Was the container alive during and after the verifier? | **Yes** — it accepted execs at 10:00:33.34, 10:00:33.95 and 10:00:35.65, and was stopped cleanly at 10:00:37.34, 3 s after the verifier phase ended | **CONFIRMED** |
| stdout | 0 bytes | **CONFIRMED** |
| stderr | merged into the same 0-byte file | **CONFIRMED** |
| Harbor exception | `exception_info: null`; job reports `n_errored_trials: 0` | **CONFIRMED** |
| Verifier exception | none recorded | **CONFIRMED** |
| Timeout | no — 2.18 s against `timeout_sec = 7200.0` | **CONFIRMED** |
| PIDs / process groups at verifier time | not recorded | **UNKNOWN** |
| Kernel/Docker OOM evidence | **none** — zero matches for `out of memory`, `oom-kill`, `oom_reaper`, `Killed process` in the Docker VM console log, which covers 2026-09-17 15:20 → 2026-09-18 03:58 local and therefore the whole run | **CONFIRMED (negative)** |

**Net picture:** `test.sh` started, wrote its initial reward line, and terminated within ~1–2 seconds **without
emitting a single byte to stdout or stderr**, while its container remained healthy. Under
`(script) > file 2>&1`, a `SIGKILL` of the subshell produces exactly this artifact set: the reward file already
written, an empty redirect target, no ctrf, and no exception — because the killed subshell cannot print and the
outer shell's own message is not captured into the file.

---

## 3. Agent-caused failure audit

**Every shell command `JnK5hsR` issued, in full (10 total):**

```
 1. sqlite3 data/warehouse.sqlite "SELECT * FROM rollout_plan LIMIT 10;"   (failed: command not found)
 2. python inspect_db.py
 3. python check_kits.py
 4. python -m sco_readout gate --warehouse data/warehouse.sqlite --out out (failed: ValueError)
 5. python -m sco_readout gate --warehouse data/warehouse.sqlite --out out
 6. head -n 10 out/analysis_panel.csv
 7. python check_estimates.py
 8. python check_basket.py
 9. python check_simple.py
10. rm inspect_db.py check_kits.py check_estimates.py check_basket.py check_simple.py
```

| Checked for | Result |
|---|---|
| `pytest.ini`, `pyproject.toml`, `conftest.py`, `tox.ini`, `setup.cfg` | **none** (absent from the captured workspace; zero trajectory hits) |
| `sitecustomize.py`, `usercustomize.py`, `.pth` | **none** |
| pip config / `.pypirc` | **none** |
| `pip install` / `pip3 install` / `apt-get` | **none** — zero occurrences |
| Shell startup changes, `PATH` / `PYTHONPATH` / `PYTHONSTARTUP` | **none** |
| stdlib or site-packages changes | **none.** The 21 `site-packages` / `/usr/local/lib` strings in the trajectory occur exclusively inside tool *results* (pandas frames in tracebacks the agent read); **0 commands reference them** |
| Process spawning / background jobs (`&`, `nohup`, `setsid`, `disown`) | **none** |
| Signal handlers, `trap`, `kill`, `ulimit` | **none** |
| Process-group manipulation | **none** |
| Docker-related actions | **none** |
| Permission changes (`chmod`, `chown`, `umask`) | **none** |
| Access to `/tests`, `/logs`, verifier or test tampering | **none** — no command references either path |
| Warehouse tampering | **none.** `data/warehouse.sqlite` is byte-identical across all three trials (sha256 `b4d32e2d4bfbcbb4…`) |
| Resource exhaustion by its own code | **none evident** — all ten commands returned output and completed; the last finished ~6 s before agent end and ~21 s before the verifier |
| Extremely large files | largest agent-produced file is `out/analysis_panel.csv`, 6.9 MB — the required deliverable, and the same size in the other trials |
| Infinite / background jobs | **none** |

**Result: no agent action was found that could plausibly affect `test.sh`.**

A comparative point strengthens this. `JnK5hsR` issued **10** shell commands and left a workspace containing only
the required outputs (it deleted its five scratch scripts). `MMGNYFS` and `PYhR2eh` issued **19 each** — nearly twice
the opportunity to leave stray processes — and both verifiers ran normally. **The trial with the fewest processes and
the cleanest workspace is the one whose verifier failed.**

---

## 4. Stray-process-sweep analysis

**A. How it works** (`tests/test.sh`, lines 16–33, read only):

```bash
p=$$; top=$$
while :; do
  pp=$(awk '/^PPid:/{print $2}' /proc/$p/status 2>/dev/null || echo 0)
  { [ -z "$pp" ] || [ "$pp" -le 1 ]; } && break
  top=$pp; p=$pp
done
T0=$(awk '{print $22}' /proc/$top/stat 2>/dev/null || echo 0)
TBOOT=$(( $(awk '{print $22}' /proc/1/stat 2>/dev/null || echo 0) + 3 * $(getconf CLK_TCK) ))
for d in /proc/[0-9]*; do
  pid=${d#/proc/}
  [ "$pid" = "1" ] && continue
  st=$(awk '{print $22}' "$d/stat" 2>/dev/null) || continue
  [ -z "$st" ] && continue
  [ "$st" -le "$TBOOT" ] && continue
  [ "$st" -lt "$T0" ] && kill -9 "$pid" 2>/dev/null || true
done
```

It walks from its own PID up to the ancestor just below PID 1 (`top`), takes that ancestor's start time (`T0`), and
`SIGKILL`s every process whose start time lies strictly between container-init+3 s and `T0`.

**B. Intended targets:** processes left running by the agent session, which by construction started before the
verifier's exec chain.

**C. Can it kill …**

| Target | Analysis |
|---|---|
| itself | **No.** `test.sh` starts after `top`, so `st > T0` |
| its parent / the exec chain | **No.** `top` has `st == T0`, and the test is strict `<`; intermediate ancestors start later still |
| pytest | **No** — not yet started when the sweep runs |
| container init (PID 1) | **No** — skipped explicitly, and again by the `TBOOT` guard |
| Harbor verifier infrastructure | **Not inside this container**: the docker-exec shim lives outside the container's PID namespace. Anything Harbor had running *inside* the container from an earlier phase is in range |
| a shell / process group the verifier needs | **Not by this analysis** — but see E |

**D. Safeguards:** skip PID 1; skip anything started within 3 s of PID 1 (`TBOOT`, added after the G24 incident);
strict `<` comparison against `T0`; `2>/dev/null || true` so failures do not abort.

**E. Race condition:** yes, one is structurally present. `TBOOT` is a **3-second heuristic**. If a process Harbor
needs inside the container started more than 3 s after container init — plausible when three containers start
simultaneously on a memory-oversubscribed VM (3 × `memory_mb = 4096` requested against 7.654 GiB total) — it is not
protected and will be killed if it also started before `T0`. Start-time granularity is in clock ticks, so
near-simultaneous processes can compare equal; the strict `<` makes that direction safe rather than unsafe.

**F. Analogous G24 incident:** yes, and it is on the record. During G24 pre-baseline validation, Harbor returned
reward 0 in **0.8 s**: `test.sh`'s kill loop had killed Harbor's container main command. The fix was the `TBOOT`
guard now present. The present failure has the same shape — a sub-3-second verifier returning 0 with no test output —
but a different container-level outcome: in G24 the container died, whereas here it demonstrably survived.

**G. Evidence consistent with this failure mode:**
- The 2.18 s duration places death in the sweep's window (the sweep is the first block after the reward write, and
  the only one in that window that terminates processes without printing).
- Zero bytes of stdout+stderr is what an uncatchable `SIGKILL` of the redirected subshell produces.
- `reward.txt` = `0` from line 11, written before the sweep.
- A precedent exists in the same verifier lineage (F).

**H. Evidence inconsistent with this failure mode:**
- **The container survived.** It accepted three further execs and was stopped cleanly 3 s later. The G24 mechanism
  killed the container.
- **The chain is protected by construction** (C): on the analysis above the sweep cannot kill `test.sh` or its
  ancestors.
- **The sibling trials ran the identical script, from the identical image, at the same moment, with more agent
  processes outstanding, and were unaffected.**

**Reproduction not performed, and not necessary for this adjudication.** A copy of the sweep logic could be run in a
throwaway container outside the candidate directory with no model or API, and it would refine *which* verifier-side
mechanism fired. It would not change the classification, because every candidate mechanism identified lies inside
`test.sh` or the Harbor exec path — that is, outside Gemini's solution either way. Recorded as an option for a
future investigation.

---

## 5. Resource / OOM analysis

| Check | Finding |
|---|---|
| Kernel / cgroup OOM in the Docker VM log | **None.** Zero matches for `out of memory`, `oom-kill`, `oom_reaper`, `Killed process` in `console.log`, which spans 2026-09-17 15:20 → 2026-09-18 03:58 local and covers the entire run. A cgroup-v2 memory kill would appear here |
| Docker `OOMKilled` container flag | **UNKNOWN** — `delete: true` removed the container; the event ring buffer no longer reaches 10:00 |
| Container memory records | **UNKNOWN** — no historical telemetry was collected; `docker stats` is instantaneous only |
| Were the other two trials alive at that moment? | **Yes, CONFIRMED.** At 10:00:32–34 both sibling containers were mid-agent-execution (`MMGNYFS` ended 10:00:55, `PYhR2eh` 10:01:28). All three containers were resident |
| Did the verifier coincide with peak memory? | **UNKNOWN.** Structurally, `JnK5hsR`'s verifier was the *only* verifier running at that time; the heavy pytest phases of the other two came later (10:01:03 and 10:01:34) and did not overlap it. The two siblings were then running agents, which are lighter than the verifier's pandas/bootstrap workload |
| Resource oversubscription | **CONFIRMED as a configuration fact:** `task.toml` requests `memory_mb = 4096` and `cpus = 2` per container; three concurrent containers therefore request 12 GB against a 7.654 GiB Docker VM that also hosted 10 unrelated containers using ~1.24 GiB |
| Unusually memory-heavy leftover agent processes | **None found** — all ten commands were short-lived and had returned |

**Assessment:** oversubscription was real, but the direct evidence is against OOM: no kernel OOM lines, and the
container was alive and serving execs immediately after the failure. An OOM kill of the `test.sh` subshell alone
(rather than the container) would be logged by the kernel; nothing was.

---

## 6. Application of the pre-registered validity rule

The rule, as written before the baseline:

| Counts if | `JnK5hsR` |
|---|---|
| Gemini initializes | ✓ yes |
| Task presented normally | ✓ yes — identical prompt, identical `task_checksum` `56c1d86e…` |
| Intended workspace available | ✓ yes — warehouse byte-identical to the other trials |
| Normal execution opportunity | ✓ yes — 3m46s, 38 tool calls, outputs written |
| **Grading completes normally** | **✗ NO — no test was collected or run** |

| Does NOT count if | `JnK5hsR` |
|---|---|
| Agent setup failure | no |
| Authentication failure | no |
| Provider failure before task execution | no |
| Harbor infrastructure failure | not established |
| Docker / OOM failure | not established (§5) |
| Corrupted workspace | no |
| Task never presented | no |
| **Verifier unable to execute for infrastructure reasons** | **YES — the verifier did not execute** |

Four of five "counts" conditions are met; the fifth — *grading completes normally* — is not, and the corresponding
"does not count" condition is met directly.

The rule also states that a **genuine agent-caused failure counts**, including "verifier failure caused by agent
modifications". §3 found **no agent modification of any kind** capable of causing this.

---

## 7. Classification

**(B) INVALID INFRASTRUCTURE FAILURE.**

## 8. Confidence

**MEDIUM.**

HIGH is not claimed: the precise mechanism is undetermined, and the exit code, signal and container exit status are
irrecoverable (§2). An unknown agent–environment interaction cannot be excluded outright, only shown to have no
identified pathway.

LOW is too weak: the evidence is specific and convergent rather than merely absent.

## 9. Justification

1. **Grading did not occur.** No test was collected, no pytest session started, no `ctrf.json` was produced. The
   pre-registered rule makes grading completion a requirement, not a nicety.
2. **`test.sh` began and then died silently.** `reward.txt` proves it reached line 11; the 0-byte merged
   stdout+stderr stream proves it printed nothing, which excludes every one of its own `refuse` paths and every
   ordinary bash error.
3. **The failure was not the agent's.** A complete audit of ten shell commands, the captured workspace and the
   trajectory found no config file, hook, install, permission change, background process, signal manipulation or
   tampering — and the warehouse is byte-identical across all three trials. The failing trial was the *least*
   process-heavy of the three.
4. **The cause therefore lies in `test.sh` or the Harbor exec path**, both of which are outside Gemini's solution.
   Whether it is the verifier's own stray-process sweep (a documented prior incident in this exact lineage) or
   another harness interaction, it is not attributable to the agent under any of the identified mechanisms.
5. **A controlled comparison exists.** Two sibling trials ran the identical script from the identical image in the
   same minute, with more outstanding agent processes, and graded normally. That isolates the difference to
   execution environment rather than to solution content.
6. **The counter-evidence is acknowledged and does not overturn this.** The container survived, and the sweep is
   protected against killing its own chain by construction — which is why confidence is MEDIUM, not HIGH.

**Explicitly excluded from this reasoning:** the scientific quality of the trial's analysis. Its output would have
failed grading; that fact was not used, and must not be used, to decide validity.

## 10. Is a replacement warranted?

**Yes.** Under (B) the official baseline currently stands at **2 valid trials, both failures**, and the third slot
requires **one** replacement trial.

## 11. Exact proposed replacement command — **NOT RUN**

```
harbor run -p candidates/g05-sco-rollout-gate -a gemini-cli -m google/gemini-3-flash-preview -k 1 -n 1 -o jobs \
  --job-name g05-gemini3flash-baseline-2 --artifact /workspace --agent-setup-timeout-multiplier 3 -y
```

`-k 1 -n 1`: exactly one replacement trial, not three. Recommended operational precaution, since it does not touch
the task: run it with the other Docker stacks stopped, so the container is not competing for the 7.654 GiB VM.

## 12. Official baseline bookkeeping until this is confirmed

> **G05: 0/2 among definitively valid trials; one trial pending validity adjudication.**

G05 must **not** be entered into candidate-set pass@3 arithmetic as though three valid trials exist. The
qualitative trajectory findings from `JnK5hsR` remain usable — all three trials showed the same omission of format
conditioning — but must be labelled as coming from a trial with unresolved verifier validity.

## 13–16. Integrity

- **G05 checksum: `77a6e432d9d2cba2`** — unchanged.
- **All frozen checksums unchanged:** G08 `b1f0fa1304fb88f5`, G10 `047195e7a12d34cd`, G24 `2c9cc2055ef796a5`,
  Tasks 01 `67259f9d0d438f7c`, 02 `f696367794c1a25f`, 02-explicit-invariant `0e8200bd6d99c77b`,
  03 `a8443d183fe160e6`, 04 `885b541eb480a020`, 05 `8daa31d646dfcb59`, 06 `cd572b17bd537b4d`.
- **Model / API spend during this investigation: $0.00.** No model was run. All evidence came from existing job
  artifacts, the Docker daemon and VM logs, the installed Harbor source, and the frozen `test.sh` (read only).
- **Secrets:** none exposed; no key was read or printed during this investigation.

---

## Addendum, 2026-09-22: the mechanism has been reproduced

Written four days after the adjudication above, while validating G41. **Nothing in this file has been
edited; this section only adds what was since established.** No G05 file was touched, no G05 trial was
re-run, and the G05 checksum is unchanged.

The stray-process sweep — listed as stage **UNKNOWN** in §1 — is the cause. It kills processes that
started before the verifier, sparing only those from the container's first three seconds. Harbor's
container runs `sh -c sleep infinity` as PID 1 and the real `sleep infinity` as PID 7; under load PID 7
starts *after* that three-second grace and is killed, which ends the container's main command mid-grading.

Reproduced directly with dry-run instrumentation on G41 (`jobs/g41-oracle-diag`, PID 7 starting 5.98 s
after PID 1, marked `WOULD_KILL`), and reproduced as a failure 3 times in 6 Oracle trials while the
machine was loaded — each with `JnK5hsR`'s exact signature: verifier ≈ 2 s, empty stdout, container
stopped ~3 s later. With the sweep corrected, the same task passed 3/3 under the same load.

Consequences for this adjudication:

- the conclusion is unchanged — **(B) invalid infrastructure failure** — and its confidence rises from
  **MEDIUM to HIGH**;
- the failure is independent of what the agent did, which is what §1's structural comparison argued;
- the defect can only convert a pass into a 0, never the reverse, so excluding `JnK5hsR` remains correct
  and is conservative in the direction of the model's measured performance.

Full write-up: `research/harness_process_sweep_defect.md`.
