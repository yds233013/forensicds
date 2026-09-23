# safety_rate

HSE reporting for Meridian Industrial Services. Re-run against each monthly warehouse extract.

```
python -m safety_rate rate --warehouse data/warehouse.sqlite --out out
```

| Path | What |
|---|---|
| `safety_rate/` | the reporting tool (`cli.py`, `exposure.py`, `cases.py`, `report.py`) |
| `data/warehouse.sqlite` | the extract: sites, workers, shift entries, incident cases, contract terms |
| `docs/` | the recordable-case standard, the hours-worked policy, the table dictionary, the output contract |
| `reports/` | the published safety report for the current window |
| `notes/` | notes from the HSE leads |
| `out/` | where a run writes `readout.json` and `site_rates.csv` |

The extract is the system of record. Do not edit it.
