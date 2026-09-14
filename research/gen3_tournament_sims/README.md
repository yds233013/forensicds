# Generation-3 design tournament: simulations

These are small numpy/sklearn scripts used during the adversarial design tournament
(`research/gen3_design_tournament.md`). They check the statistical claims made in `research/gen3_designs/*.md`.

- They are rough approximations, not the designs' generators. No benchmark task, model, docker image or harbor job is
  involved.
- `reviewer_*.py` were written by the three tournament reviewers.
- `independent_checks.py` re-derives three of their findings independently (G21 censoring rule, G10 profile-scaling
  bias on sell-out days, G26 activation arithmetic).

## Re-run status (2026-09-14)

| Script | Claim checked | Reproduced? |
|---|---|---|
| `independent_checks.py` | G21 "censor unresolved at spell_end" biases S(180) up (0.545 vs 0.487); as-of − 30 unbiased | yes |
| `independent_checks.py` | G10 profile-scaling (I/T) overestimates demand on sell-out days (+56% at I=4, +25% at I=8, +12% at I=15, conditional on selling out) | yes (bias larger than the reviewer's unconditional I/(I−1)) |
| `independent_checks.py` | G26 blended September activation is 34.8%, not 40.3% | yes |
| `reviewer_g05_twfe.py` (imports `reviewer_g05_sim.py`) | G05 static TWFE stays positive (+0.011…+0.022) under the stated rollout; the −2.3% symptom cannot be generated | yes |
| `reviewer_g30_se.py` | G30 cost-difference SE is $75–117 per 1,000 (≈8–10 sampled fraud-loss rows), not $38 | yes |
| `reviewer_g24.py` | G24 unpaired SE ≈ 1.08× paired SE, so an `unpaired_ci` mutation likely passes | yes |
| `reviewer_g23_tz.py` | G23 naive-UTC parsing still links 100% of forward transfers; it only breaks back-transfers (≈30% outside the 0–1 day window) | yes |
| `reviewer_g01*.py`, `reviewer_g02.py`, `reviewer_g08.py`, `reviewer_g10.py`, `reviewer_g21*.py` | per-review claims (see tournament document) | not re-run |
