# Marketplace Analytics workspace

`dispatch_experiment/` produces the readout for the priority-dispatch pilot.

```
cd /workspace && python -m dispatch_experiment analyse --warehouse data/warehouse.sqlite --out out
```

- `data/warehouse.sqlite` - the pilot extract. Read only; it is the system of record.
- `docs/` - experiment design note, dispatch runbook, the FY27 rollout proposal, event dictionary.
- `docs/outputs/analysis_contract.md` - the exact shape of `out/analysis_results.json`.
- `reports/priority_dispatch_pilot_readout.md` - the readout currently circulating.
