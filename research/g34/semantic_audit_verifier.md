# G34 semantic audit B + C — verifier derivation, comparison, independent derivations

Written **after** `semantic_audit_contract_only.md` was fixed. Sources: `tests/test_reliability.py`,
`tests/scenarios.py`, `tests/world.py` (identical to `environment/build/world.py`). G34 was read only,
never modified.

## B. What the verifier grades

Truth is computed from the **latent generator** (`world.truth`) over every unit in the extract, never
from an estimator helper. Each unit has latent times t_fail (Weibull × frailty), t_ovhl (24 +
Exp(mean 7)) and t_ret (Weibull), drawn **independently**. Administrative censoring is the unit's age
at cut-off, drawn uniformly over the commissioning window.

| field | verifier truth / check | exact formula | weighting | population | horizon | events | censoring |
|---|---|---|---|---|---|---|---|
| `unplanned_failure_rate_36m` | `cif_failure_36` | #{t_fail ≤ 36, t_fail < t_ovhl, t_fail < t_ret} / N | each unit once | all N register units | 36 | first-event | none (latent; admin cut-off is irrelevant to the truth) |
| `overhaul_rate_36m` | `cif_overhaul_36` | #{t_ovhl ≤ 36 and first} / N | unit | all | 36 | first-event | latent |
| `retirement_rate_36m` | `cif_retirement_36` | #{t_ret ≤ 36 and first} / N | unit | all | 36 | first-event | latent |
| `still_original_assembly_36m` | `survival_36` | #{min(t_fail, t_ovhl, t_ret) > 36} / N | unit | all | 36 | none of the three | latent |
| `assembly_failure_rate_36m` | `q2_net_failure_36` | #{t_fail ≤ 36} / N | unit | all | 36 | failure only; overhaul and retirement **do not prevent it** (net / latent) | latent |
| tolerance | 5.0 × SE_REF (100 redraws, AJ / KM estimator RMSE) | | | | | | |
| `recommendation` | `decision` | "expanded" iff cif_failure_36 > 0.28 (strict) | | | | | |
| `installed_base_units`, `event_counts` | exact vs the DB | COUNT(*); per wo_type; remainder | | | | | |
| `units_at_risk[a]` | ±max(2, 0.5 %) | #{exit_age > a}, exit = WO date or cut-off | | | | | |
| sum of the four aftermarket outcomes | \|Σ − 1\| ≤ 0.01 | | | | | | |
| two objects (visible only) | engineering − aftermarket gap > 0.5 × true gap | | | | | | |
| integrity | DB digest; pipeline runs; determinism; schema (all five are proportions) | | | | | | |

## B. Comparison with the contract-only derivation

| quantity | contract-only (A) | verifier (B) | agree? |
|---|---|---|---|
| Q1 unplanned failure | CIF_FAIL(36) under current practice, whole register | latent first-event failure share, whole register | **YES** |
| overhaul / retirement | CIF_OVHL / CIF_RET (36) | latent first-event shares | **YES** |
| still original | all-cause survival S(36) | latent share with no event by 36 | **YES** |
| Q2 engineering | 1 − KM_FAIL(36), censoring overhaul, retirement, admin; valid under non-condition-driven removal | latent share with t_fail ≤ 36; removals drawn independently of t_fail, so KM is consistent | **YES** |
| decision | Q1 > 0.28 strict | cif_failure_36 > 0.28 | **YES** |
| population | all register units (contract), with memo "today's installed base" as prose tension | all N | **YES** (contract governs) |
| units_at_risk boundary | strict > a | strict > a, ±2 | **YES** |
| telemetry | not an exit | ignored by truth; gaps precede 55 % of failures, a lure only | **YES** |

**There are no differences to reconcile.** One design property is noted, not treated as a
difference: truth is a finite-population latent share (it includes the realised latent draws of
units censored administratively). Its sampling relation to the estimator is what SE_REF measures.

## C. Two independent derivations per core quantity

I wrote these derivations from the contract. They do not reuse the solution's `estimate.py`. Code:
`tools/g34_audit/counterexamples.py`.

- **Q1 derivation 1:** Aalen–Johansen CIF on all units.
- **Q1 derivation 2:** crude first-event share in the **complete-follow-up cohort** (units
  commissioned ≥ 36 months before cut-off). This uses no survival machinery at all.
- **Q2 derivation 1:** Kaplan–Meier, censoring overhaul, retirement and administrative end.
- **Q2 derivation 2:** Weibull MLE with censoring (parametric).
- **Q2 extras:** Nelson–Aalen and complete-cohort KM.

| fixture | Q1 truth | Q1 AJ | Q1 cohort | Q1 tol | Q2 truth | Q2 KM | Q2 Weibull | Q2 NA | Q2 cohort KM | Q2 tol |
|---|---|---|---|---|---|---|---|---|---|---|
| visible | 0.35978 | 0.35703 | 0.35727 | 0.0138 | 0.55467 | 0.54425 | 0.55054 | 0.54392 | 0.54284 | 0.0490 |
| hidden_a | 0.25232 | 0.25693 | 0.26323 | 0.0130 | 0.40110 | 0.40193 | 0.41967 | 0.40174 | 0.40690 | 0.0461 |
| hidden_b | 0.25260 | 0.25397 | 0.25000 | 0.0124 | 0.55427 | 0.54751 | 0.55797 | 0.54708 | 0.53861 | 0.0829 |
| hidden_c | 0.54841 | 0.54657 | 0.54776 | 0.0150 | 0.76591 | 0.76289 | 0.77589 | 0.76236 | 0.75956 | 0.0395 |

Every derivation is inside tolerance on every extract. The oracle's `outcome_shares` is a separate AJ
implementation. **The truth is generator-latent, not produced by any shared estimator helper, so the
G36 failure (one helper defining oracle, references and truth) cannot occur here.**
