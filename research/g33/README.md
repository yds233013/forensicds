# G33 — entity resolution / measurement error

**Status: research, design and simulation only. REJECTED (DROP).** No Harbor task, no `candidates/g33-*`,
no model run, no API spend.

## Question

Can a frontier data agent determine whether the observational units used by an apparently rigorous
downstream analysis correspond to the real-world entities the business decision is about?

Domain selected: **supplier / production-node identity**, with supply-node spend concentration against a
board limit as the downstream analysis.

## Outcome

**Dropped.** Three kill criteria fired on measurement:

- **K4** raw identifiers give essentially the correct metric (mean abs error 0.027 on a truth of 0.16–0.33);
- **K9** a constant decision is correct in 54/60 worlds across all five regimes;
- **K12** identity-reconstruction errors move the result by 0.6–8%, while grain errors move it by 65–78%.

The generalisable reason is in `build_recommendation.md` §2: entity error only moves a statistic that
depends on the within-entity vs between-entity decomposition — and that class of estimand is Task 01's
ground. Escaping Task 01 by choosing a concentration metric made the entity work irrelevant.

## Files

| File | Contents |
|---|---|
| `domain_comparison.md` | eight domains × eleven criteria; why supplier identity won and B2B SaaS was eliminated on sight |
| `design.md` | incident, latent entity, identifier and relationship types, temporal identity model, estimand, invariant, ambiguity policy, 3 valid families, 11 wrong methods, cheap-solve panel |
| `simulation_results.md` | statistical gate, five diagnostics, representation-leakage audit, cheap-solve results |
| `adversarial_review.md` | hostile review by reasoning and code — **no model call**, per the brief |
| `cross_task_matrix.md` | S0–S9 placement across Task 01/02, G08, G10, G24, G05, G31, G33 |
| `build_recommendation.md` | the DROP decision, the generalisable finding, and the preconditions for any revival |
| `simulation.py`, `methods.py` | generator; valid/wrong/cheap methods |
