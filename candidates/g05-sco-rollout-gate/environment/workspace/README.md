# sco_readout: store-programme readouts

Store Analytics' package for readouts of store capital programmes (ESL shelf labels in 2025, SCO 2.0 now). It is
re-run for each programme on the warehouse extract.

```
python -m sco_readout gate --warehouse data/warehouse.sqlite --out out
```

| Path | What |
|---|---|
| `sco_readout/` | the readout (`cli.py`, `panel.py`, `estimate.py`, `report.py`) |
| `data/warehouse.sqlite` | read-only extract: `stores`, `layout_survey`, `rollout_plan`, `install_log`, `store_closures`, `kpi_store_week` |
| `docs/kpi_handbook.md` | store KPI definitions |
| `docs/finance/` | SCO 2.0 business case and finance glossary |
| `docs/programmes/sco2_programme_brief.md` | what SCO 2.0 is and how it is installed |
| `docs/store_ops/` | wave planning |
| `docs/outputs/readout_contract.md` | output files |
| `reports/programme/` | programme team readouts |
| `notebooks/` | analyst notebooks |
| `notes/` | meeting notes |
| `RELEASES.md` | release notes |

Python 3.12 with numpy, pandas, scipy and statsmodels.
