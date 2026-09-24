# P22 implementation specification — gauge recalibration

Authoritative source: `research/phase2/HANDOFF_2026-09-23.md` §16 (P22 A–Z) and §20/§23/§24/§26.
This document is the *independent scientific specification* required by the build rules: it fixes the
data-generating process, the identifiable quantities and the decision rule **before** any code is written,
so that the reference implementation and the verifier can be derived separately from it.

## 1. The professional incident

Kelvin Works (an industrial OEM plant) machines hydraulic manifold bodies, part `MAN-4471`. First-pass yield
on the bore diameter fell from **97.2 %** (weeks 13–18) to **92.8 %** (weeks 19–24). Scrap is running
£180 k/month. Purchasing has opened a supplier nonconformance against the bar-stock supplier, because the
drop coincides with a change of heat family (the plant switched from the legacy `H2` heats to `H3` heats in
week 19).

Coordinate-measuring machine **CMM-1** was recalibrated at the start of week 19. The calibration certificate
records as-found and as-left deviations against a certified length standard.

## 2. The consequential decision

The supply quality agreement states: *a supplier nonconformance may be escalated to a supplier change only
if the nonconforming rate attributable to material, measured against the drawing's conformance reference,
exceeds 5.0 %.* The decision is `raise_supplier_nonconformance` vs `no_supplier_action`, worth £2.4 m.

## 3. Initially plausible explanations (≥3 required; 5 present)

1. **Material** — the H3 heats are harder/softer and the process shifted.
2. **Measurement system** — the week-19 recalibration moved CMM-1's bias, so parts that used to pass now fail.
3. **Tooling** — a tool-wear trend crossed tolerance.
4. **Operator/shift** — a new night-shift operator.
5. **Control limits** — the SPC limits were recomputed on a different period.

All five are individually checkable in the workspace. **Which are actually active varies by extract.**

## 4. The analytical object to reconstruct

> The nonconforming rate of `MAN-4471` bores **against a single, unchanged conformance reference**, with the
> observed change decomposed into the part attributable to the measurement system and the part attributable
> to material (and to tooling/operator where active).

The drawing defines conformance against the certified reference, not against whatever the instrument
currently reads. Nothing in the workspace states this as an instruction; it follows from the drawing plus
the calibration procedure.

## 5. Data-generating process (generator truth; never shipped)

For part *i* in week *w*, true bore deviation from nominal (µm):

```
X_i = m_heat(h_i) + tool_i + op_i + e_i            e_i ~ N(0, sigma_p^2)
```
* `sigma_p = 13.3` µm; spec is nominal ±30 µm, so a centred process is nonconforming at
  2·Φ(−30/13.63) ≈ **2.78 %** once measurement noise is included.
* `m_heat`: 0 µm for H2 heats; a small positive shift plus slightly inflated within-heat spread for H3 heats,
  calibrated so the **material-attributable** increase in the nonconforming rate is ≈ **0.9 pp**.
* `tool_i`: zero in the visible extract; a linear wear ramp in hidden extract C.
* `op_i`: zero in the visible extract; a small shift on one shift in hidden extract B.

Measurement on machine *k*:
```
M_ik = X_i + b_k(w) + d_ik                          d_ik ~ N(0, sigma_m^2),  sigma_m = 3.0 µm
```
* `b_CMM1(w) = 0` for w ≤ 18 and `b_CMM1(w) = B` for w ≥ 19, with **B ≈ +8.0 µm** (the as-left adjustment
  error). `b_CMM2(w) = 0` throughout — CMM-2 was not recalibrated.
* Disposition is `PASS` iff `|M| <= 30` on the machine that measured the part. This is what "yield" means in
  the plant's report, and it is instrument-dependent.

Evidence written into the world:
* **Retained reference parts**: 12 artefacts with certified deviations, measured 3× on each machine in week 17
  and again in week 20. Paired differences identify `B` with SE ≈ `sigma_m/sqrt(36)` ≈ 0.5 µm.
* **Cross-check sample**: 25 % of production parts are measured on *both* machines (routine gauge-correlation
  practice). Paired production differences give a second, independent estimate of `B`.
* **Functional (leak) test** on an 8 % sample: `FAIL` iff `|X| > 30` plus a small independent test error —
  an outcome that does not depend on either CMM.

## 6. Identifiable quantities and their estimators

| quantity | identified by | tolerance | basis |
|---|---|---|---|
| `bias_um` | paired reference-part differences, or paired cross-check differences | **±1.0 µm** | ≈2× the 0.5 µm SE of the reference bridge |
| `baseline_nonconforming_rate_pct` (w13–18) | direct count on CMM-1 | ±0.3 pp | binomial SE ≈0.13 pp at n≈12,000 |
| `reported_nonconforming_rate_pct` (w19–24) | direct count on CMM-1, uncorrected | ±0.3 pp | reproduces the incumbent |
| `corrected_nonconforming_rate_pct` (w19–24) | count on `M − bias_um` | ±0.3 pp | binomial SE + bias SE propagated ≈0.15 pp |
| `attribution_pp.measurement_system` | `reported − corrected` | ±0.5 pp | difference of two rates |
| `attribution_pp.material` | `corrected − baseline` **restricted to the heat families present** | ±0.5 pp | as above |
| `attribution_pp.tooling`, `.operator`, `.other` | residual after the above, from the wear/shift diagnostics | ±0.5 pp | zero in the visible extract, non-zero in hidden B and C |
| `cmm2_nonconforming_rate_pct` (w19–24, cross-check sample) | direct count on CMM-2 | ±0.6 pp | binomial SE ≈0.28 pp at n≈6,000 |
| `supplier_decision` | the agreement's 5.0 % rule applied to the material-attributable rate | exact | — |

**Not identifiable and therefore not graded:** the latent per-part `X_i`; the exact split between "material
mean shift" and "material variance inflation"; any retrained-model-style quantity. The verifier grades the
decomposition, not the mechanism's internal parameters.

## 7. The correct investigation

Reproduce both rates → enumerate the five explanations → find the calibration certificate and the retained
reference parts → estimate `B` from the paired differences → re-disposition the parts on the corrected scale
→ re-test the heat-family effect on the corrected scale → check tool wear and shift → allocate the change →
apply the agreement's rule.

## 8. The sophisticated incorrect investigation

A textbook SPC and capability study on the **raw CMM-1** values: control charts by shift and heat lot,
Cp/Cpk before and after, and an ANOVA showing a highly significant heat-family effect (it *is* significant,
because the heat change is real and n is large). Conclusion: the H3 heats are out of specification; escalate
to a supplier change. This ties out against the scrap ledger, the charts are in control apart from the step,
Cpk recomputes consistently, and the timing coincides with the heat changeover. **Nothing inside this frame
can fail.**

## 9. Falsification opportunities (≥2 required; 3 present)

| route | competing predictions | evidence |
|---|---|---|
| retained reference parts | material ⇒ 0 µm paired difference; measurement ⇒ ≈ `B` | 12 parts × 3 reps × 2 machines × 2 dates |
| second, un-recalibrated CMM | material ⇒ CMM-2's rate rises too; measurement ⇒ CMM-2 flat | 25 % cross-check sample |
| functional leak test | material ⇒ leak-fail rate rises ≈ proportionally; measurement ⇒ rises only by the material component | 8 % sample |

## 10. Deliverables and verifier strategy

`out/readout.json` with `baseline_nonconforming_rate_pct`, `reported_nonconforming_rate_pct`,
`corrected_nonconforming_rate_pct`, `cmm2_nonconforming_rate_pct`, `bias_um`,
`attribution_pp` (five neutral keys summing to the observed change), `supplier_decision`; and
`out/part_dispositions.csv` with the corrected per-part disposition (graded only for internal consistency
with the reported rate, because two valid bias estimates flip a handful of boundary parts).

The verifier re-runs the agent's pipeline unprivileged on the visible extract and three hidden extracts,
recomputes every quantity from an independent derivation, and emits `reward.json` with one criterion per
scientific stage plus the binary `reward`.

**The attribution vocabulary is deliberately neutral** — it names all five candidate causes and privileges
none — which is how the output contract can be exhaustive without stating the answer.
