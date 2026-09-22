# Cheap-solve panel (existing results only; no new simulation was permitted)

| proxy | result |
|---|---|
| constant "expand" | correct on 3/5 fixtures (visible, b, c) |
| constant "hold" | correct on 2/5 (a, d) |
| sign of the observed pre/post change / dashboard (W01) | decision correct 100 / 10 / 99 / 100 / 96 %. Fails the pure-RTM fixture, succeeds elsewhere |
| company dashboard % (W02) | same decision profile |
| post-treatment raw rate / long-run historical mean | W03 / W10 decision rates in `counterexample_search.md` |
| number of treated units | 84 / 101 / 85 / 115 / 114 vs decision expand / hold / expand / expand / hold: not monotone, no proxy |
| trigger severity, file names, row counts, fixture identity, simple correlations | **not evaluated.** New simulation was prohibited, and the task was not built, so there are no files |

The dashboard proxy gets 4/5 decisions right. **In a built task it would have to be defeated by the
continuous quantity, which cannot be graded.** This is a further reason the design fails.
