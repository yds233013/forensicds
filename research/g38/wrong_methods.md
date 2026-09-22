# Wrong-method panel (R1): 29 implemented, 26 wrong + 3 labelled ambiguous before scoring

Classes follow the brief's W1–W25:

| class | methods |
|---|---|
| treated pre/post | W01 |
| dashboard | W02 |
| average pre/post | W03 |
| exclude the trigger window | W04, W04b |
| DiD / event study | W05, W06, W07 |
| matching on trigger value | W08 |
| raw counts | W12 |
| wrong Q2 weighting | W13 |
| no measurement-noise handling | W14 |
| over-shrinkage / population mean | W15 |
| no seasonality | W16, W22 |
| wrong time zero | W17 |
| future information | W18 |
| treated-trend extrapolation | W20 |
| iid transients | W21 |
| wrong population | W23 |
| hyperparameters contaminated by treated months | W24 |
| wrong ρ | W26 |
| shrink without persistence | W28 |

- **Ambiguous** (pre-labelled): W09 historical S-matching, W11 RD extrapolation, W27 GLM on all
  unit-months.
- **Not implemented, with reasons:**
  - W19 survivor-only: the DGP has no exits;
  - W21-brief (wrong uncertainty): not a point estimate, and uncertainty is not graded;
  - W24-brief (trigger-rule inversion): not a plausible analysis;
  - W22/W23-brief (decision proxies) are in `cheap_solve.md`;
  - the verbatim duplicate W25 (= W07) was deleted before the run.

Full results are in `sim/g38_R1_supplier.json`, and the per-method table in `counterexample_search.md`.

**Only W15 (fleet-average counterfactual, detect 18.1) and W18 (future information, 4.0) are
separable at all.** Every other wrong method has detect ≤ 0.82 on its second-best fixture.
