# Natural-implementation-path audit (C1, D2)

Minimal edits to a planned incumbent that computes dashboard Ppk on raw station values.

| smallest plausible edit | method | detect per fixture (vis a b c d) | decision correct (vis a b c d) |
|---|---|---|---|
| none: raw post Ppk | W01 | 62.4 41.6 69.9 14.0 49.2 | 0 % 65 % 0 % 100 % 100 % |
| vendor offset / block calibration | W02 | 57.2 35.3 63.1 11.5 43.3 | 0 % 64 % 0 % 100 % 100 % |
| mean shift from the bridge | W03 | 11.9 4.2 11.8 12.0 2.5 | 7 % 99 % 48 % 100 % 100 % |
| OLS new~old | W04 | 7.9 9.3 5.2 10.7 6.5 | 6 % 100 % 71 % 100 % 100 % |
| OLS old~new, inverted | W05 | 6.7 3.8 12.8 5.6 5.7 | 100 % 86 % 100 % 0 % 19 % |
| simple ratio | W15 | 5.2 5.5 1.8 6.1 3.5 | |
| drop the old period (pre carry-over) | W21 | 0.8 17.7 0.1 37.7 14.5 | |
| reference standards only | W20 | 57.2 35.3 63.1 11.5 43.3 | |
| bridge mean difference only | = W03 | | |

**The natural path does not solve the task.** Every minimal edit fails on ≥ 2 fixtures. This gate
**passes**. The design fails later, on the counterexample and window gates.
