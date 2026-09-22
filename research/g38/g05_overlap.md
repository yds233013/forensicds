# G05 overlap gate

**G05's core:** staggered rollout; the parallel-trends assumption fails because of format-conditional
trends; the fix is conditioning the comparison on format and trend structure.

**G38's intended core:** treatment is selected on an **extreme realisation of the outcome process**,
so the observed pre-treatment level is a biased estimate of the counterfactual level.

## Conceptual ablation
Suppose timing were exogenous and everything else stayed the same: random suppliers enrolled at
random months, with the same effect. Then:
- the enrollees' pre-period is an unselected draw, so treated pre/post is unbiased up to seasonality;
- DiD against never-enrolled suppliers is unbiased;
- **the hard part disappears.**

This is the desired answer. It is measured in `sim/aux_audits.py` (results in the table below).

## Why DiD does not rescue it
- Shocks are **supplier-specific**, not common, so control units cannot absorb them.
- Excluding the trigger window from the pre-period does not remove the problem:
  - the first-crossing condition affects the months before the trigger;
  - the shock at t0−1 **persists** into the SDP months (ρ > 0).

The DiD variants are panel members W05/W06/W07.

## Quantitative ablation (filled from `sim/aux_audits.json`)
See the table appended below.

### Measured ablation (`sim/aux_audits.json`, 60 draws per fixture)
Bias in SE_REF units. The exogenous-timing arm keeps the same DGP and the same number of enrollees,
but enrols random suppliers in random months 24–29.

| fixture | trigger: V2 | trigger: W01 pre/post | trigger: W05 DiD | trigger: W07 DiD-excl | **exogenous: W01** | **exogenous: W05** | **exogenous: W07** |
|---|---|---|---|---|---|---|---|
| visible | +0.3 | **+2.3** | −0.7 | −1.3 | +0.1 | +0.2 | +0.2 |
| hidden_a | +0.3 | **+3.7** | −0.4 | −1.1 | +0.2 | +0.1 | +0.1 |
| hidden_b | +0.3 | +0.5 | **−2.6** | **−3.1** | +0.1 | +0.4 | +0.4 |
| hidden_c | +0.3 | −1.8 | −0.8 | −1.1 | −0.2 | 0.0 | 0.0 |
| hidden_d | +0.8 | +0.6 | −0.4 | −0.6 | −0.3 | −0.1 | 0.0 |

**Verdict: PASS (no G05 overlap).** With exogenous timing, every naive method's bias collapses to
|bias| ≤ 0.4. The difficulty is genuinely selection on an extreme realisation, not staggered-treatment
confounding. This gate passing does not rescue the task; the window gate fails.
