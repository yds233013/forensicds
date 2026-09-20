# Output contract - priority-dispatch readout

`python -m dispatch_experiment analyse --warehouse <db> --out <dir>` writes `analysis_results.json`.
Numbers are written unrounded. All effects are in **fulfilment-rate points** (a proportion, so 0.02
means two percentage points) and are demand weighted: orders, not merchants, are the unit the
business counts.

```json
{
  "n_dispatch_blocks": <int>,
  "n_merchant_days": <int>,
  "orders_requested_total": <int>,
  "blocks_by_saturation": {"0.00": <int>, "0.25": <int>, "0.50": <int>, "0.75": <int>, "1.00": <int>},
  "effects": {
      "direct_effect_50": <float>,
      "spillover_50": <float>,
      "policy_effect_full": <float>
  },
  "recommendation": "launch" | "hold"
}
```

- `n_dispatch_blocks` - dispatch pools in the extract.
- `n_merchant_days` - merchant-by-service-date rows.
- `orders_requested_total` - total orders customers placed.
- `blocks_by_saturation` - pools per assigned saturation, keyed to two decimal places.
- `effects.direct_effect_50` - the difference in fulfilment between merchants **with** priority and
  merchants **without** it, among pools assigned **50%** saturation.
- `effects.spillover_50` - the difference in fulfilment for merchants **without** priority between
  pools assigned 50% saturation and pools assigned 0%.
- `effects.policy_effect_full` - the change in fulfilment for the marketplace under the **proposed
  FY27 rollout** described in `docs/fy27_rollout_proposal.md`, relative to no merchant having the
  feature.
- `recommendation` - from the commitment gate in the rollout proposal.

These three effects are different quantities and are expected to differ.
