# fcaccuracy: forecast accuracy mart

Trading Analytics' forecast accuracy mart. It builds the evaluation examples, monthly KPI and model head-to-head
that feed the monthly forecast accuracy pack and the desk scorecard.

```
python -m fcaccuracy build --as-of 2026-09-22T06:00:00Z     # writes out/accuracy/
```

`--as-of` is the UTC instant the mart is built for (the nightly job passes its start time). Options: `--db`
(default `data/warehouse.sqlite`), `--out` (default `out/accuracy`).

## Layout

| Path | What |
|---|---|
| `fcaccuracy/` | the mart (`cli.py`, `warehouse.py`, `mart.py`, `kpi.py`, `outputs.py`) |
| `sql/accuracy_examples.sql` | example query used by `mart.py` |
| `data/warehouse.sqlite` | warehouse extract (settlement, forecasts, portfolios, models, KPI close log) |
| `docs/mart/accuracy_mart.md` | output specification |
| `docs/kpi/`, `docs/finance/` | KPI definition, scorecard policy, retired Billing feeds |
| `docs/settlement/` | how settlement volumes are published |
| `docs/trading/`, `docs/forecasting/`, `docs/models/` | day-ahead process, forecast store, model notes |
| `docs/data/data_dictionary.md` | warehouse tables and views |
| `docs/portfolio/` | portfolio restructures |
| `notebooks/kpi_pack_legacy.ipynb` | the notebook that produced packs until June 2026 |
| `reports/` | signed-off packs, the September accuracy review, ops dashboard |
| `notes/`, `ops/` | team thread, settlement incidents |
| `RELEASES.md` | mart release notes |

Python 3.12 with pandas; no network access is needed.
