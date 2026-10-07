# 09 — Benchmark integrity audit

Every defect this project documented, re-examined against artifacts. Each entry states whether I
**independently reran** the check in this session or am **relaying a prior report**.

## Independent verification performed in this session

| check | method | result |
|---|---|---|
| all ten final tasks match the evaluated versions | extracted `samples/<task>/` from `submission_final10.zip` and diffed against `candidates/<task>` | **10/10 IDENTICAL** — RERUN |
| submission archive intact | `shasum -a 256 -c SUBMISSION_SHA256.txt` | **OK** — RERUN |
| fallback archive untouched | `shasum -a 256 submission_5task_fallback.zip` | `c8561aad8300df6c832921fa…` — matches the recorded value — RERUN |
| per-task aggregate hashes | path+content SHA-256 walk, `__pycache__` excluded | recorded in `MACHINE_READABLE_INVENTORY.csv` — RERUN |
| which tasks emit criterion rewards | derived from observed `criteria.json` in trial dirs, then cross-checked against `tests/*` | **5 directories**, with file/line citations below — RERUN |

A note on that last row: my first pass used a regex over `tests/*` and **wrongly** reported `p20`, `p22`
and `p31` as binary-reward only. The authoritative source is what the trials actually emitted. The
inventory column was corrected and now carries a `criteria_observed` field. Recorded here because a
silent correction would be the kind of thing this chapter exists to catch.

Instrumentation, verified: `g50` → `tests/test_boost.py:424`, `tests/test.sh:144,149`;
`p20` and `p20-v1.1` → `tests/test_monitoring.py:7,56`, `tests/test.sh:99,104`;
`p22` → `tests/test_gauge.py:6,55`; `p31` → `tests/test_fill.py:10,59`.

## Defect register

### D1 — `p20` sign-convention ambiguity

- **Discovery.** Criterion-note audit found 7 field-level failures where `|agent| ≈ |truth|` within
  tolerance but the sign was inverted.
- **Cause.** `readout_contract.md` never stated the sign convention for `programme_effect_pp`. The
  reference computes *excluded-clinic minus programme-clinic* (positive = programme helps), and no
  agent-visible artifact disambiguated it.
- **RERUN:** `grep` for the convention text — **absent in v1, present in `p20-noshow-monitoring-v1.1`**.
- **Impact on claims.** Material but not outcome-changing: all three v1 trials also failed on
  independent genuine grounds, so `p20`'s 0/3 is not manufactured by the defect. The v1.1 re-exposure
  recorded **0/3 with zero sign failures**, which is the confirming test.
- **Exposure.** v1 had been exposed. It was **preserved byte-for-byte**; the fix lives in a separate fork.
- **Unresolved risk — and a NEW finding from this dossier.** The cross-model Claude run used `p20` **v1**,
  not the fixed v1.1, so **Claude inherited the defect**. A field-level sign audit over all instrumented
  trials in both arms (RERUN this session) finds 12 sign-flip field failures across Claude's three `p20`
  trials and 7 across Gemini's three v1 trials, against **zero** in the fixed `p20-v1.1` Gemini trials and
  zero in `p22`/`p31` for either arm.
  - Using v1 for Claude was defensible — both arms graded on the identical frozen task — but it means
    both arms' `p20` quantity numbers are partly contaminated, and the clean control exists for Gemini only.
  - **No trial fails on sign alone**; every `p20` trial in both arms has independent genuine quantity
    failures. So `p20`'s 0/3 in both arms stands.
  - **Claim now qualified:** chapter 08's Shape 2 must exclude the `programme_effect_pp` component. This
    was not recorded in any prior project document.
- A subtler contract ambiguity could still exist in a binary-reward task, where no field-level notes exist
  to detect it. **UNKNOWN.**

### D2 — `02-renewal-risk-regression` image-layer leakage

- **Discovery.** Dockerfile audit across all ten.
- **Cause.** Single-stage build: `COPY build/ /tmp/build/` creates a layer; the later `rm -rf` only
  whiteouts it. `docker save` recovers `world.py` **and `pit_reference.py`** — the reference
  implementation, i.e. the answer.
- **RERUN (static):** `02` → `multistage=False, copy_build=True, rm_in_later_layer=True` → **LEAK**;
  `02-…-v1.1` → `multistage=True` → **SAFE**. `environment/build/pit_reference.py` present, 10,301 bytes.
- **RERUN (dynamic):** **NOT reran this session** — the Docker daemon is not running. The layer
  extraction and the `ls /tmp/build` → *No such file* check are **REPORTED BUT NOT REVERIFIED** here.
- **Impact on claims.** The agent could not reach the files at runtime (whiteout), and the v1.1 fork's
  agent-visible workspace hashes identically to v1, so the six existing `02` trials remain valid.
- **Unresolved risk.** Any built-and-shared v1 image leaks the reference. The repository itself always
  contains the answers — that is normal for a benchmark author — so the exposure surface is the *image*,
  not the source tree.

### D3 — `g50` break-even threshold not binding

- **Cause.** On the original four worlds the rollout effect never fell between 0 and −1.4961 pp, so a
  mutation that rolls out on *any* reduction passed. The £0.19/£12.70 arithmetic was never tested.
- **Fix.** A fifth world `hidden_d` calibrated to −0.3049 pp, added **while `g50` was still unexposed**.
- **RERUN:** `tests/scenarios.py` declares `hidden_a, hidden_b, hidden_c, hidden_d` — **confirmed**.
- **Impact on claims.** None adverse; strictly strengthened the task. The unadjusted estimator now misses
  by 18.6 pp on `hidden_d` (**REPORTED BUT NOT REVERIFIED** — requires Docker).
- **Exposure.** Fixed pre-exposure, so no version fork was needed.

### D4 — `g50` verifier refusal, `/etc/ld.so.cache` (Gemini arm)

- **Discovery.** By the **first real agent run**, after 63 adversarial submissions had passed.
- **Cause.** `/etc/ld.so.cache` was hash-pinned; `apt-get` runs `ldconfig`, which regenerates it. Agent
  scaffolds install their own tooling; `oracle` and `nop` install nothing, so the path was never exercised.
- **Fix.** Pin removed; replaced by a *resolution* check (every shared object the verifier actually loads
  must resolve to a manifest-pinned path).
- **RERUN:** `ld.so.cache` entries in the arm64 manifest = **0**; `"resolves outside the pinned set"`
  present in `tests/test.sh` = **1**. Fix is in place — confirmed.
- **Impact.** Three Gemini trials invalidated and re-run. The replacements are the reported `g50` results.

### D5 — `g50` verifier incompatible with `claude-code` (unresolved)

- **Observation.** Four `claude-code` attempts, four refusals:
  `interpreter, library tree or sandbox tools differ from the pinned image; refusing to grade`.
- **De-confounded.** The final attempt had a funded, active agent (**16 recorded steps, $0.66 billed**) and
  the verifier still refused. So this is **not** a billing artifact and **not** a model failure.
- **Which pinned file is tripped: UNKNOWN.** `tests/test.sh:76` runs
  `sha256sum --quiet --strict -c "$MANIFEST" >/dev/null 2>&1`, discarding the filename. I attempted the
  diagnostic — replicate the `claude-code` installer (`apt-get install curl`, then `nodejs npm`) in the
  frozen image and rerun the manifest check — but **the Docker daemon is not running**, so it is unresolved.
- **Important correction.** It is *not* the `ld.so.cache` failure recurring: D4's fix is verifiably in
  place. `claude-code` changes a **different** pinned file. Earlier project notes describing this as the
  "same `ld.so.cache`-class failure" were **imprecise**, and this chapter supersedes them.
- **Impact on claims.** `g50` has **zero** valid Claude trials. It is excluded from the cross-model
  comparison. The frozen verifier was **not** modified.
- **Unresolved risk.** `g50` cannot currently be graded for any scaffold that installs tooling differently
  from `gemini-cli`. Its Gemini result stands; its generality does not.

### D6 — Invalid trials across both arms

45 attempts produced no graded result. Full register: `INFRASTRUCTURE_FAILURE_REGISTER.md`.

| cause | n | arm |
|---|---|---|
| `credit-balance-too-low` | 20 | claude |
| `verifier-refused` (+ `-ldsocache`, `-agent-did-run`) | 10 | 6 claude, 4 gemini-era g50 |
| `agent-setup-timeout` | 3 | gemini |
| `api-key-rejected` | 3 | gemini |
| `free-tier-quota` | 3 | gemini |
| `free-tier-rpm-stopped` | 3 | gemini |
| `session-interrupted-during-agent-setup` | 3 | gemini |

The 20 credit failures are worth dwelling on. The agent returned `billing_error` after 2 steps with an
empty workspace, and the verifier then **graded the empty submission**, producing `criteria.json` with
every criterion 0. Read from `reward.json` alone this is indistinguishable from a catastrophic model
failure. That is why this dossier derives validity from the **trajectory** (did the agent act?) and the
**verifier stdout** (did it refuse?), never from the reward value.

### D7 — The cross-model integrity-script false alarm

- **What happened.** A late integrity check reported DRIFT on 5 of 10 tasks.
- **Cause.** The reference copy had been extracted to `/tmp` earlier in the session and macOS had
  partially cleaned it, so directories present in `candidates/` read as "Only in candidates". Compounding
  it, the script printed an unconditional "all 10 byte-identical" line that masked the warning.
- **Resolution.** A fresh extraction showed **all ten IDENTICAL**. **RERUN this session** — confirmed again.
- **Lesson, and why it is in this chapter.** A false drift report is more dangerous than a missed one: it
  invites "repairing" a benchmark that was never broken. Integrity checks must extract their reference
  fresh and must not print a verdict they have not computed.

## Claims that remain defensible

1. The ten final tasks are byte-identical to the evaluated versions. **RERUN.**
2. Gemini's 31 valid trials / 1 pass / 3.2% / 10% pass@3 reproduce exactly from raw rewards. **RERUN.**
3. Claude's 27 valid trials / 13 passes on 9 tasks reproduce exactly from raw rewards. **RERUN.**
4. No invalid attempt is counted as a model failure anywhere. **RERUN.**
5. No frozen task, verifier, tolerance, dataset or scoring rule was modified during either evaluation.

## Claims that are weaker than previously stated

0. **`p20`'s criterion-level quantity failures in BOTH arms are partly a contract artifact** (D1 above).
   Previously reported as a clean capability signal for Claude. Corrected here.
1. `g50`'s refusal for `claude-code` was described as the same `ld.so.cache` class. **It is not** — the
   specific file is UNKNOWN (D5).
2. `g50`'s adversarial-validation record (63 submissions, 40 malformed-output attacks, 8 sandbox attacks)
   is **REPORTED BUT NOT REVERIFIED** here; it requires Docker.
3. The claim that `hidden_d` strengthened the pre-adjustment invariant is **REPORTED BUT NOT REVERIFIED**.
