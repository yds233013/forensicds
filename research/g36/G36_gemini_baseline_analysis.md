# G36 — Gemini baseline: trajectory and benchmark-validity analysis

> **STATUS (adjudication, 2026-09-21): the frozen result 0/3 stands as recorded and is classified
> CONTAMINATED BY AN F8 BENCHMARK DEFINITION DEFECT.** The adjudicated replay (2/3 under the
> load-weighted response) is a counterfactual, not the official baseline. Neither number enters the
> benchmark aggregate. See `adjudication/`.

**Task:** `candidates/g36-tou-capacity-gate`, frozen at **`85197582fa38141d`** (commit `a2196df`)
**Model:** `google/gemini-3-flash-preview` via `gemini-cli`
**Trials:** 3 attempted, 3 valid, 0 invalid. No replacements. Run sequentially.
**Frozen-verifier result: 0 / 3. Task-level pass@3 = 0.**
**Adjudicated finding: 2 of the 3 failures are benchmark false negatives (F8).**
**Baseline cost: $0.35536060**

G36 was not modified before, during or after the baseline. All three trials carry the identical Harbor
`task_checksum` `d2f4f542e4113ece`.

---

## 1. Headline

The frozen verifier scored every trial 0. That number **must not be reported as a clean difficulty
measurement**.

- **Trial 1** is a genuine model failure under any reading of the contract.
- **Trials 2 and 3** computed a scientifically correct estimator — equivalent to the reference
  family F1 — whose forecast passed on every fixture, including the tightest (`hidden_c`), with every
  decision correct. They failed only because the verifier grades `estate_tou_response_at_target_cdd`
  under a **different definition** from the one the output contract's wording describes.

The defect is in the benchmark specification, not in the model. It is recorded here for external
adjudication. **Nothing in G36 was changed.**

---

## 2. Trial table

| | trial 1 `9ireeNt` | trial 2 `gtUvxU3` | trial 3 `gZDvdHD` |
|---|---|---|---|
| valid | yes | yes | yes |
| reward | 0 | 0 | 0 |
| pytest | 10 passed / 3 failed | 11 passed / 2 failed | 11 passed / 2 failed |
| job runtime | 6 m 42 s | 7 m 07 s | 5 m 22 s |
| agent runtime | 2 m 39 s | 4 m 02 s | 2 m 18 s |
| trajectory steps / tool calls | 54 / 36 | 44 / 31 | 40 / 28 |
| tokens in / cached / out | 704,517 / 575,462 / 17,300 | 465,955 / 368,293 / 14,280 | 423,949 / 336,287 / 13,143 |
| cost | $0.14520060 | $0.11008565 | $0.10007435 |
| `task_checksum` | `d2f4f542e4113ece` | same | same |
| exception | none | none | none |

Validity: all three initialised `gemini-cli` normally, worked in the task workspace, produced full
trajectories, and reached a normally executing verifier. None shows an infrastructure signature.

---

## 3. What each trial submitted (visible extract)

| | target_peak_kw | error / tol | estate response | decision |
|---|---|---|---|---|
| truth | 3.00996 | — | 0.06201 (frozen definition) | defer |
| trial 1 | 3.00356 | 0.13 | 0.07697 | defer |
| trial 2 | 3.00854 | 0.03 | 0.07545 | defer |
| trial 3 | 3.00852 | 0.03 | 0.07545 | defer |

All three passed every visible-extract check. The differences appear only in the hidden extracts.

---

## 4. Forensic replay: every trial's submitted code on every fixture

Each trial's submitted `capacity_forecast` package was re-executed deterministically on all five
fixtures (`tools/g36/replay_submissions.py`). This is replay of frozen artefacts, not a model call.

| trial | fixture | forecast / tol | response / tol (frozen def.) | response / tol (load-weighted) | decision |
|---|---|---|---|---|---|
| 1 | visible | 0.13 | 0.87 | 0.03 | ok |
| 1 | hidden_a | 0.07 | 0.38 | 0.03 | ok |
| 1 | hidden_b | **1.21** | **1.04** | **1.16** | ok |
| 1 | hidden_c | **4.01** | **3.56** | **3.32** | **WRONG** |
| 1 | hidden_d | 0.64 | **1.78** | 0.43 | ok |
| 2 | visible | 0.03 | 0.78 | 0.05 | ok |
| 2 | hidden_a | 0.15 | 0.22 | 0.13 | ok |
| 2 | hidden_b | 0.05 | **2.21** | 0.01 | ok |
| 2 | hidden_c | 0.06 | 0.65 | 0.41 | ok |
| 2 | hidden_d | 0.32 | **1.53** | 0.18 | ok |
| 3 | (identical to trial 2 on every fixture to 12 significant figures) | | | | |

| | frozen verifier | load-weighted response | forecast + decision only |
|---|---|---|---|
| trial 1 | fail | fail | **fail** |
| trial 2 | fail | **pass** | **pass** |
| trial 3 | fail | **pass** | **pass** |

---

## 5. The benchmark defect (F8)

### What the contract says

`docs/outputs/analysis_contract.md`:

> `estate_tou_response_at_target_cdd` — the **estate-wide fractional reduction in peak-window load**
> attributable to the tariff, at the target season's mean cooling degree days.

### What the verifier grades

`tests/test_capacity.py::_truth_values`:

```
sum(estate_share[s] * response_fraction[s])     # household-weighted mean of segment fractions
```

### What the trials computed

All three trials, independently, computed

```
( sum_s p_s * base_s  -  sum_s p_s * tariff_load_s ) / sum_s p_s * base_s    # load-weighted
```

which is the literal "fractional reduction in peak-window **load**" for the estate.

### Why the two differ

High-response segments (`HOUSE_SMART_HVAC`, `HOUSE_LARGE_POOL`) also carry more load, so the
load-weighted fraction is systematically larger than the household-weighted mean:

| fixture | frozen truth (hh-weighted) | load-weighted | trial 2/3 reported |
|---|---|---|---|
| visible | 0.06201 | 0.07637 | 0.07545 |
| hidden_a | 0.04347 | 0.05340 | 0.04972 |
| hidden_b | 0.13924 | 0.17137 | 0.17157 |
| hidden_c | 0.04309 | 0.05312 | 0.06996 |
| hidden_d | 0.09116 | 0.11199 | 0.11477 |

Trials 2 and 3 match the load-weighted object to within **0.01–0.41 of tolerance** on every fixture.
They miss the frozen object by **2.21x** (`hidden_b`) and **1.53x** (`hidden_d`).

### Evidence that this is a specification defect, not a model misreading

1. **Three of three trials chose the same definition independently.** The model read the contract
   the same way every time.
2. **The contract's wording supports their reading.** "Fractional reduction in peak-window load" at
   estate level is a load ratio. The household-weighted mean of per-segment fractions is a legitimate
   quantity, but a different one — the average customer's fractional reduction — and the contract
   does not say that.
3. **My validation could not have caught it.** All three reference estimator families (F1, F2, F3)
   computed the response through one shared helper, `estate_response_at_target_cdd`, which implements
   the household-weighted definition. K9 established independence of the *forecast*; it never tested
   the response's *definition*. The mutation suite's M28/M29, which justified retaining the check,
   perturbed the value, not the definition. The ambiguity was invisible to every gate I ran.

### Verdict

**F8 — benchmark/verifier issue.** Trials 2 and 3 are **false negatives**. Under the contract's plain
reading they would each score reward 1, giving 2/3 and task-level pass@3 = 1.

**Recommended for external adjudication, not for silent repair.** Candidate resolutions, none applied:
(a) grade the load-weighted definition; (b) keep the household-weighted definition and reword the
contract to "the estate-average, across customers, of each segment's fractional reduction"; or
(c) remove the response check and grade the forecast plus decision only. Option (c) would lose the
detection of `M28`/`M29`, which the forecast check cannot catch.

---

## 6. The hidden_c false-negative audit (as pre-registered)

The frozen margins raised a specific concern: `hidden_c` sits 2.0 SE_REF from the capacity ceiling, so
a legitimate but less efficient estimator might miss it.

**That concern did not materialise.** Trials 2 and 3 — the legitimate estimators — passed the
`hidden_c` forecast at 0.05–0.06 of tolerance with the correct `procure` decision. Trial 1 failed
`hidden_c` at 4.01x with the wrong decision, which is a structural error rather than a margin effect
(see §7). **No F8 concern arises from the decision margins.** The only F8 finding is the response
definition in §5.

---

## 7. Trajectories

### Trial 1 — `9ireeNt` — genuine failure

**Reconstruction.** Read the README, contract, incumbent, extract dictionary, load-research note and
capacity memo; did not open the pilot design note. Step 8 tabulated the pilot's pooled reduction by
CDD and found the **absolute** kW reduction roughly flat (0.43–0.56 kW across CDD 4–7). Step 12 counted
enrolment by segment. Steps 22–24 fitted history, pilot-control and pilot-treatment lines per segment
and saw near-equal slopes (large-pool 0.237 vs 0.236). It reasoned:

> "the slopes are nearly identical while the intercepts show a notable drop in kW. This suggests that
> the absolute reduction is constant across cooling degree days … implies a decreasing fractional
> reduction as CDD increases, which aligns with … 'Scope for shifting'."

It then paused — *"reviewing the assumption that absolute reduction remains constant in hot days. This
is a point of concern"* — re-checked on the visible pilot, and concluded it held.

**What it built.** A per-segment constant kW reduction, taken as the treatment–control intercept gap
with the treatment slope **forced equal to the historical slope**, subtracted from the incumbent's
segment forecasts, weighted to estate shares.

**What it got right.** Stratification by segment and estate weighting; reuse of the stable historical
curve; a genuine check that pilot controls match history.

**What it missed.** It turned a pattern observed on one extract into a hard model restriction. On the
visible extract, the constant-kW description is empirically accurate because rising load and falling
fraction offset each other. Where heat genuinely suppresses the response (`hidden_c`, response
quarters) the restriction overstates the reduction by 3.5x and flips the decision. On `hidden_b`,
where the fraction is flat, the restriction understates the reduction: a systematic +0.78 to +1.89x
tolerance bias across five redraws, so not noise.

**Why it stopped.** After the visible pipeline ran, it wrote and ran an implementation test
(`test_capacity_forecast.py`), deleted it, and reported. That was validation of implementation, not of
the restriction's transportability.

**Codes.** Primary **F7** (validated an assumption on the visible extract only, then hardcoded it
despite the instruction that the method must hold across extracts). Secondary **F9** (right method
family, wrong response object: constant absolute kW instead of a CDD-dependent response).

### Trial 2 — `gtUvxU3` — scientifically correct; benchmark false negative

**Reconstruction.** Read the contract, memo, extract dictionary, incumbent, backtest report and
programme note. Explored treatment against control across CDD, inspected the absolute reduction for
large-pool homes across CDD, and compared the baseline forecast with the pilot control group. It
reasoned:

> "recognising the voluntary nature of the pilot program, even if the assignment within the pilot was
> random" … "a decreasing response with increasing CDD … less flexibility on the hottest days."

**What it built.** Per segment: a historical baseline line, plus **separate free-slope lines for the
pilot treatment and control arms**; the treatment/control ratio evaluated at every target-season day's
CDD, applied to the baseline, averaged over the season and weighted to estate shares. This is the
reference family F1.

**The misdiagnosis.** It checked selection on the wrong dimension — whether enrollees' load curves
matched history *within* segment — and concluded the pilot was "very representative". The actual
selection is in the segment *mix* (0.32x–2.49x over-representation), which it neutralised only because
its analysis was stratified by segment.

**Why it stopped.** After a successful run and a correct narrative. No uncertainty quantification.

**Codes.** No model-failure code. **F8** (verifier grades a different response definition).

### Trial 3 — `gZDvdHD` — scientifically correct; benchmark false negative

**Reconstruction.** The most thorough reading: all four docs including the pilot design note. Wrote
inspection scripts for enrolment, CDD against response, and fit comparisons. It reasoned:

> "I realized that the enrolled group may not be representative, so I'm shifting focus … for each
> segment" … "Analyzing Enrollment Bias: … surprisingly low … But, after re-reading the pilot design
> notes, the enrolled group wasn't randomly drawn. This is creating a conflict."

**What it built.** The same free-slope treatment/control arm fits as trial 2, taking the ratio of
target-season means rather than per-day ratios. For linear fits these coincide at the season mean,
which is why the two trials' responses agree to 12 significant figures.

**Notable.** Its narrative concluded, like trial 1, that "the constant kW reduction model appears
valid" — yet its implementation fitted the treatment slope freely and so generalised. The difference
between trials 1 and 3 is not what they believed but what they encoded.

**Codes.** No model-failure code. **F8**.

---

## 8. S0–S9 matrix

| stage | trial 1 | trial 2 | trial 3 |
|---|---|---|---|
| S0 incident recognition | PASS — incumbent unusable because it ignores the tariff | PASS | PASS |
| S1 evidence discovery | PARTIAL — never opened the pilot design note | PASS | PASS — read all four docs |
| S2 operational reconstruction | PASS | PASS | PASS |
| S3 target / estimand | PASS — whole estate, mandatory tariff, 2027 weather | PASS | PASS |
| S4 statistical object | **FAIL** — constant absolute kW reduction | PASS | PASS |
| S5 identification / assumptions | **FAIL** — forced equal slopes; heat transport assumed away | PARTIAL — selection checked on the wrong dimension | PARTIAL — same |
| S6 estimator | PARTIAL — correct arithmetic for a wrong model | PASS | PASS |
| S7 falsification | PARTIAL — tested the restriction, only on the visible extract | PARTIAL | PARTIAL |
| S8 uncertainty | FAIL — none | FAIL — none | FAIL — none |
| S9 decision | PARTIAL — right on 4 of 5 fixtures | PASS — 5 of 5 | PASS — 5 of 5 |

The model-caused failure sits at **S4–S5**, where the design predicted it. S8 was never attempted by
any trial; uncertainty is not graded.

---

## 9. Recognition versus execution

| | trial 1 | trial 2 | trial 3 | total |
|---|---|---|---|---|
| selection — recognised explicitly | no (never stated) | yes (voluntary noted) | yes (not representative noted) | **2 / 3** |
| selection — executed correctly | yes | yes | yes | **3 / 3** |
| heat dependence — recognised | yes (tested explicitly) | yes | yes | **3 / 3** |
| heat dependence — executed correctly | **no** (restricted away) | yes | yes | **2 / 3** |
| both combined into the target forecast | no | yes | yes | **2 / 3** |

### The finding that matters most for the benchmark design

**Selection transport did not discriminate.** Every trial executed it correctly, and none of them
compared the enrolled segment mix with the estate mix, which is the diagnostic the design expected to
separate a correct analyst from `M09`. They got it right for free: the incumbent scaffold already
stratifies by segment and weights to estate shares, so any analysis built on top of it inherits the
correct transport. The design intended two orthogonal transports; in the packaged task, **only one —
heat dependence — was live**.

**Heat dependence discriminated sharply,** and it did so at the level of execution rather than
recognition. All three trials looked at it. What separated them was whether the treatment arm's CDD
slope was **estimated** or **constrained**. That is exactly the recognition-versus-execution gap G36
was built to expose: trial 1 recognised the phenomenon, tested it, and encoded the wrong restriction.

---

## 10. Pre-registered failure modes

| pre-registered mode | trial 1 | trial 2 | trial 3 |
|---|---|---|---|
| retrain-and-stop | — | — | — |
| pilot headline applied to estate | — | — | — |
| selection-corrected-and-stopped | **yes** — the closest match | — | — |
| heat-corrected-only | — | — | — |
| forecast the pilot population | — | — | — |
| reweight outcomes rather than effects | — | — | — |
| backtest-as-validity | — | — | — |
| right decision from wrong forecast | on 4 of 5 fixtures | — | — |
| no transport test | — | — | — |
| one specification and stop | **yes** | yes (but correct) | yes (but correct) |

**Unexpected modes.**

1. **Locally-valid restriction hardcoded.** Trial 1's error was not ignoring heat but *testing* it on
   one extract, finding an accurate local description, and hardcoding it. That is subtler than any
   pre-registered mode and more instructive.
2. **Selection checked on the wrong axis.** Trials 2 and 3 tested within-segment representativeness,
   found none, and were reassured, while the real selection sat in the segment mix. It did not hurt
   them only because of stratification.
3. **A consistent reading of the contract that differs from the verifier's.** Three of three.

---

## 11. Correct-decision / wrong-science audit

| trial | forecast (5 fixtures) | response, frozen | response, load-weighted | decision (5 fixtures) | category |
|---|---|---|---|---|---|
| 1 | 3 within tol | 3 within tol | 3 within tol | 4 correct | **correct decision + wrong forecast** on `hidden_b`; all wrong on `hidden_c` |
| 2 | 5 within tol | 3 within tol | 5 within tol | 5 correct | **correct forecast + "wrong" response** — definitional |
| 3 | 5 within tol | 3 within tol | 5 within tol | 5 correct | same as trial 2 |

Trial 1 on `hidden_b` is the G24/G05 pattern: the right `defer` call from a forecast outside
tolerance. The verifier correctly refused it.

---

## 12. Falsification behaviour

| check | trial 1 | trial 2 | trial 3 | scientific or implementation? |
|---|---|---|---|---|
| pilot control vs historical curve | **yes** | **yes** | **yes** | scientific — tests that the tariff did not change the weather response |
| response against CDD | **yes** | **yes** | **yes** | scientific |
| tested its own model restriction | **yes** (on one extract) | — | partially | scientific, but not across extracts |
| enrolled mix vs estate mix | no | no | no | — |
| within-segment representativeness | — | yes (wrong axis) | yes (wrong axis) | scientific, misdirected |
| negative control / placebo | no | no | no | — |
| alternative specification | absolute vs fractional considered | considered | considered | scientific |
| uncertainty / sensitivity | no | no | no | — |
| unit test of the pipeline | **yes** | — | — | implementation only |

Every trial performed some genuine scientific falsification, and all three ran the same valuable
check (controls against history). None ran a negative control, and none checked the enrolled mix
against the estate. Trial 1 was the most self-critical — it explicitly doubted its own restriction —
and was the one that failed, because it tested the doubt on the extract it could see rather than
encoding a model general enough to hold on the extracts it could not.

---

## 13. Metrics

| metric | value |
|---|---|
| successes / 3 (frozen verifier) | **0 / 3** |
| empirical single-run success-rate estimator (frozen) | 0.000 |
| task-level pass@3 (frozen) | **0** |
| successes / 3 under adjudicated F8 correction (load-weighted response) | **2 / 3** — reported for adjudication, not as a result |
| correct decisions, visible extract | 3 / 3 |
| correct decisions, all five fixtures | **2 / 3** trials (2 and 3); trial 1 correct on 4 of 5 |
| correct target forecast on all fixtures | **2 / 3** |
| correct estate response on all fixtures, frozen definition | 0 / 3 |
| correct estate response on all fixtures, load-weighted definition | 2 / 3 |
| recognised both mechanisms | 2 / 3 explicitly (3 / 3 heat, 2 / 3 selection) |
| executed both mechanisms | 2 / 3 |
| performed meaningful scientific falsification | 3 / 3 (partial in every case) |

**Clopper–Pearson 95 % interval for 0 / 3: [0.000, 0.708]. For 2 / 3: [0.094, 0.992].** Neither is a
pass rate.

---

## 14. Assessment

**BENCHMARK ISSUE — NEEDS ADJUDICATION.**

The frozen 0/3 does not measure what G36 was built to measure. Two of three trials solved the
scientific problem — correctly handling both transports and forecasting every fixture, including the
hardest, within tolerance — and were failed on a quantity whose graded definition differs from the one
the contract describes.

**The underlying task is scientifically informative.** The one genuine failure is exactly the kind G36
was designed to expose: a model that recognised heat dependence, tested it, and encoded a locally
valid restriction that does not transport. The heat mechanism separated trial 1 from trials 2 and 3
cleanly, and the separation sat at S4–S5 as predicted.

**But two findings qualify it as a final candidate:**

1. **The response-definition defect** (F8) must be resolved before any G36 number is used.
2. **The selection transport is inert in practice**, because the incumbent scaffold hands it over.
   G36 effectively tests one transport, not two.

If adjudication adopts the load-weighted definition, the measured result becomes 2/3 with task-level
pass@3 = 1. That is similar to G34's 2/3 and informative about *where* the model fails, but not a
discriminating difficulty measurement.

---

## 15. Biggest remaining uncertainty

Whether the 2/3 that would result from a definitional correction reflects the task's true difficulty,
or whether trials 2 and 3 — which share an estimator to 12 significant figures — represent one
approach sampled twice. Three trials cannot distinguish "this model usually solves G36" from "this
model has one good approach and one bad one, and drew the good one twice". That is a sample-size
limit, and it is not resolvable without additional authorised trials.

---

## 16. Cost

| item | cost |
|---|---|
| trial 1 (valid) | $0.14520060 |
| trial 2 (valid) | $0.11008565 |
| trial 3 (valid) | $0.10007435 |
| invalid runs | $0.00 (none) |
| **G36 Gemini baseline total** | **$0.35536060** |
| G36 `harbor check` (validation) | $0.46880000 |
| **G36 total model spend** | **$0.82416060** |

Session model spend (from $1.0958 before G36 validation): **$1.9200** of the $3.00 cap.
