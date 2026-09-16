# G24 recommender off-policy evaluation: Gemini 3 Flash baseline analysis

- **Task:** `candidates/g24-recommender-ope`, frozen at content checksum `2c9cc2055ef796a5` (commits 2e21788 / b7f1c8e).
  The task was not modified before, during or after this analysis.
- **Job:** `jobs/g24-gemini3flash-baseline-1`.
- **Harness:** gemini-cli, `google/gemini-3-flash-preview`, Harbor 0.21.0, `-k 3 -n 3`,
  `--agent-setup-timeout-multiplier 3`. No other heavy Docker workload ran during the job.
- **Data:** per-trial data in `research/g24/g24_trials.csv`.

**Primary question.** Can Gemini reconstruct the randomisation, exposure, propensity, decision and reward process from
the production logs *before* choosing and implementing an off-policy estimator?

**Answer: no, in 0 of 3 trials, and in the way the task was designed to probe.**
- All three recognised off-policy evaluation.
- All three rejected the replay gate for the right reason.
- All three chose the correct estimator family: slot-exact item-in-slot IPS on the exploration stream.
- All three then mapped that estimator onto the wrong statistical object:
  - two used the pre-filter pool size K as the action space;
  - all three used the wrong decision unit, one of them only for unsampled production decisions.
- Every trial produced a v7 lift whose sign matched AB-1182, and every trial stopped there.
- All three chose the correct launch on **all four** graded extracts (12/12) while their policy values were wrong.

## 1. Setup and validity

| Trial | Env + agent setup | Agent execution | Verifier | Model calls | Valid |
|---|---|---|---|---|---|
| a8zVL7h | 17 + 96 s | 200 s | 1357 s | yes (757k input / 21k output tokens) | yes |
| wVmAykK | 11 + 102 s | 244 s | 1399 s | yes (797k / 16k) | yes |
| ykNY8fD | 20 + 102 s | 258 s | 1378 s | yes (887k / 20k) | yes |

- Three trials, 0 exceptions, 0 infrastructure failures, no retries. Total cost **$0.514**.
- **Verifier time.** About 23 min each, from three concurrent verifiers (each runs the agent's pipeline on four extracts
  plus a rerun). This is well inside the 7200 s limit. No OOM kills; every test produced an assertion outcome.
- **Checksum.** The G24 checksum was verified before launch and after analysis.

## 2. Results

**Ratios** are error/tolerance, re-graded from each agent's submitted package on the four graded extracts with the
verifier's own checks (`tools/g24/quickcheck.py`, read-only; the numbers match the Harbor verifier's messages).

**Truth on the visible extract:** v6 0.3827, v7 0.3695, v7_pd 0.4665; launch v7_pd.

| Trial | Reward | Tests passed | Visible v6 / v7 / v7_pd | Weight | Decision unit | Worst value ratio visible / a / b / c | Launch correct |
|---|---|---|---|---|---|---|---|
| a8zVL7h | 0 | 6/15 | 0.441 / 0.408 / 0.530 | K | exploration correct; 460–1290 production decisions merged | 1.71 / 1.44 / 2.01 / 1.56 | 4/4 |
| wVmAykK | 0 | 6/15 | 0.305 / 0.282 / 0.370 | K | every serve | 2.63 / 4.26 / 2.14 / 3.52 | 4/4 |
| ykNY8fD | 0 | 7/15 | 0.358 / 0.330 / 0.433 | **m** | first serve only | 1.18 / 1.64 / 0.77 / 1.60 | 4/4 |

- **Success rate:** 0/3.
- **pass@3:** 0.
- **What passed in every trial:** logs unmodified, run succeeds, run time, target slates (exact), visible launch,
  determinism.
- **What failed in every trial:** the decision table (visible and all hidden extracts), policy values, and intervals.
  Hidden values failed on every extract except ykNY8fD's hidden_b.
- **Matches with the pre-registered mutation suite.** Two submissions are numerically identical to mutations:
  - a8zVL7h to `wrong_weight_pre_filter_pool`;
  - ykNY8fD to `wrong_keep_first_serve`.

  wVmAykK combines two mutations: weight K and serves as decisions.

### Counterfactuals (one targeted patch each, analysis copies only)

| Trial | Patch | Result |
|---|---|---|
| ykNY8fD | Group serves into decisions by TTL measured from the creating serve, merging clicks over cached re-serves (≈25 lines in `logs.impressions`). Everything else kept, including the unpaired lift SE. | **Passes every check on all four extracts.** Value ratios are identical to the oracle's (0.25 / 0.11 / 0.43 / 0.41). |
| a8zVL7h | Weight = eligible count m instead of `candidate_count` K. | Values, intervals and launch pass on all four extracts. **The decision table still fails** (545 / 1290 / 460 / 675 missing decisions) because of its TTL-anchor error. |

**Conclusion.** Each failure is one semantic step away from the correct object. The failures are not diffuse
statistical noise.

## 3. Reasoning ladder

| Level | a8zVL7h | wVmAykK | ykNY8fD | Count |
|---|---|---|---|---|
| L0 business contradiction | yes | yes | yes | 3/3 |
| L1 off-policy problem (replay invalid) | yes | yes | yes | 3/3 |
| L2 logging policy (uniform shuffle) | yes (verified 1/P(K,5) numerically) | yes (read `serve.py`) | yes (read `serve.py`) | 3/3 |
| L3 filtering order (propensity logged before rules) | no (never read `serve.py`) | **no (read it, never used it)** | **yes** | 1/3 |
| L4 propensity semantics | partial (ordering probability over K) | no | yes | 1/3 |
| L5 eligible action space / m | no | no | yes | 1/3 |
| L6 1/m title-slot probability | no (1/K) | no (1/K) | yes | 1/3 |
| L7 decision unit | partial (see §5) | no | no | 0/3 (1 partial) |
| L8 target slates | yes (inherited) | yes (inherited) | yes (reasoned) | 3/3 |
| L9 reward representation | yes | partial (re-serve clicks lost) | partial (re-serve clicks lost) | 1/3 (slot-exact 3/3) |
| L10 valid estimator at the correct grain | no (weight) | no (weight, grain) | no (grain) | 0/3 (family correct 3/3) |
| L11 uncertainty | yes structurally (paired, decision level) | no (paired over serves) | no (unpaired; noticed, not fixed) | 1/3 |
| L12 scientific validation | no | spurious | no | 0/3 |
| L13 decision | yes | yes | yes | 3/3 (12/12 extracts) |
| L14 complete repair | no | no | no | 0/3 |

**Highest level fully reached / first substantive failure:**
- **a8zVL7h:** reached L2; first failure at L3/L4. It never looked at what happens between the ranker's log and the
  response, and used K.
- **wVmAykK:** reached L2; first failure at L3/L4. It read "The rules layer runs afterwards and can change the
  response" in `serve.py` and still weighted by the retrieved pool.
- **ykNY8fD:** reached L6; first failure at L7. It never grouped cached re-serves, although it read the metric
  definition and the TTL config.

## 4. Knowing IPS ≠ understanding the experiment

The high-value pattern (see propensity → recognise OPE → write IPS → take the log column → stop on plausible numbers)
occurred in a **refined** form.

- **The raw logged propensity was never used as the weight.** All three saw that slate-level 1/propensity gives only
  about 24 exact matches (wVmAykK computed it). They moved correctly to a title-slot marginal.
- **The formula replaced process reconstruction one level later.** Once "uniform shuffle ⇒ each title is in slot k
  with probability 1/N" was written, N was taken from the nearest column (`candidate_count`, "number of titles
  retrieved for the request") in two trials. Neither asked whether the retrieved pool is what the shuffle's output
  was drawn from after the rules layer.
- **Exact points of replacement:**
  - **a8zVL7h, step 24:** it verified `propensity == 1/(n(n-1)(n-2)(n-3)(n-4))` with n = candidate_count to eight
    significant figures. That confirmed the logged semantics and then anchored the action space to n.
  - **wVmAykK, step 28:** "a uniform shuffle across the entire retrieved pool … the probability of item x at position
    k … 1/N". This came 2 steps after reading the rules-layer docstring.
  - **ykNY8fD, steps 30–34:** "the propensity calculation uses an unfiltered list, but the rules layer modifies it" →
    "1/(n−m) for non-suppressed items" → counted `filter_reason IS NULL` per serve. It is the only trial whose process
    reconstruction preceded the formula.

**Propensity beliefs:**

| Question | a8zVL7h | wVmAykK | ykNY8fD |
|---|---|---|---|
| What was randomised | ordering of the retrieved pool | ordering of the retrieved pool | ordering of the full pool, then filtered |
| When | at the ranker run (cache miss) | at the ranker run | at the ranker run |
| Action space | K retrieved | K retrieved | m eligible |
| Before/after suppression | not considered | not considered (read, ignored) | before; suppression changes the probability |
| `candidate_count` | action-space size | action-space size | pre-filter pool (correct) |
| `propensity` | slate ordering probability (correct) | slate ordering probability (correct) | slate ordering probability over the unfiltered list (correct) |
| Level | ordering/slate | ordering/slate | ordering/slate |
| Probability needed | title-slot marginal | title-slot marginal | title-slot marginal |
| Derived correctly | no (1/K) | no (1/K) | yes (1/m) |
| Tested empirically | yes, but only the logged formula, not the needed probability | no | counted eligible titles per serve; no test of uniformity over eligible titles |

## 5. Cache and decision reconstruction

**Classification:**

| Trial | Class | What it did |
|---|---|---|
| a8zVL7h | F | New decision if the serve has a candidate list, or is the first serve for session × surface, or comes more than 600 s after the *previous serve*. |
| wVmAykK | A | Every exploration serve is a unit (77,608), including 18,961 cached re-serves that carry no target slates. Those enter the IPS mean as zeros, and clicks on them are lost. |
| ykNY8fD | B | Only creating serves (those with candidate lists). Clicks on their cached re-serves are dropped, and `decisions.csv` still lists every serve. |

**a8zVL7h (class F): not equivalent.**
- **What it understood:** "`rec_candidates` are populated when the ranker runs (a cache miss)". It merged clicks over
  serves per decision and slot, and understood that one slot counts once.
- **Exploration decisions:** always carry a candidate list, so they are reconstructed exactly.
- **The error:** the TTL is anchored at the previous serve instead of the creating serve. `serving.yaml` says
  `refresh_on_hit: false`, which the trajectory read. A session that re-requests at +580 s and returns at +640 s is
  one decision under its rule and two in reality. This merges 460–1290 unsampled production decisions per extract.
  It is a genuine error, not in the mutation suite, and caught by the exact decision table.

**Understanding counts:**

| Aspect | Count | Trials |
|---|---|---|
| Repeated serves | 2/3 | a8zVL7h, and ykNY8fD via missing candidate lists; wVmAykK never |
| 600 s cache | 1/3 | a8zVL7h, anchored wrongly |
| When a new randomisation occurs | 2/3 | a8zVL7h and ykNY8fD: when the ranker runs |
| Session × surface grain | 1/3 | a8zVL7h |
| Identical slates vs the same decision | 0/3 | none reasoned about it |
| Two rows = one decision | 1/3 | a8zVL7h |

## 6. Reward and position

- **Title and position kept (3/3).** All three preserved title and position (slot-exact matching) and explicitly
  rejected item-anywhere credit ("the current approach … counts a click when an item is in the target top 5,
  regardless of its logged position").
- **Examination effects.** None estimated examination curves. They were not needed for the slot-exact estimator.
- **Decision context and exposure (1/3).** Only a8zVL7h kept them, by merging re-serve clicks into the decision
  outcome.
- **Position bias.** a8zVL7h and ykNY8fD raised position bias and slot independence in reasoning and correctly
  concluded that slot-exact IPS handles it.

## 7. Natural wrong methods selected

| Method | Trials |
|---|---|
| Production replay gate | rejected 3/3 |
| Logged-propensity (slate) IPS | considered and rejected 3/3 (wVmAykK computed it: 24 matches) |
| Weight = K | a8zVL7h, wVmAykK |
| Per-slot replay without propensity | none |
| Each serve as a decision | wVmAykK (and in `decisions.csv` for ykNY8fD) |
| First serve only | ykNY8fD |
| Item-anywhere credit | rejected 3/3 |
| Target slates before rules filtering | none (inherited filter-aware helper) |
| Clipped IPS / direct method only | none |
| Identical-slate merging / session-only grouping | none |
| Other | a8zVL7h: TTL gap from the previous serve; ykNY8fD: unpaired lift intervals |

## 8. Hypothesis search

| Hypothesis | Considered | Tested | Revisited |
|---|---|---|---|
| Replay-selection bias | 3/3 | 3/3 (by replacing the estimator) | — |
| Propensity semantics | 1/3 (ykNY8fD); a8zVL7h checked the logged formula only | ykNY8fD counted eligible titles | no |
| Slate-IPS variance | 2/3 | wVmAykK (24 exact matches) | — |
| A/B test defect | 0/3 | — | — |
| Novelty effect | 0/3 | — | — |
| Cache inflation | 0/3 as a gate-bias hypothesis | — | — |
| Device mix | 0/3 | — | — |
| Exploration representativeness | 2/3 (wVmAykK, ykNY8fD) | no | no |

- **Why AB-1182 was never questioned:** all three accepted it as ground truth for v7's sign, and its sample-ratio
  numbers were never used.
- **Contradicting evidence:** no trial looked for evidence against its own estimate. None compared the magnitude of
  its v7 lift (−7.3% to −7.6%) with the A/B (−3.8% per response, −2.6% per member).

## 9. Intermediate plausible success

| What looked correct | What was incorrect | Diagnostic that would have exposed it | Performed? | Premature convergence? |
|---|---|---|---|---|
| v7 lift negative, matching AB-1182 (all) | values 1.2–4.3 τ off; wrong weight or grain | on-policy v6 clicks **per decision** from `prod_rank` (0.38 visible) vs IPS v6 | no (wVmAykK compared per response, see below) | yes, all three |
| wVmAykK: "IPS v6 0.305 astonishingly close to 0.2975 production" | both numbers per serve; the production number came from a fan-out join (92,222 rows > 88,170 serves) | the same comparison at decision grain; row-count sanity check | no | yes; treated as proof the estimator is "highly accurate" |
| v7_pd significant +20–21% (all) | level wrong in all; lift CI unpaired in ykNY8fD | IPS self-evaluation of the logging policy (uniform shuffle ⇒ explore mean) | no | yes |
| Tight lift intervals excluding zero | SE at the wrong unit (wVmAykK), unpaired (ykNY8fD) | paired bootstrap over decisions | no | — |
| **Correct launch on 12/12 extracts** | every value outside tolerance on at least three extracts | — | — | — |
| ykNY8fD: hidden_b values inside tolerance | dropped re-serve clicks bias all values low; the extract happened to be within 0.8 τ | decision reconstruction, then click-rate comparison between first serves and re-serves | no | — |

**The G10 lesson reproduced exactly.** A correct launch decision coexisted with wrong policy values in every trial.
The multiplicative biases (K/m inflation, re-serve dilution, first-serve truncation) scale all three policies similarly,
so the sign and ranking of the lifts survive. A decision-only grader would have scored this baseline 3/3.

## 10. Scientific validation

**Code validation.**
- All three ran the pipeline and read `policy_values.csv` and `launch.json`.
- a8zVL7h checked decision row counts.
- ykNY8fD checked for duplicate click events and self-lift = 0.

**Statistical validation.** 0/3.

| Diagnostic | Used |
|---|---|
| On-policy v6 mean at decision grain | no (wVmAykK at serve grain, fan-out) |
| On-policy v7 A/B arm mean | no |
| Effective sample size / weight normalisation (mean weight × matches = 1) | no |
| SNIPS vs IPS, DR vs IPS | no |
| Self-policy / A/A (evaluate the uniform logger by IPS) | no |
| Position-stratified checks | no |
| Overlap / support | no (implicitly fine) |
| Reload / cache sensitivity | no |

A one-line normalisation check (Σ matches × weight / decisions ≈ 1 per slot) would have exposed weight K in two trials.

## 11. Reasoning → implementation gap

| Rule | a8zVL7h | wVmAykK | ykNY8fD |
|---|---|---|---|
| Rules layer runs after the propensity is logged | never recognised | read, never recognised | fully implemented (not validated) |
| Weight = eligible count | never recognised | never recognised | fully implemented |
| Decision = first serve + TTL from the creating serve | recognised incorrectly (anchor) | never recognised | never recognised (read the definition) |
| Clicks merged over a decision's serves | fully implemented | never recognised | never recognised |
| Paired lift uncertainty | implemented (decision level) | implemented (serve level) | recognised at the last step, omitted |
| Metric is per decision, not per response | recognised and implemented | read, not implemented | read, not implemented |

G08/G10 showed reasoned rules dropped during implementation. G24 shows this in two forms:
- **ykNY8fD's pairing:** noticed, not fixed.
- **Read but never reasoned about:** wVmAykK and ykNY8fD read the metric's decision-vs-serve definition, and wVmAykK
  read the filtering order.

## 12. Trajectory depth

| Trial | ATIF steps | Tool calls | Distinct files | Query calls | Scripts | Package edits | Pipeline runs | Agent time |
|---|---|---|---|---|---|---|---|---|
| a8zVL7h | 58 | 41 | 13 | 10 | 6 | 3 | 1 | 200 s |
| wVmAykK | 60 | 46 | 17 | 8 | 6 | 3 | 3 | 244 s |
| ykNY8fD | 70 | 42 | 17 | 11 | 1 | 3 | 2 | 258 s |

**Other counts:**
- Hypotheses tested: 1–3 per trial.
- Material hypothesis changes: one per trial (replay → exploration IPS).
- Estimator variants attempted: 1–2; wVmAykK tried slate IPS then slot IPS.
- Statistical diagnostics: 0 (1 spurious).

**Files never read by any trial:** the June IPS notebook, v6/v7 model cards, and `logging_schema` re-serve details
beyond the table. a8zVL7h and ykNY8fD never read a gate report.

**Why each trial ended:** all three by **D, premature confidence after plausible output.** The trigger was the same in
each: the v7 lift turned negative, "aligning with AB-1182", followed by output regeneration and a summary within 1–2
minutes. No time or implementation limit was near: 3.3–4.3 min of a 90-min budget.

## 13. Novel estimators

No new estimator was used. All three implemented slot-exact item-in-slot IPS, the accepted estimator. What varied was
the probability (K vs m) and the unit (serve / first serve / decision). Those are representation errors, not
alternative estimators. There is **no benchmark-validity problem of type E**.

## 14. Benchmark flaw audit

| Failed reward | Classification |
|---|---|
| a8zVL7h | A (action space K; TTL anchor) + C |
| wVmAykK | A (action space K; serves as decisions) + C |
| ykNY8fD | A (decision grain) + C |

**Pre-baseline risks, checked against the trajectories:**
- **`serve.py` near-recipe:** 2/3 read it, and only one derived m from it. It did not make the task cheap: the reader
  who used it still failed at L7.
- **Exploration decisions identifiable from candidate logs:** a8zVL7h and ykNY8fD used candidate presence as the
  decision marker. This is valid under the DGP (candidates are logged at the ranker run). It helped a8zVL7h reconstruct
  exploration decisions but did not produce a pass.
- **Thin separations (1.1–1.6 τ):**
  - ykNY8fD failed the visible values on v7 alone at 1.18 τ and passed hidden_b.
  - Its bias is systematic (dropped re-serve clicks are always negative), and it fails three of four extracts.
  - The exact decision table fails it independently.
  - **Classification: not a tolerance artifact (F).** This is the closest a real failure came to a value tolerance.
- **Permissive interval floor/ceiling:** the counterfactual shows ykNY8fD's *unpaired* lift intervals pass the width
  check (conservative, within 3× reference). This is lenient but statistically defensible (valid if wide); it did not
  change any reward here.
- **Decision-table strictness:** a8zVL7h with weight m would fail only because 0.4–0.9% of decisions are merged.
  - The table and the decision_id rule are documented in `docs/outputs/ope_outputs.md`, and the merge contradicts the
    documented `refresh_on_hit: false`. It is a genuine semantic error.
  - The magnitude is small and invisible in values. A maintainer who views `decisions.csv` as secondary could argue
    this is harsh. Classification: **D-adjacent, not a flaw** (documented output, genuine error). Recorded as the
    only judgement call in this baseline.
- **Process cleanup / memory:** no effect. The verifiers completed with full pytest output under 3× concurrency.
- **Hidden-regime dependence (H):** none. All failures appear on the visible extract.
- **Answer-key leakage (I):** none observed. No trial accessed `/tests`, the generator or the solution.
- **Infrastructure (J):** none.

**Reward hacking / security:** none. No attempts to modify logs, outputs or the verifier. All scratch scripts were
deleted by the agents themselves.

## 15. Comparison with G10

| | G10 | G24 |
|---|---|---|
| Broad diagnosis | 3/3 censoring | 3/3 OPE / replay bias |
| Mechanism recognition | 3/3 censoring; informative censoring mostly | 3/3 logging policy; 1/3 filtering order |
| Correct probabilistic object | 0/3 overdispersion | 1/3 propensity (1/m); 0/3 decision unit |
| Valid estimator | 0/3 | 0/3 at the correct grain (family correct 3/3) |
| Scientific validation | 0/3 | 0/3 (1 spurious) |
| Correct decision despite wrong estimands | 1 trial 8/8 actions | 3 trials, 12/12 extracts |
| Error size | 9.7–68 × tolerance | 0.8–4.3 τ |
| Closest trial after one targeted patch | still 3.4–7.2× | **passes all extracts** |
| Agent time | 4.4–12.4 min | 3.3–4.3 min |
| pass@3 | 0 | 0 |

**Which failure mode:**
- Not (1): Gemini understands OPE.
- a8zVL7h and wVmAykK are (2): they misunderstand the logged policy's action space.
- ykNY8fD is (3): policy understood, decision grain wrong.
- All three are also (7): they stop on plausible aggregate output.

**The G10 pattern generalises:**

| Stage | Result |
|---|---|
| Correct broad diagnosis | 3/3 |
| Plausible statistical method | slot IPS 3/3 |
| Invalid assumption or representation | action space 2/3, decision unit 3/3 |
| Plausible output | A/B sign 3/3, launch 12/12 |
| Insufficient scientific validation | 0/3 validated |
| Failure | 0/3 |

**Difference from G10: distance to success.** G10's errors were modelling errors that one patch could not fix. G24's
errors are representation errors that one semantic step fixes. G24 therefore measures *process reconstruction*
rather than modelling sophistication, which is what it was designed to measure.

## 16. Comparison with Task 02 and G08

- **Task 02 (0/3) and G08 (1/3).** Both are semantic-lock / point-in-time tasks where the failure was an un-investigated
  target definition.
- **G24's decision-grain failure (ykNY8fD) is the same family.** A documented definition (`home_row.md`) was read and
  not implemented.
- **G24 adds a statistical layer** (probability of the observed action) that Task 02 and G08 lack, and it failed there
  in two of three trials.
- **Horizon: G24 was the shortest yet.**

  | Task | Tool calls | Agent time |
  |---|---|---|
  | G24 | 41–46 | 200–258 s |
  | G10 | 42–46 | 266–744 s |
  | Task 02 | 49–57 | 195–278 s |
  | G08 | 55–66 | 362–467 s |

  The difficulty comes from stopping early on a sign that matches external evidence, not from horizon length.

## 17. Verdict and recommendation

- **Difficulty verdict: HARD, with a near-miss profile.**
  - 0/3, pass@3 = 0.
  - Every failure is an intended semantic trap. The closest trial is one decision-reconstruction step from a full
    pass, and one trial reached the central propensity insight.
  - With three trials the 95% upper bound on the true pass rate is still about 63%. The near-miss profile suggests a
    non-zero pass rate over more trials or stronger models. This is useful headroom, not a guaranteed floor.
- **Final-benchmark recommendation: include (statistical process reconstruction).** It complements G10 (modelling
  failure far from the answer) with a task where the failure is representation close to the answer. It covers a
  distinct domain (recommender OPE) and has no observed benchmark flaw.
- **Keep the value-level grading.** The launch decision alone would have passed all three trials.

## 18. Implications for G05, G01 and remaining candidates

1. **Grade estimands, not only decisions.** In both G10 and G24, decision outputs were right while the estimands were
   wrong. G05 (staggered DiD) and G01 (label maturity) should grade effect sizes or rates with pre-registered
   tolerances, not only the go/no-go.
2. **Use a sign-matching attractor.** In both tasks, all trials stopped the moment an estimate agreed in sign with a
   trusted external number (A/B readout, ice-cream trend). G05/G01 designs should include one piece of external
   evidence that a plausible-but-wrong estimate agrees with.
3. **Representation errors beat modelling errors for headroom and interpretability.** G24's failures are crisp and
   attributable: identical to named mutations, and one patch from passing. Prioritise designs where the trap is *which
   object* the correct method is applied to (unit, action space, time basis), e.g. G05's base-period contamination
   and G01's label-maturity window.
4. **Horizons remain short (≤ 46 calls, ≤ 12 min) across generation-3 tasks.** Length is not the lever. Evidence that
   must be *reconciled*, not merely read, is.
5. **Next step (not started):** G05 and G01 as ranked in the shortlist. No build is started by this analysis.
