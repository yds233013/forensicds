# ForensicDS — Decision-grade production data science under competing interpretations

**A benchmark of ten Harbor tasks, and a measured capability gap in a frontier agent.**

Prepared for the Abundant AI research take-home. All numbers in this report are computed from the raw
job artefacts in `logs/` by `scripts/extract_trajectories.py` and the metric scripts named in §36.

---

## 1. Executive summary

Ten Harbor tasks were built and validated around a single capability: recovering the decision-relevant
scientific object from messy production evidence when a plausible but scientifically wrong analysis is
already in the room. Each task hands the agent work inherited from another data scientist — an
executable incumbent analysis, the artefacts that produced it, the operational documents that govern the
decision, and a consequential business decision that depends on getting the quantity right.

`google/gemini-3-flash-preview` was evaluated with at least three valid trials per task. The headline
numbers are in §18. The research result is not the difficulty.

**The research result is where the failures sit.** Across the failing trials in the final ten,
**83% (25/30) named the correct scientific mechanism in their own reasoning and still failed.** On the
four tasks that emit criterion-level rewards, the failure is concentrated at one point:

| criterion | passed | failed |
|---|---|---|
| `evidence_reconstruction` | 8/9 | 1/9 |
| `scientific_object` | 8/9 | 1/9 |
| `estimator_implementation` | 8/9 | 1/9 |
| `independent_validation` | 8/9 | 1/9 |
| **`quantitative_results`** | **2/9** | **7/9** |
| `decision` | 2/9 | 7/9 |

Agents reconstruct the evidence, frame the right object, implement an estimator, and pass their own
validation. What they fail to do is turn a correctly framed analysis into a number that is right and
that stays right when the underlying mechanism changes.

The sharpest single case is `p22`. All three trials produced a **fully correct** visible-world
attribution — correctly blaming the measurement system rather than the supplier, and correctly declining
to raise a supplier nonconformance — and all three scored 0. They failed on one sibling world where the
true driver is tooling, because the attribution code they wrote had no path that could ever assign the
change to tooling. They did not commit to a wrong explanation. They wrote a procedure that encoded the
one explanation they had found.

Two prospectively plausible stories are **disconfirmed** by this data and are reported as such in §29:
that agents fail because they do not run discriminating tests, and that failure tracks effort.

---

## 2. Research question

> Can an AI agent recover the decision-relevant scientific object from messy production evidence,
> correctly identify and execute the analysis that answers it, revise its interpretation when later
> evidence contradicts earlier conclusions, validate the resulting analysis, quantify uncertainty where
> necessary, and make a defensible professional decision when a plausible but scientifically wrong
> analysis is already available?

The question is answered **capability by capability** rather than with a single pass rate, because the
criterion-level results show the capabilities dissociate sharply.

---

## 3. Benchmark thesis

A data scientist's expensive failures are rarely coding failures. They are failures to notice that the
number being computed is not the number the decision needs. That error is *coherent*: the analysis runs,
the diagnostics pass, the confidence interval is narrow, and the conclusion is wrong because the
population, the estimand, the unit of intervention, the measurement instrument or the observation process
is not what the analyst assumed.

A benchmark that isolates this must therefore supply:

1. an **incumbent analysis that is not incompetent** — executable, documented, quantitatively plausible,
   and passing the checks a professional would run;
2. **objective visible evidence** sufficient to discover the real mechanism, without being told;
3. a **decision** with an externally fixed rule, so the answer is right or wrong for stated reasons;
4. **sibling worlds** in which the mechanism differs, so a procedure that encodes one explanation is
   distinguishable from a procedure that recovers whichever explanation holds.

Point 4 is what makes the p22 result observable at all, and it is the design lesson we would carry into
any future version of this work.

---

## 4. Why this slice of data science

The slice is *decision-grade production analytics*: work where an analysis feeds a named decision with
money attached, and where the evidence is operational exhaust rather than a curated dataset. We chose it
because it is (a) economically dense — the decisions in these ten tasks include a capital tranche
release, a £1.8m contractual claim, a national incentive rollout, a supplier change, capacity
procurement, and a clinical model replacement; (b) the dominant real failure mode is scientific rather
than algorithmic; and (c) it is poorly covered by existing agent benchmarks, which mostly measure
whether code runs and a metric improves.

---

## 5. Real-distribution definition

A task is in distribution if a working data scientist could be handed its `/workspace` on a Monday
morning and recognise every artefact. Concretely, for each task we require: a named professional role, a
named industry, a consequential decision with an externally written rule, inherited artefacts that a real
organisation would actually possess, and a failure mechanism documented in the professional or academic
literature as something that really happens.

Each of the ten tasks carries a `REAL_DISTRIBUTION_PROVENANCE.md` with ten fields, including public
sources. §9 summarises them; the files are the authority.

---

## 6. Related work and design lessons taken

We did not copy tasks. The lessons we took:

- **MLE-bench / DSBench / DSEval-style benchmarks** measure end-to-end ML or analysis competence against
  a target metric. Their limitation for our purposes is that a metric target tells the agent what to
  optimise, which is exactly the step we want to test. Our tasks therefore specify a *decision* and a
  *contract*, never a metric to maximise.
- **Off-policy-evaluation literature** supplied the observation that offline and online outcomes
  correlate weakly and that flaws in offline evaluation setups are widespread rather than exceptional —
  directly motivating `g24`.
- **Two-sided marketplace experimentation literature** supplied both the mechanism and the real
  magnitudes for `g50`: interference made an auction experiment's estimate wrong by a factor of two
  (Blake and Coey 2014), and a marketplace search experiment can overestimate by 50% (Fradkin 2019).
- **Feature-store / point-in-time-correctness practice** supplied `02` and part of `p20`: without
  point-in-time joins, models leak future information and produce metrics that collapse in production.
- **Real-time-data / revision-risk econometrics** supplied `g08`: scoring a forecast against restated
  actuals exaggerates apparent performance.
- **Harbor** supplied the execution and grading substrate. We used its criterion-level `reward.json`
  facility, which was essential: a binary reward would have hidden the entire result in §1.

Sources are cited per task in the provenance files and in §9.

---

## 7. Task distribution

| domain | tasks |
|---|---|
| Retail / grocery / FMCG supply chain | `g05`, `g10`, `p31` |
| Healthcare provider operations | `p20` |
| Precision manufacturing | `p22` |
| B2B SaaS revenue | `02` |
| Consumer internet personalisation | `g24` |
| Regulated electric utility | `g36` |
| Energy trading analytics | `g08` |
| On-demand delivery marketplace | `g50` |

| decision type | tasks |
|---|---|
| Capital / procurement release | `g05`, `g36`, `g10` |
| Contractual claim or escalation | `p31`, `p22` |
| Model deployment / retirement | `02`, `p20`, `g08`, `g24` |
| Programme rollout | `g50` |

No two tasks share a scientific mechanism (§10).

---

## 8. The final ten

| # | task | mechanism | verifier | pass@3 |
|---|---|---|---|---|
| 1 | `02-renewal-risk-regression` | point-in-time correctness / leakage | retrain + re-evaluate | 0% |
| 2 | `g05-sco-rollout-gate` | identification under staggered adoption | gate figure + decision | 0% |
| 3 | `g10-censored-demand` | informative censoring endogenous to the programme | baselines + decision | 0% |
| 4 | `g24-recommender-ope` | off-policy evaluation under a logging policy | policy value + decision | 0% |
| 5 | `g36-tou-capacity-gate` | population definition under tariff migration | scalar gate | 0% |
| 6 | `p20-noshow-monitoring` | policy feedback + feature vintage + drift decomposition | criterion-level, 4 worlds | 0% |
| 7 | `p22-gauge-recalibration` | measurement-system bias vs process change | criterion-level, 4 worlds | 0% |
| 8 | `p31-fill-rate-dispute` | contractual metric definition reconciliation | criterion-level, 4 worlds | 0% |
| 9 | `g50-courier-boost-rollout` | interference / unit of intervention | criterion-level, re-execution on 5 worlds | see §18 |
| 10 | `g08-forecast-accuracy-vintages` | data vintage / restated actuals | accuracy pack + decision | 100% |

Selection rationale and every exclusion: `report/CURATION_TABLE.md`. Selection was **not** by difficulty
rank — two zero-pass artefacts were excluded and one task with a pass was included, for mechanism
coverage and verifier strength.

---

## 9. Professional workflow provenance

Each task's full provenance is in `candidates/<task>/REAL_DISTRIBUTION_PROVENANCE.md`. Summary, in the
form the assignment asks for:

**`p22-gauge-recalibration`** — *This task represents* a process data scientist restating a supplier
escalation under a supply quality agreement. *The analyst inherits* a CMM inspection database with gauge
and operator identifiers, a calibration procedure (QP-07), heat-lot genealogy, tooling-change events, the
`quality` package that produced the published report, and the agreement itself. *The consequential
decision is* whether to raise a formal nonconformance and change bar-stock supplier. *The mechanism is*
measurement-system bias presenting as a process shift. *This is representative because* calibration
corrects instrument bias while Gauge R&R addresses consistency — a gauge can be perfectly calibrated and
still fail R&R — and a control chart built on an unvalidated gauge shows false out-of-control signals that
trigger adjustments which add variation. *The synthetic abstraction is* the plant and its measurements.
*It preserves* the artefact surface, the contractual output form, and the fact that the measurement and
material explanations are both locally consistent with the headline.
Sources: [MoreSteam MSA](https://www.moresteam.com/toolbox/measurement-system-analysis) ·
[Gauge R&R vs Calibration](https://microprecision.com/blog/gauge-rr-vs-calibration/) ·
[Five Common Mistakes with Gage R&R](https://www.spcforexcel.com/knowledge/measurement-systems-analysis-gage-rr/five-common-mistakes-gagerr/)

**`p31-fill-rate-dispute`** — *represents* a demand-science analyst supporting Commercial and Legal on a
service-level dispute. *Inherits* order/shipment/delivery tables, the published 97.7% report, the
counterparty's 91.5% report for the same period, the supply agreement, shortfall tickets, and the
reporting code. *Decision:* a £1.8m claim, plus the team's own bonus gate. *Mechanism:* two defensible
definitions of the same KPI. *Representative because* there is no universal OTIF standard and disputes
turn on order vs line vs case level, request vs promise date, and the treatment of partial fills — with
the documented consequence that brands reporting a healthy 97% fill rate see OTIF in the 80s and
chargebacks arrive anyway, which is exactly this task's gap. Walmart enforces 98% OTIF with a 3%-of-COGS
charge on the non-compliant portion.
Sources: [What Is OTIF?](https://blog.inymbus.com/what-is-otif-on-time-in-full-explained) ·
[OTIF chargebacks](https://www.fulfyld.com/knowledge/what-does-otif-mean-retail/) ·
[DIFOT](https://en.wikipedia.org/wiki/DIFOT)

**`g10-censored-demand`** — *represents* a demand scientist preparing a Q3 buy plan during an
inventory-reduction programme. *Inherits* sales, inventory snapshots, stockout records, the LEAN-26
configuration, and a category review recommending cuts in all eight categories. *Decision:* the buy plan
and the programme extension. *Mechanism:* informative censoring created by the very programme being
evaluated. *Representative because* observed sales understate demand at stockout, models trained on
censored sales underestimate demand, reorder quantities fall, and stockouts recur — a documented
self-reinforcing cycle; without stockout annotation, models treat censored signals as accurate.
Sources: [FreshRetailNet-50K](https://arxiv.org/abs/2505.16319) ·
[Demand forecasting under lost sales stock policies](https://www.sciencedirect.com/science/article/abs/pii/S0169207023000961)

**`g50-courier-boost-rollout`** — *represents* a Finance-facing decision scientist re-deriving an
experiment readout before an investment committee. *Inherits* an operational warehouse, the incumbent
`northline_eval` package, the readout claiming a 4.0-point improvement, a dispatch-queue design note, the
experiment plan, and a decision memo with a £0.19/£12.70 break-even. *Decision:* national rollout.
*Mechanism:* interference — a boosted offer pre-empts an unboosted one in a shared market-hour courier
queue, so the arm contrast measures redistribution. *Representative because* interference is a documented
SUTVA violation with large measured magnitudes: wrong by a factor of two in an auction experiment,
50% overestimation in a marketplace search experiment.
Sources: [Interference, Bias and Variance in Two-Sided Marketplace Experimentation](https://dl.acm.org/doi/fullHtml/10.1145/3485447.3512063) ·
[Experimental Design in Two-Sided Platforms](https://arxiv.org/pdf/2002.05670)

**`02-renewal-risk-regression`** — *represents* a revenue data scientist whose promoted model is not
holding up in production. *Inherits* the training pipeline, the warehouse extract, monitoring that does
not match the evaluated model, a Sales note, and the offline evaluation that justified promotion.
*Decision:* release the Q3 retrain or not. *Mechanism:* point-in-time correctness. *Representative
because* without point-in-time joins models leak future information and produce metrics that collapse in
production, and training-serving skew is named as the first thing to suspect when a model degrades.
Sources: [Databricks point-in-time joins](https://docs.databricks.com/aws/en/machine-learning/feature-store/time-series) ·
[Point-in-Time Correctness in Real-Time ML](https://towardsdatascience.com/point-in-time-correctness-in-real-time-machine-learning-32770f322fb1/)

**`g08-forecast-accuracy-vintages`** — *represents* an analytics engineer owning a forecast-accuracy mart.
*Inherits* forecasts with origin timestamps, a restated actuals series, the mart that replaced a
notebook, and the accuracy review recommending retirement of v3. *Decision:* retire a forecast model.
*Mechanism:* vintage-correct accuracy measurement. *Representative because* using revised rather than
as-of data exaggerates apparent forecast performance, and "scoring a day-one forecast using current field
values instead of the values as of day one" is described as the single most common reason a backtest
overstates accuracy.
Sources: [Revision Risk in Real-Time Macroeconomic Forecasting](https://arxiv.org/pdf/2607.05882) ·
[Backtesting a sales forecast model](https://orm-tech.com/blog/how-to-backtest-a-sales-forecast-model)

**`g24-recommender-ope`** — *represents* a personalisation analyst choosing what serves a high-traffic
surface. *Inherits* logged interactions from the deployed policy, candidate score snapshots, and an
offline gate ranking v7 above v6 and v7_pd highest. *Decision:* which ranker serves the home row.
*Mechanism:* off-policy evaluation under a logging policy. *Representative because* offline evaluation is
an imperfect proxy for online performance, recommendation data are biased by the exposure process, and
flaws in offline setups are widespread.
Sources: [Widespread Flaws in Offline Evaluation of Recommender Systems](https://arxiv.org/pdf/2307.14951) ·
[Offline A/B Testing for Recommender Systems](https://arxiv.org/pdf/1801.07030)

**`p20-noshow-monitoring`**, **`g05-sco-rollout-gate`**, **`g36-tou-capacity-gate`** — see their
provenance files. `p20` is a healthcare model-risk submission under a written standard (MRM-04) with four
competing causes for one symptom; `g05` is a retail capital-committee gate under staggered wave adoption;
`g36` is regulated utility capacity procurement where a tariff migration is entangled with the scalar the
regulator's reserve applies to.

---

## 10. Scientific mechanisms

| task | what the incumbent computes | what the decision needs | why the incumbent is plausible |
|---|---|---|---|
| `02` | AUC on a training matrix with overwritten features | performance achievable at scoring time | the offline number was genuinely computed, and cleanly beat the prior model |
| `g05` | before/after or naive TWFE across waves | the effect the business case's gate is defined on | assignment is documented, the estimate is signed and precise |
| `g10` | baselines from observed sales on "clean" days | latent demand, uncensored | filtering to stockout-free days *sounds* like removing contamination |
| `g24` | an offline ranking metric on logged data | the policy value of the candidate on the deployment population | the gate is the team's established process and ranks candidates confidently |
| `g36` | mean peak-window kW on the observed population | the quantity the regulator's reserve applies to | the arithmetic in the memo is correct given its inputs |
| `p20` | monitored AUC vs validation AUC | the decomposition MRM-04 requires, on the standard's population | the vendor's review is competent and its recommendation is coherent |
| `p22` | nonconforming rate from CMM readings | the rate attributable to each named cause | the readings are real, the rate step is real, the report is arithmetically right |
| `p31` | fill rate at one aggregation level | the contractual floor at the contractual unit | 97.7% is a correct computation of *a* fill rate |
| `g50` | the phase-2 arm contrast | the estate-wide effect of turning Boost on for everyone | it is the *correct* estimate of the arm contrast, with a narrow interval and consistency across all 16 markets |
| `g08` | WAPE against latest actuals | WAPE against vintage-correct actuals | the mart is well-engineered and its numbers reconcile internally |

The unifying property: **in every case the incumbent answer is a correct computation of a different
quantity.** No task's incumbent contains a bug that a code review would catch.

---

## 11. Long-horizon dependency structure

These tasks are long because of reasoning depth, not file volume. A representative dependency graph
(`p22`; the others are structurally similar and are documented per task in the repository):

```
D1  read the published quality report and the escalation draft
 ↓
D2  reproduce the 92.8% first-pass yield from the inspection database
 ↓
D3  notice the step is not uniform across gauges / operators / heat lots
 ↓
D4  formulate competing causes with professional reason to be considered:
      material (supplier changed heat lots)   tooling (insert change)
      operator (new starter)                  measurement (CMM recalibrated)
 ↙                ↓                ↓                    ↘
D5a stratify by   D5b tooling-    D5c operator-      D5d compare the two
    heat lot          change          level rate         CMMs against the
                      dates                              calibration log
 ↘                ↓                ↓                    ↙
D6  resolve: the yield step coincides with a CMM re-zero, and the offset is
    present in the reference artefact measurements, not only in production parts
 ↓
D7  redefine the scientific object: the *conformance-referenced* rate, with the
    gauge offset removed, is what Schedule 3 §3.2 requires
 ↓
D8  reconstruct the population the agreement specifies (window, part, strata)
 ↓
D9  implement the attribution across all named causes
 ↓
D10 validate: does the corrected rate reconcile with the independent reference artefact record?
 ↓
D11 quantify: the residual attributable to material, with the agreement's tolerance
 ↓
D12 apply Schedule 3 §3.2's threshold and state the supplier action
```

Each edge is evidence-driven: D3 → D4 because the step is not uniform, so a single global cause is
already improbable; D5d → D6 because the offset appears in *reference artefact* measurements, which
cannot have been affected by the supplier's material; D6 → D7 because the agreement defines the rate on
a conformance reference. Nothing in the agent-visible material states the answer.

The graph is benchmark-author documentation and is not exposed to the target model.

Dependency depth across the ten tasks ranges from 8 (`g36`) to 12 (`p20`, `g50`). Every task requires
evidence from at least two operational systems; six require at least three.

---

## 12. Task construction

Every task is a Harbor task directory with `instruction.md`, `task.toml` (schema 1.4),
`environment/Dockerfile`, a seeded generator, an agent-visible `/workspace`, `tests/`, and
`solution/solve.sh`. The generator runs in a build stage whose layers are not copied into the final
image, so the data-generating process is absent from every layer the agent can reach (verified for `g50`
by exporting the image and scanning all 13 layer blobs; §32).

The incumbent analysis is a real Python package in `/workspace` that produces the published report. It is
executable and coherent; in `g50` it is *correct* — it computes the phase-2 arm contrast accurately, with
a narrow interval, consistent across all 16 markets. Its capacity check is designed so that it cannot
fail, because both arms draw on the same courier pool.

Sibling worlds are generated from the same code with different seeds and different mechanism parameters.
`p20`, `p22`, `p31` have four; `g50` has five.

---

## 13. Verification

Four tasks (`p20`, `p22`, `p31`, `g50`) emit criterion-level rewards through Harbor's flat
`reward.json` map. `g50` additionally **re-executes the agent's own command** against five privately
regenerated worlds: it copies the submitted code into an opaque scratch tree excluding `data/` and
`out/`, writes that world's warehouse, deletes the output directory, runs
`python -m northline_eval readout --db data/northline.sqlite --out out` as an unprivileged user, and
grades only files that post-date the run.

`g50`'s verifier hardening, all verified by attack rather than assertion:

- the generator, scenario specs and verifier are unreadable to the pipeline user — confirmed from *inside*
  the re-execution, which reports `PermissionError` for each;
- the original `/workspace` and its outputs are unreachable, so a correct `readout.json` cannot be copied
  forward;
- scratch directories are named `r0`…`r4` inside an opaque `mkdtemp` root and the parent is not listable,
  so there is nothing to branch on;
- the interpreter, the whole library tree including `site-packages`, the sandbox binaries, their `ldd`
  closure, and the loader configuration are hash-pinned per architecture;
- writing `/etc/ld.so.preload` triggers refuse-to-grade.

Sixty-three adversarial submissions were run against it (§16).

**Verifier limitation, stated plainly:** six of the ten tasks emit a binary reward only. They were
exposed before criterion-level reporting existed, and retrofitting it would change an exposed verifier,
which Part XX of the assignment forbids. The criterion-level analysis in §20 therefore rests on four
tasks and nine trials. That is the single largest measurement weakness in this report.

---

## 14. What reward establishes

A reward of 1 on a criterion-instrumented task is evidence that, on every graded world, the agent:
reconstructed the metric population and the evidence exactly; produced a decision quantity that is a
different object from the incumbent's; landed within tolerance of the world-specific truth; reported an
interval at the right unit of inference; and applied the written decision rule. For `g50` it is
additionally evidence that one procedure did all of this on five worlds it had never seen.

## 15. What reward does not establish

Reward does not establish that the agent reasoned about the mechanism, understood why the incumbent was
wrong, or would generalise beyond the worlds tested. Specifically for `g50` (the case we audited hardest):
post-treatment weighting, a boost-share dose-response extrapolation, and using the never-enrolled markets
as a comparison group all pass, and are *not* distinguished from the reference. Two of these are
scientifically weaker warrants that this world does not punish. The full list is in `g50`'s handoff §6.

**We do not claim the benchmark measures reasoning. It measures reconstruction and decision.**

---

## 16. Pre-exposure integrity

`g50` is the only task whose entire validation happened before any target-model exposure, and it is
therefore the integrity reference. Before exposure it was subjected to:

| suite | count | result |
|---|---|---|
| legitimate estimator routes run as real submissions | 11 | 4 intended routes pass; 6 of 11 score 1 |
| mutations | 23 | 21 correctly rejected |
| malformed-output attacks through the grading function | 40 | 0 mismatches |
| sandbox / isolation attacks through the container | 8 | all 0 |
| reproducibility | 2 identical runs | byte-identical criteria |
| world regenerations across all runs | 92 | four (later five) distinct anchor sets, no drift |

Freeze manifests record five independent hash groups (target-visible, generator, verifier, oracle,
complete task) so a later reader can tell which kind of change a digest shift represents.

For the other nine tasks, Oracle=1 and Nop=0 were recorded before their Gemini exposure, and their
exposure ledger is reproduced in full in §18. Two tasks in the pool carry `__INVALID` job directories
from earlier infrastructure failures (free-tier quota, API key rejection, session interruption); those
are excluded from all metrics and are listed in §18.

---

## 17. Evaluation setup

```bash
harbor run -p <task-path> -a gemini-cli -m google/gemini-3-flash-preview \
  -k 1 -n 1 -o jobs --job-name <name> -y --agent-setup-timeout-multiplier 3.0
```

Three independent single trials per task, separate job names, rather than `-k 3`, so one crashed trial
cannot contaminate the others. `--agent-setup-timeout-multiplier 3.0` is required on this host: sibling
tasks recorded agent-setup timeouts without it, and one job directory is preserved as
`g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` to document that.

Authentication, provider and infrastructure failures are invalid trials and were replaced, never counted
as model failures. All trials were run one at a time; concurrent Docker execution on this 8-CPU host
produced the timeouts that generated the invalid directories.

---

## 18. Results

All numbers computed by `scripts/compute_metrics.py` from the raw job artefacts in `logs/`.

### Final ten

| task | valid trials | passes | pass@1 | pass@3 | median steps | median tool calls | median completion tokens |
|---|---|---|---|---|---|---|---|
| `02-renewal-risk-regression` | 3 | 0 | 0.0% | **0** | 84 | 51 | 22,676 |
| `g05-sco-rollout-gate` | 4 | 0 | 0.0% | **0** | 65 | 40 | 16,881 |
| `g10-censored-demand` | 3 | 0 | 0.0% | **0** | 62 | 44 | 21,913 |
| `g24-recommender-ope` | 3 | 0 | 0.0% | **0** | 60 | 42 | 19,901 |
| `g36-tou-capacity-gate` | 3 | 0 | 0.0% | **0** | 44 | 31 | 14,280 |
| `p20-noshow-monitoring` | 3 | 0 | 0.0% | **0** | 52 | 45 | 19,034 |
| `p22-gauge-recalibration` | 3 | 0 | 0.0% | **0** | 60 | 52 | 18,819 |
| `p31-fill-rate-dispute` | 3 | 0 | 0.0% | **0** | 38 | 32 | 18,027 |
| `g08-forecast-accuracy-vintages` | 3 | 1 | 33.3% | 1 | 90 | 64 | 30,266 |
| `g50-courier-boost-rollout` | 3 | 0 | 0.0% | **0** | 76 | 50 | 19,956 | | | | | | |

### Suite aggregates

| metric | value |
|---|---|
| tasks | 10 |
| total valid trials | 31 |
| total passes | 1 |
| **aggregate pass@1** | **3.2%** |
| **task-level pass@3** | **10% (1 of 10 tasks)** |
| assignment target | < 30% pass@3 |
| target met | ****yes** — 10% against a <30% target** |

Invalid trial directories excluded from every metric, preserved on disk with the reason in the directory
name: `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout`,
`task01-gemini3flash-diagnosis__INVALID-api-key-rejected`,
`task01-gemini3flash-diagnosis__INVALID-free-tier-quota`,
`task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped`,
`task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup`.

### Context: the whole candidate pool

Across all 21 exposed tasks (including the eleven excluded from the final ten), 61 valid trials produced
24 passes — **aggregate pass@1 = 39.3%**. The final ten are therefore a deliberately selected hard
subset, and the contrast is itself informative: the excluded tasks are not easier versions of the same
mechanisms, they are mechanisms this model has largely mastered (`g35`, `g42`, `03`, `05`, `06` all 3/3).

### Ablation: does telling the agent the invariant help?

`02-renewal-risk-regression__explicit-invariant` is the same world with the invariant stated outright in
the instruction. **3 valid trials, 0 passes.** Making the issue explicit did not produce a pass. This is
direct evidence that the difficulty is not concentrated in *noticing* the problem.

### Version fork: `p20` v1.1

`p20-noshow-monitoring-v1.1` fixes the contract defect in §31. **3 valid trials, 0 passes**, with **zero** `programme_effect_pp` sign failures where v1 had seven. The fix removed the artefact and the task remains hard for genuine reasons. Trial 2 passed **six of seven** criteria, failing only `quantitative_results` — the single cleanest instance of the failure mode in the dataset.

---

## 19. Difficulty profile

| pass@3 | tasks |
|---|---|
| 0 of 3 | `02`, `g05`, `g10`, `g24`, `g36`, `p20`, `p22`, `p31` (8 tasks) |
| 1 of 3 | `g08` |
| `g50` | 0 of 3 |

The distribution is deliberately not uniform. A suite in which every task scores 0 would be consistent
with tasks that are simply impossible or mis-specified; `g08` passing once, and the eleven excluded tasks
passing routinely, is what establishes that the ten are hard for a reason rather than broken. The
strongest single piece of evidence on that point is `p22`, where all three trials produced a *correct*
analysis of the visible world and were defeated only by a sibling world.

---

## 20. Criterion-level results

From the four tasks that emit criterion rewards (`p20`, `p22`, `p31`, `g50`). This is the most
informative table in the report.

Criterion names differ slightly between tasks (`g50` uses `quantitative_result` and adds `uncertainty`
and `courier_supply_response`; the others use `quantitative_results`, `identification`,
`estimator_implementation`, `independent_validation`). Mapped to a common scheme across all **15**
instrumented trials:

| capability | criterion(s) | passed | rate |
|---|---|---|---|
| reconstruct the evidence | `evidence_reconstruction` | 14/15 | **93%** |
| implement an estimator | `estimator_implementation` | 11/12 | **92%** |
| validate its own work | `independent_validation` | 11/12 | **92%** |
| frame the right object | `scientific_object` | 11/15 | 73% |
| argue identification | `identification` | 5/12 | 42% |
| decide | `decision` | 4/15 | 27% |
| **produce the right number** | `quantitative_result(s)` | **2/15** | **13%** |
| quantify uncertainty (`g50` only) | `uncertainty` | 0/3 | 0% |
| measure the surviving channel (`g50` only) | `courier_supply_response` | 1/3 | 33% |

The four-task subset used for the per-trial matrix below (before `g50` was exposed):

| criterion | passed | rate |
|---|---|---|
| `evidence_reconstruction` | 8/9 | 89% |
| `scientific_object` | 8/9 | 89% |
| `estimator_implementation` | 8/9 | 89% |
| `independent_validation` | 8/9 | 89% |
| `identification` | 4/9 | 44% |
| **`quantitative_results`** | **2/9** | **22%** |
| `decision` | 2/9 | 22% |

Per trial:

| task / trial | decision | estimator | evidence | identification | validation | quantitative | object |
|---|---|---|---|---|---|---|---|
| `p20`/TirBLuz | PASS | PASS | PASS | PASS | PASS | **fail** | PASS |
| `p20`/iwPaF7u | PASS | PASS | PASS | **fail** | PASS | **fail** | PASS |
| `p20`/c654dzn | **fail** | PASS | PASS | **fail** | PASS | **fail** | PASS |
| `p22`/rBUvW2D | **fail** | PASS | PASS | PASS | PASS | **fail** | PASS |
| `p22`/nt5YXX8 | **fail** | PASS | PASS | PASS | PASS | **fail** | PASS |
| `p22`/DxMjiB7 | **fail** | PASS | PASS | PASS | PASS | **fail** | PASS |
| `p31`/GyUgp7D | **fail** | **fail** | **fail** | **fail** | **fail** | **fail** | **fail** |
| `p31`/AjqzDN8 | **fail** | PASS | PASS | **fail** | PASS | PASS | PASS |
| `p31`/3fnpGae | **fail** | PASS | PASS | **fail** | PASS | PASS | PASS |

**Reading.** Eight of nine trials reconstructed the evidence, framed the right scientific object,
implemented an estimator and passed independent validation. Seven of nine then failed to produce the
right number. One trial (`p31`/GyUgp7D) failed everything — a single outright collapse, not the pattern.
Two `p31` trials produced the right numbers and still failed `identification` and `decision`: a different
sub-pattern, where the quantity is right but what it licenses is not.

The verifier's `independent_validation` criterion passing 8/9 deserves a caveat: it checks that the agent
performed *a* validation, not that the validation was capable of detecting the error it made. Agents
validated, and their validation passed, and they were still wrong — which is itself a finding about what
self-validation is worth here.

---

## 21. Trajectory analysis

Every valid trajectory was parsed (`scripts/extract_trajectories.py` → `report/analysis/trajectories.json`):
61 trials across the exposed pool, all with a complete `agent/trajectory.json`, plus the final `/workspace`
each agent left behind. For each trial we extracted tool calls, files touched, shell commands, step and
token counts, the final output artefacts, the verifier's per-criterion notes, and the agent's own reasoning
(`reasoning_content`), from which we scored seventeen professional-move signals.

### What agents actually did

Across all 61 valid trials:

| professional move | share of trials showing it |
|---|---|
| read the governing policy/contract document | 97% |
| noticed an anomaly | 89% |
| discussed identification / confounding / assignment | 87% |
| revised something | 82% |
| mapped to a decision threshold | 70% |
| redefined the population | 52% |
| considered competing hypotheses | 30% |
| quantified uncertainty | 16% |
| performed independent validation | 11% |

Agents are not skipping the investigation. They read the contract, they notice the anomaly, they talk about
identification, and they revise. The two moves that *are* rare — independent validation (11%) and
uncertainty quantification (16%) — are exactly the two that would catch the error they go on to make.

### Qualitative reads

`g10-censored-demand`, all three trials: heavy, correct engagement with the mechanism (29–36 separate
mentions of censoring/stockout). One trial recomputed the ice-cream baseline from −5.3% to **+9.96%**,
explicitly noting this "confirms that the Head of Planning was onto something", computed post-go-live lost
share at 11.6% and forecast bias at −8%, and identified the selection bias in using stockout-free days only.
Reward 0.

`g24-recommender-ope`, all three trials: identified the incumbent gate's "Direct Match" estimator as the
source of bias. One trial went further and diagnosed its *own* first correction as biased — "I was only
counting clicks on items where the logging and candidate policies aligned… this created a biased result.
I've corrected this now." Reward 0.

`p22-gauge-recalibration`, all three trials: produced **byte-identical, correct** visible-world output
(measurement-system 2.88 pp, material 1.06 pp, corrected rate 3.81%, `no_supplier_action`). All three
closed with high confidence — "everything is correct", "I'm ready to submit". All three scored 0 on one
sibling world where tooling is the driver, reporting `tooling: 0.0`.

---

## 22. First consequential errors

Where the first error that determined the outcome occurred, from the criterion notes and the trajectories:

| location of first consequential error | trials | example |
|---|---|---|
| quantitative reconstruction after a correct diagnosis | 7/9 instrumented | `p20` reports `feed_defect_share_pct` 51.15 where truth is 0.0 |
| procedure encodes the discovered mechanism and cannot express another | 4/9 instrumented | `p22` `tooling: 0.0` on every world |
| what a correct quantity licenses (identification → decision) | 2/9 instrumented | `p31` AjqzDN8/3fnpGae: right numbers, wrong decision |
| outright collapse of the whole analysis | 1/9 instrumented | `p31` GyUgp7D fails all seven criteria |
| output-contract compliance rather than science | 7 field-instances | `p20` v1 sign convention — **our defect, not the model's** (§31) |

**Not** observed as the first consequential error in any trial: failure to read the governing document,
failure to reproduce the incumbent number, or failure to notice that something was wrong.

### Model-side versus environment-side

Of the 30 failing trials in the final ten, 29 are model-side. One class is environment-side: the `p20` v1
sign-convention defect, which contributed to 2 of 3 `p20` trials. Even there, both trials failed on
independent genuine grounds, so no trial's *outcome* is attributable to the environment. Five job
directories are infrastructure failures and are excluded as invalid trials, not counted as model failures.

---

## 23. Contradiction handling

Agents encountered contradictions and engaged with them. `g10` trials confronted the summer-ice-cream
contradiction the Head of Planning raised and resolved it correctly. `g24` trials confronted the gap
between the offline gate's confident ranking and the logged data's exposure structure. `p22` trials
confronted a yield step that was not uniform across gauges.

What we do **not** see is contradiction handling that reaches back into already-completed downstream work.
The modal pattern is: contradiction → local diagnosis → local correction → proceed. The `g24` trial that
caught its own biased correction is the strongest counter-example in the set and it is a single trial.

## 24. Revision behaviour

Revision language appears in 82% of trials — and in **86% of failing trials versus 75% of passing ones**.
Revision is not scarce and it does not predict success. Inspecting the revisions: they are almost always
*local* — a filter changed, an estimator swapped, a population narrowed — rather than a re-derivation of
what the reported quantity should be.

## 25. Recursive scientific reasoning

The capability we most wanted to observe is the one the data show least of: a revision that propagates
through every downstream quantity. `p22` is the cleanest demonstration of its absence. The agents revised
correctly (from "supplier caused it" to "the gauge caused it"), reached the right decision, and left in
place an attribution function whose structure still encoded a world in which tooling contributes nothing.
The revision changed the *answer* without changing the *procedure*.

`p31` AjqzDN8 shows the mirror image: the procedure produced correct quantities and the agent did not
propagate them into the identification argument or the decision.

## 26. Effort and cost

| | median steps | median tool calls | median completion tokens | median prompt tokens |
|---|---|---|---|---|
| passing trials (all 61) | 41 | 28 | 11,596 | — |
| failing trials (all 61) | 58 | 44 | 19,034 | — |

Taken at face value this says failure costs more work. **It is a task-difficulty confound and we discard
it** (§29). Prompt-token totals are large because the scaffold re-sends context: one representative `p22`
trial recorded 850,103 prompt tokens of which 696,018 were cached, against 18,819 completion tokens.
Monetary cost was not recorded per job; at published flash-tier pricing the 61 valid trials are of order
single-digit dollars, which we state as an estimate, not a measurement.

## 27. Decision-only over-credit

Two of nine criterion-instrumented trials (22%) earned the `decision` criterion while failing the science:
`p20`/TirBLuz (failed `quantitative_results`) and `p20`/iwPaF7u (failed `identification` and
`quantitative_results`). Both would have scored a pass under a decision-only rubric.

This is the empirical case for criterion-level grading. A benchmark of this kind that grades only the final
recommendation would have credited 2 of 9 trials for reaching the right conclusion from an analysis that
does not support it — and, in `p22`'s case, would have *failed* three trials whose visible-world science was
entirely correct. Both errors are avoided only by grading the components separately and re-executing.

## 28. Prospective hypotheses

Recorded before this run's analysis:

| hypothesis | status |
|---|---|
| H1: the agent will produce a coherent-but-wrong analysis rather than an incoherent one | **supported** — no trial produced incoherent work; every failing analysis ran and was internally consistent |
| H2: the agent will commit early to one explanation and not revise | **disconfirmed** — 82% revised (§24) |
| H3: the agent will fail because it does not run discriminating tests | **disconfirmed** (§29) |
| H4: the decision will sometimes be right for the wrong reasons | **supported** — 2/9 (§27) |
| H5: making the invariant explicit will raise the pass rate | **disconfirmed** — the `02` ablation is 0/3 with the invariant stated |

## 29. Disconfirmed hypotheses, in detail

**"Agents fail because they don't run discriminating tests."** This was our leading prospective
explanation and the data do not support it. 89% of trials noticed an anomaly, 87% engaged with
identification, 82% revised, and 97% read the governing document. In `g10` all three trials ran the
discriminating test — recomputing baselines with availability accounted for — and got a qualitatively
correct answer. They still failed. **We explicitly decline to claim this, per the assignment's Part XXIV.**

**"Failure tracks effort."** In aggregate, failing trials show more steps (58 vs 41), more tool calls
(44 vs 28), more reasoning (14.3k vs 9.4k characters) and *more* of the good professional moves —
competing hypotheses 41% vs 12%, reproduce-incumbent 51% vs 25%. This is entirely confounded by task
difficulty: harder tasks draw more effort and produce more failures. **Controlling for task**, across the
six tasks with mixed outcomes, effort is pass-higher in 3/6 and fail-higher in 3/6 for every effort
measure. There is no within-task effort signal, and the aggregate result is an artefact.

**"The model does not understand the mechanism."** Disconfirmed as a general claim. Searching each failing
trial's own reasoning for task-specific mechanism language: **25 of 30 (83%) named the correct mechanism
and still failed.** Per task: `g05` 4/4, `g10` 3/3, `g36` 3/3, `p22` 3/3, `02` 2/3 (and the explicit-invariant
ablation 3/3), `g24` 2/3, `p31` 2/3, `g08` 2/2, `p20` 1/3. This is a keyword measure over truncated
reasoning and therefore a lower bound (§33 item 2).

---

## 30. G50 case study: what building one task to destruction taught us

`g50` received roughly the validation effort of the other nine combined, before any target exposure. It is
the methodological centrepiece of this submission and the source of most of our design rules.

**The task.** A delivery marketplace randomised a courier incentive per order and measured a 4.0-point
reduction in late deliveries across 120,671 orders. The investment committee's decision rests on a
different quantity: the estate-wide change if the incentive were on for every order rather than none, with
a £0.19/£12.70 break-even of 1.4961 percentage points.

**The mechanism.** A boosted offer pre-empts an unboosted offer in the same market-hour courier queue. The
priority reordering is *mean-preserving* within a market-hour, so the arm contrast is almost entirely
redistribution and collapses at full rollout. What survives is a faster acceptance decision, a
courier-supply response, and an offsetting idling cost.

**The incumbent is not wrong.** It is the correct estimate of the arm contrast: assignment is clean, the
realised share tracks the configured target in every market-week, the arms were balanced pre-programme,
the effect is present in all sixteen markets, and the interval is four tenths of a point wide. Its
capacity check compares courier hours available to each arm and finds them identical to within 0.08% —
because the arms share the same couriers. **That check cannot fail, and that is the designed trap.**

### Seven lessons, each of which changed the build

1. **Numerical proximity to generator truth does not establish scientific validity.** We separated, for
   every task thereafter: the business estimand, the latent simulation truth, what the design actually
   identifies, the reference estimator, what the verifier can observe, and what it *cannot* distinguish.
   `g50`'s own audit concluded that post-treatment weighting, a boost-share dose-response extrapolation,
   and using never-enrolled markets as the comparison group are all observationally equivalent to the
   reference here. We accepted them and narrowed the claim rather than blacklisting them.

2. **An outcome-graded benchmark cannot detect a circular warrant.** A dose-response extrapolation
   through the interference region is the closest route to truth of any tested (0.717 pp vs the
   reference's 0.811). The reason is a property of *this world* — the realised dose-response is nearly
   linear because the priority mechanism is mean-preserving — not a property of the method. We report
   that `g50` provides **no** evidence about extrapolation through interference, rather than engineering a
   world to punish it.

3. **Verifier bugs are found by the oracle failing, not by inspection.** The first oracle run failed
   `evidence_reconstruction` on 43–49 market-weeks per world because the verifier graded lateness from the
   generator's unrounded latent flag while the analyst can only see the value stored to two decimals. The
   agent was right and the verifier was wrong. Roughly 1.5–2.1 orders per 10,000 sit exactly on that
   boundary.

4. **Ambiguity in the output contract is a difficulty inflator, and it is invisible until measured.** Two
   defensible sources exist for one panel field; the rule was weakened to what both agree on. In `p20` the
   same class of defect was found *after* exposure and cost a version fork (§31).

5. **Re-execution against unseen worlds is the only thing that kills hardcoding.** The decisive evidence:
   a mutation that runs the correct analysis once, reads its own output and bakes it in as a literal
   passes the visible world and fails all six criteria on the three unseen ones. Static grading would have
   scored it 1.

6. **Author quality gates are not assignment requirements.** A "every wrong route must separate by ≥3×
   tolerance" rule was retired once we recognised it as self-imposed. Measured separations (2.57× for the
   raw arm contrast) are reported as they are.

7. **Design goals can be in arithmetic tension, and the tension must be measured rather than assumed
   away.** Moving the visible world's effect away from the decision threshold — done to stop legitimate
   estimators disagreeing on the decision — made the £0.19/£12.70 break-even *never binding*: a mutation
   that rolls out on any reduction at all passed. With a worst-accepted-route deviation of 1.072 pp and a
   1.4961 pp threshold, the only effect band satisfying both requirements is roughly [−0.35, −0.10] pp.
   A fifth world was calibrated to −0.3049 pp, which closed the gap and, as a side effect, strengthened
   the pre-period-adjustment invariant (an unadjusted estimator now misses by 18.6 pp there).

8. **Adversarial validation against `oracle` and `nop` does not exercise the paths a real scaffold takes,
   and this is the most consequential lesson in the list.** `g50` survived 11 estimator routes, 35
   mutations, 40 malformed-output attacks and 8 sandbox attacks. The *first* real agent run was refused
   outright: `verifier: interpreter, library tree or sandbox tools differ from the pinned image`. The cause
   was our own hardening — `/etc/ld.so.cache` was hash-pinned to close a loader-redirection path, and
   `apt-get` runs `ldconfig`, which regenerates it. Every agent scaffold installs its own tooling; `oracle`
   and `nop` install nothing, so 63 adversarial submissions never touched the failing path. Reproduced
   deterministically with `apt-get install curl`. Three trials were discarded as invalid, the check was
   replaced with a **resolution** test (every shared object the verifier's interpreter and sandbox tools
   actually load must resolve to a manifest-pinned path, which is immune to unrelated installs and is the
   property a redirection attack must break), and the task was re-frozen and re-exposed. **Any future
   task must be validated against a scaffolded agent, not only against the reference, before exposure.**

**Status.** `g50` was still unexposed when lesson 7 was acted on, so the fix was legitimate. Had it been
exposed, the honest course would have been a version fork, as with `p20`. Lesson 8's defect *was* found
after exposure; the three affected trials are invalid rather than model failures, and the corrected version
is `v2.3`.

---

## 31. The failure mode we actually found

**Agents recover the correct scientific mechanism and fail to convert it into a correct, generalising
quantitative object.**

Stated as the chain the tasks are built around, with where it breaks:

```
read evidence ✓ 97%   →  notice anomaly ✓ 89%   →  name the mechanism ✓ 83% of failures
   →  frame the scientific object ✓ 89%   →  implement an estimator ✓ 89%
   →  ✗ PRODUCE THE RIGHT NUMBER  22%
   →  ✗ WRITE A PROCEDURE THAT SURVIVES A DIFFERENT MECHANISM  (4/9 instrumented failures)
   →  ✗ decision  22%
```

Two distinguishable sub-modes:

**(a) Procedure-level overfitting.** The agent writes code that encodes the explanation it found rather
than a method that recovers whichever explanation holds. `p22` is the clean case: three trials, correct
visible-world science, `tooling: 0.0` hardwired, defeated by one sibling world. This is only observable
because the verifier re-executes against worlds with different mechanisms — a static grader would have
scored all three as correct.

**(b) Quantitative reconstruction failure after a correct diagnosis.** The agent names the mechanism and
its numbers still miss. `p20` invents a 51% feature-feed defect share where truth is 0%; `g10` gets the
direction right and the magnitudes wrong.

**(c) Failure to reframe the estimand at all.** On `g50` all three trials reported
`programme_effect_pp` **identical to the arm contrast** (within 0.000 pp), with an order-level interval
1.882 pp wide, a `courier_hours_response_pct` of +0.366 — the incumbent's zero-power capacity identity —
and `decision: roll_out`, the expensive wrong answer. They reproduced the incumbent's analysis and walked
into every designed trap. `evidence_reconstruction` passed in all three; nothing downstream did.

**The failure localises differently by mechanism class, and only criterion-level grading reveals this:**

| task | mechanism class | where it breaks |
|---|---|---|
| `g50` | interference / unit of intervention | **the estimand** — 3/3 never reframed; reported the arm contrast |
| `p22` | measurement-system attribution | **generalisation** — 3/3 framed correctly, procedure could not transfer |
| `p20` | drift decomposition | **the quantity** — up to 6 of 7 criteria pass, the number is wrong |
| `p31` | contractual definition | **split** — 1/3 outright collapse, 2/3 right numbers with wrong identification |

This is a more useful result than a single bottleneck would have been. Where the task requires *choosing* a
different estimand against a confident incumbent, the agent does not choose it. Where the task requires
*recovering a mechanism*, the agent recovers it and then fails to generalise or to get the number right.

**Scope: across how many tasks and trajectories.** Sub-mode (a) is directly evidenced on `p22` (3/3) and
`p31` (1/3) — the tasks whose verifiers re-execute on sibling worlds — and is *structurally untestable* on
the six binary-reward tasks, which is a measurement limitation, not evidence of absence. Sub-mode (b) is
evidenced across all nine tasks with trials: 29 of 30 failing trials, and 25 of 30 with an explicitly
correct mechanism identification.

**Why this is not a benchmark artefact.** Four independent checks: (i) the same model passes 24 of 61
trials on the wider pool, including 3/3 on five excluded tasks, so it is not a scaffold or harness
failure; (ii) Oracle=1 and Nop=0 on every final task, so the tasks are solvable and not trivially
passable; (iii) we audited every criterion failure for sign and unit artefacts and found exactly one such
defect, in `p20`, which we then fixed and re-ran (§18) — and which did not change any trial's outcome;
(iv) `g50` survived 23 mutations, 40 malformed-output attacks and 8 sandbox attacks before exposure.

## 32. Alternative explanations we cannot rule out

1. **Scaffold stopping behaviour.** Many trials end with confident "ready to submit" reasoning. If
   `gemini-cli` terminates before the model would have continued, some of what we score as reconstruction
   failure is premature stopping. We cannot separate these without a second scaffold.
2. **Output-contract friction.** The `p20` defect proves this class exists. We audited for it and found
   one instance; a subtler instance could remain in a binary-reward task where we have no field-level
   notes.
3. **Tolerance calibration.** Our tolerances are author-set. `g50`'s were pre-registered by a stated rule
   and deliberately not re-tuned after seeing mutation results, but the other tasks' tolerances were not
   held to that discipline as explicitly.
4. **Model scale.** `gemini-3-flash-preview` is a fast-tier model. The failure may substantially close at
   a larger scale, which would change the economic reading without changing the mechanism.

---

## 33. Limitations

Ordered by how much they constrain the conclusions.

1. **Criterion-level evidence rests on four tasks and nine trials.** Six of the ten tasks emit a binary
   reward only, because they were exposed before criterion reporting existed and Part XX forbids changing
   an exposed verifier. The §20 localisation of the failure to `quantitative_results` is therefore
   measured on `p20`, `p22`, `p31` and `g50` — a minority of the suite. This is the largest measurement
   weakness in the report.
2. **Mechanism identification is measured by keyword search over truncated reasoning.** The 83% figure
   in §31 counts trials whose first, middle or last reasoning block (1,200 characters each) matches a
   task-specific pattern. It is a *lower* bound on identification, and keyword presence is not proof of
   understanding. It is corroborated qualitatively — `g10` trials recomputed the ice-cream baseline from
   −5.3% to +9.96%, `g24` trials named the Direct-Match selection bias, `p22` trials produced a fully
   correct visible-world attribution — but the headline number is a coarse instrument.
3. **One model, one scale, one scaffold.** Every result is `gemini-3-flash-preview` through `gemini-cli`.
   We cannot separate model capability from scaffold limitation. Several trajectories end with confident
   "ready to submit" reasoning, which may be a scaffold-induced stopping behaviour rather than a model
   belief.
4. **Three trials per task.** pass@3 on three trials is a coarse estimate; a task at 0/3 could have a true
   pass rate up to roughly 0.3 at 95% confidence. Task-level conclusions are safer than per-task ones.
5. **`harbor check` was never completed.** Two attempts failed for environment reasons — an agent-setup
   timeout under host load, then a missing interactive login for the check's scaffold agent. What remains
   untested is how a scaffold agent experiences the instructions, as distinct from the verifier, which is
   validated directly (§16).
6. **Synthetic worlds with imposed mechanisms.** Every DGP is a modelling choice. `g50`'s mean-preserving
   queue, `g10`'s censoring process and `p22`'s gauge offset are plausible and literature-grounded but not
   measured from any real system. Conclusions are conditional on them.
7. **`p20` v1 carries a known contract defect** (§31). Its 0/3 survives the audit because all three trials
   fail on independent genuine grounds, but the defect inflated the failure and the v1 numbers should be
   read with that in mind.
8. **`g50`'s residual blind spots**, documented rather than removed: post-treatment weighting, a
   dose-response extrapolation and a non-randomised comparison group all pass; a one-week pre-period is
   rejected on two of four arbitrary week choices and accepted on the other two, which makes the
   verifier's treatment of that dimension arbitrary.
9. **Effort metrics are confounded by task difficulty.** §29 documents this explicitly; we report the
   within-task analysis and discard the aggregate.
10. **No cost or token accounting for the earlier trials.** Token counts are present in the trajectories
    and reported in §26; monetary cost was not recorded per job and is estimated, not measured.

---

## 34. Scale plan: 10 → 1,000

The generative object is not the task. It is the **(capability, mechanism, workflow)** triple, with the
task as a rendering of it. Cosmetic reskinning of a fixed world produces clones that a model memorises;
varying the mechanism while holding the capability fixed produces genuinely distinct instances.

### Generative hierarchy

```
capability              (6 values)   the thing being measured — see the list below
  × mechanism           (~12)        why the incumbent answer is the wrong quantity
  × professional workflow (~15)      role, industry, decision, governing document
  × DGP parameterisation  (continuous) effect sizes, noise, selection strength
  × operational policy    (3–5)      how the intervention/observation process changed
  × incumbent family      (4)        which plausible-but-wrong analysis is inherited
  × artifact surface      (3)        sqlite warehouse / CSV drop / notebook + parquet
  × sibling-world set     (5 types)  invariance / sensitivity / decision-flip /
                                     identification-removed / mechanism-strength
  × decision threshold    (3)        binding / far-from-binding / interval-dependent
```

Sampling the cross-product naively gives clones. The generation rule we would actually use: **an instance
is admissible only if the correct procedure for it would produce the wrong answer on at least one other
admissible instance.** That is a computable test — run instance A's reference solution against instance
B's world — and it is exactly the discriminating property that made the `p22` result observable. It is
also the property a clone fails by construction.

### Capability axes to hold fixed while varying everything else

1. evidence lineage reconstruction
2. population / eligibility determination
3. scientific-object (estimand) selection
4. identification under a stated design
5. revision after contradiction, and propagation of that revision downstream
6. mapping a quantity to a written decision rule

### Priority mechanism templates, ordered by what this run's evidence says is missing

1. **Identification-removed / justified deferral.** No task in the current suite has a sibling world in
   which the evidence does not identify the target and the correct professional answer is to defer with a
   stated reason. This is the single highest-value addition: it tests whether an agent can decline, which
   is the behaviour production analytics most needs and which reward-seeking most punishes. The
   verifier accepts a `decision: "insufficient_evidence"` with a correctly identified obstruction.
2. **Two-revision chains.** Discover leakage → remove the feature → model still looks strong → discover
   the evaluation population is itself selected → revise again. The current suite has at most one forced
   pivot per task; §25 shows revision *happens* but is shallow.
3. **Mechanism-swap siblings for every task.** The `p22` result says procedure-level overfitting is the
   dominant observable failure. Every generated task should ship at least one sibling world in which a
   *different* named cause dominates, because that is what detects it.
4. **Delayed + selectively observed labels** (fraud/risk, credit, clinical): label maturity entangled
   with an authorisation or review policy.
5. **Competing risks / wrong statistical object** (the `g34` mechanism, currently excluded for being too
   easy at this model scale — worth regenerating at higher difficulty).

### Pipeline

| stage | what runs | gate |
|---|---|---|
| 1. specify | sample a (capability, mechanism, workflow) triple; write the dependency graph first | graph has ≥8 nodes and ≥1 branch point with two professionally motivated hypotheses |
| 2. generate | seeded DGP, warehouse, operational artefacts, incumbent analysis, governing document | incumbent executes and reproduces its published number |
| 3. reference | reference solution + sibling worlds | reference passes on all worlds; incumbent fails on ≥1 |
| 4. cross-check | **run every other instance's reference against this world** | ≥1 foreign reference fails → instance is distinct, not a clone |
| 5. adversarial | Oracle=1, Nop=0, then the mutation and attack suites from §16 automatically | 100% of mutations rejected; 0 grader exploits |
| 5b. **scaffolded dry-run** | one trial with the real agent scaffold (which installs its own tooling), checking only that the verifier **graded** rather than refused | **mandatory gate** — `g50` lesson 8: `oracle`/`nop` install nothing, so 63 adversarial submissions missed a refusal that the first real agent run triggered immediately |
| 6. contamination | search the public web and known corpora for the artefact names and numbers | no hit |
| 7. calibrate | 3 trials on the target model | keep if pass@3 < 0.3; retire above 0.7 |
| 8. expert review | human reads the dependency graph and the incumbent | "a professional could have written this incumbent" |
| 9. freeze | five hash groups, then expose | any post-exposure change forks a new version |

Stages 2–6 are fully automatable; stage 8 is the throughput limit, at roughly 30 minutes of expert time
per instance, which is ~500 expert-hours for 1,000 instances. Stage 4 is the step that prevents the
1,000 from being 10 tasks in 100 costumes, and we would not ship the generator without it.

Retirement and monitoring: track pass@3 per instance per model release; retire an instance when pass@3
exceeds 0.7 on the frontier model; monitor the distribution over capabilities and mechanisms so
retirement does not silently empty one axis.

---

## 35. RL and training relevance

**What an RL system would actually train on, and the honest limit.** Harbor verifies final state. It does
not supervise process. A reward of 1 on these tasks reinforces *whatever trajectory produced a correct
final artefact*, which includes trajectories that guessed. **We do not claim these tasks provide process
supervision, and a naive RL loop on the binary reward would be a weak learning signal at best.**

Three things make them usable as training environments anyway:

1. **Criterion-level rewards are a dense, honest signal.** The §20 matrix shows the criteria dissociate:
   a trajectory can earn `evidence_reconstruction`, `scientific_object` and `independent_validation`
   while failing `quantitative_results`. That is a per-capability reward vector, not a scalar, and it
   localises credit without needing process labels.
2. **Sibling-world re-execution converts a generalisation property into a terminal reward.** `g50`'s
   verifier rewards a *procedure* that works on five worlds, not an answer. This is the closest thing to
   process supervision obtainable from final-state verification, and it directly targets the failure this
   run measured.
3. **The dependency graphs are ready-made process labels** if one wants them. They were written before
   the tasks and are held out of the agent's context; each node is a checkable intermediate state.

**Behaviours training would plausibly improve, in the order this evidence supports:**

- writing a *mechanism-recovering* procedure rather than a mechanism-specific one (the `p22` failure);
- carrying a correct diagnosis through to a correct quantitative reconstruction (the 7/9
  `quantitative_results` failure);
- propagating a revision into every downstream quantity rather than only the one that triggered it;
- declining when the evidence does not identify the target (needs the generated deferral worlds).

**Strongest RL seeds, with reasons:**

| task | why |
|---|---|
| `g50` | re-executes a *procedure* against five worlds; the only task whose reward already encodes generalisation |
| `p22` | cleanest mechanism-swap sibling; the failure is unambiguous and the correct behaviour is well defined |
| `p20` | four competing causes with a criterion per cause — the densest reward vector in the suite |
| `g10` | the intervention creates the censoring, so revision must propagate into the decision quantity |
| `p31` | two defensible definitions with a contract selecting one; trains reading a spec over optimising a metric |

`g36` and `g08` are the weakest seeds: their mechanisms are largely single-step once identified, so the
reward has little internal structure to shape behaviour with.

---

## 36. Reproducibility

Every number in this report is recomputable from the artefacts in the submission:

```bash
python scripts/extract_trajectories.py   # -> report/analysis/trajectories.json   (61 valid trials)
python scripts/compute_metrics.py        # -> report/analysis/metrics.json        (all §18-20 numbers)
```

`scripts/extract_trajectories.py` reads only `jobs/*/config.json`, `*/verifier/*` and
`*/agent/trajectory.json`; it never reads a task's solution or generator. `scripts/compute_metrics.py`
consumes only its output. Invalid trials are identified solely by the `__INVALID` marker in the job
directory name and are excluded before any metric is computed.

Task-level reproduction:

```bash
harbor run -p candidates/<task> -a oracle -k 1 -n 1 -o jobs --job-name repro-oracle -y   # expect 1
harbor run -p candidates/<task> -a nop    -k 1 -n 1 -o jobs --job-name repro-nop    -y   # expect 0
```

Determinism evidence: `g50`'s verifier regenerates its worlds inside every grading run. Across 23
independent container runs during its validation campaign — 92 world regenerations — the printed anchors
took exactly four distinct values (one per world, before the fifth was added) with no drift in any graded
quantity. Two back-to-back oracle runs produced byte-identical criteria.

Freeze manifests for every final task are listed in `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md`, with five
independent hash groups for `g50` so a reader can distinguish a change to what the model sees from a change
to the generator, the verifier, or the reference.

**What is not reproducible:** the Gemini trials themselves. `gemini-3-flash-preview` is non-deterministic
and is a preview model that may be withdrawn; re-running will produce different trajectories. The
trajectories are therefore included in the submission as primary evidence rather than as something a
reader is expected to regenerate.

---

## 37. Conclusion

Ten Harbor tasks measure one capability: recovering the decision-relevant scientific object from inherited
production evidence when a plausible wrong analysis is already in the room. Each task is grounded in a
documented real failure mode, hands the agent a competent incumbent analysis, and turns on a decision with
an externally written rule.

`gemini-3-flash-preview` reaches 10% (1 of 10 tasks) task-level pass@3 and 3.2% aggregate pass@1 on the ten. The
difficulty is not the finding.

The finding is that the failures do not sit where a benchmark designer would naturally place them. These
agents read the governing contract (97%), notice the anomaly (89%), engage with identification (87%),
revise (82%), and name the correct mechanism in 83% of the trials they fail. They then fail to turn that
into a number that is right and that stays right when the mechanism changes: `quantitative_results` passes
in 2 of 9 criterion-instrumented trials while evidence reconstruction, scientific-object framing, estimator
implementation and self-validation each pass in 8 of 9.

The sharpest form of the failure is not a wrong belief but a wrong artefact. On `p22`, three trials produced
a fully correct analysis of the world in front of them — correctly exonerating the supplier and blaming the
measurement system — and all three shipped attribution code that could never assign the change to tooling.
When a sibling world made tooling the cause, the analysis had nothing to say. **The agents revised their
answer without revising their procedure.** That gap is invisible to a static grader and is exactly what a
training environment built on sibling-world re-execution would target.

Two tempting stories are disconfirmed here and we decline to tell them: that agents fail for lack of
discriminating tests, and that failure tracks effort. Both are contradicted by the trajectories once task
difficulty is controlled for.

We also found one defect in our own benchmark, fixed it in a forked version, preserved the exposed original,
and re-measured — which is the discipline we would want applied to any result of this kind, including ours.
