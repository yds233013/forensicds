# Output contract - weekly rebalance

`python -m service_parts plan --warehouse <db> --out <dir>` writes two files.

## `plan.csv`
The transfer plan, one row per (from_depot, to_depot, part_id) with a positive quantity:

```csv
from_depot,to_depot,part_id,qty
NW-CEDAR,NW-DELTA,PMP-SEAL-12,6
```

Quantities are whole units. A plan must be executable under the availability policy: every unit
shipped must be available to promise at the origin, above that depot's safety stock, and must arrive
by the need-by date of a job it serves.

## `readout.json`

```json
{
  "extract_date": "<YYYY-MM-DD>",
  "demand_units": <int>,
  "total_shortfall_units": <int>,
  "shortfall_by_depot": {"<depot_id>": <int>, ...},
  "transfer_units": <int>,
  "transfer_cost": <float>,
  "expedite_recommendation": "expedite" | "no_expedite"
}
```

- `demand_units` - total units required by scheduled jobs in the extract.
- `total_shortfall_units` - the minimum achievable unmet units for the week.
- `shortfall_by_depot` - unmet units by the depot that owns the job; only depots with a shortfall.
  These must sum to `total_shortfall_units`.
- `transfer_units`, `transfer_cost` - units moved and their cost under `plan.csv`, which must be the
  cheapest plan that achieves `total_shortfall_units`.
- `expedite_recommendation` - from the expedite rule in the availability policy.
