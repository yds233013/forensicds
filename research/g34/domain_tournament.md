# G34 domain and core tournament

## Domain scores

| Domain | Survival used in industry | Natural censoring | Competing events | Clear event def. | Defensible truth | Distinct from our tasks | Verdict |
|---|---|---|---|---|---|---|---|
| A. B2B SaaS churn | partly (renewals are discrete) | weak | weak | contested | medium | overlaps Task 04 | out |
| **B. Industrial equipment failure** | **yes (reliability engineering)** | **strong** | **strong (planned overhaul)** | **strong** | **strong** | **strong** | **selected** |
| C. Loan default / prepayment | yes | strong | **strong (prepayment)** | strong | medium | medium | runner-up |
| D. Marketplace seller attrition | rarely | medium | weak | fuzzy | weak | medium | out |
| E. Employee attrition | yes | medium | medium | contested | weak | medium | out |
| F. Insurance claim closure | yes | medium | weak | medium | medium | medium | out |
| G. Patient readmission | yes | strong | strong (death) | strong | medium | sensitive; overlaps G23 | out |
| H. Logistics delivery failure | rarely | weak | weak | strong | strong | weak | out |

B was selected over C because equipment maintenance gives a **decision that genuinely requires a
survival quantity** (extend the overhaul interval) and because the competing event (planned
overhaul) is under the firm's own control, which is what makes the crude-vs-net distinction
operationally real rather than academic.

## Hard-core tournament (paper stage)

| Core | Operationally natural? | Identifiable? | Shortcut risk | Distinct? | Taken forward |
|---|---|---|---|---|---|
| A. wrong time origin | **yes** — monitoring go-live vs commissioning | yes | medium | overlaps Task 02 | yes (as support) |
| B. wrong risk set | yes | yes | medium | medium | yes (as support) |
| **C. competing risks (crude vs net)** | **yes** — overhaul removes units before failure | **yes** | **low** | **strong** | **tested last; strongest** |
| D. informative censoring | yes (condition-based maintenance) | **NO — destroys the estimand** | — | collapses to G31 | rejected on test |
| E. left truncation / delayed entry | yes | yes | low | strong | **tested; inert** |
| F. recurrent events | yes | yes | medium | medium | not taken |
| G. time-varying exposure | yes | needs causal assumptions | medium | collapses to G05 | rejected |
| H. calendar vs duration time | yes | yes | medium | medium | not taken |
| I. immortal-time bias | yes | yes | low | medium | not taken |
| J. competing churn definitions | weak here | n/a | high | weak | rejected |

The tournament took **E (left truncation)** forward as the core, with A and B as support. That was
the wrong call, and the simulation said so: see `simulation_results.md`.
