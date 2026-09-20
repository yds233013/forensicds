# G34 — first and only Gemini baseline: trajectory and benchmark-validity analysis

**Task:** `candidates/g34-fleet-reliability-gate`, frozen at **`f14dd0c0dbcd763c`**
**Model:** `google/gemini-3-flash-preview` via `gemini-cli` 0.60.0
**Trials:** 3 valid, sequential, no replacements needed
**Result: 2 / 3**
**Total cost: $0.124406**

G34 was **not modified before, during or after** these trials. All three trials carry the identical
Harbor `task_checksum` `48b9cdb1bb48d5b5…`, which is independent evidence of no mid-baseline drift.

---

## 1. Authorisation note

The instruction to run this baseline came in the message of 2026-09-20 that opened with "Proceed with
the G34 Gemini baseline authorization from my previous prompt." **No such previous authorisation
existed.** The prior G34 prompt said the opposite in terms ("It is NOT authorization for a Gemini
baseline… ABSOLUTELY NO GEMINI BASELINE"); the detailed three-trial protocol being remembered belongs to
**G05**. This was raised before any credit was spent, and the baseline proceeded on the authority of the
2026-09-20 message itself, which is unambiguous on its own.

One protocol point was resolved explicitly rather than silently: G05's rule was "if any trial appears
invalid, STOP; do not automatically launch replacements", while the G34 instruction asks for three
*valid* trials. The rule applied here was: run toward three valid trials, but **stop and adjudicate
before launching any replacement**. No trial required adjudication — all three were valid on their face.

---

## 2. Trial results

| | trial 1 `hLbWzqK` | trial 2 `UPCLpLx` | trial 3 `SdvVPQN` |
|---|---|---|---|
| **reward** | **1** | **0** | **1** |
| checks passed | 14 / 14 | 11 / 14 | 14 / 14 |
| agent wall-clock | 81 s | 104 s | 75 s |
| cost | $0.038133 | $0.052794 | $0.033479 |
| tokens in / cache / out | 151 058 / 105 170 / 3 310 | 212 821 / 144 614 / 3 820 | 143 534 / 109 197 / 3 617 |
| trajectory steps | 20 | 26 | 18 |
| `task_checksum` | `48b9cdb1bb48d5b5` | `48b9cdb1bb48d5b5` | `48b9cdb1bb48d5b5` |
| exception | none | none | none |

**Validity.** All three are valid agent trials. Agent setup completed normally in each (nvm → Node 22 →
`@google/gemini-cli`, API-key auth, `--yolo --model=gemini-3-flash-preview`); no setup timeout, which was
the invalidity mode that killed `g08-gemini3flash-baseline-1`; `exception_info` is null throughout; the
verifier produced a complete `test-stdout.txt` and `ctrf.json` in every case. Nothing resembles the
`JnK5hsR` infrastructure signature.

*Process note against my own error:* mid-run I briefly reported trial 1 as a failure with an empty
verifier log. That was wrong. `tests/test.sh` writes `echo 0 > reward.txt` as its **first** action, a
fail-closed default, so the file appears seconds after the verifier starts. I had keyed my wait on that
file's existence and read an in-progress run as a finished one. The wait condition was changed to track
the Harbor process. No conclusion in this document rests on that mistaken reading.

### Produced quantities, error in tolerance units (visible extract)

| quantity | truth | trial 1 | trial 2 | trial 3 |
|---|---|---|---|---|
| unplanned_failure_rate_36m | 0.3598 | 0.3570 (0.20 τ) | **0.2757 (6.11 τ)** | 0.3570 (0.20 τ) |
| overhaul_rate_36m | 0.4104 | 0.4155 (0.30 τ) | **0.2766 (7.96 τ)** | 0.4155 (0.30 τ) |
| retirement_rate_36m | 0.1736 | 0.1710 (0.25 τ) | **0.1367 (3.61 τ)** | 0.1710 (0.25 τ) |
| still_original_assembly_36m | 0.0562 | 0.0565 (0.03 τ) | **0.3111 (23.85 τ)** | 0.0565 (0.03 τ) |
| assembly_failure_rate_36m | 0.5547 | 0.5442 (0.21 τ) | 0.5442 (0.21 τ) | 0.5442 (0.21 τ) |
| **recommendation** | expanded | expanded ✅ | **baseline ✗** | expanded ✅ |

Trials 1 and 3 produced **bit-identical** aftermarket numbers, so the two passes converged on the same
estimator rather than landing inside tolerance by luck from different directions.

---

## 3. What the failing trial actually did

Trial 2 is the most informative of the three, because it **reached the right framing and still failed.**
Its own closing summary is correct prose:

> the published figure "used the Kaplan-Meier estimator (appropriate for Engineering's study of intrinsic
> part life) instead of Cumulative Incidence… The previous method ignored the fact that overhauls and
> retirements 'compete' with failures".

It then computed raw observed proportions of the full installed base:

| outcome | implied units | of n = 9 000 |
|---|---|---|
| UNPL_FAIL | 2 481 | 0.2757 |
| PM_OVHL | 2 489 | 0.2766 |
| ASSET_RET | 1 230 | 0.1367 |
| still original | 2 800 | 0.3111 |
| **sum** | **9 000** | **1.000000** |

Every unit censored by the extract cut-off before reaching 36 months was silently counted as *still
carrying its original assembly*. Only **292** units are genuinely still under observation at 36 months,
so the censored mass is enormous: `still_original` lands at 0.3111 against a truth of 0.0562, and every
event probability is dragged downward. `unplanned_failure_rate_36m` falls to 0.2757, **below the 0.28
procurement trigger**, and the recommendation flips to `baseline` — the wrong business answer, arrived at
through an analysis whose narrative is entirely plausible.

This is the designed failure realised precisely: F10, correct decision framework, wrong statistical
object, wrong decision. It corresponds to mutation `M05_raw_fraction` compounded with the cut-off
mishandled as an outcome.

### The verifier check that mattered

**`test_probability_conservation` passed on the failing trial.** The four raw fractions partition the
installed base and sum to 1.000000 exactly. Every coherence property held. Only the tolerance comparisons
in `test_aftermarket_quantities`, `test_recommendation` and the hidden extracts caught it.

This retrospectively justifies a design decision that could have gone the other way: had G34 graded only
internal coherence plus the decision — the "cheap" verifier — trial 2 would have scored **1**.

---

## 4. What separates a pass from a fail

| | trial 1 (pass) | trial 2 (fail) | trial 3 (pass) |
|---|---|---|---|
| tool calls | 19 | **25** | 22 |
| trajectory steps | 20 | **26** | 18 |
| read `maintenance_sop.md` | **no** | yes | yes |
| "cumulative incidence" vocabulary | 16 | 16 | 8 |
| **reasoning about censoring** | **5 hits** | **0 hits** | **5 hits** |

The discriminator is **not** effort and **not** document retrieval — the failing trial did more of both.
It is whether the agent reasoned about the **risk set** at all. Both passes did; the failure never used
the concept once across 26 steps.

This is the single most reassuring finding for the task's construct validity. G34 is measuring statistical
reasoning, not reading comprehension or persistence.

---

## 5. Benchmark validity

### 5.1 The pre-registered hint-calibration risk, revisited

Before the baseline I flagged (validation report §2.1) that `instruction.md` may be too generous, because
Operations' objection states the mechanism in plain language: assemblies "are swapped out at the scheduled
overhaul, or leave with the unit, long before anything fails in service."

**The baseline shows that concern was half right, and I had overstated it.**

- It *is* generous about the **framing**. All three trials reached competing-risks vocabulary; none had to
  discover that overhaul and retirement remove assemblies. Trial 1 got there without even opening the SOP.
- It is **not** generous about the **estimator**. The hint says nothing about administrative censoring of
  the risk set, and that is exactly where trial 2 died. Saying "cumulative incidence" is not sufficient to
  compute one.

The difficulty survives the hint. I am recording this rather than acting on it: the task is frozen, and
changing the brief after observing model behaviour is precisely the tuning that is forbidden.

### 5.2 Is 2/3 too easy?

**n = 3 cannot answer this question, and it should not be reported as if it could.** Clopper–Pearson 95%
interval for 2 successes in 3:

| observed | 95% CI |
|---|---|
| 0/3 | [0.000, 0.708] |
| 1/3 | [0.008, 0.906] |
| **2/3** | **[0.094, 0.992]** |
| 3/3 | [0.292, 1.000] |

The interval spans **0.094 to 0.992** — width 0.90. This baseline cannot distinguish a task that a flash
model solves 10% of the time from one it solves 99% of the time. Per the G05 O.1 adjudication, **2/3 must
not be reported as a pass@1 of 0.667.** It is three observations, and the honest statement is: *this model
solved G34 on two of three attempts, and the sampling uncertainty is nearly the whole unit interval.*

### 5.3 The genuine concern, stated plainly

Setting the interval aside, the raw fact remains that a **flash-tier** model solved a task designed as
hard, twice, in **81 and 75 seconds**, for **under four cents each**. Even with n = 3, that is weak
evidence for high difficulty.

Three considerations pull against over-reacting:

1. **The failure mode is real and expensive.** When it failed, it failed by recommending the wrong
   procurement decision with a confident, coherent, plausible narrative. That is exactly the failure
   ForensicDS exists to detect, and it is not a contrived one.
2. **The two passes were genuinely correct**, not lucky — bit-identical numbers, all three hidden extracts
   passed, and a correct verbal diagnosis of the estimand distinction.
3. **Difficulty is model-relative and this is one model at one point in time.** A task that a 2026
   flash model solves 2/3 of the time is not thereby worthless; it is a task with a measured difficulty.

My assessment: **G34 is a valid task with lower discriminating power against `gemini-3-flash-preview` than
its design intended.** It is not broken — the verifier caught the failure it was built to catch, wrong
analyses fail by 1.94–122 τ, and the pass/fail split tracks a substantive reasoning difference. But it
should not be presented as a hard task for frontier-adjacent models on this evidence.

### 5.4 What did not happen

- No trial modified `data/warehouse.sqlite` (`test_warehouse_unmodified` passed in all three).
- No trial hard-coded values; `test_rerun_is_deterministic` and the hidden extracts passed in both passes.
- No cheap-solve or leak was exercised: the failing trial failed *statistically*, not by shortcut.
- No fourth trial was run.

---

## 6. Cost

| item | cost |
|---|---|
| trial 1 | $0.038133 |
| trial 2 | $0.052794 |
| trial 3 | $0.033479 |
| **Gemini baseline total** | **$0.124406** |
| `harbor check` (validation, pre-baseline) | $0.419600 |
| **G34 total model spend** | **$0.544006** |

Oracle and Nop runs cost $0 — they run no model.

---

## 7. Recommendation to the maintainer

1. **Keep G34, frozen as-is.** Do not retune the brief, the tolerance or the fixtures in response to
   these results.
2. **Record its measured difficulty honestly** — 2/3 on `gemini-3-flash-preview`, CI [0.094, 0.992] — and
   do not quote a pass rate.
3. **If more resolution is wanted, that is a separate, explicitly authorised decision.** Distinguishing
   "easy" from "moderate" at this precision needs n ≈ 20–30, roughly $1–1.5 at observed per-trial cost.
   I have not run it and will not without instruction.
4. **Carry the §3 finding into future task design:** coherence checks (sums to one, internally
   consistent) are worth little on their own. The failing trial satisfied every one of them. Tolerance
   comparisons against latent truth are what did the work.
