# Phase 2 — the six prospective-validation candidates

Selected on design quality (scorecard), then checked against the diversity constraint. **P23 (alloy
trial, unit of inference) scores 55 and would otherwise be in this six; it is displaced by the diversity
constraint** — it shares the manufacturing domain and the inference-validity mechanism cluster with P22 —
and becomes the first task of the second wave, together with P12 (surrogate validity).

| # | task | domain | mechanism | decision |
|---|---|---|---|---|
| 1 | **P27** roster that is optimal and illegal | workforce ops / logistics | wrong feasible set + stochastic feasibility | headcount vs overtime |
| 2 | **P20** no-show model degraded by its own deployment | healthcare operations | policy feedback on the evaluation population | retrain / replace / change policy |
| 3 | **P13** limit increase that looks safe on approved accounts | consumer credit | multi-stage selection (selective labels) + performativity | programme go/no-go |
| 4 | **P22** yield drop after a gauge recalibration | discrete manufacturing | measurement-system change | supplier change vs spec recalibration |
| 5 | **P02** elasticity from the price changes we chose | grocery pricing | policy-induced (endogenous) variation | price change on 200 lines |
| 6 | **P07** margin per order once the kitchen is paid for | rapid-delivery unit economics | economic object + non-linear cost | close 12 sites or not |

---

## Coherence → falsification map (section 24)

| task | plausible wrong analysis | coherence checks it passes (L1) | robustness it may pass (L2) | discriminating test that exposes it (L3) |
|---|---|---|---|---|
| P27 | tighten the MIP, prove optimality over the modelled constraints, report a 12-driver saving with a volume sensitivity table | solver optimality certificate; all modelled constraints satisfied; ties to payroll rates | ±10 % volume sensitivity; alternative solver | **replay the roster through the payroll rules engine** (an independent implementation) → rejected on rest and consecutive-night rules; and **simulate against historical absence/peak draws** → service level breached in 18 % of weeks |
| P20 | full drift analysis (PSI/KS per feature), temporal CV showing monotone degradation, retrain and restore AUC 0.77 | drift metrics elevated; retrained model validates on a recent holdout; monitoring reconciles | retrain with different windows; different drift metrics | **evaluate on the holdback clinics** (never score-driven): AUC is still 0.77, so the model has not degraded; and the retrained model is *worse* there |
| P13 | principled reject inference (parcelling, bivariate probit with an exclusion restriction), PD calibrated and validated on the approved book | calibration and discrimination on approved accounts; score distributions align; policy versions handled | alternative reject-inference weights; different functional forms | **the random-approval stratum**: PD is materially higher, concentrated in the targeted band; and within the pilot, default rises with granted limit at fixed score (limit is not exogenous) |
| P22 | textbook SPC investigation: control charts by shift and lot, Cp/Cpk before/after, ANOVA showing a significant material-lot effect | charts in control apart from the shift; Cpk recomputes; lot means differ significantly | different chart rules; robust ANOVA | **retained reference parts** measured on both machines read ~8 µm apart, which alone moves the pass rate; and the **second, un-recalibrated CMM** shows no yield change |
| P02 | panel log-log demand model with store and week effects, promo flags, competitor control, clustered SEs | good fit; coefficient stable across FE specifications; balanced residuals | alternative controls; placebo on a non-price covariate | **the forgotten randomised price test**: elasticity is materially smaller; and splitting observational variation **by reason code** yields inconsistent "structural" elasticities |
| P07 | site-level cost regression with fixed effects → a marginal cost per order, compared with revenue and reported as the true incremental economics | ties to the site P&L; marginal cost stable; good fit | alternative functional forms; outlier handling | **estimate the cost curve either side of the courier tier boundary** — the pooled slope averages two regimes and misprices the boundary sites; and the **closed sites' catchments show demand recapture** the closure case ignores |

Note the structural property every row shares: the L1 checks are computed *inside* the wrong frame, so
they cannot fail. That is the design requirement, not an accident.

---

## Hardness analysis (section 23)

| task | consequential commitments | plausible hypotheses | evidence systems | revision after contradiction expected? | falsification requires *constructing* a diagnostic? | decision can be accidentally right? |
|---|---|---|---|---|---|---|
| P27 | 3 — the constraint set; stochastic vs expected-value feasibility; the headcount/overtime cost object | 5 | 6 (optimiser, contracts, certification register, rules engine, absence history, forecast) | yes — the re-solve changes the answer | **yes** (build the replay harness and the absence simulation) | partly: "do not cut 12" is reachable by scepticism, so the graded object is the *sustainable* headcount and the binding constraints, not the yes/no |
| P20 | 3 — the evaluation population; the outcome under treatment; the feature vintage | 5 | 5 (appointments, model registry, policy engine, call logs, backfill note) | yes — the retrain decision reverses | **yes** (construct the holdback evaluation and re-evaluate the retrained model there) | no: the naive action (retrain) is the wrong action, so a lucky decision is unlikely |
| P13 | 3 — the outcome population; the causal effect of the limit; recombination into a loss figure | 5 | 6 (decision logs, bureau vintages, random stratum, pilot, performance, policy) | yes | partly (the stratum exists; the dose-response must be constructed) | yes — with a wide enough risk appetite; mitigated by grading PD and the dose-response |
| P22 | 3 — the measurement reference; variance allocation; the material effect after correction | 5 | 5 (two CMMs, calibration certificate, reference parts, material certs, functional test) | yes — the supplier verdict reverses | no (the bridge is retrieval), but the **bias quantification** must be constructed | no: the naive action (switch supplier) is wrong |
| P02 | 3 — the source of identifying variation; the line group the decision applies to; base-price construction | 5 | 5 (price registry with reason codes, EPOS, competitor feed, randomised test, cost file) | yes | **yes** (the reason-code consistency test must be invented) | partly: the sign of the decision may survive; the graded object is the elasticity and the segment |
| P07 | 3 — allocated vs incremental; the cost non-linearity; the closure counterfactual | 5 | 6 (order logs, rosters, capacity model, site P&Ls, courier contract, two closures + one shift addition) | yes — the closure list changes | **yes** (construct the kinked cost estimate and the displacement measurement) | partly: "do not close all 12" is reachable; graded object is the per-site incremental margin and the ranked list |

Every task requires **three** consequential, dependent commitments, and in every case the wrong first
commitment makes the second and third look clean. None of the six reaches its difficulty through file
volume: the largest workspace is ~25 artefacts.

---

## Novelty against the existing five (section 22)

| task | not Task02 because | not G05 because | not G10 because | not G24 because | not G34 because |
|---|---|---|---|---|---|
| **P27** | nothing temporal or point-in-time; no features | no treatment, no identification | no censoring or latent quantity | no policy value, no logging | no time-to-event |
| **P20** | the *labels and population* are policy-induced, not the features; the correct action is **not** to rebuild the pipeline but to change the evaluation and keep the model | no staggered adoption; the contamination is caused by the model itself | no censored demand | no propensities or action space; the object is discrimination on a policy-invariant population | no competing events |
| **P13** | no as-of feature reconstruction | selection is by policy, not by rollout timing; no trends | censoring is of *labels by policy*, not of demand by stock | no logged propensity or decision unit; the object is a loss rate under a counterfactual policy | no competing risks |
| **P22** | no temporal state | no treatment effect | no latent demand | no policy evaluation | no survival object |
| **P02** | no point-in-time features | identification comes from finding *exogenous* variation, not from conditioning on trends; there is no staggered rollout | no censoring | no OPE | no competing risks |
| **P07** | no features, no leakage | no causal identification of a treatment effect | no censoring | no OPE | no survival |

The sharpest distinctions are P20 vs Task02 (policy-induced labels vs mis-timed features, and opposite
correct actions) and P13 vs G24 (policy selection vs logging policy, and a counterfactual-policy loss
rate vs a policy value).

---

## Verifier feasibility (section 26)

Common shape, inherited from the phase-1 harness: the agent leaves a runnable command; the verifier
re-runs it unprivileged on the visible extract **and three hidden extracts** from the same generator;
reward is binary on exact bookkeeping plus the scientific quantities within a calibrated tolerance plus
the decision.

| task | graded quantities | tolerance basis | why it does not overfit to one method |
|---|---|---|---|
| P27 | minimum sustainable headcount; the set of binding constraints; simulated service level; cost-optimal headcount/overtime split | headcount and binding-constraint set exact; service level to 0.1 pp from a fixed-seed simulation specified in the contract | any solver/formulation reproducing the same feasible headcount and cost passes |
| P20 | holdback AUC and lift; the treated-population decomposition; the backfill component; the retrain decision | AUC to ±0.01 from a Monte-Carlo reference; decomposition shares to ±2 pp | holdback evaluation, a policy-aware correction, or an IPW reconstruction all accepted if they reproduce the decomposition |
| P13 | PD on the eligible population; the limit dose-response slope; programme loss; go/no-go | PD to ±0.3 pp (3× the stratum's sampling SE, pre-registered); slope sign and magnitude band | the random stratum or any assumption-checked reject inference that reproduces it |
| P22 | measurement bias (µm); corrected nonconforming rate; residual lot effect; supplier decision | bias to ±1 µm; rate to ±0.3 pp | reference-part bridge or second-machine comparison |
| P02 | exogenous elasticity; the observational-exogenous gap; segment elasticities; price decision | elasticity to ±0.15 (calibrated from the test's SE) | randomised-test estimate or a valid IV landing in the band |
| P07 | incremental margin per order per site; tier-boundary effect; displacement rate; the closure list | margin to ±£0.03; displacement to ±3 pp; list exact | natural-experiment or engineering-build routes |

Two grading rules carried from the audit: **grade the quantities beneath the decision** (6 of 13 phase-1
failures had the decision right), and **never grade a stylistic choice** — only quantities that a
scientifically correct analysis must reproduce.

---

## Cheap-solve / shortcut audit (section 27)

| shortcut | P27 | P20 | P13 | P22 | P02 | P07 |
|---|---|---|---|---|---|---|
| one filter | no | no | no | no | no | no |
| one join | no | no | no | no | no | no |
| one formula | no | no | no | no | no | no |
| one doc lookup | no — contracts give constraints but not the stochastic-feasibility notion or the cost mix | no — the policy engine config reveals the holdback exists but not what to do with it | no — policy defines eligibility, not the selection correction | no — the certificate proves a recalibration happened, not its magnitude or the corrected rate | no — the registry shows reason codes; it does not identify the elasticity | no — the allocation basis doc distinguishes allocated from incremental, not the kink or displacement |
| decision-only guess | partial (scepticism gets "do not cut"), defeated by grading the sustainable headcount and binding set | no | partial, defeated by grading PD and the dose-response | no | partial, defeated by grading the elasticity | partial, defeated by grading the per-site list |
| copy a prior report | no — the prior artefacts are the wrong analyses | no | no | no | no | no |
| **residual risk** | medium: the rules engine must be discoverable but not advertised | medium: the holdback must be inferable from the policy ramp | low | low | **medium: the randomised price test is the crux and must not be signposted** | low |

Mitigations to be applied at build: the discriminating artefact is never named in the instruction, never
in a filename that states its purpose, and never in a document whose title implies "the answer is here".
It is reachable from a registry, a config or a log the agent must read for other reasons.

---

## Ambiguity audit (section 28)

| task | ambiguity risk | mitigation (in the workspace, decided before build) |
|---|---|---|
| P27 | which service level is committed; whether agency labour counts | the customer commitment and the labour policy state both; the rules engine is authoritative on compliance |
| P20 | which population the monitoring metric is defined on | the model-risk standard states that monitoring must be on a policy-invariant population **without** saying the holdback is it |
| P13 | the eligible population; the horizon of the loss estimate | credit policy defines eligibility; the committee paper states the horizon and risk appetite |
| P22 | which measurement is the specification reference | the drawing and the calibration procedure state the reference; the certificate dates the change |
| P02 | which line group and which horizon the price decision covers | the pricing policy names the group and the evaluation horizon |
| P07 | allocated vs incremental; whether displacement counts | the allocation basis document is explicit, and the investment policy states that closure cases must be net of recapture |

Rule applied throughout: **the documents fix the *question* precisely and the *answer* not at all.** Two
independent readers must derive the same estimand from the documents alone before freeze.

---

## Multiple-valid-method audit (section 25)

| task | accepted routes | how the verifier accepts them |
|---|---|---|
| P27 | MIP re-solve with the full constraint set; constraint programming; a heuristic plus a proven lower bound | grades the feasible headcount, the binding set and the simulated service level — not the algorithm |
| P20 | holdback evaluation; policy-aware IPW on treated accounts; a joint model of attendance and reminder | grades the decomposition and the decision |
| P13 | random-approval stratum; reject inference validated against it; a bounds approach (Manski-style) reported with the same decision | grades PD on the eligible population within a pre-registered band, plus the dose-response |
| P22 | reference-part bridge; second-machine comparison; a regression bridge on the overlap | grades the bias and the corrected rate |
| P02 | randomised-test estimate; IV using cost shocks; a reason-code-restricted estimate | grades the elasticity within a band and the segment pattern |
| P07 | natural-experiment cost curve; engineering build from the tier schedule; a switching-regression estimate | grades incremental margin, the tier effect and the list |

Where two legitimate routes could in principle disagree, the data-generating process is calibrated so
that their *predictions coincide within tolerance* (the phase-1 lesson from G10's mixing-family
narrowing: if two defensible families disagree materially, the task is not gradable and must be
re-specified or the disagreement must itself be the graded object, as in P02's gap).
