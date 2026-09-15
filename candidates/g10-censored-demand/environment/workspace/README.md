# demandsci: demand science review

The Demand Science team's review package. It builds the demand history planning retrains on, the category baseline
trends that feed the buy plan, and the LEAN-26 programme impact.

```
python -m demandsci review --db data/warehouse.sqlite --out out/review
```

## Layout

| Path | What |
|---|---|
| `demandsci/` | the review (`cli.py`, `warehouse.py`, `demand.py`, `trends.py`, `impact.py`, `outputs.py`) |
| `sql/availability_kpi.sql` | store operations availability KPI |
| `data/warehouse.sqlite` | warehouse extract (stores, calendar, SKUs, planogram, promotions, hourly sales, availability events, daily inventory, replenishment orders, forecasts, programme assignment) |
| `docs/outputs/review_outputs.md` | output specification |
| `docs/planning/` | buy-plan process and demand definitions |
| `docs/replenishment/`, `docs/programmes/` | how store orders are set; LEAN-26 |
| `docs/models/` | forecast model cards |
| `docs/stores/` | store operations |
| `docs/data/data_dictionary.md` | warehouse tables |
| `notebooks/` | analyst notebooks |
| `reports/` | category review, availability KPI, LEAN-26 readout |
| `notes/` | meeting notes and field notes |
| `RELEASES.md` | release notes |

Python 3.12 with numpy, pandas, scipy and statsmodels installed. No network access.
