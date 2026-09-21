# G36 development defect log

Every defect below was found by deterministic measurement. **No target-model output influenced any
correction: no Gemini, no Claude, no model of any kind has seen this task.**

---

## D1 - `truth()` returned the median, not the mean

**How discovered.** The K9 gate reported all three independent estimator families carrying a shared
positive bias of +0.065 to +0.095 kW, five to eight times their own sampling sd. Three genuinely
independent methods agreeing on a bias is evidence about the *truth*, not about the methods.

**The error.** Observed load is `median * exp(N(0, sigma))`, whose expectation is
`median * exp(sigma^2/2)` = median x 1.0245 at sigma = 0.22. `truth()` returned the median. A utility
must serve *expected* load, so the target quantity was wrong by 2.45 %.

**What it invalidated.** Every K9 measurement taken before the fix, and any tolerance that would have
been derived from them.

**Correction.** Split into `_load_median()` (used by the generator) and `_load_expected()` (used by
`truth()` only). A first attempt applied the correction inside the single shared helper, which moved
the generator and the truth together and left the bias exactly where it was - recorded here because
it is an easy mistake to repeat.

**Rerun.** Full K9 gate. Post-fix biases: +0.0083, +0.0022, -0.0018.

---

## D2 - F2 was misspecified, not independent

**How discovered.** After D1, F2 still disagreed with F1 systematically.

**The error.** F2 fitted an **additive** tariff term (`[1, cdd, tariff, tariff*cdd]`) against a
mechanism that is **multiplicative**. It was a wrong estimator wearing the name of an independent
valid family. Had it been retained, K9 would have "failed" for a reason that was not about the
design.

**What it invalidated.** The first two K9 runs' disagreement statistics.

**Correction.** Rewritten as Gauss-Newton nonlinear least squares on the correctly specified form
`(base + beta*cdd) * (1 - r0 - r1*(cdd - ref))^tariff`, fitted jointly over history and pilot.

**Rerun.** Full K9 gate.

---

## D3 - F1 carried a ratio-estimator bias

**How discovered.** After D1 and D2, F1 retained a +0.020 kW bias (about two sampling sds) while F2
and F3 were near zero.

**The error.** F1 formed `1 - mean(treatment)/mean(control)` **per pilot day** and then regressed
those daily ratios on CDD. A noisy denominator inside an average is a classic ratio-estimator bias.

**Correction.** Smooth each arm against CDD first, then form the ratio from the fitted values.

**Rerun.** Full K9 gate. F1 bias fell to +0.0083.

---

## D4 - the negative control was confounded by segment imbalance

**How discovered.** The pre-pilot negative control - which must find approximately zero tariff
response in a season before any tariff existed - returned +0.027 and -0.038 on two fixtures.

**The error.** The control pooled across segments. Random assignment of ~550 enrolled households
leaves segment imbalance between the arms, and segment base loads span 1.05 to 3.30 kW, so a small
imbalance manufactures a few per cent of spurious "response". A property of the diagnostic, not of
the data.

**Correction.** Stratify by segment, which is what the main analysis does anyway.

**Rerun.** Negative control on all five fixtures: -0.0026 to +0.0027.

---

## D5 - the leakage probe used the wrong statistic

**How discovered.** The probe reported `corr(segment, enrolled) = +0.014 to +0.026`, which was
implausible given opt-in propensities differing sevenfold across segments.

**The error.** A linear correlation computed on an **alphabetically coded nominal variable**. The
alphabetical order (`APT`, `HOUSE_LARGE_POOL`, `HOUSE_SMART_HVAC`, `HOUSE_STANDARD`) scrambles the
propensity order (0.03, 0.22, 0.16, 0.05), so the linear association is near zero while the actual
selection is severe.

**Correction.** Report enrolment over-representation ratios instead. Measured: 0.32x to 2.49x on the
visible extract, 0.07x to 2.90x on hidden_a. The selection is strong and was never absent - only
mismeasured.

---

## D6 - a mutation rendered identically to another

**How discovered.** The mutation generator's own duplicate-hash rule.

**The error.** `M23_seasonal_naive` rendered byte-identical to `M05_historical_mean`, because this
design's history has no multi-year seasonal structure for a seasonal-naive baseline to exploit.

**Correction.** Replaced with `M23_control_arm_level`, a genuinely distinct wrong analysis. The rule
was not weakened.

---

## D7 - the oracle applied a stale decision threshold

**How discovered.** The Oracle scored **0** on its first packaged run, failing
`test_procurement_decision` and `hidden_d` while passing all eleven numeric checks.

**The error.** The business threshold moved from 2.825 to 3.057 during the provenance audit, and
both CLI modules still carried `CAPACITY_GATE_KW = 2.825`. The oracle computed the right forecast
and applied the wrong ceiling.

**Correction.** Both CLIs updated; repository swept for stale occurrences.

**Rerun.** Oracle 13/13 reward 1, Nop reward 0.

---

## What the pattern says

Five of these seven defects were in **my own measurement apparatus**, not in the task: a wrong truth,
a mislabelled estimator, a biased implementation, a confounded diagnostic, a wrong statistic. Each
would have produced a confident, internally consistent, wrong conclusion about the benchmark.

That is precisely the failure mode ForensicDS exists to detect, occurring in the construction of
ForensicDS. The defence in every case was the same: **an independent measurement that disagreed**,
and taking the disagreement seriously rather than explaining it away.
