# Readout output contract (Finance, SCO 2.0 tranche 2)

`python -m sco_readout gate --warehouse <db> --out <dir>` writes two files. Numbers are written unrounded.

## `analysis_panel.csv`

One row per row of `kpi_store_week` (every store and week in the extract).

| Column | Meaning |
|---|---|
| `store_id`, `week_start` | the store-week |
| `wave` | the store's wave in the rollout plan |
| `go_live_week` | `week_start` of the store's go-live week; empty if the store is not live in the extract |
| `event_week` | weeks from the go-live week to this week (0 in the go-live week, negative before); empty if not live |
| `comparable` | 1 if the week is a comparable trading week (`docs/kpi_handbook.md`), else 0 |
| `log_net_sales` | natural log of `net_sales` |

## `readout.json`

```json
{
  "effect_by_wave": {"1": {"estimate": 0.0, "ci_low": 0.0, "ci_high": 0.0}, "...": {}},
  "gate_effect": {"estimate": 0.0, "ci_low": 0.0, "ci_high": 0.0},
  "decision": "continue"
}
```

- `effect_by_wave`: one entry per wave that is live in the extract, keyed by wave number: that wave's stores'
  run-rate uplift in weekly net sales (`docs/finance/glossary.md`), with a 95% interval.
- `gate_effect`: the figure the tranche-2 continuation gate is evaluated on (`docs/finance/sco2_business_case.md` §3),
  with a 95% interval.
- `decision`: `continue` if `gate_effect.estimate` meets the gate's hurdle, else `stop`.

Figures are in log points.
