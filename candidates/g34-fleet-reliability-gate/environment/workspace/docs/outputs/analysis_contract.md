# Output contract — installed-base reliability run

`python -m fleet_reliability analyse --warehouse <db> --out <dir>` writes `analysis_results.json`.
Numbers are written unrounded. All rates are proportions of the installed base in the extract.

```json
{
  "horizon_months": 36,
  "installed_base_units": <int>,
  "event_counts": {"UNPL_FAIL": <int>, "PM_OVHL": <int>, "ASSET_RET": <int>, "no_work_order": <int>},
  "units_at_risk": {"12": <int>, "24": <int>, "36": <int>},
  "aftermarket": {
      "unplanned_failure_rate_36m": <float>,
      "overhaul_rate_36m": <float>,
      "retirement_rate_36m": <float>,
      "still_original_assembly_36m": <float>
  },
  "engineering": {"assembly_failure_rate_36m": <float>},
  "recommendation": "expanded" | "baseline"
}
```

- `installed_base_units` — units in the extract.
- `event_counts` — units whose work order is of each type; `no_work_order` is the remainder.
- `units_at_risk` — units still in service with their original assembly, and still inside the
  extract window, at 12 / 24 / 36 months of service age.
- `aftermarket` — the four outcomes of a unit's original assembly by 36 months of service age, as
  proportions of the installed base. They describe mutually exclusive outcomes of the same units.
- `engineering` — the quantity described in the engineering note.
- `recommendation` — from the procurement rule in the planning memo.
