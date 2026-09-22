# G38 estimand — written BEFORE any simulation

Selected-for-simulation concept (from `domain_tournament.md`, ranked #1): the **Supplier Development
Programme (SDP)** at an automotive tier-1. Suppliers whose rolling 3-month defect rate exceeds
1,500 ppm are enrolled in a 6-month SDP: a supplier-quality engineer on site, 8D, and layered audits.

## Notation
- Supplier i; calendar month t = 0..35.
- Programme launch at t = 24.
- E_it = parts received (exposure).
- D_it = defective parts found at incoming inspection or on the line.
- λ_it = the latent defect rate; D_it ~ Poisson(E_it λ_it).
- t0_i = the first enrolment month; the trigger is evaluated at the end of month t0_i − 1.
- λ⁰ and λ¹ are the latent rates without and with SDP. The population 𝒯 is suppliers enrolled in
  launch months 24–29 (first enrolment only).
- Horizon H = the 6 enrolment months t0_i … t0_i + 5.

## Graded quantities (proposed)
| id | formula | population | time zero | horizon | weighting | units | business meaning |
|---|---|---|---|---|---|---|---|
| **Q1** `defects_averted_per_enrollee` | (1/\|𝒯\|) Σ_{i∈𝒯} Σ_{h=0}^{5} E_{i,t0+h}(λ⁰ − λ¹)_{i,t0+h} | suppliers enrolled in months 24–29 | first SDP month t0_i | 6 months | each enrollee once (cost is incurred per enrollee) | defective parts | what one SDP engagement buys; **decision-bearing** |
| **Q2** `relative_defect_reduction` | Σ_𝒯Σ_h E(λ⁰ − λ¹) / Σ_𝒯Σ_h E λ⁰ | same | same | same | exposure × counterfactual-rate weighted (a ratio of sums) | fraction | share of counterfactual defects the programme removed |
| **D** `expand_sdp` | "expand" iff Q1 ≥ 75 | — | — | — | — | — | **algebraically forced** by Q1 and the rollout threshold |

Q1 and Q2 are **ATT** quantities for the threshold-enrolled suppliers. They are **not** an ATE over
all suppliers, and **not** effects at the threshold (RD-local). The contract must say this in words
and in formula.

Truth (verifier only) uses the **latent expected** counts along each enrollee's realised latent path
(finite-sample ATT). The analyst sees only the counts D and exposures E.

## Why this estimand, and not a convenient one
- Q1 follows the cost structure: engineer time is billed per enrollee, and savings come per averted
  defect.
- Q2 is what the dashboard claims ("ppm fell 45 %"), made causal.
- Neither was chosen for separation. Whether each is *gradable* is decided later by the window gate
  (principle 11).
