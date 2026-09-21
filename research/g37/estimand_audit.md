# G37 estimand audit — written BEFORE any generator or simulation existed

Order of work, recorded for provenance:
1. this file and `threshold_provenance.md`;
2. `domain_tournament.md`;
3. only then `sim/`.

## Leading concept C1: in-line thickness gauge replacement at a precision-shim supplier

### Which capability quantity does the business actually care about?
| candidate | what it measures | appropriate here? |
|---|---|---|
| **Cpk** | short-term / within-subgroup capability: σ from R̄/d₂ or pooled within-subgroup SD | **No.** It describes what the process *could* do if between-coil variation vanished. The customer receives parts from every coil, so between-coil variation reaches the customer. Cpk is also only meaningful for a process in statistical control. |
| **Ppk** | overall (long-term) capability of the parts actually produced in a window: σ = overall SD | **Yes, as the contractual index.** It is what the customer supply agreement specifies (below), and it needs no stability assumption to be *defined* as a moment ratio. |
| fraction nonconforming (ppm) | P(true thickness outside spec) | Business-relevant for scrap cost, but it depends on the **tail shape**. Under normality it is a monotone function of μ and σ; without normality it is not identified from moments and replicate-based deconvolution. Grading it would require a normality assumption the analyst cannot fully verify from the evidence. **Not graded**, and not reported as a graded fact. |
| expected scrap cost | ppm × cost | same tail problem, plus a cost model. Not graded. |
| P(Ppk < 1.33) | a posterior probability | depends on the prior and the analyst's uncertainty model; not a property of the parts. Not graded. |

**Decision:** the graded business quantity is **latent-process Ppk**. It is computed on the *true*
thickness of the parts produced in the evaluation window, defined as the thickness the contractual
reference method would report without random error.

### Cpk/Ppk assumption audit
- **Stability.** Ppk as a moment ratio needs none. Its *interpretation* as a defect rate needs
  normality, which is not graded.
- **Normality.** Not needed for any graded quantity. The latent mean and variance are
  moment-identified.
- **Within vs overall variation.** Overall, by contract. Within-subgroup σ is a wrong object
  (W16, "Cpk instead of Ppk").
- **Specification limits.** Both limits come from the customer drawing (`2.500 ± 0.060 mm`). This is
  not a one-sided characteristic.
- **Subgroups.** Production records carry a coil ID; coils are the rational subgroups. They matter
  only for the within-vs-overall distinction.

### Pinned graded quantities (C1)
The reference scale is the thickness the customer-agreed **contact reference method** (the old
gauge's method, drawing note 4) reports without random error. The window is the post-change
evaluation period. The population is every part produced in that window, with each part weighted
once. Because every coil in the window is sampled, the truth is **finite-population over the coils
actually produced**, and the within-coil part population is effectively infinite.

| quantity | units | population | window | weighting | formula | business meaning |
|---|---|---|---|---|---|---|
| `latent_mean_post_mm` | mm, reference scale | all parts produced post-change | post window | each part once | μ₁ = E[X] over produced parts | where the process is centred |
| `latent_sd_post_mm` | mm, reference scale | same | post window | each part once | σ₁ = SD[X], overall (between- plus within-coil) | true part-to-part spread |
| `latent_ppk_post` | dimensionless | same | post window | — | min(USL − μ₁, μ₁ − LSL) / (3σ₁) | contractual capability; **algebraically forced** by μ₁, σ₁ and the drawing limits |
| `latent_sd_pre_mm` | mm, reference scale | all parts produced in the pre-change window | pre window | each part once | σ₀ = SD[X], overall | answers "did the process really change?" |
| `customer_notification` | "notify" / "no_notification" | — | post window | — | "notify" iff latent_ppk_post < 1.33 | contractual action; **forced** |

**Reported but NOT graded:**
- the new gauge's calibration slope and offset on parts;
- the per-gauge error SDs;
- the observed (dashboard) Ppk.

They are intermediates. Per principle 11, an intermediate is graded only if its own window is
measured and adequate, and the business question does not need them graded.

## Estimands for the other top-4 concepts (fixed before their prototypes)
- **C2 (assay transfer):** latent lot-potency Ppk over the CPV window,
  σ = SD of true lot potency across released lots, with spec 95.0–105.0 % LC. Decision: CPV
  escalation iff Ppk < 1.33.
- **C7 (inspection-model migration):** latent defect prevalence among shipped units in the window,
  p = P(unit truly defective), per shipped unit. Decision: supplier chargeback iff p > 0.50 %
  (contract).
- **C9 (CD-SEM fleet matching):** latent wafer-to-wafer SD of true critical dimension across the
  product's wafers in the window, weighted per wafer. Decision: yield-model trigger iff
  σ > 1.2 nm (process-window budget).
