# Next-task research tournament (post-G36) — RESEARCH ONLY, NOTHING BUILT

**Coverage already saturated:**
- Task02: as-of state
- G05: causal identification / trends
- G10: censored demand
- G24: OPE object / grain
- G08: forecast vintages
- G34: competing risks
- G35: interference
- G36: regime transport

Every direction below is screened against principles 8–14 (IGQA, natural path, counterexample search,
identifiability window, fixture coverage, decision/tolerance, recognition ≠ execution). None is
optimised for any model.

## D1 — Measurement-system change (errors-in-variables calibration transfer)

| aspect | detail |
|---|---|
| domain | manufacturing quality |
| business incident | A plant replaced its thickness gauge mid-year. The dashboard shows capability (Cpk) collapsing, and a capital request for a new line rides on it. |
| scientific object | latent true process mean and SD (→ Cpk) across a measurement-system change; the old→new mapping is estimated from a bridge study where **both** gauges carry noise |
| why not covered | no task has *observed ≠ latent because of the instrument*; all prior tasks measure outcomes without error |
| recognition | the gauge-change log and the bridge study exist in docs |
| execution | an OLS new-on-old bridge fit is **attenuated** (regression dilution). A correct fit uses reference standards / Deming with repeatability from the gauge R&R table. The variance must be de-noised for Cpk. Recognising "the gauge changed" does not give the estimator. |
| natural path | apply the vendor's stated offset, or regress new on old; both are wrong by design |
| cheap-solve risk | the vendor note gives the exact slope → trivial. The docs must give only the design, never the mapping. |
| graded-fact evidence | latent mean and SD are generator truth; Cpk is algebraic from them |
| verifier | grade latent SD and mean (IGQA: two derivations, Deming vs method-of-moments with R&R); Cpk forced; decision on a Cpk threshold with a designed margin (principle 13). The window must be measured: attenuation bias ≫ SE by construction (reliability ≈ 0.7). |

## D2 — Immortal-time / time-zero misalignment (target-trial emulation)

| aspect | detail |
|---|---|
| domain | subscription business |
| business incident | "Premium-support customers churn 40 % less." Premium is bought months after signup, so membership requires having survived. |
| scientific object | effect of adopting premium on 12-month churn, emulating a trial with aligned time zero (landmark, or time-varying exposure) |
| why not covered | G05 identification is about trends; G34 is about competing events. None is about **exposure defined by future survival**. |
| recognition | the adoption dates are in the data |
| execution | landmark or sequential-trial emulation with a correct risk set; the naive "ever-premium" cohort is biased |
| natural path | the "ever vs never" split in the existing churn report (wrong) |
| cheap-solve risk | moderate: "landmark at 90 days" is a known recipe. Hidden extracts must vary adoption-time distributions so a fixed landmark fails. |
| graded-fact evidence | latent potential outcomes from the generator |
| verifier | the estimand **must be pinned** (landmark-specific vs per-protocol), or it risks a G36-type F8. **Highest semantic risk of the five.** |

## D3 — Selection on a noisy outcome: regression to the mean with a threshold rule

| aspect | detail |
|---|---|
| domain | retail operations |
| business incident | Stores below a shrink threshold got a loss-prevention programme; shrink "fell 30 %". |
| scientific object | programme effect at the threshold (RD) or with transient-shock modelling |
| why not covered | G05's causal task has no selection-on-outcome mechanism |
| recognition | the threshold is in the SOP |
| execution | local-linear RD bandwidth / variance; pre/post and DiD both inherit RTM |
| natural path | pre/post on treated stores (wrong) |
| cheap-solve risk | low |
| graded-fact evidence | generator truth |
| verifier | **identifiability risk (principle 11).** An RD SE at feasible n may be too large to separate a DiD-with-RTM route. The window needs simulation first. Estimand pinning: effect at cutoff vs ATT. |

## D4 — Clustered design inference at the decision boundary

| aspect | detail |
|---|---|
| domain | marketplace or logistics |
| business incident | A depot-randomised pilot was analysed per parcel; its CI excludes zero. |
| scientific object | cluster-level effect and its design-based CI; the decision is whether the lower bound clears zero |
| why not covered | partly: G24's grain problem is adjacent |
| recognition | the randomisation unit is documented |
| execution | correct unit, few clusters (small-sample correction) |
| natural path | per-parcel t-test |
| cheap-solve risk | moderate |
| verifier | grading a CI is a data functional, so IGQA is fine. Decision/tolerance compatibility is intrinsic, because the decision sits on the interval bound. **Overlaps G24.** |

## D5 — Left truncation / delayed entry after a system migration

| aspect | detail |
|---|---|
| domain | equipment warranty |
| business incident | The warranty database only holds units alive at a 2023 migration; the failure curve looks too good. |
| scientific object | survival with delayed entry (risk set from entry age) |
| why not covered | G34 is right-censoring + competing risks; truncation is a different risk-set error |
| recognition | the migration note |
| execution | risk set from entry age |
| natural path | ordinary KM (wrong) |
| cheap-solve risk | moderate (lifelines `entry=`) |
| verifier | clean IGQA. **Same domain family as G34**, so it adds less new coverage. |

## Scoring against the new principles

(+ = favourable, ! = needs a gate before any build)

| | IGQA pinnable | natural path fails | counterexample risk | identifiability window | recognition ≠ execution | new coverage |
|---|---|---|---|---|---|---|
| D1 | + | + | ! (Deming vs OLS-with-R&R-correction must both be valid and separate from naive) | + (by construction) | **+** | **+** |
| D2 | ! | + | ! | + | ! (recipe known) | + |
| D3 | ! | + | ! | **!** | + | + |
| D4 | + | + | ! | + | ! | ! (overlaps G24) |
| D5 | + | + | + | + | ! | ! (overlaps G34) |

## Recommendation: **D1 — measurement-system change**

**Why it adds new scientific coverage.** It is the only direction where the error is in the
*measurement model*, not the population, time, selection or estimand. The failure it targets is
treating an observed quantity as the latent one after an instrument change. It lies outside every
existing task, including G34 (whose observed events are exact) and G10 (whose censoring is
mechanical, not noisy).

**Required pre-build gates (all before any implementation):**
1. **IGQA.** Write the latent-mean / latent-SD / Cpk definitions from the planned contract text
   alone. Build two estimator families with no shared helper (Deming with known variance ratio;
   method-of-moments with the gauge R&R table).
2. **Natural-path audit.** Minimal edits to the planned scaffold (vendor offset; OLS bridge;
   raw-reading Cpk) must all fail by ≥ 3 × tolerance.
3. **Counterexample search.** Plausible wrong models: OLS bridge; reverse regression; ignoring
   repeatability in SD; pooling pre/post without mapping; using the bridge-study mean only. None may
   pass on all fixtures.
4. **Identifiability window.** Measured max(valid err) < tol < min(wrong err), ratio ≥ 3, **before
   freeze**. Reject the design if it cannot be met.
5. **Fixture coverage.** Every wrong method is rejected on ≥ 2 extracts, with no single-fixture
   dependence.
6. **Decision/tolerance.** |Cpk truth − threshold| > tolerance on every extract. The threshold comes
   from business economics (G36 lesson), never from margin-maximisation.
7. **Recognition ≠ execution.** Give "the gauge changed and a bridge study exists" for free and
   confirm naive executions still fail.
8. **Cheap-solve, leakage, representation and determinism gates** as for G35/G36.
