# Output contract — quarterly performance certificate

`python -m screen_perf report --warehouse <db> --out <dir>` writes `performance.json`:

```json
{
  "window_start": "<YYYY-MM-DD>",
  "window_end": "<YYYY-MM-DD>",
  "flagged_transactions": <int>,
  "adjudicated_sample_reviews": <int>,
  "sensitivity": <float, 6 dp>,
  "specificity": <float, 6 dp>,
  "observed_precision": <float, 6 dp>,
  "contract_precision": <float, 6 dp>,
  "decision": "accept" | "remediate"
}
```

- `flagged_transactions` — transactions the screen flagged in the window.
- `adjudicated_sample_reviews` — review cases that are part of the quality programme's sample and have
  an adjudication.
- `sensitivity`, `specificity` — the screen's detection performance on Kestrel's production traffic for
  the quarter, from the quality programme's evidence (`docs/review_queue_sop.md`).
- `observed_precision` — the share of Kestrel's own flagged transactions in the quarter that were
  adjudicated fraudulent.
- `contract_precision` — precision under clause 3.2 of the service agreement.
- `decision` — `remediate` when `contract_precision` is below `precision_floor`, otherwise `accept`.
