# Resource Planning Analytics workspace

`capacity_forecast/` produces the residential peak-load readout for the FY27 capacity decision.

```
cd /workspace && python -m capacity_forecast analyse --warehouse data/warehouse.sqlite --out out
```

- `data/warehouse.sqlite` - the planning extract. Read only; it is the system of record.
- `docs/` - tariff programme note, pilot design note, load-research note, extract dictionary.
- `docs/outputs/analysis_contract.md` - the exact shape of `out/analysis_results.json`.
- `reports/` - the capacity memo and the incumbent model's backtest.
