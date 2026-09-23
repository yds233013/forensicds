# Harness defect: the verifier's stray-process sweep can tear down the container

Found 2026-09-22 while validating G41. Reproduced, root-caused and fixed in G41's verifier. Recorded
here because the same code ships in the frozen tasks, and because it changes the confidence of an
earlier adjudication (`research/g05/G05_JnK5hsR_validity_forensics.md`).

## 1. What the code does

Every ForensicDS verifier begins by killing processes the agent may have left running, so that
nothing of the agent's can act during grading. Processes are identified by start time: kill anything
that started before the verifier's own process chain, except processes from the container's first
three seconds, which are assumed to be the container's own main command.

```bash
TBOOT=$(( $(awk '{print $22}' /proc/1/stat) + 3 * $(getconf CLK_TCK) ))
...
[ "$st" -le "$TBOOT" ] && continue      # the container's own init-era processes (main command) stay
[ "$st" -lt "$T0" ] && kill -9 "$pid"
```

## 2. The defect

Harbor's container runs `sh -c sleep infinity` as PID 1, which forks the actual `sleep infinity` as
PID 7. On an idle machine PID 7 starts within a few hundred milliseconds of PID 1 and the three-second
grace protects it. **On a loaded machine it does not.** Measured directly (dry-run instrumentation,
`jobs/g41-oracle-diag`):

```
pid=1 start=80404423 cmd=sh -c sleep infinity   fds=/dev/null,pipe:[65999257],pipe:[65999258]
pid=7 start=80405021 cmd=sleep infinity         fds=/dev/null,pipe:[65999257],pipe:[65999258]
WOULD_KILL 7
```

PID 7 started 598 ticks — 5.98 s — after PID 1, outside the grace window, so the sweep kills it. Killing
it ends the container's main command: the container stops, the verifier's stdout pipe dies mid-script,
and Harbor records the reward file's initial value, `0`.

**Signature of an affected trial: reward 0, verifier stdout file 0 bytes, verifier phase ≈ 2 s,
container stopped ~3 s later.** A correctly graded 0 always leaves the pytest failure report behind.

Observed rate while the machine was loaded (fifteen Docker builds running before the run): 3 of 6 G41
Oracle trials. On an idle machine: 0 of 3 before the load, and the same task then passed 3/3 after the
fix under identical load.

## 3. Direction of the error

The defect can only turn a passing run into a 0; it cannot turn a failing run into a 1, because the
reward file starts at 0 and is only overwritten after pytest exits cleanly. So it is conservative
against the agent: a benchmark carrying it **understates** model performance and never overstates it.

## 4. Consequence for the frozen five-task suite

Every recorded trial was scanned for the signature (reward 0 with an empty verifier stdout file):

| Trial | Status |
|---|---|
| `g05-sco-rollout-gate__JnK5hsR` | already excluded as an invalid infrastructure trial before this was found |
| `final-nop-g05-sco-rollout-gate`, `g34-nop-final` | Nop runs; both tasks also have a Nop trial that graded normally and scored 0 (`g05-nop-prebaseline`, `final-nop-g34-fleet-reliability-gate`) |

**No graded trial in the reported results is affected.** All fifteen valid target-model trials carry a
full pytest report. `scripts/final_audit.sh` now checks this explicitly, so the claim is re-verified
on every audit rather than asserted once.

The frozen tasks are **not** modified: they are frozen, their results are recorded against their
digests, and the defect cannot have inflated any reported number. New tasks built after this date
carry the fix.

## 5. The fix

Identify the container's own main command by the standard streams it inherited from PID 1 rather than
by when it started:

```bash
MAIN_OUT=$(readlink /proc/1/fd/1); MAIN_ERR=$(readlink /proc/1/fd/2)
...
[ "$st" -ge "$T0" ] && continue                        # started with or after the verifier
o=$(readlink "$d/fd/1"); e=$(readlink "$d/fd/2")
[ "$o" = "$MAIN_OUT" ] || [ "$e" = "$MAIN_ERR" ] && continue   # container's own stdio: infrastructure
kill -9 "$pid"
```

An agent process cannot acquire those pipes: the agent phase runs in its own `docker exec` session with
its own pipes, so the sweep still removes anything the agent left behind. Verified after the fix:
Oracle 3/3 = 1 under the same load that produced the failures, Nop = 0 with a full grading report.

## 6. Effect on the G05 `JnK5hsR` adjudication

That trial was adjudicated **(B) invalid infrastructure failure, confidence MEDIUM**, with the stray-
process sweep listed as an *unknown* stage. Its recorded evidence — verifier phase 2.18 s, no stdout,
container stopped 3.1 s later, no pip/pytest activity — is exactly the signature above. The mechanism is
now reproduced and root-caused, so the adjudication stands with **confidence HIGH**, and the decision
to exclude it quantitatively was correct. No number changes: it was already excluded.
