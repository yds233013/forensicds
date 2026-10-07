# G50 — Northline Boost rollout

A two-sided delivery marketplace randomised a courier incentive per order. The order-level arm contrast is
technically correct and answers a different question from the one the rollout decision is written on, because
the incentive acts through a courier pool the two arms share.

- Generator: `environment/build/world.py` (also shipped to the verifier as `tests/world.py`).
- Graded extracts: `tests/scenarios.py` — visible plus hidden_a/b/c.
- Incumbent analysis: `environment/workspace/northline_eval/`.
- Reference solution: `solution/`.

Latent truth is produced by counterfactual re-simulation of the same market-hours, not by a reference
estimator.
