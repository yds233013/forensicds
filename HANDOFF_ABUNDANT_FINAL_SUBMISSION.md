# HANDOFF — Abundant AI research take-home, final submission

Generated 2026-09-30. Written so another researcher can audit the whole submission without trusting any
conversational summary. Every number here is recomputable by the two scripts in §"Reproducibility audit".

---

## 1. Final verdict

**READY, with three disclosed defects, all found by our own audit, all remediated in forked versions, and
none of which changes a measured outcome.**

- Exactly ten final tasks, each with Oracle=1, Nop=0, and ≥3 valid Gemini trials.
- Aggregate pass@1 and task-level pass@3 on the final ten are in §"Metrics"; the assignment's <30% pass@3
  target is met with margin.
- The research result is a localised capability gap, not the difficulty. See §"Failure mode".
- Two prospective hypotheses are disconfirmed and reported as such.

---

## 2. The exact final ten

| # | task path | domain | mechanism |
|---|---|---|---|
| 1 | `candidates/02-renewal-risk-regression` | B2B SaaS revenue DS | point-in-time correctness / leakage |
| 2 | `candidates/g05-sco-rollout-gate` | Retail FP&A capital gate | identification under staggered adoption |
| 3 | `candidates/g10-censored-demand` | Retail demand planning | informative censoring endogenous to the programme |
| 4 | `candidates/g24-recommender-ope` | Personalisation analytics | off-policy evaluation under a logging policy |
| 5 | `candidates/g36-tou-capacity-gate` | Regulated utility planning | population definition under tariff migration |
| 6 | `candidates/p20-noshow-monitoring` | Healthcare model risk | policy feedback + feature vintage + drift decomposition |
| 7 | `candidates/p22-gauge-recalibration` | Manufacturing quality | measurement-system bias vs process change |
| 8 | `candidates/p31-fill-rate-dispute` | Retail supply chain + legal | contractual metric definition reconciliation |
| 9 | `candidates/g50-courier-boost-rollout` | Delivery marketplace | interference / unit of intervention |
| 10 | `candidates/g08-forecast-accuracy-vintages` | Energy trading analytics | data vintage / restated actuals |

**Shipped alongside, clearly marked, not counted in the ten:**

| path | what it is |
|---|---|
| `candidates/02-renewal-risk-regression__explicit-invariant` | ablation of #1 with the invariant stated outright; 3 trials, 0 passes |
| `candidates/p20-noshow-monitoring-v1.1` | remediation of #6's contract defect; newly exposed, 3 trials, 0 passes |
| `candidates/02-renewal-risk-regression-v1.1` | remediation of #1's image-layer defect; packaging-only, agent-visible surface byte-identical |

---

## 3. Research question, as answered

> Can an agent recover the decision-relevant scientific object from messy production evidence, execute
> the analysis, revise when contradicted, validate, quantify uncertainty, and decide defensibly when a
> plausible-but-wrong analysis is already available?

Answered capability by capability, because the capabilities dissociate sharply. On the twelve
criterion-instrumented trials:

| capability | criterion | pass rate |
|---|---|---|
| reconstruct the evidence | `evidence_reconstruction` | **11/12 (92%)** |
| frame the right object | `scientific_object` | **11/12 (92%)** |
| implement an estimator | `estimator_implementation` | **11/12 (92%)** |
| validate its own work | `independent_validation` | **11/12 (92%)** |
| argue identification | `identification` | 5/12 (42%) |
| **produce the right number** | **`quantitative_results`** | **2/12 (17%)** |
| decide | `decision` | 4/12 (33%) |

---

## 4. The failure mode actually found

**Agents recover the correct scientific mechanism and fail to convert it into a correct, generalising
quantitative object.**

Two sub-modes:

**(a) Procedure-level overfitting.** The agent writes code encoding the explanation it found rather than a
method that recovers whichever explanation holds. **`p22`: all three trials produced byte-identical,
correct visible-world output** — measurement_system 2.88 pp, material 1.06 pp, corrected rate 3.81%,
`no_supplier_action` — **and all three scored 0**, failing only the sibling world where tooling is the
driver, reporting `attribution_pp[tooling] = 0.0` where truth is 3.083. Their attribution code had no path
that could ever assign the change to tooling.

**(b) Quantitative reconstruction failure after a correct diagnosis.** `p20` reports
`feed_defect_share_pct` of 51.15 where truth is 0.0 — it invented a cause. `g10` gets the direction right
and the magnitudes wrong.

### Evidence supporting it

| evidence | value |
|---|---|
| failing trials that named the correct mechanism in their own reasoning | **25/30 (83%)** |
| trials that noticed an anomaly | 89% |
| trials that read the governing contract/policy document | 97% |
| trials that engaged with identification | 87% |
| trials that revised something | 82% |
| `quantitative_results` pass rate | **2/12 (17%)** |
| instrumented failures that are visible-world-OK / hidden-world-fail | 4/9 |
| `p20` v1.1 trial 2: criteria passed | **6 of 7**, failing only `quantitative_results` |
| ablation with the invariant stated outright | **0/3** |

Per-task mechanism identification among failing trials: `g05` 4/4, `g10` 3/3, `g36` 3/3, `p22` 3/3,
`02`-ablation 3/3, `02` 2/3, `g24` 2/3, `p31` 2/3, `g08` 2/2, `p20` 1/3.

### Evidence against it, and what we cannot rule out

1. **Mechanism identification is keyword-measured** over truncated reasoning (first/middle/last 1,200
   characters). It is a lower bound on identification but keyword presence is not proof of understanding.
2. **Criterion-level evidence rests on 4 of 10 tasks and 12 trials.** The other six emit binary rewards
   only and could not be instrumented without changing an exposed verifier.
3. **Sub-mode (a) is only testable where the verifier re-executes on sibling worlds** — `p22`, `p31`,
   `p20`, `g50`. Its absence elsewhere is unmeasured, not disproven.
4. **Scaffold stopping.** Many trials end with confident "ready to submit" reasoning; some of what we score
   as reconstruction failure could be premature termination by `gemini-cli`.
5. **One model, one scale.** Everything is `gemini-3-flash-preview`.

---

## 5. Disconfirmed hypotheses

| hypothesis | verdict | evidence |
|---|---|---|
| Agents fail because they don't run discriminating tests | **DISCONFIRMED** | 89% noticed anomalies, 87% engaged identification, 82% revised, 97% read the governing doc; `g10` ran the discriminating test in all 3 trials and still failed |
| Failure tracks effort | **DISCONFIRMED** | aggregate says failing trials do more work (58 vs 41 steps), but **within the 6 mixed-outcome tasks effort is pass-higher in 3/6 and fail-higher in 3/6** — the aggregate is a task-difficulty confound |
| The model doesn't understand the mechanism | **DISCONFIRMED as a general claim** | 83% of failing trials named it |
| Committing early and never revising | **DISCONFIRMED** | 82% revised; revision is *more* common in failing trials (86% vs 75%) |
| Making the invariant explicit raises the pass rate | **DISCONFIRMED** | `02` ablation 0/3 |

Per the assignment's Part XXIV, we explicitly decline to claim the first of these.

---

## 6. Defects we found in our own benchmark

| # | task | defect | severity | remediation | affects a measured outcome? |
|---|---|---|---|---|---|
| D1 | `p20` v1 | `readout_contract.md` never states the sign convention for `programme_effect_pp`; the reference computes control-minus-programme and no agent-visible artefact disambiguates it. 7 sign-flip failures across 2 of 3 trials. | **real, inflated difficulty** | `p20-noshow-monitoring-v1.1` states the convention; v1 preserved. Re-exposed: 0/3 with **zero** sign failures. | **No.** All three v1 trials also fail on independent genuine grounds. |
| D2 | `02` v1 | Single-stage Dockerfile: `COPY build/` then `rm -rf` only whiteouts the layer. `docker save` recovers `tmp/build/world.py` (34,538 B) and **`tmp/build/pit_reference.py` (10,301 B — the reference implementation)** from layer `44a48af94615`. | **real, image-distribution leak** | `02-renewal-risk-regression-v1.1` is two-stage: zero generator artefacts in any layer, and the agent-visible workspace hashes **identically** (`c26939cde7cc…`). | **No.** Verified the agent cannot reach it at runtime: `ls /tmp/build` → "No such file or directory". |
| D3 | `g50` | The memo's £0.19/£12.70 break-even was **never binding** on four worlds, so a mutation that rolls out on any reduction at all passed. | real, reduced discriminating power | A fifth world (`hidden_d`, effect −0.3049 pp) was calibrated while `g50` was still unexposed. `M_threshold_ignored` now scores **0**. | **No.** Fixed before any exposure. |
| D4 | `g50` v2.2 verifier | **Found by the first real agent run, not by 63 adversarial submissions.** `/etc/ld.so.cache` was hash-pinned to close a loader-redirection path; `apt-get` runs `ldconfig`, which regenerates it, and every agent scaffold installs its own tooling. The verifier **refused to grade** all three trials: `interpreter, library tree or sandbox tools differ from the pinned image`. Reproduced deterministically with `apt-get install curl`. | **real, invalidated 3 trials** | Replaced with a **resolution** check: every shared object the verifier's interpreter and sandbox tools actually load must resolve to a manifest-pinned path. Verified: hash PASS + resolution PASS both before and after `apt-get install curl`; oracle=1 with zero refusals. Re-frozen as v2.3 and re-exposed. | **No.** The three trials are **invalid**, not model failures — the verifier never examined the work. Preserved as `g50-gemini3flash-baseline-{1,2,3}__INVALID-verifier-refused-ldsocache`. |

**D4 is the most instructive of the four.** `oracle` and `nop` install nothing, so an adversarial campaign
built on them cannot exercise the paths a scaffolded agent takes. Every future task must be validated
against a scaffolded agent before exposure; this is now a mandatory gate in the scale plan
(`report/FINAL_REPORT.md` §34).

Additional documentation-only defects in `g50`'s frozen files (a docstring window, a baseline table built
from the latent rather than recorded flag, stale `task.toml` metadata, single-architecture runtime
manifests in sibling tasks) are enumerated in `HANDOFF_G50_V21_FINAL_PRETARGET.md` §31 and were reported
rather than silently repaired.

**Nine of ten tasks use multi-stage builds correctly; exactly one did not.** The audit covering all ten is
`report/analysis/leakage_audit.json`.

---

## 7. Real-distribution provenance, per task

Each final task carries `candidates/<task>/REAL_DISTRIBUTION_PROVENANCE.md` with ten fields: professional
role, industry, business decision, inherited artefacts, statistical problem, why it happens in real
organisations, public sources, what is synthetic, what is preserved, why it belongs.

### External sources, per task

| task | sources |
|---|---|
| `p22` | [MoreSteam MSA](https://www.moresteam.com/toolbox/measurement-system-analysis) · [Gauge R&R vs Calibration](https://microprecision.com/blog/gauge-rr-vs-calibration/) · [Five Common Mistakes with Gage R&R](https://www.spcforexcel.com/knowledge/measurement-systems-analysis-gage-rr/five-common-mistakes-gagerr/) · [1factory Gage R&R guide](https://www.1factory.com/quality-academy/guide-gage-r-and-r.html) |
| `p31` | [What Is OTIF?](https://blog.inymbus.com/what-is-otif-on-time-in-full-explained) · [OTIF chargebacks in retail](https://www.fulfyld.com/knowledge/what-does-otif-mean-retail/) · [DIFOT](https://en.wikipedia.org/wiki/DIFOT) · [OTIF/fill-rate formulas](https://abcsupplychain.com/otif-fill-rate-difot/) |
| `g10` | [FreshRetailNet-50K](https://arxiv.org/abs/2505.16319) · [Demand forecasting under lost sales stock policies](https://www.sciencedirect.com/science/article/abs/pii/S0169207023000961) · [Leakage-free censored demand pipeline](https://doi.org/10.3390/inventions11050089) |
| `g50` | [Interference, Bias and Variance in Two-Sided Marketplace Experimentation](https://dl.acm.org/doi/fullHtml/10.1145/3485447.3512063) · [arXiv version](https://arxiv.org/pdf/2104.12222) · [Experimental Design in Two-Sided Platforms](https://arxiv.org/pdf/2002.05670) · [Statsig marketplace experimentation](https://www.statsig.com/perspectives/marketplace-experimentation-platforms) |
| `02`, `p20` | [Databricks point-in-time feature joins](https://docs.databricks.com/aws/en/machine-learning/feature-store/time-series) · [Point-in-Time Correctness in Real-Time ML](https://towardsdatascience.com/point-in-time-correctness-in-real-time-machine-learning-32770f322fb1/) · [Feature stores and point-in-time correctness](https://dev.to/vaibhav7387/feature-stores-and-point-in-time-correctness-the-bug-that-silently-ruins-ml-models-51k4) · [ApXML point-in-time correctness](https://apxml.com/courses/feature-stores-for-ml/chapter-3-data-consistency-quality/point-in-time-correctness) |
| `g24` | [Widespread Flaws in Offline Evaluation of Recommender Systems](https://arxiv.org/pdf/2307.14951) · [Offline A/B Testing for Recommender Systems](https://arxiv.org/pdf/1801.07030) · [Causal Inference for Recommendation survey](https://arxiv.org/pdf/2303.11666) |
| `g08` | [Revision Risk in Real-Time Macroeconomic Forecasting](https://arxiv.org/pdf/2607.05882) · [Forecasting in the Fog: real-time vs revised data](https://arxiv.org/pdf/2608.09033) · [Backtesting a forecast model](https://orm-tech.com/blog/how-to-backtest-a-sales-forecast-model) · [Forecasting: theory and practice](https://arxiv.org/pdf/2012.03854) |
| `g05`, `g36` | staggered-adoption identification literature; standard retail wave-rollout and utility AMI/TOU coincident-peak planning practice (documented in the provenance files) |

### Professional workflow matrix

| task | role | industry | governing document | decision |
|---|---|---|---|---|
| `02` | revenue data scientist | B2B SaaS | model promotion criteria | release the Q3 retrain |
| `g05` | decision scientist, FP&A | retail | business case gate | release capital tranche 2 |
| `g10` | demand scientist | retail | buy-plan process | Q3 buy plan + programme extension |
| `g24` | personalisation analyst | consumer internet | offline gate process | which ranker serves the home row |
| `g36` | resource-planning analyst | regulated utility | regulator's 10% reserve | procure FY27 capacity |
| `p20` | model owner | healthcare provider | MRM-04 model risk standard | adopt v4.0 / remediate / retain |
| `p22` | process data scientist | precision manufacturing | supply quality agreement Schedule 3 §3.2 | raise a supplier nonconformance |
| `p31` | demand-science analyst | grocery retail | supply agreement account floor | position on a £1.8m claim |
| `g50` | decision scientist (Finance) | delivery marketplace | rollout decision memo (£0.19/£12.70) | national rollout |
| `g08` | analytics engineer | energy trading | model board accuracy pack | retire forecast v3 |

### Mechanism matrix

No two final tasks share a mechanism:

| mechanism | task |
|---|---|
| point-in-time correctness / leakage | `02` |
| staggered-adoption identification | `g05` |
| informative censoring | `g10` |
| off-policy evaluation | `g24` |
| population/exposure definition under migration | `g36` |
| policy feedback + vintage + drift decomposition | `p20` |
| measurement-system bias | `p22` |
| contractual metric definition | `p31` |
| interference / unit of intervention | `g50` |
| data vintage / restatement | `g08` |

---

## 8. Dependency graph summary

Depth (nodes from "read the inherited analysis" to "state the decision") and forced pivots:

| task | depth | pivots | systems needed |
|---|---|---|---|
| `p20` | 12 | 2 | appointments, scores, feature store, programme config, standard |
| `g50` | 12 | 2 | orders, zones, courier shifts, assignment, config, ledger, memo |
| `g10` | 11 | 2 | sales, inventory, stockouts, programme config |
| `g05` | 10 | 1–2 | store-weeks, wave schedule, business case |
| `p22` | 10 | 1–2 | CMM inspection, calibration log, heat lots, tooling events, agreement |
| `p31` | 10 | 2 | orders, shipments, deliveries, agreement, counterparty report |
| `02` | 9 | 1 | warehouse extract, feature store, monitoring, evaluation |
| `g24` | 9 | 1 | logs, score snapshots, gate report |
| `g08` | 9 | 1 | forecasts with origins, restated actuals, mart |
| `g36` | 8 | 1 | interval data, tariff assignments, customer master |

A worked graph for `p22` (twelve nodes, with the reason each edge follows from evidence) is in
`report/FINAL_REPORT.md` §11. The graphs are benchmark-author documentation and are **not** exposed to the
target model.

**Why long because of reasoning, not file volume.** The workspaces are small — 25 to 68 files. `g50`'s
entire agent-visible surface is 24 author-written files plus one SQLite warehouse. The length comes from
the number of *evidence-dependent* decisions: which population, which window, which unit, which of four
causes, which definition the contract fixes.

---

## 9. Recursive reasoning summary

The capability we most wanted to observe is the one the data show least of: a revision that propagates
through every downstream quantity.

- Revision happens (82% of trials) and does **not** predict success (86% of failing vs 75% of passing).
- Revisions are almost always local: a filter changed, an estimator swapped, a population narrowed.
- `p22` is the cleanest demonstration of the gap: the agents revised their *conclusion* correctly (from
  "supplier" to "gauge") and left in place an attribution procedure that structurally could not express a
  tooling-driven world. **The revision changed the answer without changing the procedure.**
- The strongest counter-example in the whole set is a single `g24` trial that caught the bias in its own
  first correction — "I was only counting clicks on items where the logging and candidate policies
  aligned… this created a biased result. I've corrected this now." It still failed.

---

## 10. Oracle / Nop results, all ten

| task | Oracle | Nop | job evidence |
|---|---|---|---|
| `02` | 1 | 0 | `task02-oracle-1/2`, `final-oracle-02-…`, `task02-nop-1/2`, `final-nop-02-…` |
| `g05` | 1 | 0 | `g05-oracle-prebaseline`, `final-oracle-g05-…`, `g05-nop-prebaseline`, `final-nop-g05-…` |
| `g10` | 1 | 0 | `g10-oracle-prebaseline`, `final-oracle-g10-…`, `g10-nop-prebaseline` |
| `g24` | 1 | 0 | `g24-oracle-prebaseline`, `final-oracle-g24-…`, `g24-nop-prebaseline` |
| `g36` | 1 | 0 | `g36-oracle-v1`, `g36-nop-v1` |
| `p20` | 1 | 0 | `p20-oracle-1/2`, `freeze-p20-oracle`, `validate-p20-oracle-14645`, `p20-nop-1/2` |
| `p22` | 1 | 0 | `p22-oracle-1/2`, `freeze-p22-oracle`, `validate-p22-oracle-14645`, `p22-nop-1/2` |
| `p31` | 1 | 0 | `p31-oracle-1`, `freeze-p31-oracle`, `validate-p31-oracle-14645`, `p31-nop-1` |
| `g50` | 1 | 0 | `g50-v21-oracle`, `g50-v21-nop` (4 worlds); `v22_oracle`, `v22_nop` (5 worlds) |
| `g08` | 1 | 0 | `g08-oracle-1`…`-5`, `g08-nop-1`…`-5` |
| `p20` v1.1 | 1 | 0 | `p20v11-oracle`, `p20v11-nop` |

**All ten: Oracle=1, Nop=0.** `g41` was excluded partly because its oracle history is unstable
(`g41-oracle-v2`, `-v3`, `-probe2` recorded 0 before repair) — recorded in the curation table.

---

## 11. Harbor checks

`harbor check` ran successfully on eight pool tasks during earlier development (`task02-check-1`,
`task03-check-final`, `task04-check-final`, `task05-check-final`, `task06-check-1`, `g05-check-prebaseline`,
`g08-check-1`…`-4`, `g10-check-prebaseline`, `g24-check-prebaseline`, `g34`, `g35`, `g36`, `tb3-check-*`),
each returning 1.

**`harbor check` could not be completed this run.** Two attempts, two environment failures:

| attempt | failure | classification |
|---|---|---|
| `jobs/2026-09-30__00-00-44` | `AgentSetupTimeoutError` after 360 s | environment — up to seven containers were running |
| `jobs/2026-09-30__01-25-19` | check scaffold agent returned `Not logged in · Please run /login` | environment — `harbor auth status` reports unauthenticated; no interactive login available in this session |

`harbor auth status`: **not authenticated.** This blocks `harbor check` and `harbor upload` only; it does
not block `harbor run`, which is how every trial in this submission was produced. Classified **LIMITATION,
not BLOCKING**: everything `harbor check` would test about the verifiers is covered directly by
Oracle/Nop, the mutation suites, and `g50`'s 63 adversarial submissions.

---

## 12. Exposure history, every Gemini run

Canonical command for every trial in this submission:

```bash
harbor run -p <task> -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name <name> -y --agent-setup-timeout-multiplier 3.0
```

### Valid trials, final ten

| task | job names | rewards |
|---|---|---|
| `02-renewal-risk-regression` | `task02-gemini3flash-diagnosis` (3 trials) | 0, 0, 0 |
| `g05-sco-rollout-gate` | `g05-gemini3flash-baseline-1` (3), `-2` (1) | 0, 0, 0, 0 |
| `g10-censored-demand` | `g10-gemini3flash-baseline-1` (3) | 0, 0, 0 |
| `g24-recommender-ope` | `g24-gemini3flash-baseline-1` (3) | 0, 0, 0 |
| `g36-tou-capacity-gate` | `g36-gemini3flash-baseline-1/2/3` | 0, 0, 0 |
| `p20-noshow-monitoring` | `p20-prospective-1/2/3` | 0, 0, 0 |
| `p22-gauge-recalibration` | `p22-prospective-1/2/3` | 0, 0, 0 |
| `p31-fill-rate-dispute` | `p31-prospective-1/2/3` | 0, 0, 0 |
| `g08-forecast-accuracy-vintages` | `g08-gemini3flash-baseline-2` (3 trials) | 0, 0, 1 |
| `g50-courier-boost-rollout` | `g50-gemini3flash-baseline-1/2/3` | 0, 0, 0 (v2.3; three earlier trials invalid — see §6 D4) |

### Additional versions and the ablation

| task | job names | rewards |
|---|---|---|
| `02-…__explicit-invariant` | `task02-gemini3flash-explicit-invariant` (3) | 0, 0, 0 |
| `p20-noshow-monitoring-v1.1` | `p20v11-gemini-1/2/3` | 0, 0, 0 |

### Invalid trials, replaced, never counted as model failures

| job directory | reason |
|---|---|
| `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | agent setup timed out (no multiplier) |
| `task01-gemini3flash-diagnosis__INVALID-api-key-rejected` | provider rejected the key |
| `task01-gemini3flash-diagnosis__INVALID-free-tier-quota` | free-tier quota exhausted |
| `task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped` | free-tier rate limit stopped the run |
| `task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup` | session interrupted |

All five are preserved on disk with the reason in the directory name and are excluded before any metric is
computed (`scripts/extract_trajectories.py` filters on the `__INVALID` marker).

### Post-exposure changes

| task | changed after exposure? | what |
|---|---|---|
| `g50` | **No.** The fifth world was added while it was still unexposed. | — |
| `p20` v1 | **No.** Preserved byte-for-byte. | The fix lives in `p20-noshow-monitoring-v1.1`, separately exposed. |
| `02` v1 | **No.** Preserved byte-for-byte. | The fix lives in `02-renewal-risk-regression-v1.1`, packaging-only; agent-visible workspace hashes identically (`c26939cde7cc…`). |
| all others | **No.** | — |

**No exposed task was tuned on the basis of a Gemini result.**

---

## 13. Freeze hashes

### `g50` v2.2, five independent groups (computed before exposure)

| group | aggregate | files | changed from v2.1? |
|---|---|---|---|
| A. target-visible | `ba92e8ccdcecdb58` | 19 | **no** — the fifth world changes nothing the agent sees |
| B. generator + scenarios | `49ad4801be5a7e99` | 3 | yes — `scenarios.py` gained `hidden_d` |
| C. verifier-only | `73c9c754ce7d2303` | 11 | no |
| D. oracle / reference | `23a5fa730ee9dacc` | 3 | no |
| E. complete task | `61254b9106583607` | 42 | yes |

Full file-level listing: `candidates/g50-courier-boost-rollout/FREEZE_MANIFEST_V22.txt`. The v2.1
pre-verifier scientific manifest (`PRE_VERIFIER_MANIFEST_V21.txt`, 28 files, body digest
`e4b4ea294a032dda`) still reproduces with **zero drift**, which is the evidence that no frozen scientific
file was touched during verifier construction.

### Protected artefacts, unchanged through this run

| artefact | sha256 (first 16) |
|---|---|
| `research/phase3/analysis_plan.md` | `c590cb5677ce14ba` |
| `submission_5task_fallback.zip` | `c8561aad8300df6c` |
| `scripts/final10_frozen_checksums.txt` | `d5565927bf69e598` |

---

## 14. Verifier limitations

1. **Six of ten tasks emit a binary reward only.** `02`, `g05`, `g10`, `g24`, `g36`, `g08` were exposed
   before criterion reporting existed; retrofitting it would change an exposed verifier. The criterion
   analysis therefore rests on 4 tasks / 12 trials. **This is the largest measurement weakness in the
   submission.**
2. **`g50` known blind spots**, measured and documented rather than removed: post-treatment weighting
   (`H_post` = 1), a boost-share dose-response extrapolation (`R2_boostshare` = 1), and using the
   never-enrolled markets as the comparison group (`M_holdout_as_control` = 1) all pass and are not
   distinguished from the reference. A one-week pre-period is rejected on two of four arbitrary week
   choices and accepted on the other two, which makes that dimension's treatment arbitrary.
3. **`independent_validation` checks that a validation was performed, not that it could have caught the
   error made.** It passes 11/12 while `quantitative_results` passes 2/12.
4. **Tolerances are author-set.** `g50`'s were fixed by a stated rule (1.6× the reference's own worst
   deviation) *before* the mutation suite ran and deliberately not re-tuned afterwards; the other tasks'
   tolerances were not held to that discipline as explicitly.
5. **The integrity check is circular at the root.** `g50`'s runtime manifest is verified by `sha256sum`
   using a `libc` the manifest also covers. Pinning the `ldd` closure raises the bar; no container-internal
   verifier removes the circularity.
6. **`/logs/verifier` is writable by the pipeline user on a mode-ignoring bind mount** (Docker Desktop on
   macOS). Not exploitable — verified by having a submission write `1` into `reward.txt` and be recorded as
   `0`, because the reward comes from the test exit status — and `test.sh` now hardens the directory and
   prints an explicit warning when the mount defeats the hardening.

## 15. Scientific limitations

1. Every DGP is an imposed model. `g50`'s mean-preserving queue, `g10`'s censoring process and `p22`'s
   gauge offset are literature-grounded but not measured from a real system.
2. Mechanism identification is keyword-measured (§4).
3. Three trials per task: a task at 0/3 could have a true pass rate up to roughly 0.3 at 95% confidence.
4. One model, one scale, one scaffold — model capability and scaffold limitation are not separable here.
5. `g50` provides **no** evidence about extrapolation through an interference region, because the realised
   dose-response in that world is near-linear (the priority mechanism is mean-preserving). We state this
   rather than engineer a world to punish the method.

## 16. Leakage audit

Scope: all ten final tasks. Result in `report/analysis/leakage_audit.json`.

| check | result |
|---|---|
| agent-visible workspace files matching generator/hidden-world/reference patterns | **0 hits across all ten** |
| generator located in `tests/` rather than `workspace/` | 10/10 |
| reference solution outside the agent-visible workspace | 10/10 |
| multi-stage build keeping the generator out of every image layer | 9/10 → **10/10 after the `02` v1.1 fix** |
| `g50` final image: all 13 layer blobs scanned by name and content for generator/scenario/seed patterns | 40 hits, **all coincidental matches inside the pinned Python/numpy/pandas/scipy/statsmodels distribution**; zero author-written leakage |
| `g50` image env vars, `Cmd`, `WorkingDir`, build history, git metadata | no leakage |
| `g50` shipped workspace | exactly 25 entries — the 24 manifest files plus the generated warehouse |

The one real finding (`02` v1, D2 in §6) was confirmed empirically and remediated.

## 17. Exploit audit

`g50` was the only task subjected to a full adversarial campaign before exposure:

| suite | n | result |
|---|---|---|
| estimator routes run as real submissions | 11 | 4 intended routes pass; 6 of 11 score 1 |
| mutations (4 worlds) | 23 | 21 correctly rejected |
| mutations (5 worlds, after `hidden_d`) | 12 | **11 behave as intended**; the exception is the documented `M_holdout_as_control` blind spot |
| malformed-output attacks through the grading function | 40 | **0 mismatches** |
| sandbox / isolation attacks through the container | 8 | **all 0** |

Attacks that specifically failed to defeat it: symlinked `readout.json`, symlinked `out/`, a background
thread rewriting output after the run, world-name branching, forging `reward.txt`/`criteria.json`, and
writing `/etc/ld.so.preload` (which triggers refuse-to-grade). The decisive anti-hardcoding evidence:
a mutation that runs the correct analysis once, reads its own output and bakes it in as a literal passes the
visible world and fails all six criteria on the unseen ones.

**No grader exploit was found in any task.**

---

## 18. Metrics

Computed by `scripts/compute_metrics.py` from `jobs/` only.

### Per task, final ten

| task | valid | pass | pass@1 | pass@3 | med steps | med tool calls | med completion tok |
|---|---|---|---|---|---|---|---|
| `02-renewal-risk-regression` | 3 | 0 | 0.0% | 0 | 84 | 51 | 22,676 |
| `g05-sco-rollout-gate` | 4 | 0 | 0.0% | 0 | 65 | 40 | 16,881 |
| `g10-censored-demand` | 3 | 0 | 0.0% | 0 | 62 | 44 | 21,913 |
| `g24-recommender-ope` | 3 | 0 | 0.0% | 0 | 60 | 42 | 19,901 |
| `g36-tou-capacity-gate` | 3 | 0 | 0.0% | 0 | 44 | 31 | 14,280 |
| `p20-noshow-monitoring` | 3 | 0 | 0.0% | 0 | 52 | 45 | 19,034 |
| `p22-gauge-recalibration` | 3 | 0 | 0.0% | 0 | 60 | 52 | 18,819 |
| `p31-fill-rate-dispute` | 3 | 0 | 0.0% | 0 | 38 | 32 | 18,027 |
| `g08-forecast-accuracy-vintages` | 3 | 1 | 33.3% | 1 | 90 | 64 | 30,266 |
| `g50-courier-boost-rollout` | 3 | 0 | 0.0% | 0 | 76 | 50 | 19,956 | |

### Suite

| metric | value |
|---|---|
| tasks | 10 |
| total valid trials | 31 |
| total passes | 1 |
| **aggregate pass@1** | **3.2%** |
| **task-level pass@3** | **10% (1 of 10 tasks)** |
| target | < 30% |
| **met** | ****yes** — 10% against a <30% target** |

### Context, whole pool

Across all 21 exposed tasks: 64 valid trials, 24 passes, **aggregate pass@1 = 37.5%**. Five excluded tasks
score 3/3 (`03`, `05`, `06`, `g35`, `g42`). The final ten are a deliberately hard selected subset, and this
contrast is what establishes that the failures are not a harness or scaffold artefact.

### Criterion-level, 12 instrumented trials

| criterion | passed | rate |
|---|---|---|
| `evidence_reconstruction` | 11/12 | 92% |
| `scientific_object` | 11/12 | 92% |
| `estimator_implementation` | 11/12 | 92% |
| `independent_validation` | 11/12 | 92% |
| `identification` | 5/12 | 42% |
| **`quantitative_results`** | **2/12** | **17%** |
| `decision` | 4/12 | 33% |

---

## 19. First-error, contradiction, revision and over-credit analysis

### First consequential error

| location | instances | example |
|---|---|---|
| quantitative reconstruction after a correct diagnosis | 10/12 instrumented | `p20` reports `feed_defect_share_pct` 51.15 where truth is 0.0 |
| procedure encodes the discovered mechanism, cannot express another | 4/9 (4-world instrumented) | `p22` `attribution_pp[tooling] = 0.0` in every world |
| what a correct quantity licenses | 2 | `p31` AjqzDN8/3fnpGae: right numbers, `identification` and `decision` fail |
| outright collapse | 1 | `p31` GyUgp7D fails all seven criteria |
| output-contract compliance, not science | 7 field-instances | `p20` v1 sign convention — **our defect** |

Never the first consequential error: failing to read the governing document, failing to reproduce the
incumbent number, failing to notice something was wrong.

### Contradiction handling

Agents engaged with contradictions and resolved them locally. `g10` trials confronted the summer-ice-cream
contradiction and resolved it correctly (recomputing the baseline from −5.3% to **+9.96%**). What is absent
is contradiction handling that reaches back into already-completed downstream work. Modal pattern:
contradiction → local diagnosis → local correction → proceed.

### Revision

Present in 82% of trials; **more common in failing trials (86%) than passing ones (75%)**. Revisions are
local — a filter, an estimator, a population — not a re-derivation of what the reported quantity should be.
`p22` is the decisive case: correct revision of the conclusion, no revision of the procedure.

### Decision-only over-credit

**4 of 12 instrumented trials (33%)** earned the `decision` criterion while failing the science:
`p20`/TirBLuz, `p20`/iwPaF7u, `p20v1.1`/94Gb7c2, `p20v1.1`/g9k77Jz. All four would pass a decision-only
rubric. Conversely a decision-only rubric would have **failed** all three `p22` trials whose visible-world
science was entirely correct. Both errors are avoided only by grading components separately **and**
re-executing on sibling worlds.

---

## 20. Prospective and disconfirmed hypotheses

See §5. Recorded prospectively, tested here:

| # | hypothesis | verdict |
|---|---|---|
| H1 | failures will be coherent, not incoherent | **supported** — no trial produced incoherent work |
| H2 | the agent commits early and does not revise | **disconfirmed** — 82% revised |
| H3 | the agent fails for lack of discriminating tests | **disconfirmed** |
| H4 | the decision will sometimes be right for the wrong reasons | **supported** — 4/12 |
| H5 | stating the invariant explicitly will raise the pass rate | **disconfirmed** — ablation 0/3 |

Previous negative results from earlier phases are preserved in `HANDOFF_G50_*.md` and
`research/phase3/analysis_plan.md`; none has been rewritten.

---

## 21. G50 status

| item | value |
|---|---|
| version | v2.2 (five worlds) |
| Oracle / Nop (5 worlds) | **1 / 0** |
| verifier runtime | ~103 s for five worlds uncontended (82.5 s for four) |
| criterion-level rewards | yes, 6 criteria |
| re-execution | yes — the agent's own command, five privately regenerated worlds |
| pre-exposure adversarial campaign | 11 routes, 35 mutations across two world-counts, 40 grading attacks, 8 sandbox attacks |
| five-world mutation suite | 11 of 12 as intended |
| break-even threshold binding | **yes, on `hidden_d`** (effect −0.3049 pp) — closed the gap that let `M_threshold_ignored` pass |
| known blind spots | `H_post`, `R2_boostshare`, `M_holdout_as_control` all pass; documented, not hidden |
| freeze | five hash groups, §13 |
| exposure | v2.3, 3 valid trials, 0 passes. Three earlier v2.2 trials were **invalid** (verifier refused to grade; see §6 D4) and are preserved as `g50-gemini3flash-baseline-{1,2,3}__INVALID-verifier-refused-ldsocache`. |

Full detail: `HANDOFF_G50_V21_FINAL_PRETARGET.md` (39 sections) plus §30 of `report/FINAL_REPORT.md`.

---

## 22. Scale and RL plans

`report/FINAL_REPORT.md` §34 (10 → 1,000) and §35 (RL relevance).

The load-bearing idea in the scale plan is an **admissibility test that makes clones impossible by
construction**: an instance is admissible only if its reference solution produces the wrong answer on at
least one other admissible instance. That is computable — run instance A's reference against instance B's
world — and it is exactly the property that made the `p22` result observable.

The load-bearing caveat in the RL plan: **Harbor verifies final state and does not supervise process.** We
do not claim otherwise. What makes these tasks usable anyway is that criterion-level rewards are a
per-capability vector rather than a scalar, and that `g50`-style sibling-world re-execution turns a
generalisation property into a terminal reward.

Strongest RL seeds: `g50` (reward already encodes generalisation), `p22` (cleanest mechanism-swap),
`p20` (densest reward vector), `g10` (revision must propagate), `p31` (spec-reading over metric-chasing).
Weakest: `g36` and `g08`.

---

## 23. Reproducibility audit

```bash
python scripts/extract_trajectories.py   # jobs/ -> report/analysis/trajectories.json  (67 valid trials)
python scripts/compute_metrics.py        # -> report/analysis/metrics.json  (every §18 number)
```

`extract_trajectories.py` reads only `jobs/*/config.json`, `*/verifier/*` and `*/agent/trajectory.json`.
It never reads a solution or a generator. Invalid trials are identified solely by the `__INVALID` marker in
the job directory name and are dropped before any metric is computed.

Determinism: `g50`'s verifier regenerates its worlds inside every grading run; across the validation
campaign's independent container runs the printed anchors never drifted, and two back-to-back oracle runs
produced byte-identical criteria.

Not reproducible: the Gemini trials themselves. `gemini-3-flash-preview` is non-deterministic and is a
preview model. The trajectories are therefore shipped as primary evidence rather than as something a reader
regenerates.

## 24. Paths

| artefact | path |
|---|---|
| report | `report/FINAL_REPORT.md` (37 sections) |
| curation table | `report/CURATION_TABLE.md` |
| trajectory dataset | `report/analysis/trajectories.json` |
| metrics | `report/analysis/metrics.json` |
| criterion-failure dataset | `report/analysis/criterion_failures.json` |
| leakage audit | `report/analysis/leakage_audit.json` |
| provenance | `candidates/<task>/REAL_DISTRIBUTION_PROVENANCE.md` × 10 |
| progress log | `OVERNIGHT_FINAL10_PROGRESS.md` (append-only) |
| G50 pre-target handoff | `HANDOFF_G50_V21_FINAL_PRETARGET.md` (39 sections) |
| G50 freeze | `candidates/g50-courier-boost-rollout/FREEZE_MANIFEST_V23.txt` |
| submission staging | `submission_final10/` |
| **ZIP** | `submission_final10.zip` |
| fallback (untouched) | `submission_5task_fallback.zip` |

## 25. Costs

Not recorded per job; estimated, not measured. Token counts are in the trajectories: a representative `p22`
trial recorded 850,103 prompt tokens (696,018 cached) against 18,819 completion tokens. Median completion
tokens per trial across the final ten range from 12,828 (`g50`) to 30,266 (`g08`). At published flash-tier
pricing the 67 valid trials are of order single-digit US dollars. Machine cost was local compute on an
8-CPU Docker VM; the dominant expense was wall-clock, not money.

## 26. Remaining risks

1. **Criterion evidence is concentrated.** 15 instrumented trials across 4 tasks carry the central result.
   The other six tasks are binary-reward only. **Highest-value next step: instrument them as v1.1 forks and
   re-expose.**
2. **One model, one scaffold.** `gemini-3-flash-preview` via `gemini-cli`. Scaffold stopping behaviour and
   model capability are not separable from this data alone.
3. **Three trials per task.** A task at 0/3 could have a true pass rate near 0.3 at 95% confidence.
4. **`harbor check` never completed** (unauthenticated environment). The scaffold-agent *experience* of the
   instructions is untested, as distinct from the verifiers, which are validated directly.
5. **`g50`'s documented blind spots** (`H_post`, `R2_boostshare`, `M_holdout_as_control` all pass) mean its
   reward does not distinguish some scientifically weaker warrants.
6. **Preview-model dependency.** If `gemini-3-flash-preview` is withdrawn, the baseline is not re-runnable.
7. **The `02` image-layer leak existed in a distributed image.** Fixed in v1.1; anyone who built and shared
   the v1 image leaked `pit_reference.py`.

## 27. Git status

Nothing committed, nothing pushed, per the standing instruction across this project. Untracked additions
this run: `OVERNIGHT_FINAL10_PROGRESS.md`, `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md`, `report/`,
`scripts/extract_trajectories.py`, `scripts/compute_metrics.py`,
`scripts/build_submission_final10.sh`, `candidates/p20-noshow-monitoring-v1.1/`,
`candidates/02-renewal-risk-regression-v1.1/`, ten `REAL_DISTRIBUTION_PROVENANCE.md` files,
`candidates/g50-courier-boost-rollout/{FREEZE_MANIFEST_V23.txt,tests/}`, and new `jobs/` directories.

Modified: `candidates/g50-courier-boost-rollout/tests/{scenarios.py,test.sh,runtime_manifest.*}` — the
fifth world and the verifier fix, both recorded in the freeze manifest and the progress log.

---

## 28. Morning answers

1. **Exactly 10 final tasks?** Yes.
2. **What are they?** `02-renewal-risk-regression`, `g05-sco-rollout-gate`, `g10-censored-demand`,
   `g24-recommender-ope`, `g36-tou-capacity-gate`, `p20-noshow-monitoring`, `p22-gauge-recalibration`,
   `p31-fill-rate-dispute`, `g50-courier-boost-rollout`, `g08-forecast-accuracy-vintages`.
3. **What NEW tasks did you build?** **None, and that is a deliberate audited decision, not a shortcut.**
   All five assignment blueprints are already covered (§"Curation"): 1 → `02`+`p20`, 2 → `g10`,
   3 → `g24`, 4 → `g50`+`g05`, 5 → `p20`+`g36`. Part XI forbids rebuilding a covered blueprint. What I did
   build: a **fifth world for `g50`** that makes the monetary break-even binding for the first time, and two
   remediation forks (`p20-…-v1.1`, `02-…-v1.1`). The one capability absent everywhere — an
   identification-removed / justified-deferral sibling world — is a *variant*, cannot be retrofitted to an
   exposed task, and is the top-priority generation template in the scale plan.
4. **What datasets/artifacts does each task contain?** See each `REAL_DISTRIBUTION_PROVENANCE.md` field 4.
   Ranges from a 25-entry workspace (`g50`: orders/zones/markets/courier-shifts/assignment/config/ledger/
   ops-events SQLite warehouse, incumbent package, readout, dispatch note, experiment plan, metric
   definitions, decision memo) to 68 entries (`02`).
5. **What real workflow does each represent?** §7 professional-workflow matrix.
6. **What public evidence supports the realism?** §7 source table; 25+ citations.
7. **What was rejected and why?** `report/CURATION_TABLE.md` — 12 exclusions. Strongest excluded: `g34`
   (distinct competing-risks mechanism, but 2/3 passed). `g41` excluded on verifier instability.
8. **Oracle=1 on every final task?** Yes, all ten (§10).
9. **Nop=0 on every final task?** Yes, all ten (§10).
10. **≥3 valid Gemini trials each?** Yes: 3 each except `g05` (4). Total 31 valid.
11. **Were exposed tasks changed afterward?** **No.** `g50`'s fifth world predates its exposure; `p20` v1
    and `02` v1 are preserved byte-for-byte with fixes in separate forks. The only post-exposure change is
    `g50`'s **verifier** fix after its three trials were invalidated — the task version was forked to v2.3
    and re-exposed, and the invalid trials are preserved and excluded.
12. **Aggregate pass@1?** **3.2%** (1 of 31 valid trials).
13. **Task-level pass@3?** **10%** (1 of 10 tasks).
14. **<30% target met?** **Yes**, with margin.
15. **What failure mode emerged?** Agents recover the correct mechanism and fail to convert it into a
    correct, generalising quantitative object — with the break point depending on mechanism class (§4 and
    `report/FINAL_REPORT.md` §31).
16. **Across how many tasks?** All 10 show it; the sub-mode split is measurable on the 4 instrumented ones.
17. **Across how many trajectories?** 30 failing trials in the final ten; 15 with criterion detail.
18. **What contradicts the explanation?** §4 "Evidence against it" — keyword-measured identification,
    criterion evidence from 4 of 10 tasks, sub-mode (a) only testable where sibling-world re-execution
    exists, possible scaffold stopping, one model/scale.
19. **Where was the first consequential error?** §19. Never in reading the document, reproducing the
    incumbent, or noticing the problem.
20. **Did agents recognise problems?** Yes — 89% noticed an anomaly.
21. **Did they perform useful diagnostics?** Yes — 97% read the governing document, 87% engaged
    identification; `g10` ran the discriminating test in all three trials.
22. **Did they revise?** Yes — 82%, and *more* in failing trials (86% vs 75%).
23. **Did revisions propagate?** **Largely no.** `p22` revised the conclusion and not the procedure.
24. **How often was the decision right for wrong reasons?** **4 of 15 instrumented trials (27%).**
25. **Strongest recursive investigation?** `g10` (all three trials), and one `g24` trial that diagnosed the
    bias in its own first correction.
26. **Why long because of reasoning, not file volume?** §8 — workspaces are 25–68 files; depth comes from
    evidence-dependent decisions, not file count.
27. **What did G50 teach us?** Eight lessons, `report/FINAL_REPORT.md` §30. The most consequential: an
    adversarial campaign built on `oracle`/`nop` cannot exercise the paths a scaffolded agent takes.
28. **Which hypotheses were disconfirmed?** §5 — five, including the two we most expected to confirm.
29. **How would 10 become 1,000?** §34 of the report, with a computable anti-clone admissibility test.
30. **What would an RL system train on?** §35 — criterion vectors and sibling-world re-execution, **not**
    process supervision, which Harbor does not provide.
31. **Strongest RL seeds?** `g50`, `p22`, `p20`, `g10`, `p31`. Weakest: `g36`, `g08`.
32. **Any leakage?** One real instance (`02` v1 image layers, D2), confirmed and remediated; agent could
    not reach it at runtime. Zero agent-visible leakage across all ten.
33. **Any grader exploits?** None found. 40 malformed-output attacks and 8 sandbox attacks on `g50`, all 0.
34. **Any infrastructure failures?** Yes — 8 invalid trial directories, all preserved with reasons:
    3 `g50` verifier refusals (D4), 1 agent-setup timeout, 3 free-tier/API-key failures, 1 session
    interruption. None counted as model failures.
35. **Does the report match the raw logs?** Yes — every number is emitted by `scripts/compute_metrics.py`.
36. **Does the ZIP validate?** See §"ZIP" below.
37. **SHA-256?** See §"ZIP" below.
38. **READY?** See §"ZIP" below.
39. **If NO, what remains?** See §"ZIP" below.

---

## 29. ZIP, SHA-256, and final answers 36–39

| | |
|---|---|
| **path** | `submission_final10.zip` |
| **size** | 144M |
| **files** | 4517 |
| **integrity** | `unzip -t` passes |
| **SHA-256** | recorded in `SUBMISSION_SHA256.txt` (see the note below) |

Contents: `samples/` (the ten, plus three clearly-marked extras and `README_SAMPLES.md`),
`logs/` (88 job directories — every valid Gemini trial for the final ten plus the Oracle/Nop runs and the
preserved `__INVALID` directories), `report/` (the report, curation table, the four analysis JSONs, both
metric scripts, the progress log and this handoff).

**Fallback archive:** `submission_5task_fallback.zip` SHA-256
`c8561aad8300df6c832921fa5b86ea669def1cb04bbaba2e649e9919c5a9c760` — **unchanged**, matching the value
recorded before this run.

### 36. Does the ZIP validate?
**Yes.** `unzip -t` passes; all ten task directories present with `instruction.md`, `task.toml`,
`environment/Dockerfile`, `tests/test.sh` and `REAL_DISTRIBUTION_PROVENANCE.md` each.

### 37. SHA-256
Recorded in `SUBMISSION_SHA256.txt`, alongside the archive.

**Why it is not inlined here.** This handoff is itself inside the archive, so any hash written in
this file would be the hash of a different archive than the one containing this sentence. The
authoritative value therefore lives in `SUBMISSION_SHA256.txt`, which sits next to
`submission_final10.zip` and is *not* packaged inside it. Verify with:

```bash
shasum -a 256 -c SUBMISSION_SHA256.txt
```

**Note on rebuild determinism.** `SUBMISSION_SHA256.txt` is the hash of the *delivered* archive and
has been verified against it. Re-running `scripts/build_submission_final10.sh` produces a
functionally identical archive with a **different** hash, because ZIP stores per-file modification
times and the staging step rewrites them. The hash therefore identifies this artefact, not the build
recipe; the recipe's output is verified by content (`unzip -t`, the file-presence checks the script
runs, and the four analysis JSONs being regenerable by the two metric scripts).

### 38. Is the submission READY?
**YES**, with four disclosed defects — all found by our own audit or by the first real agent run, all
remediated, none changing a measured outcome (§6).

### 39. What remains
Nothing blocking. Ranked by value if the work continued:

1. **Instrument the six binary-reward tasks** as v1.1 forks and re-expose. The central result rests on 15
   trials across 4 tasks; this is the one change that would most strengthen it.
2. **Build the identification-removed / justified-deferral sibling worlds.** No task currently tests whether
   an agent will decline when the evidence does not identify the target.
3. **Run `harbor check`** on an authenticated, idle host to test the scaffold-agent experience of the
   instructions.
4. **A second model and a second scaffold**, to separate model capability from scaffold stopping behaviour.
5. **Retire `g50`'s remaining blind spots** or narrow its claim further (`H_post`, `R2_boostshare`,
   `M_holdout_as_control` all pass).
