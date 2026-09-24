# Pre-exposure record — prospective target-model evaluation

**Created 2026-09-24, before any target-model call against any of the three frozen tasks.**

## 1. Freeze under evaluation

| item | value |
|---|---|
| freeze tag | `phase3-freeze-2026-09-24` |
| freeze commit | `aeddc1c06d6584df1554abe8b101f0d2ca6af12c` |
| HEAD at this record | `aeddc1c06d6584df1554abe8b101f0d2ca6af12c` (identical to the freeze commit) |

## 2. Manifest checksums, verified immediately before this record

| task | accepted checksum | recomputed now | match |
|---|---|---|---|
| `candidates/p22-gauge-recalibration` | `a0570585c3927b53` | `a0570585c3927b53` | ✅ |
| `candidates/p20-noshow-monitoring` | `2c3c374b07f233fa` | `2c3c374b07f233fa` | ✅ |
| `candidates/p31-fill-rate-dispute` | `e18bf13d6080f987` | `e18bf13d6080f987` | ✅ |

`git diff aeddc1c HEAD` over the three task directories is **empty**.

## 3. Authoritative task identities

Observed in both the Oracle and the Nop `lock.json` for each task at freeze, identical in each pair.

| task | `lock.json` → `trials[].task.digest` |
|---|---|
| p22-gauge-recalibration | `sha256:72fedb37da7b48c8488ad8afbcdf0d46b501dcdb52a6b05698a20370425629a7` |
| p20-noshow-monitoring | `sha256:f033ea1f5a8876514566174e8a99cf36d24e09cd54e9bba7ddfb5c16ffe60d8a` |
| p31-fill-rate-dispute | `sha256:3208a6d39014bff924784636da9a0837d528833f22e0666197d445330821f3ae` |

A trial whose `task.digest` is not one of these three does not belong to this evaluation.

## 4. Target model and configuration

| item | value |
|---|---|
| model identifier | **`google/gemini-3-flash-preview`** |
| agent | `gemini-cli` |
| attempts per trial (`-k`) | 1 |
| concurrent trials (`-n`) | 1 — sequential by construction |
| `--agent-setup-timeout-multiplier` | **3.0** |
| artifacts collected | `/workspace` |
| task timeouts | as frozen in each `task.toml`: agent 5400 s, verifier 5400 s. Not overridden |

The setup-timeout multiplier of 3.0 is a **pre-existing protocol setting**, not a choice made for this run: it
was introduced for the phase-1 G05/Task01 baselines because the `gemini-cli` agent's npm install exceeded the
default 360 s setup timeout locally, which is what made `g08-gemini3flash-baseline-1` an invalid
agent-setup-timeout trial. It is recorded here and fixed before the first call.

Exact command template, identical for every trial except the task path and job name:

```
harbor run -p <task-path> -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name <job> --agent-setup-timeout-multiplier 3.0 \
  --artifact /workspace -y
```

No other model will be run. No model will be used as an exploit agent. `harbor check` will not be run.

## 5. Intended trial count

**Three valid trials per task; nine valid trials in total.** No fourth valid trial will be run for any reason.

## 6. Execution order, fixed before reading any target output

1. `p22-prospective-1`
2. `p22-prospective-2`
3. `p22-prospective-3`
4. `p20-prospective-1`
5. `p20-prospective-2`
6. `p20-prospective-3`
7. `p31-prospective-1`
8. `p31-prospective-2`
9. `p31-prospective-3`

One Harbor job per trial. Each job is launched only after the previous job has completed and its
infrastructure-validity adjudication has been recorded. A replacement trial, if the preregistered rule requires
one, is appended with the suffix `-r<n>` and keeps its place in this order.

## 7. Invalid-trial rule

The rule is **`research/phase3/analysis_plan.md` §2**, frozen in commit `aeddc1c` and not modified. Reproduced
here for the record, unaltered:

> A trial is **invalid** and replaced by one authorised re-run if it shows any of: an API, quota or
> authentication error; an agent-setup timeout; a verifier that never executed; or the container-teardown
> signature documented in `research/harness_process_sweep_defect.md` — **reward 0 with 0-byte verifier stdout and
> a verifier phase of roughly 2 seconds**. The adjudication is made from the job artefacts alone. Reading a
> trial's reasoning before adjudicating it is a protocol violation.
>
> At most one replacement per task without a written reason. Invalid trials are reported with their count and
> cause; they never enter an aggregate.

**Scientific incorrectness is not a ground for invalidation.**

## 8. Analysis plan checksum

`research/phase3/analysis_plan.md`

```
sha256  c590cb5677ce14ba8298824929aa9e90323506b5d678438d601705323c8a7824
```

This checksum will be recomputed after the runs and must be unchanged.

## 9. Cost control

A ledger will record each trial's cost as Harbor reports it. **If cumulative new spend would exceed $10 before
nine valid trials exist, the run stops before incurring further cost** and the state is reported.

## 10. Explicit statement

**No target-model exposure of `p22-gauge-recalibration`, `p20-noshow-monitoring` or `p31-fill-rate-dispute` has
occurred at the time this record is committed.** Every Harbor job that has ever referenced these three tasks used
the `oracle` or `nop` agent; this was verified by reading `trials[].agent.name` from every `jobs/*/lock.json` and
finding only those two values. No Gemini call, and no `harbor check`, has been made against any of them.
