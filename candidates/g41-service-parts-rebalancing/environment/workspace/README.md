# service_parts

Field Service planning tool for the weekly spare-parts rebalance. Re-run against each weekly warehouse
extract.

```
python -m service_parts plan --warehouse data/warehouse.sqlite --out out
```

| Path | What |
|---|---|
| `service_parts/` | the planner (`cli.py`, `inventory.py`, `network.py`, `report.py`) |
| `data/warehouse.sqlite` | the weekly extract: stock, allocations, inbound orders, jobs, lanes, safety stock |
| `docs/` | the parts-availability policy, the table dictionary, the output contract |
| `reports/` | last week's published rebalance readout |
| `notes/` | notes from the depots |
| `out/` | where a run writes `plan.csv` and `readout.json` |

The extract is the system of record. Do not edit it.
