# Audit 2026-09-23 — quantitative evidence computed directly from the repository

Read-only. No model was run. Every number here comes from `jobs/*/*/result.json`,
`jobs/*/*/agent/trajectory.json`, `jobs/*/*/verifier/test-stdout.txt` or `candidates/`.

## 1. Measured pool (valid target-model trials, google/gemini-3-flash-preview)

| task | valid trials | rewards | pass@3 | in final five |
|---|---|---|---|---|
| task01 revenue reconciliation | 3 | 0,1,1 | 1 | no |
| task02 renewal-risk features | 3 | 0,0,0 | 0 | **yes** |
| task03 lead-score evaluation | 3 | 1,1,1 | 1 | no |
| task04 retention metrics | 3 | 0,0,1 | 1 | no |
| task05 experiment readout | 3 | 1,1,1 | 1 | no |
| task06 usage statement close | 3 | 1,1,1 | 1 | no |
| g05 staggered rollout gate | 3 (+1 invalid) | 0,0,0 | 0 | **yes** |
| g08 forecast vintages | 3 | 0,1,0 | 1 | no |
| g10 censored demand | 3 | 0,0,0 | 0 | **yes** |
| g24 recommender OPE | 3 | 0,0,0 | 0 | **yes** |
| g34 fleet reliability | 3 | 1,0,1 | 1 | **yes** |
| g35 dispatch interference | 3 | 1,1,1 | 1 | no |
| g41 parts rebalancing | 3 | 0,0,1 | 1 | no (built after the fallback) |
| g42 contractor safety rate | 3 | 1,1,1 | 1 | no |
| g44 screening precision | 3 | 0,1,1 | 1 | no |
| g36 TOU capacity gate | 3 | 0,0,0 | — | **EXCLUDED, contaminated (F8)** |

Also measured but not a separate task: the task02 "explicit-invariant" instruction ablation (3 trials, 0,0,0).

Valid measured tasks: **15**. Valid measured trials: **45** (+3 excluded G36, +1 excluded G05 JnK5hsR,
+9 infrastructure-invalid Task01/G08 attempts).

## 2. Investigation depth per task (trajectory steps and completion tokens, medians)

| task | result | steps (median, range) | completion tokens (median) |
|---|---|---|---|
| task01 | 2/3 | 84 (52–94) | 16,165 |
| task02 | **0/3** | 84 (84–94) | 22,676 |
| task03 | 3/3 | 68 (62–76) | 13,896 |
| task04 | 1/3 | 34 (32–56) | 17,947 |
| task05 | 3/3 | 40 (38–42) | 9,656 |
| task06 | 3/3 | 82 (54–116) | 23,982 |
| g05 | **0/3** | 65 (42–76) | 16,881 |
| g08 | 1/3 | 90 (90–106) | 30,266 |
| g10 | **0/3** | 62 (58–72) | 21,913 |
| g24 | **0/3** | 60 (58–70) | 19,901 |
| g34 | 2/3 | **20 (18–26)** | **3,617** |
| g35 | 3/3 | 28 (18–32) | 10,211 |
| g41 | 1/3 | 42 (24–52) | 19,946 |
| g42 | 3/3 | 24 (20–32) | 7,352 |
| g44 | 2/3 | 34 (30–52) | 10,356 |

Observation (association, not causation): every 0/3 task sits at 60–84 median steps, i.e. the model
invested substantial effort and still failed. G34, the one final-suite task it solved, has the
*shortest* trajectories in the entire pool (20 steps, 3.6k completion tokens, $0.03–0.05 per trial).

## 3. Evidence inventory per task (from `environment/workspace`, plus generator CREATE TABLEs)

| task | files | evidence categories present | warehouse tables |
|---|---|---|---|
| task01 | 28 | db, code, docs, config, logs, csv | 8 |
| task02 | 34 | db, code, docs, notes, config, logs, csv | 10 |
| task03 | 18 | db, code, docs, notes, config | 7 |
| task04 | 21 | db, code, docs, notes, config, model | 4 |
| task05 | 19 | db, code, docs, notes, config | 7 |
| task06 | 24 | code, docs, report, notes, config, contracts | file-based (no sqlite) |
| g05 | 15 | db, code, docs, notes | 6 |
| g08 | 24 | db, code, docs, notes, model | 11 |
| g10 | 22 | db, code, docs, notes, model | 11 |
| g24 | 19 | db, code, docs, notes, config, model | 4 |
| g34 | 13 | db, code, docs, report | 4 |
| g35 | 12 | db, code, docs, report | 6 |
| g41 | 12 | db, code, docs, report, notes | 9 |
| g42 | 13 | db, code, docs, report, notes | 5 |
| g44 | 13 | db, code, docs, report, notes | 4 |

The four 0/3 tasks span 15–34 files and 4–7 evidence categories; the four 3/3 tasks span 12–24 files
and 4–6 categories. **Evidence volume and heterogeneity do not separate hard from easy tasks.**

Every task requires a state-changing repair: the oracle rewrites 1–4 modules of the incumbent pipeline
and re-runs it. No task is report-only.

## 4. Falsification keyword scan (lower bound, all 55 trials with a reward)

Regex scan of full trajectories, then manual inspection of every hit:

| pattern | genuine hits |
|---|---|
| placebo test | **0 trials** |
| pre-trend / parallel-trends check | **0 trials**, including all four G05 trials where parallel trends is the identifying assumption |
| hold-out / back-test / out-of-sample validation | **0 trials** (all keyword hits are the tasks' own vocabulary: a "holdout" arm in G10/Task03) |
| simulation with a known answer | **0 trials** |
| independent recomputation / cross-check by a second method | 2 trials (G08 pXphfXM, G35 GxLG9yo) |
| sensitivity / robustness analysis | 1 trial (G08 pXphfXM). All G44 "sensitivity" hits are the metric name, not an analysis |
| explicit falsification language ("could be wrong", "test my assumption") | **0 trials** |
| reconcile to the published number | 1 trial (Task04 AEZ8pU4), which is a coherence check against a trusted figure |

This is a keyword lower bound and cannot prove absence; it is consistent with, and independent of, the
trajectory-level classification in the main audit.

## 5. What the verifier actually rejected, per failed final-suite trial

| trial | first graded complaints |
|---|---|
| task02 JctTpSi | 206 rows wrong on `open_expansion_opps`; then 1,538 on `health_score`; eval AUC 0.6347 vs 0.7806 |
| task02 nXXMdDm | 4 rows on renewal-opportunity features; rank correlation 0.9461 (needs ≥0.98) |
| task02 pf9zaPc | renewal-stage/forecast features wrong; rank correlation 0.9464 |
| task02 (ablation) 6LSZCFK | ticket features wrong (138 rows); rank correlation 0.9773 |
| task02 (ablation) 95Q6LAG | ticket + health features wrong; rank correlation **0.9798 vs 0.98** |
| task02 (ablation) j5oNxeF | ticket features only (138, 71, 75, 74 rows across extracts) |
| g05 MMGNYFS | wave effects off 0.031–0.033 vs tolerance 0.005–0.007; intervals miss truth at double width; **decision `continue`, expected `stop`** |
| g05 PYhR2eh | wave effects off 0.026–0.050; intervals miss truth at double width |
| g05 rsDKTXQ | wave effects off 0.020–0.038; gate effect off 0.007–0.016 |
| g10 LhEU3ny | lost units **−49 %**; expected demand off 3–15 %; baseline change off 4–6 pp |
| g10 cLtM9yi | lost units −35 % (promo −62 %); expected demand off 3–9 % |
| g10 eMXZbBi | lost units **+104 %**; expected demand off 3.5–44 % |
| g24 a8zVL7h | **545 decision rows missing**; policy values off 0.039–0.063 vs tolerance ≈0.033 |
| g24 wVmAykK | **178,890 unexpected decision rows**; policy values off 0.078–0.096 |
| g24 ykNY8fD | **178,890 unexpected decision rows**; v7 value off 0.039 vs 0.033 |
| g34 UPCLpLx | failure rate off 0.084 vs tolerance 0.014; **recommendation `baseline`, expected `expanded`** |

Two facts follow directly. (a) G24's failures are a *decision-unit* error visible in the row keys, not a
numerical slip. (b) Task02's failures are residual-feature errors on a minority of features, and two
ablation trials sit within 0.003 of the rank-correlation gate — the feature check, not the correlation
gate, is what binds.

## 6. Coverage of process checks

All five final tasks have: a frozen checksum, a final Oracle=1 run, a final Nop=0 run, a TB3
`harbor check` rubric run, and three valid target-model trials on a single Harbor task digest.

## 7. Decision-level correctness in failed trials (computed directly, no model run)

### G24 — the launch decision passed in all three failed trials
`test_ope.py::test_launch_decision` **PASSED** in a8zVL7h, wVmAykK and ykNY8fD while
`test_decision_table`, `test_policy_values` and `test_intervals` failed. This is F10 in its cleanest
form: the launch call was right in 3/3 while the policy values were off by 0.039–0.096 (tolerance
≈0.033) and the decision table was wrong by 545 missing or 178,890 unexpected rows.

### G05 — decision correct on 10 of 12 extract-level evaluations, not "2/3 correct"
In the G05 verifier a `'decision': None` entry means the decision check passed on that extract.

| trial | visible | hidden_a | hidden_b | hidden_c | decision-correct everywhere? |
|---|---|---|---|---|---|
| MMGNYFS | **wrong** (`continue`, expected `stop`) | pass | pass | pass | no |
| PYhR2eh | pass | pass | pass | pass | **yes** |
| rsDKTXQ | pass | pass | **wrong** (`stop`, expected `continue`) | pass | no |

The report's phrasing ("G05: 2/3, 'stop' was correct") is imprecise: only one of three trials is
decision-correct on every graded extract.

### G10 — recomputed from the agents' own submitted outputs
The buy-plan action is graded after the baseline-tolerance assertion, so the verifier log does not
reveal it. Comparing each trial's `out/review/category_trends.csv` (preserved in `artifacts/`) with
truth recomputed from the task's own generator:

| trial | lost-units error | buy-plan actions matching truth |
|---|---|---|
| LhEU3ny | −49 % | 4 / 8 |
| cLtM9yi | −35 % | **8 / 8** |
| eMXZbBi | +104 % | 1 / 8 |

So one G10 trial reached **every** category decision correctly while its latent-demand estimate was
wrong by a third. The decision rule is a ±5 pp band, which is what makes this possible: moderate
object error preserves the action, large object error destroys it. Decision robustness is therefore
a property of the decision rule's margin, not evidence that the analysis was sound.

### G34 UPCLpLx and Task02 — no F10
G34's failing trial also got the recommendation wrong (`baseline` vs `expanded`). Task02 has no
decision object; it is graded on features and model metrics.

## 8. Engineering cost per task (Python lines: generator + verifier + solution + incumbent)

| generation | tasks | median total lines |
|---|---|---|
| gen-1 (Task01–06, 12–16 Sep) | 6 | 1,700 |
| gen-2 (G05, G08, G10, G24, G34, G35, 15–20 Sep) | 6 | 1,565 |
| gen-3 (G41, G42, G44, 22–23 Sep) | 3 | **1,011** |

Range 924 (G44) to 3,506 (Task01). The marginal cost fell about 2.5× from the first task to the most
recent once the harness (`test.sh`, wheels, runtime manifest, mutation runner, freeze script) was
reusable. This is the concrete evidence behind the report's scale claim: the binding cost is generator
and verifier authoring, and it amortises.
