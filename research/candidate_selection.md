# ForensicDS candidate pool and selection status

Updated: 2026-09-14.

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

Source: `research/gen3_implementation_shortlist.md` (after `research/gen3_design_tournament.md`). S1 (G08) is built and
baselined. The others are designed only, and their baseline fields are UNKNOWN. Build order matches the S-number.

| Shortlist | Design | Mechanism | Build status | Baseline status | pass@3 | Expected hardness (prior) | Likely final-set role |
|---|---|---|---|---|---|---|---|
| S1 | G08 forecast vintages (built: `candidates/g08-forecast-accuracy-vintages`, frozen at e07103d) | target vintage: charge basis as known at KPI close (effective vs recorded status), UK-gate forecast lock at unit grain, effective-dated portfolios | built, pre-baseline validated (Oracle 1, Nop 0, mutations 40/40, harbor check 11/11, 2 adversarial reviews) | run (1/3: h7TpDUG 0, pXphfXM 1, wmwSU97 0; $0.96) | 1 | USEFUL MEDIUM-HARD (failures: target vintage never investigated; issue-grain lock + reasoned status rule not implemented; both stopped on plausible aggregates) | candidate (medium-hard); does not reach headroom target alone |
| S2 | G24 recommender OPE | slate/position propensities, decision grain | designed; fixes + Phase-0 margins | UNKNOWN | UNKNOWN | MEDIUM-HARD | undecided |
| S3 | G23 readmission episodes | episode grain across facility vocabularies | designed; fixes required | UNKNOWN | UNKNOWN | MEDIUM | undecided |
| S4 | G10 censored demand | stopping-time censoring, latent demand | designed; gated on Phase-0 tolerance pilot | UNKNOWN | UNKNOWN | HARD | undecided |
| S5 | G11 training–serving skew | multi-feature serving semantics + embedded negative control | designed; scope cut; gated on S1 baseline | UNKNOWN | UNKNOWN | HARD | undecided |
| S6 | G05 staggered rollout DiD | base-period contamination, trade-area confounding | designed; symptom rework + Phase-0 margins | UNKNOWN | UNKNOWN | MEDIUM-HARD | undecided |
| S7 | G25 search judgment pool | label identity/scale reconciliation, audit frame | designed; fixes + Phase-0 margins | UNKNOWN | UNKNOWN | MEDIUM-HARD | undecided |
| S8 | G01 collections label maturity | label maturity × value date × source completeness | designed; policy layer reduced; Phase-0 margins | UNKNOWN | UNKNOWN | HARD | undecided |

Alternates: G17, G21, G20.

G08 baseline analysis: `research/g08/g08_gemini_analysis.md` (horizon only modestly longer than Task 02; G11 gate not met, so G11 is not built next).

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
