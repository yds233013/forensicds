# G05 SCO 2.0 tranche-2 gate: pre-baseline validation

**Task:** `candidates/g05-sco-rollout-gate/`

**Status:** PENDING_STATUS

**No model has been run on this task.** No Gemini, no Claude, no other model; $0 of model spend.

**Related documents:**
- Re-audit of the old design and the redesign decision: `research/g05/G05_research_audit.md`
- Phase-0 simulation gate, rounds 1–6 including the failed round 5: `research/g05/G05_phase0_gate.md`
- Fixture audit (frozen tolerances and per-extract separation): `research/g05/fixture_audit.json`
- Mutation suite report: `research/g05/shortcuts_report.json`
- Overnight execution log: `research/overnight_2026-09-17.md`

## 1. Summary

| Check | Result |
|---|---|
| Phase-0 gate, round 6 (final calibration): accepted estimators | 7/7 at 240/240 validation worlds, worst 0.92 τ |
| Phase-0 gate, round 6: wrong analyses | 20/21 fail ≥ 99% of one regime; **kit-conditioned DiD at 98.3%** (§9.1) |
| Fixture audit on the four frozen extracts | accepted ≤ 0.69 τ; every wrong analysis fails ≥ 1 extract; gate margins 8.7–14.3 SE |
| Mutation suite, 38 cases in the task image with the real `test.sh` | 38/38 as expected |
| Harbor oracle / Nop | HARBOR_ORACLE_NOP |
| `harbor check` | HARBOR_CHECK |
| Clean clone: rebuild, workspace, Oracle, Nop | CLEAN_CLONE |
| Answer-key audit | no estimator recipe, population rule, conditioning set, hidden regime, verifier or truth in any agent-visible file |
| Cheap-solve audit | every shortcut fails (§11) |
| Decision-shortcut audit | forced "stop" fails on effects at 2.1–11.7 τ on all four extracts |
| Falsification audit | placebo pre-effects and a pharmacy negative control separate the correct and incorrect designs |
| Frozen checksums (01–06, 02-explicit-invariant, G08, G10, G24) | unchanged |
| Secret scan | clean |

## 2. The task

**Real workflow.** A grocery chain (Meridian Foods, 900 stores) installs a self-checkout redesign (SCO 2.0) in waves.
Finance must decide whether to release tranche 2 of the capital, covering waves 5–6, which are not yet installed.

**Business decision.** The Capital Committee's continuation gate: release tranche 2 if the expected run-rate uplift in
weekly net sales for the waves 5–6 stores, with the kit each is planned to receive, is at least 2.5%.

**Visible incident.** Two credible analyses say continue:
- the Programme team's readout (static TWFE, store and week fixed effects, on log basket size): **+8.0% in wave 1,
  +5.5% overall**;
- FP&A's quick check (the same readout rerun on log net sales): **+6.7%**.

The correct gate figure is **+1.07%**, which means stop.

**Causal estimand.**

```
τ_st        = Y_st(G_s) − Y_st(∞)                                       effect on log net sales
θ_s         = mean over { t : t − G_s ∈ [12, 25], comparable }  of τ_st  store run-rate effect
θ_k         = mean over installed stores with kit k of θ_s              kit-version effect, store-weighted
θ_R         = Σ_k π_k^R · θ_k,  π_k^R = kit shares of waves 5–6         the gate quantity
decision    = continue iff θ_R ≥ 0.025
```

Also graded: θ_w, the same run-rate average for each installed wave.

**Treatment unit:** the store. **Outcome unit:** store × ISO week, log net merchandise sales of a comparable trading
week. **Assignment:** wave and planned go-live from the rollout plan; Store Operations sequenced waves by format, and
within a format put stores with a usable rear bagging bay first. **Time zero:** the actual go-live week from the
install log, not the plan (109 of 536 live stores slipped). **Exposure:** absorbing from go-live, with a learning ramp
and then a run-rate plateau; the kit version (full with a big-basket lane, or compact) is the treatment version.

**Data-generating process.** Untreated log sales = store effect + format trend + a season common to all stores +
stationary AR(1) noise. Installation closes a store for one or two trading days in the week or two before go-live,
which makes those weeks non-comparable. The redesign raises basket size and lowers transactions; net sales is their
sum in logs. Full-kit stores gain about +4.3% in net sales at run-rate, compact-kit stores about −0.3%.

**Identification assumptions.**
1. Conditional parallel trends given format (format is the sequencing variable).
2. No anticipation outside the install-closure weeks; the redesign is invisible to customers before go-live.
3. Absorbing treatment; consistency within kit version.
4. No interference between stores (documented in the programme brief).
5. Transport: a store's run-rate effect depends on the store only through its kit version, plus idiosyncratic
   variation independent of wave. Testable in the data (within-kit stability by format and wave).
6. Overlap: every format has not-yet-installed and never-installed stores through every run-rate week; each kit
   version has ≥ 100 installed stores.

**Main identification threats, and how the task handles them:**

| Threat | Handling |
|---|---|
| Waves sequenced by format, and formats trend differently | conditional parallel trends; unconditional controls fail |
| Install closures depress the weeks before go-live | those weeks are not comparable; a g−1 base or an event-study reference at −1 sits in the dip |
| Planned dates differ from actual | actual go-live from the install log; graded exactly in the panel |
| Basket size is a ratio with a treated denominator | the gate is on net sales; conditioning on transactions blocks the channel |
| Installed stores are not the remaining stores | transport by kit version; pooled or format-transported effects fail |

## 3. Why each attractor is wrong

### 3.1 Programme readout: +8.0% wave 1, +5.5% overall, continue

1. **What it estimates.** A variance-weighted average of two-period comparisons on **log basket size**, with planned
   treatment dates and every week included, where already-installed stores serve as controls for later waves.
2. **Why that is not the estimand.** Three separate reasons: the outcome is the ratio sales/transactions, whose
   denominator the treatment changes; static TWFE under staggered adoption with a ramp uses treated units as controls;
   and planned dates mis-time 109 stores.
3. **Why it looks credible.** Basket size is the Programme team's documented KPI, the fixed-effects panel regression is
   the house method used for the earlier ESL programme, and every wave is individually significant with a monotone
   pattern that reads as a learning curve.
4. **Visible contradiction.** The mediator decomposition: transactions fall (−1.7% full kit, −1.2% compact) while
   basket size rises (+6.0%, +1.0%), so basket size overstates the sales effect. The business case gate is on net
   sales, not basket size.
5. **Falsification.** Recompute on net sales; run the same regression with event-time dummies and see the pre-period
   dip at −1; compare against a clean-comparison estimator.
6. **Could an expert defend it?** Not as the gate figure. It answers "what happened to basket size in installed
   stores", which the business case does not ask.
7. **Hidden regimes.** It fails all four extracts at 4.8–11.9 τ.

### 3.2 FP&A quick check: +6.7% net sales, continue

1. **What it estimates.** The same static TWFE, on the right outcome.
2. **Why that is not the estimand.** Forbidden comparisons under staggered adoption and a ramp; unconditional trends;
   planned dates; and it answers for installed stores, not for waves 5–6.
3. **Why it looks credible.** It is on the gate metric, it is large, and it agrees in direction with the Programme
   team, which is exactly the "two analyses agree" pattern.
4. **Visible contradiction.** Placebo pre-period effects are non-zero without format-conditional controls (mean
   |effect| 0.0106 across event weeks −16..−4); the pharmacy negative control, which SCO cannot affect, shows +0.0115.
5. **Falsification.** Event-study pre-trends; the negative control; per-kit effects, which reveal that the compact kit
   does nothing.
6. **Could an expert defend it?** No: TWFE's staggered-adoption bias is well known, and the population is wrong.
7. **Hidden regimes.** Fails all four at 4.5–14.3 τ; its decision is right in only 75% of pilot worlds.

### 3.3 The correct gate figure, +1.07%

Not "because the verifier says so": it follows from the estimand. The gate is defined over the waves 5–6 estate as
planned. Those stores are 71% compact-kit, and the compact kit has no big-basket lane, so its run-rate net-sales
effect is about −0.3% against +4.3% for the full kit. Transporting the kit-version effects onto the waves 5–6 kit mix
gives +1.07%, below the 2.5% hurdle. The installed estate's pooled effect (+3.1%) is higher only because installed
stores are disproportionately full-kit, which is a consequence of the documented sequencing rule.

## 4. Round-6 calibration (final)

See `research/g05/G05_phase0_gate.md` §7 for the full tables, including the failed round 5.

- 60 calibration + 60 validation worlds per regime, disjoint seed blocks per regime.
- τ = 3.5 × RMSE of the least efficient accepted estimator, per regime and quantity. Unchanged rule since round 1.
- Accepted estimators: 7/7 at 240/240. Worst ratio 0.92; p99 ≤ 0.87. Calibration and validation RMSE agree.
- τ is set by the single-base-week DiD in every regime: a legitimate design, 1.5–2.3× noisier than the most efficient
  accepted estimator.

**Round 5 → round 6 is (A), a legitimate reduction of calibration uncertainty.** The DGP and estimator files were last
modified before round 5 started and are unchanged; only the gate runner's sample sizes and seed separation changed;
the tolerance rule and graded set are identical; and τ moved in both directions across quantities.

## 5. Mutation suite (38 cases, task image, real `test.sh`)

All 38 behaved as expected. Accepted implementations score 1; every wrong analysis, cheat and patch scores 0; the three
overfits fail only hidden extracts.

**Accepted (reward 1):** oracle; independent pandas DiD; never-installed controls; store-trend imputation;
format × kit × week imputation; single-base-week DiD.

**Correct method, wrong causal object (the G24 failure class):**

| Mutation | Wrong object | Caught first by | Decision still right? |
|---|---|---|---|
| `wrong_panel_planned_dates` | treatment timestamp (assignment vs exposure) | analysis panel (17,004 rows) | yes |
| `wrong_panel_event_week_from_1` | event-time origin | analysis panel (83,616 rows) | yes |
| `wrong_panel_comparable_txns` | eligibility of outcome weeks | analysis panel (4,642 rows) | yes |
| `wrong_gate_pooled_installed` | population (installed ≠ remaining) | effects (gate) | no, flips in visible |
| `wrong_gate_by_format` | transport variable, ignoring treatment version | effects (gate) | often yes |
| `wrong_gate_by_sqft` | transport by store size | effects (gate) | sometimes |
| `wrong_outcome_basket` | outcome (ratio with treated denominator) | effects (all waves) | sometimes |
| `wrong_mediator_control` | conditioning on a post-treatment mediator | effects | sometimes |
| `wrong_unconditional_imputation` / `wrong_unconditional_did` | control group (format trends) | effects | yes |
| `wrong_kit_week_conditioning` / `wrong_kit_conditioning_did` | conditioning coarser than the assignment variable | effects | yes |
| `wrong_closure_weeks_comparable` / `wrong_closure_weeks_in_window` | contaminated pre-period / outcome weeks | effects | yes |
| `wrong_window_0_25` (3 implementations) | outcome window (ramp vs run-rate) | effects | yes |
| `wrong_did_base_g_minus_1` | base period inside the install closure | effects | no |
| `wrong_twfe_event_study_ref_minus1` | event-study reference in the dip | effects | no |

Four of these keep a correct business decision while estimating the wrong quantity, and three more do so in most
worlds. This is the structure G24 showed is necessary: the decision alone cannot carry the grade.

**Cheats and tampering (reward 0):** output-only patch; warehouse edit (caught by the content digest); importing the
verifier's generator; stdlib exit hook, shadow pytest and root pytest config (all refused before grading); a
site-packages `.pth`; a pip config.

**Overfits (visible pass, hidden fail):** hard-coded decision (fails hidden_a and hidden_c); hard-coded compact-kit
effect (fails hidden_a and hidden_c); hard-coded format trends (fails hidden_b).

## 6. Alternative valid implementations

| Implementation | Assumptions | Distinction | Worst ratio (frozen extracts) |
|---|---|---|---|
| oracle: imputation, store + format × week, bootstrap by store within format | conditional PT given format | reference | 0.39 |
| independent pandas DiD: same-format not-yet-installed controls, base = comparable weeks −10..−3 | same | written independently, long-format pandas, different CI construction | 0.69 |
| never-installed controls only | same, narrower control set | control pool | 0.53 |
| store-specific linear trends + week effects | linear untreated trends | different untreated-outcome model | 0.51 |
| format × kit × week effects | finer conditioning | conditioning set | 0.38 |
| single comparable base week (e −8..−3) | same | base period | 0.60 |
| base weeks −4..−3 | same | base period | 0.67 |

All seven pass every frozen extract and all four in-container runs. The accepted family therefore spans imputation and
2×2 designs, three conditioning sets, two control pools and four base-period choices.

## 7. Verifier

Graded below the business decision:

1. `analysis_panel.csv`, exactly: every store-week, its wave, the actual go-live week, event week, comparability and
   log net sales.
2. Each installed wave's run-rate uplift, within 3.5 × SE_ref.
3. The gate figure, within 3.5 × SE_ref.
4. Intervals: contain their estimate, width between 0.10× and 3× the reference, and cover the truth when doubled.
5. The decision.
6. Determinism (byte-identical rerun) and a 20-minute runtime limit.
7. The same checks on three hidden warehouses.

SE_ref is frozen in `tests/scenarios.py`: the RMSE of the least efficient accepted estimator over 30 Monte-Carlo noise
redraws per extract with the design held fixed, and validated on 30 further independent redraws.

`test.sh` is the hardened G24 verifier: pinned base image with a runtime manifest, refusal on pytest configuration
files, a venv built with `-I -S`, hash-pinned wheels installed with `--no-index --require-hashes`, pytest under
`env -i` with `--noconftest -c /dev/null`, the pipeline sandboxed as uid 65534, `/tests` mode 700 and verified
unreadable, and a stray-process sweep that spares container init.

## 8. Hidden regimes

| Extract | What changes causally | Truth gate | Decision |
|---|---|---|---|
| visible | baseline | +1.07% | stop |
| hidden_a | the compact kit also lifts sales (kit effects nearly equal) | +3.88% | continue |
| hidden_b | untreated format trends reversed, slower ramp, some Supercentres without a bay | +0.96% | stop |
| hidden_c | 32% of stores slip, installs mostly two weeks before go-live | +3.45% | continue |

Two extracts say continue and two say stop, so a constant decision cannot pass. Each regime changes only documented
mechanisms: effect sizes by kit, untreated trends, the ramp, slip rates, install timing, chain size and calendar. No
hidden rule is introduced. In hidden_a the population errors are correct by construction, because the kit versions
behave alike there; they are rejected by visible and hidden_b.

## 9. Unresolved validity risks

### 9.1 Kit-conditioned DiD misses the pre-registered separation bar

- The pre-registered rule is that every wrong analysis fails ≥ 99% of the worlds of at least one regime.
- Kit-conditioned DiD (same-kit rather than same-format controls) reaches 59/60 = 98.3% in its best regime.
- No tolerance or DGP change was made in response.
- Its joint probability of passing all four regimes is ≈ 1.6 × 10⁻⁵, and on the four **frozen** extracts, which are
  what the task grades, it fails all four at 1.06–1.92 τ.
- **Judgement:** the benchmark instance is not at risk, but the criterion as written is not met. Whether this blocks a
  freeze is a maintainer decision, recorded here rather than adjudicated away.

### 9.2 Other risks

- **Window-of-analysis near-misses.** The weeks 0–25 error is rejected at 0.91–2.4 τ depending on implementation; it
  passes 1–2 of 60 worlds in the reversed-trend regime and fails 60/60 in visible.
- **Population errors pass hidden_a.** By construction. Discrimination rests on visible and hidden_b.
- **Interval checks are permissive.** The lower width bound is 0.10× the reference; several interval methods pass.
  They do not separate methods, by design.
- **Panel-only errors.** Planned timing and transactions-based comparability are numerically small and are caught only
  by the exact panel columns. That is intended, and it is what makes the decision-shortcut audit pass, but it means a
  correct estimator with a wrong panel fails on state rather than on numbers.
- **`serve.py`-style recipe risk does not apply here**, but the KPI handbook's comparable-week definition is close to
  operational. It is a KPI fact used for like-for-like reporting, not an estimator instruction.

## 10. Falsification opportunities (agent-visible)

| Diagnostic | Distinguishes |
|---|---|
| Placebo/pre-trend effects by event week | unconditional (mean \|effect\| 0.0106) vs format-conditional (0.0004) |
| Pharmacy sales negative control | unconditional +0.0115 vs format-conditional +0.0011 (truth 0) |
| Per-kit effect split | the population error: +4.3% full vs −0.3% compact |
| Mediator decomposition (sales = transactions + basket) | the basket-outcome error |
| SCO share jump at go-live (+0.19) | actual vs planned timing |
| Closure records around go-live | the install dip: 82% of e = −1 weeks are non-comparable |
| Within-kit stability across formats and waves | the transport assumption |

## 11. Cheap-solve audit

| Shortcut | Result |
|---|---|
| Copy the Programme readout | it is Nop: 0 |
| Copy the FP&A notebook | static TWFE on net sales: fails 4.5–14.3 τ |
| Standard staggered DiD without investigating the process | unconditional controls fail at 1.9–8.7 τ |
| One filter (drop closure weeks only) | still fails: outcome, population and conditioning remain wrong |
| grep for treatment terms | finds the install log: timing only, which the values do not even grade |
| Read one document | the business case gives the gate in business language, not the method |
| Hard-code "stop" | passes visible, fails hidden_a and hidden_c |
| Hard-code the visible values | same |
| Restore an earlier release | RELEASES 2.0/2.3 are the same TWFE family |
| Match a published number | +8.0%, +5.5% and +6.7% are all wrong |

## 12. Integrity

FROZEN_CHECKSUMS

## 13. Proposed baseline (NOT RUN)

```
harbor run -p candidates/g05-sco-rollout-gate -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs \
  --job-name g05-gemini3flash-baseline-1 --artifact /workspace --agent-setup-timeout-multiplier 3 -y
```
