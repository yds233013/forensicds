# ForensicDS candidate pool and selection status

Updated: 2026-09-18.

Tasks 01–05 are **candidate/development tasks**. The final submitted benchmark (5–10 tasks, target pass@3 < 30%) will be
selected from the pool later. The selection criteria are:

- task quality
- distribution coverage
- uncontaminated baseline results
- headroom

Nothing here is a final selection. Early tasks and their results are kept as development evidence and are not rewritten.

Model: `google/gemini-3-flash-preview` via gemini-cli (Harbor 0.21.0), 3 trials per task in the diagnosis condition.
UNKNOWN means not built or not run.

| Task | Mechanism | Build status | Baseline status | pass@3 | Difficulty verdict | Likely final-set role |
|---|---|---|---|---|---|---|
| 01 revenue reconciliation | entity grain / identity | built, validated (harbor check did not complete at the time) | run (2/3) | 1 | USEFUL EASY ANCHOR | easy anchor (undecided) |
| 02 renewal-risk regression | temporal leakage / point-in-time | built, validated | run (0/3); explicit-invariant ablation 0/3 (confounded) | 0 | DIFFICULT BUT INFORMATIVE | likely include |
| 03 lead-score evaluation | evaluation population / selective labels | built, validated, sandboxed verifier | run (3/3) | 1 | TOO EASY | pilot/development only |
| 04 retention metrics | KPI lifecycle semantics / trusted-number attractor | built, validated, sandboxed verifier | run (1/3) | 1 | USEFUL EASY ANCHOR (attractor risk) | undecided |
| 05 experiment readout | randomization unit / exposure | built, validated, sandboxed verifier | run (3/3) | 1 | TOO EASY | pilot/development only |
| 06 usage statement close | event time / processing time / revisions / adjustments | built, pre-baseline validated (Oracle 1, Nop 0, 29/29 mutations, harbor check 11/11) | run (3/3) | 1 | TOO EASY (close cutoff inherited from faulty code; designed attractors never engaged) | pilot/development only (possible easy anchor) |
| 07 shared-cluster cost allocation | many-to-many allocation | designed; redesign required before build | UNKNOWN | UNKNOWN | UNKNOWN | undecided |
| 08 processor API version change | external source-contract change | designed; revisions required before build | UNKNOWN | UNKNOWN | UNKNOWN | undecided |
| 09 conversion mix shift | negative control (no pipeline bug) | designed; to be replaced by twin-incident design | UNKNOWN | UNKNOWN | UNKNOWN | undecided |

## Generation-3 shortlist

Source: `research/gen3_implementation_shortlist.md` (after `research/gen3_design_tournament.md`). S1 (G08), S2 (G24) and S4
(G10) are built and baselined. The others are designed only, and their baseline fields are UNKNOWN. Build order matches the S-number.

| Shortlist | Design | Mechanism | Build status | Baseline status | pass@3 | Expected hardness (prior) | Likely final-set role |
|---|---|---|---|---|---|---|---|
| S1 | G08 forecast vintages (built: `candidates/g08-forecast-accuracy-vintages`, frozen at e07103d) | target vintage: charge basis as known at KPI close (effective vs recorded status), UK-gate forecast lock at unit grain, effective-dated portfolios | built, pre-baseline validated (Oracle 1, Nop 0, mutations 40/40, harbor check 11/11, 2 adversarial reviews) | run (1/3: h7TpDUG 0, pXphfXM 1, wmwSU97 0; $0.96) | 1 | USEFUL MEDIUM-HARD (failures: target vintage never investigated; issue-grain lock + reasoned status rule not implemented; both stopped on plausible aggregates) | candidate (medium-hard); does not reach headroom target alone |
| S2 | G24 recommender OPE (built: `candidates/g24-recommender-ope`, frozen at checksum 2c9cc2055ef796a5, commits 2e21788/b7f1c8e) | slate/position propensities after a rules layer, cache-TTL decision grain | built, pre-baseline validated (Oracle 1, Nop 0, mutations 30/30, harbor check 11/11, clean checkout, adversarial + statistical-validity reviews) | run (0/3: a8zVL7h 0, wVmAykK 0, ykNY8fD 0; $0.51) | 0 | HARD, near-miss (all chose slot-exact IPS; 2/3 weighted by pre-filter pool K, 3/3 wrong decision unit; all stopped when v7's sign matched AB-1182; launch correct on 12/12 extracts with values 0.8-4.3 tau off; closest trial derived 1/m and passes all extracts after one TTL-grouping patch) | recommend include (statistical process reconstruction) |
| S3 | G23 readmission episodes | episode grain across facility vocabularies | designed; fixes required | UNKNOWN | UNKNOWN | MEDIUM | undecided |
| S4 | G10 censored demand (built: `candidates/g10-censored-demand`, frozen at checksum 047195e7a12d34cd, commits 3efed5c/ffbe949) | stopping-time censoring, latent demand, informative censoring | built, pre-baseline validated (Oracle 1, Nop 0, mutations 33/33, harbor check 11/11, pre-registered tolerance recalibration, adversarial + statistical-validity reviews) | run (0/3: LhEU3ny 0, cLtM9yi 0, eMXZbBi 0; $0.58) | 0 | FRONTIER-HARD (all diagnosed censoring and selection bias; none modelled the latent day shock or validated assumptions; forecast imputation / Poisson plug-in / per-day scaling; all stopped on a plausible ice-cream trend; one trial 8/8 actions correct with lost units 24-63% low) | recommend include (frontier-hard statistical reasoning) |
| S5 | G11 training–serving skew | multi-feature serving semantics + embedded negative control | designed; scope cut; gated on S1 baseline | UNKNOWN | UNKNOWN | HARD | undecided |
| S6 | G05 staggered rollout DiD (built: `candidates/g05-sco-rollout-gate`, frozen at checksum 77a6e432d9d2cba2, commits a13a1a3/2fc7e5e/f7ba34b/0b86b03) | continuation-gate estimand: outcome choice, population transport by treatment version, format-conditional trends, install-closure time zero | built, pre-baseline validated (Oracle 1, Nop 0, mutations 38/38, harbor check 11/11, clean clone, phase-0 gate rounds 1-6 with round 5 failed and recorded, 2 independent reviews) | **run, COMPLETE (0/3 over three VALID trials: MMGNYFS 0, PYhR2eh 0, rsDKTXQ 0; $0.4910 valid-baseline spend). JnK5hsR excluded as an invalid infrastructure trial (verifier never executed); one authorised replacement was run after adjudication** | 0 | HARD, confirmed (3/3 reconstructed the panel exactly on 4/4 extracts and fixed the outcome; 0/3 conditioned on format; 0/3 falsified their own specification; 2/3 correct decision on wrong values) | **recommend include** (causal identification) |
| S7 | G25 search judgment pool | measurement repair under incomplete, heterogeneous labels | **design gate GO, Phase-0 STOPPED** (`research/g25/G25_design_gate.md`) | UNKNOWN | UNKNOWN | blocked: condensed lists (the headline attractor) pass 7/10 worlds; metric levels not gradeable at useful precision | blocked; three options recorded |
| S8 | G01 collections label maturity | label maturity x observation process x policy feedback | **design gate: REDESIGN specified, Phase-0 stopped** (`research/g01/G01_design_gate.md`) | UNKNOWN | UNKNOWN | HARD but blocked: graded statistics do not separate the population errors without restoring the G24-duplicating IPW layer | blocked; three options recorded for the maintainer |

Alternates: G17, G21, G20.

G08 baseline analysis: `research/g08/g08_gemini_analysis.md` (horizon only modestly longer than Task 02; G11 gate not met, so G11 is not built next).

G10 baseline analysis: `research/g10/g10_gemini_analysis.md`:
- 0/3, pass@3 = 0, frontier-hard.
- Failures come after correct diagnosis: statistical-model errors at 9.7–68× tolerance.
- The horizon was shorter than Task 02 or G08 (42–46 tool calls).
- An overdispersion-only counterfactual on the closest trial still fails at 3.4–7.2×.
- Implication: prioritise statistical-inference candidates (S2 G24, S6 G05, S8 G01) over semantic-lock variants; do not
  build G11.

G24 baseline analysis: `research/g24/g24_gemini_analysis.md`:
- 0/3, pass@3 = 0, hard with a near-miss profile.
- All three recognised OPE and implemented the accepted estimator family, then applied it to the wrong object (action
  space K in two trials, decision unit in all three).
- All stopped when v7's lift sign matched AB-1182. Launch was correct on 12/12 extracts while values were wrong, so a
  decision-only grader would have passed every trial.
- The closest trial passes every extract after one decision-reconstruction patch.
- Shortest horizon so far (41–46 tool calls, 3.3–4.3 min).
- Implication: grade estimands (not only decisions) in G05/G01, and include a sign-matching external attractor.

G05 pre-baseline validation: `report/g05_prebaseline_validation.md`:
- frozen at 77a6e432d9d2cba2; no model has been run on it.
- Phase-0 calibration took 6 rounds; round 5 failed its accepted-estimator criterion and is recorded in full.
- Seven structurally different valid estimators pass every extract (imputation and 2x2 designs, three conditioning
  sets, two control pools, four base-period choices).
- 38-case mutation suite: every wrong causal analysis fails, including four "correct method, wrong object" cases that
  keep the right business decision.
- Known residual risk: kit-conditioned DiD separates at 98.3% against the pre-registered 99% bar (fails all four
  frozen extracts deterministically). **Adjudicated 2026-09-18** (`research/g05/G05_O1_adjudication.md`): Option A —
  keep G05 frozen as-is, keep the criterion as pre-registered, record the miss. A >=99% rule is not resolvable at
  n=60 worlds per regime, and the improved criterion (analytic invalidity + joint pass probability + deterministic
  failure on the shipped extracts) is to be pre-registered for the *next* gate, not applied retroactively.

## Model-cost accounting (corrected 2026-09-18)

`harbor check` is a model run: it invokes `claude-code` / `claude-sonnet-4-6` by default and costs ~$0.2-0.6 per
invocation. Several reports claimed "no model was run / $0 model spend" for validation phases that included a check;
those statements were corrected in `report/g05_`, `g08_`, `g10_` and `g24_prebaseline_validation.md` and in
`research/overnight_2026-09-17.md`. Total recorded check spend across the project: **$7.604092** over 16 jobs.
Baselines remain uncontaminated - the check agent audits task quality and is given the solution and tests
deliberately; it never attempts a solution. Protocol: `research/harbor_check_protocol.md`.

G05 baseline analysis: `research/g05/G05_gemini_baseline_analysis.md` (§14 is the final record), trials in
`research/g05/g05_trials.csv`:
- **COMPLETE. 0/3 over three valid trials; pass@3 = 0.** Valid trials: MMGNYFS, PYhR2eh, rsDKTXQ. No further Gemini
  run will be made on G05.
- Chronology: the first run attempted 3 trials; JnK5hsR's verifier failed before grading and was adjudicated
  **(B) INVALID INFRASTRUCTURE FAILURE, MEDIUM** (`research/g05/G05_JnK5hsR_validity_forensics.md`, commit 939f1cd)
  **before** exactly one replacement (rsDKTXQ) was authorised and run. No benchmark modification occurred at any
  point; the replacement ran against the identical frozen checksum. JnK5hsR is qualitative evidence only.
- **All three valid trials reconstructed the analysis panel exactly on all four extracts** (actual go-live,
  event-time origin, comparability, log net sales) and all three fixed the outcome to net sales.
- **0/3 discovered format sequencing; 0/3 conditioned on format; 0/3 falsified their own specification.**
- **2/3 reached the correct business decision with the underlying quantities wrong (F10).** Decision-only grading
  would have scored this baseline 2/3 instead of 0/3.
- New mechanism in rsDKTXQ: it considered kit transport, called it "essential", then chose the pooled
  installed-estate effect because the decision was "stop" either way and that was "safe" - a wrong estimand chosen
  *because the decision was insensitive to it*. MULTI-PATCH failure; the other two are one-patch near misses.
- The designed attractors (+8.0%/+5.5% basket, +6.7% TWFE) were bypassed by every trial. Difficulty is real but not
  where the design predicted, and the "agrees with a trusted external number" link seen in G08/G10/G24 is absent -
  replaced by self-consistency and defensibility.
- Gemini spend: $0.49097560 official valid baseline; $0.60094955 including the invalid attempt. Validation-model
  spend ($0.52425255, harbor check) is a separate category.
- Measured-set arithmetic: {02, G05, G10, G24} = 0/4; {02, G05, G08, G10, G24} = **1/5 = 20%**, below the <30%
  target on 15 valid trials; adding an easy anchor pushes it to 2/6 = 33%.

G25 design gate: `research/g25/G25_design_gate.md` - GO at design, stopped at Phase 0 after three iterations. The
frame-restriction trap reached the required 2.5 tau, but condensed lists are not materially biased at k=10 and the
metric levels carry audit sampling error common to every valid estimator.

G01 design gate: `research/g01/G01_design_gate.md` - stopped before implementation. Two Phase-0 iterations showed the
business decision is insensitive to the population errors (max-coverage watermark, empirical lag, contiguous coverage,
label-determined population, excluding the acquired book all reproduce the correct status). Restoring statistical
content means restoring the holdout/IPW layer, which duplicates G24.

- Not shortlisted: G02, G14 and G30 (WEAK); G26 (REJECT as a headroom task; its idea is embedded in S5).
- The earlier Task 07–09 designs are not being built. The G26 tournament result supersedes the Task 09
  twin-incident replacement idea.

## Notes

- **Development-only status.** Tasks marked "pilot/development only" remain in the repository with their full validation
  and baseline records. They can still serve as easy anchors if the final benchmark wants a calibration floor.
- **Headroom arithmetic.** With four of five current candidates at pass@3 = 1, adding tasks cannot bring the current five
  under target. The final set must be selected from a deeper pool.
- **Contamination.** Tasks 01–05 have been run once with Gemini 3 Flash. Any future changes to them would create new
  task versions that need new uncontaminated baselines. No such changes are planned.
