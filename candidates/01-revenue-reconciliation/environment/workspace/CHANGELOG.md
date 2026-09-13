# revrec changelog

## 3.4.1 - 2026-08-26
- dashboard: add `top_accounts_latest_period.csv` extract for the exec account tile.
- dashboard: `mom_change_pct` rounded to 2 dp.

## 3.4.0 - 2026-08-18
- recognition: vectorized ratable schedule expansion (numpy repeat instead of a
  per-line Python loop). Nightly run time 1.9s -> 0.3s. Allocation logic unchanged;
  schedule output compared row-for-row against 3.3.2 on the July extract.

## 3.3.2 - 2026-07-09
- fx: read monthly average rates from billing `fx_rates` (treasury feed) instead
  of the static `fx_rates.csv` maintained by FP&A.

## 3.3.0 - 2026-04-02
- checks: data quality gates before publish (account populated, FX coverage,
  segments, period coverage). Pipeline fails instead of publishing partial data.

## 3.2.0 - 2026-03-03
- accounts: report migrated accounts under their successor account (first
  entity transfers went live 2026-02-01).

## 3.1.0 - 2025-12-01
- accounts: attribute revenue using the CRM account record history, taking the
  record in effect at the end of each revenue month, so segment and region
  reflect the period being reported.

## 3.0.0 - 2025-09-08
- Rebuilt on the new billing platform extracts (billing go-live 2025-09-01).
- Ratable daily recognition over service periods; credit notes in issue month.
