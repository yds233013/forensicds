# screen_perf

Kestrel Screening — contract performance reporting. Re-run against each quarterly warehouse extract.

```
python -m screen_perf report --warehouse data/warehouse.sqlite --out out
```

| Path | What |
|---|---|
| `screen_perf/` | the reporting tool (`cli.py`, `labels.py`, `metrics.py`, `report.py`) |
| `data/warehouse.sqlite` | the extract: transactions, reviews, the benchmark panel, contract terms |
| `docs/` | the service agreement, the review-queue SOP, the table dictionary, the output contract |
| `reports/` | the published quarterly performance report |
| `notes/` | notes from the fraud operations team |
| `out/` | where a run writes `performance.json` |

The extract is the system of record. Do not edit it.
