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
| 06 usage statement close | event time / processing time / revisions / adjustments | built, pre-baseline validated (Oracle 1, Nop 0, 29/29 mutations, harbor check 11/11, independent review + fixes) | not run (awaiting review) | UNKNOWN | UNKNOWN (pre-baseline reviewer estimate: may be passable by strong models; batch history is a backtest key) | undecided |
| 07 shared-cluster cost allocation | many-to-many allocation | designed; redesign required before build | UNKNOWN | UNKNOWN | UNKNOWN | undecided |
| 08 processor API version change | external source-contract change | designed; revisions required before build | UNKNOWN | UNKNOWN | UNKNOWN | undecided |
| 09 conversion mix shift | negative control (no pipeline bug) | designed; to be replaced by twin-incident design | UNKNOWN | UNKNOWN | UNKNOWN | undecided |

## Notes

- **Development-only status.** Tasks marked "pilot/development only" remain in the repository with their full validation
  and baseline records. They can still serve as easy anchors if the final benchmark wants a calibration floor.
- **Headroom arithmetic.** With four of five current candidates at pass@3 = 1, adding tasks cannot bring the current five
  under target. The final set must be selected from a deeper pool.
- **Contamination.** Tasks 01–05 have been run once with Gemini 3 Flash. Any future changes to them would create new
  task versions that need new uncontaminated baselines. No such changes are planned.
