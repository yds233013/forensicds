# recs_eval: home-row ranking evaluation

The offline evaluation the Personalisation team runs before a ranker launch.

```
python -m recs_eval ope --logs data/logs.sqlite --out out/ope
```

## Layout

| Path | What |
|---|---|
| `recs_eval/` | the evaluation (`cli.py`, `logs.py`, `replay.py`, `metrics.py`, `report.py`) |
| `data/logs.sqlite` | home-row log extract (`rec_serves`, `rec_candidates`, `click_events`, `items`) |
| `serving/` | extract of the serving path and its configuration |
| `docs/data/logging_schema.md` | log tables and fields |
| `docs/metrics/home_row.md` | the engagement metric and its glossary |
| `docs/outputs/ope_outputs.md` | output specification |
| `docs/launch_policy.md` | when a candidate ranker may be launched |
| `docs/models/` | ranker model cards |
| `reports/` | offline gate reports and the AB-1182 readout |
| `notebooks/` | analyst notebooks |
| `notes/` | team notes |
| `RELEASES.md` | release notes |

Python 3.12 with numpy, pandas, scipy and statsmodels installed.
