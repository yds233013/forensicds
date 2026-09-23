# Table dictionary — screening warehouse

| Table | Grain | Notes |
|---|---|---|
| `transactions` | one row per authorisation in the quarter | `screen_decision` is `FLAG` or `PASS`; `screen_score` is the model score |
| `reviews` | one row per review case | joins to `transactions` on `txn_id`; `review_source` says how the case was selected; `outcome` is the adjudication |
| `benchmark_panel` | one row per case in the published benchmark | a fixed case set the marketing team quotes; assembled from historical confirmed cases, deliberately case-rich |
| `contract_terms` | key/value | window, merchant, `merchant_fraud_rate`, `precision_floor`, `quality_sample_one_in`, and the permitted values of the coded columns |
