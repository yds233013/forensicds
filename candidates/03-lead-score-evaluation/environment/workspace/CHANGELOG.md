# lead_eval changelog

## 2.0.3 - 2026-08-11
- `by_source` conversion rates added for the operating review.

## 2.0.0 - 2026-07-06
- Read outcomes from RevOps lifecycle v2 (`lead_lifecycle.converted_60d`) instead of joining
  `conversions` in the pipeline (RA-512).
- Evaluation population expanded to all accepted leads whose outcome window has closed; the larger
  sample gives more stable monthly metrics and per-source breakdowns (RA-512).
- Dependencies: pandas 2.2.3, scikit-learn 1.5.2.

## 1.4.2 - 2026-01-12
- Equal-count score bins break ties by `lead_id` (stable month-over-month bins).

## 1.4.0 - 2025-11-03
- `recommended_threshold` for router threshold reviews (RA-455).

## 1.0.0 - 2025-02-17
- First monthly evaluation of lsm-3.x.
