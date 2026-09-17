# G05 re-audit and redesign (before any implementation)

- **Status:** design audit. Nothing is built. No model has been run.
- **Sources re-read:**
  - `research/gen3_designs/G05_staggered_rollout_did.md` (old design, "G05 v1");
  - `research/gen3_candidate_pool.md` (concept);
  - `research/gen3_design_tournament.md` (R3 review, finding #5 ✔ and #6 (R));
  - `research/gen3_tournament_sims/reviewer_g05_sim.py` and `reviewer_g05_twfe.py`;
  - `research/gen3_implementation_shortlist.md` (S6 rationale);
  - the G10 and G24 baseline analyses.

## 1. Re-audit of G05 v1

### 1.1 What the tournament found (treated as binding)

| Finding | Status | Consequence for G05 v2 |
|---|---|---|
| Static TWFE stays **positive** (+0.011…+0.022) under the stated rollout; the −2.3% "roll back" symptom cannot be generated | reproduced ✔ | The symptom must be rebuilt from mechanisms that actually produce it. No sign-flip headline. |
| A `g−1` base inside the install closures inflates effects (+0.042); region × week FE alone leaves +0.015 on the confounded wave | reproduced ✔ | The install-disruption mechanism is real and kept. |
| Event-study reference week in the dip pushes coefficients *up* (~+0.045), not to −0.006 | reviewer (R) | Derive attractor numbers from the generator, never from prose. |
| Oracle / generator seasonality mismatch (region × season term absent from the oracle) | reviewer (R) | The generator's time structure and the valid estimators' untreated-outcome models must be reconciled in the Phase-0 gate. |
| Cheapest path ≈ 30–35 actions: contract + handbook → fiscal calendar + install log → R4 note names ValuMart → exposure → imputation | reviewer | See §1.2. |
| **Binding criticism: easy for an agent with causal-inference knowledge** | reviewer + shortlist | See §1.3. |

### 1.2 Answer keys and weak points in v1

1. **The estimand is handed over verbatim.** The output contract defines:
   - wave ATT over comparable store-weeks, event weeks 0–25, in log basket;
   - overall = the same over all adopting stores;
   - recommendation = sign.

   "What causal quantity does the business need?" is therefore never asked. This is the capability the G05 brief now
   puts first.
2. **The confounder is a coincidence with a name.** A competitor (ValuMart) closed in the region of wave 3 in the week
   wave 3 went live. It is real-world plausible, but it is a *single planted coincidence*: one grep finds it, one
   covariate removes it, and it does not generalise as a causal lesson. The tournament asked for it to be buried and
   un-named. That makes it harder to find, not more principled.
3. **Fiscal-calendar arithmetic** (Sunday weeks, 53-week year, ISO-week misplacement) is deterministic panel hygiene of
   the Task 06 kind. It is graded exactly, but it is not causal reasoning, and it inflates the task without testing
   the causal capability.
4. **The decision is sign-only** (`keep` iff overall ≥ 0), with truth far from 0 in every fixture. In v1, any
   estimator with roughly the right sign gets the decision right. G24 showed that decision-level grading hides
   estimand errors (12/12 correct launches with wrong values).
5. **The outcome is a ratio KPI** (basket = sales / transactions), but v1 treats it as unproblematic. In the real
   workflow, a self-checkout redesign changes *which trips* happen, so the denominator is itself affected by treatment.
   v1 misses the most realistic estimand problem in its own setting.

### 1.3 Does substantial reasoning remain after the method is identified?

**Test.** Assume a strong agent immediately says "staggered adoption, TWFE is biased, use not-yet-treated clean
comparisons or an imputation estimator". What remains in v1?

| Remaining step in v1 | Causal reasoning? | Survives a knowledgeable agent? |
|---|---|---|
| Fiscal-week join, 53-week year, ISO-vs-Sunday | no (calendar hygiene) | yes, but it is not the capability |
| Actual vs planned go-live | yes (time zero), small numeric effect | mostly graded by the exact panel |
| Install weeks non-comparable, not usable as base | yes (time zero / anticipation) | an imputation estimator using all pre-weeks nearly passes anyway (tournament: did2s residual ≈ 0.002) |
| ValuMart confounder | yes, but a single grep-able coincidence | found by one heterogeneity split or one grep |
| Estimand | **not asked** (given in contract) | — |

**Verdict: v1 fails the binding criticism.** After the method is recognised, one real causal step remains (the
install-week base), plus hygiene and a findable coincidence. **G05 is redesigned (v2) before any implementation.**

## 2. G05 v2: real workflow

### 2.1 Setting (kept from v1, because it remains the strongest)

A regional grocery chain (fictional "Meridian Foods") is rolling out **SCO 2.0** (a self-checkout redesign) across its
stores in waves. Retail capital programmes like this are routinely:
- staged by operational readiness;
- installed with short store closures;
- shipped in kit variants by store size;
- judged by a finance gate for the remaining capital.

### 2.2 Workflow questions

| # | Question | Answer in v2 |
|---|---|---|
| 1 | Who is the data scientist? | A decision scientist in **Finance Analytics** (FP&A). They own the capital-programme gate reviews. They are not the programme team, which owns the house readout. |
| 2 | What intervention happened? | SCO 2.0 installed in stores: redesigned self-checkout bank, integrated scales, and, in the **full kit** only, a "big basket" self-checkout lane. Stores with less than ~30k sq ft receive the **compact kit** (no big-basket lane; floor-space constraint). |
| 3 | Who made the decision? | The rollout was approved by the Capital Committee in stages. Wave sequencing was set by Store Operations: large formats first ("floor-space readiness and installer crews"). |
| 4 | What decision depends on the analysis? | The Capital Committee's **continuation gate** for the *remaining* installation waves (not yet installed): fund the remaining capital or stop the programme. Reverting installed stores is not on the table (sunk cost). |
| 5 | Causal estimand | §3. The run-rate effect of SCO 2.0 on weekly net sales **for the stores in the remaining waves**, if they receive their planned kit. |
| 6 | Treatment unit | Store (installation is store-level; one kit version per store). |
| 7 | Outcome unit | Store × week: log net merchandise sales of a comparable trading week. |
| 8 | When is treatment assigned? | Wave membership and planned go-live week come from the rollout plan (set before installs by Store Ops). |
| 9 | When does treatment actually begin? | At the **actual go-live** (install log). 15–30% of stores slip 1–4 weeks. The prewire/install work closes the store for 1–2 days in the week(s) *before* go-live. |
| 10 | Can treatment change over time? | Once live, it stays live (absorbing). Its effect is dynamic: a learning ramp over ~12 weeks, then a run-rate plateau. Kit version is fixed per store. |
| 11 | What creates the counterfactual problem? | Rollout timing is not random. Large formats went first, and large formats sit in growing suburban trade areas with different secular trends. Installed stores and remaining stores differ in format and kit, so the installed stores' effect is not the remaining stores' effect. Installation disrupts the weeks just before go-live. |

## 3. Estimand before estimator

### 3.1 Notation

- **Stores and times.** Stores s. Weeks t = 1..T. G_s = actual go-live week (∞ for stores not installed by the end of
  the panel). Event time e = t − G_s.
- **Potential outcomes.** Y_st(g) is log net sales of store s in week t if its go-live were week g. Y_st(∞) is log
  net sales without SCO 2.0.
- **Kit version and populations.**
  - k_s ∈ {full, compact}: the kit version assigned to s (fixed, recorded in the plan and the install log).
  - I = installed stores (G_s ≤ T − 25, so the run-rate window is observed).
  - R = stores in the remaining waves (not installed in the panel; planned kit k_s recorded).
- **Run-rate window.** E_rr = {e : 12 ≤ e ≤ 25} (finance: "weeks 13–26 after go-live, go-live week = week 1").
- **Comparable weeks.** C_st = 1 if store s traded full hours all 7 days of week t (KPI handbook definition).

### 3.2 Candidate estimands (deliberately distinct)

| Symbol | Quantity | Who would compute it |
|---|---|---|
| β_basket | ATT on log basket size (sales / transaction), installed stores, e ≥ 0 | programme team (house readout, TWFE) |
| θ_I(e) | ATT on log net sales at event time e over installed stores | event-study readouts |
| θ_I^rr | run-rate ATT on log net sales, store-weighted over installed stores | "the programme's effect so far" |
| θ_k^rr | run-rate ATT on log net sales among installed stores with kit k | heterogeneity by treatment version |
| **θ_R^rr** | **Σ_k π_k^R · θ_k^rr**, π_k^R = share of remaining stores planned to get kit k | **the gate quantity** |

Written out:

```
τ_st        = Y_st(G_s) − Y_st(∞)                                        (for installed s, t ≥ G_s)
θ_s^rr      = mean over { t : t − G_s ∈ E_rr, C_st = 1 } of τ_st          (store run-rate effect)
θ_k^rr      = mean over { s ∈ I : k_s = k } of θ_s^rr                     (store-weighted, kit version k)
θ_R^rr      = Σ_k π_k^R θ_k^rr,  π_k^R = |{s ∈ R : k_s = k}| / |R|
decision    = "continue" if θ_R^rr ≥ g (gate hurdle from the business case), else "stop"
```

**Identification of θ_R^rr from installed stores** requires the store run-rate effect to depend on the store only
through the kit version (plus mean-zero idiosyncratic variation independent of wave). The DGP is built so that this is
true, and the workspace documents why:
- the kit versions differ in the big-basket lane;
- within-kit wave order was set by installer crew logistics.

It is an assumption a skilled analyst must state. Its falsifiable implications are checkable: within-kit effects
similar across waves, formats and sizes. The generator also includes a **negative falsification** in a hidden regime
(§7), where within-kit effects are equal but kit shares differ.

**Grading below the decision** (§8):
- wave-level run-rate effects (test control validity, outcome, time zero and horizon);
- kit-level effects;
- the gate quantity with its interval;
- the decision.

## 4. Data-generating process / causal graph

```
format f_s ──► sqft ──► kit k_s (full if sqft ≥ 30k) ──────────────────────► effect size A_k
   │                                                                              │
   ├──► wave sequence (large formats first; within format: installer region) ──► G_s (planned + slip)
   │                                                                              │
   └──► format × week secular trend μ_f(t) + common seasonality δ_t ─────────────┐│
store FE α_s, AR(1) noise ────────────────────────────────────────────────────────┤│
install closures in e = −1 / −2 (1–2 closed days) ─► C_st = 0, sales dip ───────┤│
other closures (weather, refrigeration; ~3% of store-weeks) ─► C_st = 0, dip ───┤│
SCO effect on log basket b_k(e) and on log transactions c_k(e) (ramp) ◄───────────┘┘
log txns_st   = α^n_s + μ^n_f(t) + δ^n_t + c_k(e)·D_st + closure_n + ε^n
log basket_st = α^b_s + μ^b_f(t) + δ^b_t + b_k(e)·D_st + closure_b + ε^b
log sales_st  = log txns_st + log basket_st
```

**Variable roles:**

| Variable | Role |
|---|---|
| format, sqft, region, opened_on | pre-treatment covariates |
| kit version | treatment version (pre-determined by sqft) |
| wave, planned go-live | assignment |
| actual go-live | exposure start |
| install closures | treatment-induced pre-period disruption (not anticipation by customers) |
| customer transactions | **mediator** (post-treatment) |
| basket size | ratio of outcome and mediator |
| other closures | eligibility (non-comparable weeks), unrelated to treatment |
| format-specific trends | confounder of timing via wave sequencing |
| interference | assumed absent (brief: nearest sister store ≥ 6 miles; lost trips go to competitors/online) |

**Design targets (to be calibrated in Phase 0, not trusted):**

| Quantity | Full kit | Compact kit |
|---|---|---|
| Run-rate basket effect b | +7% | +2.5% |
| Run-rate transactions effect c | −2% | −2% |
| Run-rate net sales effect | ≈ +5% | ≈ +0.5% |

- **Installed-store pooled run-rate sales ATT** ≈ +3.5% (mostly full-kit stores).
- **Remaining-store gate quantity** ≈ +1% (mostly compact).
- **Gate hurdle** g = 2.0%.
- **Programme team's TWFE log-basket readout** ≈ +6–8% ("baskets up 8%").

## 5. Identifying assumptions

1. **Conditional parallel trends:** E[Y_st(∞) − Y_s,t'(∞) | format, G_s] = E[Y_st(∞) − Y_s,t'(∞) | format] on
   comparable weeks. Untreated trends may differ by format; within format they do not depend on the adoption week.
2. **No anticipation in comparable weeks.** The only pre-go-live effect is the installation closure, which makes those
   weeks non-comparable. Customers cannot see the redesign before go-live.
3. **Absorbing treatment and consistency within kit version.** A store's treatment is its kit version from go-live on.
4. **No interference between stores** (documented simplification).
5. **Effect homogeneity across waves within kit version** (for transport to R), up to idiosyncratic noise independent
   of wave.
6. **Overlap:** every format and kit is represented among installed stores and has not-yet-installed comparison stores
   in the same format during installed stores' run-rate windows.

## 6. Threats and natural wrong analyses (each must be simulated in Phase 0)

| # | Analysis a competent analyst might run | Wrong object | Expected direction |
|---|---|---|---|
| W1 | before/after on installed stores | no counterfactual trend | + (full-format growth) |
| W2 | programme team's static TWFE on log basket (house readout) | outcome = mediator ratio; forbidden comparisons | +6–8% "baskets up" |
| W3 | static TWFE on log sales | forbidden comparisons with a ramp | biased |
| W4 | TWFE event study, reference e = −1 | reference week inside the install closure | strongly + |
| W5 | CS-style ATT(g,t), not-yet-treated, base g−1, all formats pooled | install-week base + unconditional trends | strongly + |
| W6 | CS/imputation with clean base, **unconditional** (store + week FE) | control group: format trends | + for early waves |
| W7 | correct design, outcome **log basket** | estimand: basket ≠ sales | gate ≈ +4–6%: "continue" |
| W8 | correct design, log sales, gate = **pooled installed-store ATT** | population: installed ≠ remaining | ≈ +3.5%: "continue" |
| W9 | correct design, horizon e = 0–25 average instead of run-rate | window (ramp) | − |
| W10 | planned go-live instead of actual | time zero | small −, exact panel fails |
| W11 | log sales with **log transactions as a control** ("traffic-adjusted") | conditioning on a mediator | ≈ basket effect |
| W12 | install weeks kept as comparable untreated observations (imputation fit) | eligibility / time zero | small + (Phase 0 decides whether it separates) |
| W13 | heterogeneity by linear sqft instead of kit version | treatment version | Phase 0 decides (accepted if within tolerance) |
| W14 | never-yet-installed stores only as controls, format-conditional | — | **valid** (expected accepted) |
| W15 | kit × week FE instead of format × week FE | conditioning set coarser than the assignment variable | Phase 0 decides |

**Attractors (why the wrong answers are believable):**
- The programme team's readout says baskets +8%.
- Finance's own quick DiD on installed stores says net sales +3–4%, clearing the 2% gate.
- The COO expects "continue".
- W7 and W8 are **correct causal methodology applied to the wrong object**, with CIs excluding zero. They agree with
  both external numbers, and the true gate quantity (~+1%) says stop.

## 7. Falsification and validation opportunities (available in the workspace, none required)

- **Pre-trend event study on comparable weeks.** Unconditional controls show diverging pre-trends for early
  (large-format) waves; format-conditional controls are flat.
- **Placebo go-live dates** (shift G by −20 weeks on pre-periods).
- **Negative-control outcome.** Fuel-station / pharmacy sales (a separate department column) are unaffected by
  checkout. A spurious "effect" there signals confounding.
- **Mediator decomposition.** log sales = log txns + log basket. The transactions effect is visible and negative.
- **Within-kit effect stability across waves and formats** tests the transport assumption for θ_R.
- **Install-week dip** visible at e = −1 / −2; the KPI handbook's comparable-week definition explains it.
- **`sco_share`** (share of transactions through self-checkout) jumps at the actual go-live week and confirms timing.

## 8. Verifier sketch (below the decision)

| Output | Check |
|---|---|
| `analysis_panel.csv` (store × week) | `go_live_week` (actual), `event_week`, `comparable`, `log_net_sales` exact |
| `readout.json.effect_by_wave` | run-rate ATT on log net sales per installed wave, within τ |
| `readout.json.effect_by_kit` | run-rate ATT per kit version, within τ (if required by the contract; see §10) |
| `readout.json.gate_effect` + CI | θ_R^rr within τ; CI width band and widened coverage |
| `readout.json.decision` | exact |
| Build-time margin | \|θ_R − g\| ≥ 3 SE_ref in every extract; wave and gate truths far from their natural wrong analyses |

## 9. Hidden regimes (candidates; Phase 0 keeps only those that preserve separation)

| Regime | Changes | Catches |
|---|---|---|
| **compact kit works** | compact-kit effect large (remaining ≈ +3%) → "continue" | hard-coded stop; pooled-population copies |
| **reversed trends** | large formats declining | unconditional controls biased the other way; hard-coded sign |
| **heavy slip, dip at e = −2** | 30% slips; closures mostly two weeks before go-live | planned timing; "drop e = −1 only" |
| **remaining mix** | remaining programme contains more full-kit stores | hard-coded kit shares |

## 10. Pre-audit: cheap solves and answer keys (to be re-run on the built workspace)

**Cheap-solve paths:**

| Cheap path | Result |
|---|---|
| grep "treatment" / "go_live" | finds the install log, not the estimand or the controls |
| "DiD" → standard CS / imputation, pooled | fails W6 (trends), W7/W8 (object) |
| copy the programme team's notebook | TWFE on basket, fails everything |
| one event-study routine | no network packages; a reference week inside the dip fails |
| read the business case | gives the gate *in business language*: "run-rate uplift in weekly net sales for the remaining installation waves" |
| match an executive number | +8% (basket) and +3.5% (pooled) are both wrong |
| change one filter | no single filter fixes controls, outcome and population |

The business case does not say how to transport, which controls or which weeks. It does not mention kit-effect
heterogeneity.

**Distribution of evidence:**

| Evidence | Location |
|---|---|
| Metric (net sales), population ("remaining waves"), hurdle | business case |
| Run-rate definition | finance glossary |
| Kit versions and big-basket lane | programme brief |
| Planned kit per remaining store | rollout plan table |
| Sequencing rationale | Store Ops wave plan note |
| Comparable weeks | KPI handbook |
| Actual timing | install log |

No document states the estimand as a whole, the estimator, the conditioning set or the transport step.

**Contract risk.** An `effect_by_kit` field would point at heterogeneity. Preferred: require `effect_by_wave` and
`gate_effect` only, and let kit heterogeneity be discovered. This is decided after Phase 0 measures whether the wave
effects alone discriminate W8.

## 11. Complications removed as artificial

- ValuMart competitor coincidence (single planted coincidence; replaced by structural format-trend confounding through
  the sequencing rule).
- Fiscal 53-week year and Sunday-vs-ISO misplacement (calendar hygiene, not causal). Weeks are ISO weeks
  throughout, labelled consistently.
- Sign-only recommendation (replaced by a hurdle on the gate quantity, with margin requirements).

## 12. Phase-0 gate protocol (pre-registered; see `G05_phase0_gate.md` for results)

- **Worlds.** Regimes × seeds: calibration 6 per regime, validation 8 per regime, disjoint seeds.
- **Truth.** Exact τ from the generator (potential outcomes), averaged per §3. No estimator involved.
- **Tolerance.** τ_q = 3.5 × SE of the least efficient accepted estimator for quantity q (mean over calibration seeds,
  per regime).
- **Acceptance.**
  - Every accepted estimator passes ≥ 99% of validation worlds on every graded quantity and the decision.
  - Every named wrong analysis fails ≥ 99% of the worlds of at least one regime that is part of the graded set.
  - Every world satisfies |θ_R − g| ≥ 3 SE_ref.
  - No arbitrary modelling choice inside the accepted family decides pass/fail.
- **On failure:** change the DGP or design, not only the tolerance. Record every round.
