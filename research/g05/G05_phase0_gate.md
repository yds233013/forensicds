# G05 v2 Phase-0 simulation gate (identifiability, separation, tolerances)

**Status:** round 6 is the FINAL tolerance calibration. Accepted-estimator criterion PASSED (240/240 each); wrong-method criterion passed for 20 of 21 analyses, with one documented miss (kit-conditioned DiD, §7). Round 4 passed the original gate; round 5 failed and is recorded in full.

- **Nothing built, no model run**, before this gate passed.
- **Code:** `research/g05/pilot/g05_sim.py` (DGP, regimes, exact truth), `g05_estimators.py` (panel), `run_gate.py`
  (calibration, validation, summary).
- **Results:** `research/g05/pilot/results/r{1..4}_{cal,val}.json`, `r{1..4}_tol.json`, `r{1..4}_summary.txt`.

## 1. Pre-registered protocol (fixed before round 1)

1. **Worlds.** Four regimes × seeds: calibration 20 per regime (seeds 5000 + 17i), validation 30 per regime
   (9000 + 17i).
   - Each world is a store × week panel.
   - Rounds 1–2: 700 stores × 104/156 weeks. Rounds 3–4: 760 × 156.
2. **Truth.** Exact potential-outcome effects τ_st on log net sales, averaged as in `G05_research_audit.md` §3:
   - store run-rate mean over comparable weeks e ∈ [12, 25];
   - wave and kit means over installed stores;
   - gate θ_R = kit effects weighted by the remaining programme's kit shares.

   No estimator is involved in the truth.
3. **Tolerance.** τ_q = 3.5 × RMSE (over calibration worlds) of the least efficient accepted estimator, per regime and
   quantity. 3.5σ because a reward requires 5 quantities × 4 extracts plus decisions to hold at once.
4. **Graded quantities.**
   - Main set (A): effect for each installed wave (4), gate effect, and decision (continue iff θ_R ≥ 2.5%).
   - Set B additionally grades per-kit effects. It is reported for information only and not used, because
     requiring per-kit outputs would point the agent at the population trap.
5. **Pass rule.**
   - A method passes a world if every graded quantity is inside τ and the decision is right.
   - Every accepted estimator must pass ≥ 99% of validation worlds.
   - Every wrong analysis must fail ≥ 99% of the worlds of at least one regime. The reward requires all four
     extracts.
   - Every world must have |θ_R − hurdle| ≥ 3 SD.
6. **On failure**, change the DGP or design, not only τ. Every round is recorded below.

## 2. Regimes

| Regime | What changes | Visible-seed truth example | Decision |
|---|---|---|---|
| `visible` | format trends (large formats growing); compact kit ≈ no sales effect; 30% of remaining stores get the full kit | wave effects 1.9–4.1%; kit full 4.3% / compact −0.3%; pooled installed 3.2%; gate 1.1% | stop |
| `compact_works` | compact kit raises net sales (basket +6%) | gate ≈ 3.9% | continue |
| `reversed_trends` | large formats declining, neighbourhood growing | as visible (untreated trends only) | stop |
| `slip_dip2` | 32% slips; install closures mostly two weeks before go-live; compact kit moderate | gate ≈ 3.4% | continue |

## 3. Rounds

| Round | Change | Outcome | Decision |
|---|---|---|---|
| 1 | as designed in the audit (104 weeks, kit by sqft threshold, 6–16 h install closures) | FAIL: store-trend imputation 115/120 (short pre-period); sqft-linear transport a coin flip (16/30 visible); slip regime margin 2.3 SD | Redesign, not re-tolerance |
| 2 | 156 weeks (≥ 76 pre-weeks); **kit set by floor layout (rear bagging bay), not size**; within a format, bay stores installed earlier (readiness); ramp 10 weeks; slip-regime compact effect up | FAIL: `cs_format_never` 117/120 (supercentre never-installed control cell ≈ 14 stores); closure weeks treated as comparable passes 96/120 on values | Design change: more supercentres in the remaining programme |
| 3 | 760 stores; supercentre remaining share 0.10 → 0.20 | Accepted 5/5 at 120/120. Closure weeks treated as comparable still 83/120 (install closures were 6–16 h, below a trading day) | Realism change: installs close stores for one or two full trading days; other closures half a day to two days |
| 4 | install closures 14–28 h; other closures 7–28 h | **PASS** (§4) | build approved |

**Principle behind the changes.** Every change made an ambiguous method *reliably* classifiable by changing a
mechanism toward realism. None tightened τ to reject a method, and τ is never set per method. Separation is re-measured
on the task's own generator (`candidates/g05-sco-rollout-gate/environment/build/world.py`) in the fixture audit.

## 4. Round-4 validation (30 fresh seeds per regime, 120 worlds; graded set A)

**Accepted estimators** (worlds passed; worst error/τ in brackets):

| Estimator | Worlds | Worst ratio |
|---|---|---|
| imputation: store FE + format × week FE on comparable untreated store-weeks | 120/120 | 0.6 |
| store-level DiD vs same-format not-yet-installed controls, base = comparable weeks e ∈ [−10, −3] | 120/120 | 0.7 |
| same, never-installed (remaining programme) controls only | 120/120 | 0.7 |
| imputation: store FE + store-specific linear trends + week FE | 120/120 | 0.8 |
| imputation: store FE + format × kit × week FE | 120/120 | 0.7 |

All of them transport to the remaining programme **by kit version**. The accepted family spans:
- imputation vs 2×2 DiD;
- not-yet-installed vs never-installed controls;
- format-specific time effects vs unit-specific trends;
- coarser vs finer conditioning.

**Wrong analyses** (worlds passed; worst ratio per regime: visible / compact_works / reversed / slip_dip2):

| Analysis | Wrong object | Passed | Worst ratios |
|---|---|---|---|
| before / after on installed stores | no counterfactual | 0/120 | 16.9 / 16.9 / 14.4 / 15.2 |
| house readout: static TWFE on log basket, planned dates, all weeks | outcome (ratio with a treated denominator) + forbidden comparisons | 0/120 | 9.2 / 5.2 / 5.1 / 5.4 |
| static TWFE on log sales | forbidden comparisons under a ramp | 0/120 | 10.4 / 6.5 / 5.6 / 6.7 |
| TWFE event study, reference e = −1 | reference week inside the install closure | 0/120 | 11.3 / 7.8 / 4.1 / 7.1 |
| DiD, base week g−1, pooled controls | base inside the closure + unconditional trends | 0/120 | 47.9 / 47.9 / 46.7 / 22.5 |
| imputation with store + week FE only | control group: format trends | 0/120 | 4.9 / 4.9 / 5.1 / 4.4 |
| DiD with pooled not-yet-installed controls, clean base | control group: format trends | 0/120 | 2.3 / 2.3 / 2.1 / 2.3 |
| correct design, **log basket** outcome | estimand: basket ≠ net sales | 0/120 | 3.1 / 3.1 / 3.1 / 2.8 |
| correct design, **log transactions as a covariate** | conditioning on a mediator | 0/120 | 3.1 / 3.1 / 3.1 / 2.8 |
| correct design, closure weeks treated as comparable | eligibility / time zero | 0/120 | 2.1 / 2.1 / 2.1 / 2.2 |
| correct design, gate = **pooled installed-store effect** | population | 40/120 (never in visible) | 4.6 / 0.8 / 4.6 / 1.3 |
| correct design, gate transported **by format** | population / treatment version | 60/120 (never in visible) | 3.0 / 0.6 / 3.0 / 0.9 |
| correct design, gate by **linear sqft** model | treatment version | 56/120 (never in visible) | 3.8 / 0.6 / 3.8 / 1.0 |
| kit × week FE instead of format × week | conditioning coarser than the sequencing variable | 2/120 | 2.5 / 2.5 / 2.5 / 2.3 |
| run-rate replaced by event weeks 0–25 | horizon (ramp) | 20/120 (never in compact_works or slip_dip2) | 1.5 / 2.1 / 1.5 / 1.8 |
| planned instead of actual go-live | time zero | 120/120 on values | 0.7 |

**Planned timing** is numerically small (slips are 1–4 weeks and the run-rate window is 14 weeks). It is **not** a
value trap. It is graded only by the exact `go_live_week` / `event_week` columns of the analysis panel, which are
deterministic semantic objects.

**Population errors** (pooled or format transport) are correct in `compact_works` by construction (kit effects
similar), so they are rejected by the visible and reversed extracts. That is the intended property: the population
matters exactly when the treatment versions differ.

**Margins.** |θ_R − 2.5%| / SD ≥ 8.1 (visible, reversed), ≥ 9.3 (compact_works), ≥ 4.7 (slip_dip2) in every
validation world.

## 5. Identifiability checks

1. **Conditional parallel trends given format hold by construction.** Unconditional parallel trends fail in the
   direction set by the regime (visible: +; reversed: −).
2. **Positivity / overlap.** Every format has not-yet-installed and never-installed stores through the last run-rate
   week. Every kit version has ≥ 50 installed stores with run-rate windows.
3. **Transport.** Store run-rate effects depend on the store only through the kit version (lognormal idiosyncratic
   multiplier independent of format, size, wave and region). Kit is recorded in the plan, the install log and the
   layout survey.
4. **Accepted estimators agree** within 0.8 τ across five structurally different implementations. None uses the
   generator's parameters.

## 6. Decisions carried into the build

- **Tolerances:** τ = 3.5 × SE_ref per quantity and extract, where SE_ref is the RMSE of the least efficient accepted
  estimator under Monte-Carlo noise redraws with the design held fixed. It is computed at build time and frozen in
  `tests/`.
- **Seed screening:** each frozen extract must reproduce the round-4 properties:
  - accepted ≤ 1 τ;
  - every named wrong analysis fails that extract or another required extract;
  - gate margin ≥ 3 SD.
- **Regimes:** `visible` and three hidden regimes as §2. Seeds, chain size and wave calendars also vary.
- **Graded set A**, plus exact panel columns (`go_live_week`, `event_week`, `comparable`, `log_net_sales`), interval
  checks, and the decision.


## 7. Post-review rounds (after the independent adversarial and causal-validity reviews)

### Review findings that forced design changes

1. **Adversarial review, HIGH.**
   - A valid same-format DiD using a single comparable base week failed hidden_b on noise.
   - SE_ref had been set only by estimators averaging many pre-weeks.
   - Several wrong analyses were only 1.0–2.4 τ out.
2. **Causal-validity review, MEDIUM.**
   - Build-time τ was tighter than Phase-0 τ and was never re-validated on fresh noise.
   - Some wrong analyses (weeks 0–25 window, kit-only controls) were rejected narrowly and in few extracts.

### Round 5

**Design changes (DGP, not τ):**
- chain 760 → 900 stores;
- weekly noise sd_txn 0.022 → 0.014, sd_basket 0.016 → 0.010;
- Supercentre trend +4.5% → +6.0% per year, Market +1.5% → +1.0% (so kit-only conditioning is biased);
- the reversed regime gets a 14-week ramp.

**Panel changes:**
- accepted panel widened with `cs_base_last` (each store's latest comparable week in e ∈ [−8, −3] as base) and `cs_base_e43` (base e ∈ [−4, −3]);
- wrong panel widened with alternative implementations of thin wrong analyses: weeks 0–25 by store-trend imputation and by DiD, kit-conditioned DiD, closure weeks only in the window, pooled gate by DiD.

**Abort.** A first round-5 launch was aborted at 5% (before any result) to add the trend-gap change; that log is kept as
`results/r5_ABORTED_cal.log`.

**Result: FAIL.**
- `cs_base_last` passed 117/120 validation worlds (97.5%, criterion ≥ 99%).
- Every other accepted estimator passed 120/120.
- Every wrong analysis failed 30/30 in at least one regime.

**Diagnosis:**
- The three failures are **one** noise realisation (seed 9374) counted in three regimes. `visible`, `compact_works` and
  `reversed_trends` reuse the same seeds, so they share outcome noise.
- The failing quantity is wave 4 at 1.10 τ, with mean error ≈ 0 (no bias).
- For wave 4, τ = 3.5 × RMSE was estimated from 20 calibration worlds: calibration RMSE 0.0015 vs validation RMSE
  0.0022. This is calibration sampling error of the tolerance for the least efficient accepted design, not an estimator
  defect.

**Decision.**
- The tolerance rule is unchanged: 3.5 × RMSE of the least efficient accepted estimator per regime and quantity.
- The protocol's sample sizes change. Round 6 uses 60 calibration and 60 validation worlds per regime, with disjoint
  seed blocks per regime, so regimes are independent draws.
- No estimator, tolerance multiplier or graded set changes.

### Round 6 (final calibration)

**Protocol change (sample size only).** 60 calibration + 60 validation worlds per regime (was 20 + 30), with a
disjoint seed block per regime so regimes no longer share outcome noise. The tolerance rule, estimators, graded
quantities and regimes are unchanged.

**Accepted estimators: PASS.** All seven pass 240/240 validation worlds.

| Estimator | cal RMSE | val RMSE | worst ratio | p50 | p90 | p95 | p99 |
|---|---|---|---|---|---|---|---|
| imputation, store + format × week | 0.00084 | 0.00084 | 0.54 | 0.20 | 0.31 | 0.37 | 0.47 |
| imputation, store + format × kit × week | 0.00087 | 0.00086 | 0.55 | 0.20 | 0.33 | 0.37 | 0.46 |
| imputation, store trends + week | 0.00104 | 0.00103 | 0.60 | 0.25 | 0.37 | 0.41 | 0.50 |
| DiD, same-format not-yet-installed, base e −10..−3 | 0.00124 | 0.00123 | 0.66 | 0.29 | 0.46 | 0.51 | 0.57 |
| DiD, same-format never-installed | 0.00131 | 0.00128 | 0.67 | 0.30 | 0.48 | 0.51 | 0.59 |
| **DiD, single base week (latest comparable in e −8..−3)** | **0.00182** | **0.00189** | **0.89** | 0.44 | 0.70 | 0.79 | 0.87 |
| DiD, base e −4..−3 | 0.00162 | 0.00166 | 0.92 | 0.40 | 0.62 | 0.66 | 0.83 |

- Calibration and validation RMSE now agree for every estimator (round 5's wave-4 mismatch, 0.0015 vs 0.0022, is gone).
- τ is set by the single-base-week DiD in every regime and quantity. That estimator is a standard design (a
  Callaway–Sant'Anna-style base period moved out of the install closures), 1.5–2.3× noisier than the most efficient
  accepted estimator. It is not pathological, and the tolerance is therefore anchored on a legitimate estimator.
- No regime dominates: worst accepted ratios are 0.32–0.92 in every regime, and each regime has its own τ.

**Wrong analyses: 20 of 21 meet the criterion; one documented miss.**

| Analysis | visible | compact_works | reversed | slip_dip2 | min ratio | joint pass P | decision correct |
|---|---|---|---|---|---|---|---|
| before/after | 0/60 | 0/60 | 0/60 | 0/60 | 14.2 | 5e−9 | 50% |
| house TWFE on basket | 0/60 | 0/60 | 0/60 | 0/60 | 3.6 | 5e−9 | 50% |
| static TWFE on sales | 0/60 | 0/60 | 0/60 | 0/60 | 4.5 | 5e−9 | 75% |
| event study, ref −1 | 0/60 | 0/60 | 0/60 | 0/60 | 3.1 | 5e−9 | 75% |
| DiD base g−1, pooled | 0/60 | 0/60 | 0/60 | 0/60 | 18.4 | 5e−9 | 50% |
| unconditional imputation | 0/60 | 0/60 | 0/60 | 0/60 | 4.6 | 5e−9 | 100% |
| unconditional DiD | 0/60 | 0/60 | 0/60 | 0/60 | 1.9 | 5e−9 | 100% |
| basket outcome | 0/60 | 0/60 | 0/60 | 0/60 | 2.4 | 5e−9 | 80% |
| mediator control | 0/60 | 0/60 | 0/60 | 0/60 | 2.4 | 5e−9 | 80% |
| closure weeks comparable | 0/60 | 0/60 | 0/60 | 0/60 | 1.4 | 5e−9 | 100% |
| kit × week conditioning | 0/60 | 0/60 | 0/60 | 0/60 | 1.8 | 5e−9 | 100% |
| weeks 0–25 (imputation / trend / DiD) | 0/60 | 0/60 | 1–2/60 | 0/60 | 0.91 | 1–2e−8 | 99–100% |
| closures in window only | 0/60 | 1/60 | 0/60 | 0/60 | 0.93 | 1e−8 | 99.6% |
| gate = pooled installed (imputation / DiD) | 0/60 | 60/60 | 0/60 | 2–8/60 | 0.19 | 3–9e−6 | 50% |
| gate by format | 0/60 | 60/60 | 0/60 | 57/60 | 0.05 | 6e−5 | 97.5% |
| gate by linear sqft | 0/60 | 60/60 | 0/60 | 32/60 | 0.16 | 4e−5 | 75% |
| **kit-conditioned DiD** | **1/60** | **3/60** | **7/60** | **5/60** | **0.61** | **1.6e−5** | 100% |
| planned timing | 60/60 | 60/60 | 60/60 | 60/60 | 0.07 | 0.97 | 100% |

- **Population errors** (pooled, by format, by sqft) pass `compact_works` by construction: the two kit versions have
  similar effects there, so the population does not matter. They are rejected by `visible` and `reversed_trends`.
- **Planned timing** passes on values everywhere, as in round 4. It is graded only by the exact panel columns.
- **The miss: kit-conditioned DiD.** Its best-regime fail rate is 59/60 = 98.3%, below the pre-registered ≥ 99%.
  - No tolerance or DGP change was made in response. The criterion is recorded as **not met** for this one analysis.
  - Its joint probability of passing all four regimes is ≈ 1.6 × 10⁻⁵ (independent draws).
  - On the four **frozen** extracts, which is what the task actually grades, it fails all four deterministically at
    1.06–1.92 τ (`research/g05/fixture_audit.json`).
  - Recorded as an unresolved validity risk in `report/g05_prebaseline_validation.md`. Whether this blocks a freeze is
    a maintainer decision; the evidence is stated rather than adjudicated away.

**Round 5 → round 6 classification: (A) legitimate reduction of calibration uncertainty.** Justification from the
repository (the pilot was untracked until the first G05 commit, so file modification times are the record):
- `g05_sim.py` and `g05_estimators.py` last modified 2026-09-17 03:11, before round 5 started (03:20) and unchanged
  through round 6 (05:10): the DGP and the estimator panel are identical in both rounds;
- `run_gate.py` modified 04:33, between the rounds; the change adds `REGIME_BLOCK` (disjoint seeds per regime) and
  passes larger `n_seeds`. It does not touch the tolerance function;
- the tolerance rule (3.5 × RMSE of the least efficient accepted estimator) and the graded set are unchanged;
- τ was **not** raised to accommodate the round-5 failure: visible wave-4 τ moved 0.0052 → 0.0057 only because the
  larger calibration sample estimated that estimator's RMSE better, and other quantities moved in both directions
  (wave 1 0.0059 → 0.0064, wave 3 0.0064 → 0.0062).

**Calibration is now frozen.** It is not revisited in response to mutation-suite results.
