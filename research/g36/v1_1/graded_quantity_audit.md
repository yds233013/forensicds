# IGQA for the v1.1 response (`estate_tou_response_at_target_cdd`)

**(1) Computational independence: PASS.**
- Truth A: the verifier path through `world._load_expected` (with and without tariff), aggregated by estate shares.
- Truth B: written from the contract text alone. The generator parameters are reimplemented with no
  imported helper, and the result is `(L0 − L1)/L0` at the target mean CDD.

| fixture | A | B |
|---|---|---|
| visible | 0.0763716529 | 0.0763716529 |
| hidden_a | 0.0534018673 | 0.0534018673 |
| hidden_b | 0.1713685284 | 0.1713685284 |
| hidden_c | 0.0531190986 | 0.0531190986 |
| hidden_d | 0.1119853131 | 0.1119853131 |

The maximum disagreement is about 1e-16. The estimator is checked the same way: route A (load ratio)
vs route B (absolute kW reduction ÷ baseline) differ by 2.4e-16.

**(2) Semantic independence: PASS**, with a caveat. The contract reading "fractional reduction in
peak-window load … at the target season's mean CDD" yields R_load. The one competing reading the audit
lists, R_season (season-average), is excluded by the contract's stated evaluation point. It remains
domain-coherent, and its treatment turns out to matter for calibration (`tolerance_calibration.md`).
