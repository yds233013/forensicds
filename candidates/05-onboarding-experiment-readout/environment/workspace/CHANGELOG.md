# xp_analysis changelog

## 3.1.0 - 2026-08-10
- Sample ratio check added to readouts (`srm_p_value`); logs a warning below 0.001 rather than failing the
  readout, because exposure-based unit counts drift with client logging (XPP-19).

## 3.0.0 - 2026-06-15
- Exposure-triggered analysis (XPP-12). Analysis units are the users with a logged exposure, in the arm they
  were exposed to; activation is measured from first exposure. Removes dilution from units that never saw the
  experience and increases sample size.

## 2.4.0 - 2026-03-02
- Stratified difference in proportions with Neyman variance (XPP-7).

## 2.0.0 - 2025-11-17
- Readouts follow per-experiment plans in `docs/experiments/`.
