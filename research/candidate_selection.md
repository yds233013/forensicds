# ForensicDS candidate pool and selection status

Updated: 2026-09-16.

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
| S6 | G05 staggered rollout DiD | base-period contamination, trade-area confounding | designed; symptom rework + Phase-0 margins | UNKNOWN | UNKNOWN | MEDIUM-HARD | undecided |
| S7 | G25 search judgment pool | label identity/scale reconciliation, audit frame | designed; fixes + Phase-0 margins | UNKNOWN | UNKNOWN | MEDIUM-HARD | undecided |
| S8 | G01 collections label maturity | label maturity × value date × source completeness | designed; policy layer reduced; Phase-0 margins | UNKNOWN | UNKNOWN | HARD | undecided |

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
