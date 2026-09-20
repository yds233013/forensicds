# G35 — first and only Gemini baseline: trajectory and benchmark-validity analysis

**Task:** `candidates/g35-dispatch-priority-gate`, frozen at **`3b7c6a4bd0f403a7`**
**Model:** `google/gemini-3-flash-preview` via `gemini-cli`
**Trials:** 3 valid, sequential, no replacements needed
**Result: 3 / 3 — task-level pass@3 = 1**
**Baseline cost: $0.188005**

G35 was not modified before, during or after. All three trials carry the identical Harbor
`task_checksum` `2d0d174f177e6541`.

---

## 1. Trials

| | trial 1 `GxLG9yo` | trial 2 `7Xib8sH` | trial 3 `NbUVHJu` |
|---|---|---|---|
| **reward** | **1** | **1** | **1** |
| wall-clock | 78 s | ~95 s | ~60 s |
| cost | $0.0731 | $0.0850 | $0.0299 |
| trajectory steps | 28 | 32 | 18 |
| input tokens | 270 929 | 346 047 | 134 918 |
| `task_checksum` | `2d0d174f177e6541` | same | same |
| exception | none | none | none |

All three produced **bit-identical** effects, matching the oracle to five decimal places:

| object | all three trials | latent truth | error |
|---|---|---|---|
| `direct_effect_50` | +0.2849339 | +0.28292 | 0.0020 |
| `spillover_50` | −0.1202183 | −0.11808 | 0.0021 |
| `policy_effect_full` | **+0.0444633** | +0.04196 | 0.0025 |
| recommendation | `launch` | `launch` | — |

**Validity: all three are valid agent trials.** Clean setup, no exception, complete verifier output,
no infrastructure signature. No trial required adjudication and none was replaced.

---

## 2. Trajectory questions (brief B1)

| question | trial 1 | trial 2 | trial 3 |
|---|---|---|---|
| understood the randomisation | yes | yes | yes |
| recognised the shared courier pool | yes (12 refs) | yes (6) | yes (3) |
| recognised interference | **yes** (33) | **yes** (36) | **yes** (29) |
| distinguished own treatment from exposure to others | yes | yes | yes |
| identified the relevant saturation arms | yes (73 refs) | yes (119) | yes (57) |
| separated direct / spillover / policy | **yes, all three** | yes | yes |
| used saturation correctly | yes | yes | yes |
| merely clustered SEs | no | no | no |
| estimated the mixed experiment and answered the wrong question | **no** | no | no |
| conditioned on post-treatment congestion | no | no | no |
| extrapolated outside support | no — used the existing 0 % and 100 % arms | no | no |
| weighted by demand rather than merchants | yes | yes | yes |
| launch decision correct | yes | yes | yes |
| **right decision for the right reason** | **yes** | **yes** | **yes** |
| attempted falsification | partial (4 refs) | partial (3) | minimal (2) |
| examined control outcomes by saturation | yes — that is the spillover object | yes | yes |
| stopped after obtaining a plausible lift | **no** | no | no |

Notable: **`SUTVA` is never named in any trajectory.** The model reasoned about the mechanism in
operational language — "couriers are a fixed resource", gains "partially stolen from non-priority
stores" — rather than reaching for the textbook term. Recognition was not vocabulary retrieval.

### What the model actually said

Trial 1:
> "That number represents the **direct effect**… which ignores the fact that couriers are a fixed
> resource… non-priority merchants see their fulfilment rates drop by 12.0 points… the **policy
> effect** is **+4.45 points**."

Trial 2:
> "It is a pooled comparison that overstates the actual system-wide benefit by **nearly 4x** because
> it fails to account for the fact that priority gains are partially 'stolen' from non-priority
> stores."

Trial 2's "nearly 4x" is quantitatively right: 0.166 / 0.0445 = 3.7.

---

## 3. F0–F10 and S0–S9

**No failure codes apply.** All three trials are clean successes; the F-taxonomy has no entry to
record. This is itself a finding: G35 did not elicit F9 (right method family, wrong statistical
object), which is the failure it was designed to elicit.

S-stage performance, all three trials:

| stage | outcome |
|---|---|
| S0 incident recognition | passed — Courier Ops' objection was taken seriously, not dismissed |
| S1 evidence discovery | passed — assignment log and runbook both located |
| S2 operational reconstruction | passed |
| **S3 target/estimand** | **passed** — identified that Finance asked about a different saturation |
| **S4 statistical object** | **passed** — three objects produced and kept apart |
| **S5 identification** | **passed** — used the 0 % and 100 % arms, no extrapolation |
| S6 estimator | passed |
| S7 falsification | **weakest stage** — limited; the model largely trusted its own result |
| S8 uncertainty | not exercised (not graded) |
| S9 decision | passed |

The design hypothesis was that G35 would load S3–S5. It does — and this model clears S3–S5.

---

## 4. Benchmark validity

### 4.1 The pre-registered risk was confirmed

`research/g35/build_recommendation.md`, written **before any model ran**, recorded:

> "**K17 partially lands.** Marketplace interference is famous… once an analyst recognises that
> assigned saturation is the operative variable, several different analyses land close… The
> difficulty is concentrated in one recognition step. **Honest prediction: G35 will land in a similar
> band [to G34's 2/3], plausibly 1/3 to 3/3.**"

The outcome is 3/3 — the top of the predicted range. The prediction was correct and recording it in
advance is what makes this a measurement rather than a surprise.

### 4.2 Is G35 a valid task?

**Yes.** Every scientific gate passed and none of them depended on the model:

- the naive readout is wrong by 3.7× on the visible extract and 39× on `hidden_a`;
- 21 wrong analyses score 0, including the textbook block-FE remedy and the sophisticated
  "whole mixed experiment as the rollout effect";
- Nop passes the recommendation check and the reconciliation check and still scores 0;
- valid routes agree to 0.005; tolerance sits in a measured window.

Validity and difficulty are separate properties. G35 is valid and, for this model, easy.

### 4.3 Is it a *discriminating* task?

**No, not for `gemini-3-flash-preview`.** 3/3 with bit-identical answers, a median of 28 trajectory
steps and a median cost of $0.073. The Clopper–Pearson 95 % interval for 3/3 is **[0.292, 1.000]**,
so the data are consistent with anything from a 29 % task to a certainty — but combined with the
identical answers and the correct verbal diagnosis in every trial, the practical reading is that this
model has the capability G35 tests.

**Per the standing instruction, G35 has not been modified.** A valid success is data, not a reason to
escalate difficulty.

### 4.4 Why it turned out easier than G34

Both are "famous concept, one recognition step". The difference is what happens *after* recognition:

- **G34** required constructing a risk set correctly. Trial 2 there recognised competing risks,
  said the right words, and then built the wrong risk set — recognition did not carry the answer.
- **G35** requires selecting the right pair of arms. Once the analyst knows saturation matters, the
  contrast is `mean(π=1) − mean(π=0)`, and the cheap-solve gate had already measured that several
  different routes land within 0.007 of truth.

The lesson for G36/G37: **prefer mechanisms where recognition and execution are separately hard.**
A task whose difficulty collapses once the key variable is named will be solved by any model that
names it.

---

## 5. Effect on the measured pool

| task | successes / 3 | task pass@3 |
|---|---|---|
| Task02 | 0 / 3 | 0 |
| G05 | 0 / 3 | 0 |
| G10 | 0 / 3 | 0 |
| G24 | 0 / 3 | 0 |
| G08 | 1 / 3 | 1 |
| G34 | 2 / 3 | 1 |
| **G35** | **3 / 3** | **1** |

Seven-task pass@3: **3 / 7 = 42.9 %** (was 2/6 = 33.3 % before G35).

G35 moves the pool **away** from the < 30 % target. That is recorded as a fact, not corrected for.
Selection of a final pool is a separate decision and must not be made by tuning or by dropping
inconvenient measurements; both options — include G35 as an easier anchor for difficulty spread, or
classify it development-only — are left open for the maintainer in
`research/overnight_status_2026-09-20.md`.

---

## 6. Cost

| item | cost |
|---|---|
| trial 1 | $0.073123 |
| trial 2 | $0.084967 |
| trial 3 | $0.029915 |
| **Gemini baseline total** | **$0.188005** |
| `harbor check` ×2 (validation) | $0.907800 |
| **G35 total model spend** | **$1.095805** |

Oracle and Nop runs cost $0 — no model.

---

## 7. Recommendation

1. **Keep G35 frozen as-is.** Do not retune in response to this result.
2. **Record its measured difficulty honestly**: 3/3, CI [0.292, 1.000]; do not quote a pass rate.
3. **Classify as borderline / difficulty-spread candidate**, not as a core discriminating task.
4. **Carry the §4.4 lesson into G36**: choose a mechanism where recognition does not hand over the
   execution.
