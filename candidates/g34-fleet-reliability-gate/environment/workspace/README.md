# fleet_reliability

Aftermarket Analytics' package for installed-base reliability reporting. Re-run against each
quarterly warehouse extract.

```
python -m fleet_reliability analyse --warehouse data/warehouse.sqlite --out out
```

| Path | What |
|---|---|
| `fleet_reliability/` | the analysis (`cli.py`, `history.py`, `estimate.py`, `report.py`) |
| `data/warehouse.sqlite` | the quarterly extract: asset register, work orders, telemetry status |
| `docs/` | maintenance SOP, event dictionary, the planning memo, Engineering's note, the output contract |
| `reports/` | the last published run |
| `out/` | where a run writes `analysis_results.json` |

The extract is the system of record. Do not edit it.
