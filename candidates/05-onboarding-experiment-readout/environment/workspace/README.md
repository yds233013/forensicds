# xp_analysis - experiment readouts

Owner: Product Analytics. Produces the readout for product experiments from the product warehouse extract.

## Run

```
cd /workspace
python -m xp_analysis readout --config config/xp231.toml [--analysis-date YYYY-MM-DD]
```

## Outputs

| Path | Grain | Columns / fields |
|------|-------|------------------|
| `artifacts/XP-231_units.csv` | one row per analysis unit | `unit_id, stratum, arm, activated` |
| `reports/experiments/XP-231_readout_<analysis_date>.json`, `XP-231_latest.json` | one readout | `experiment_id, analysis_date, code_version, n_units_control, n_units_treatment, rate_control, rate_treatment, effect, se, ci_low, ci_high, decision, srm_p_value, strata[]` (`stratum, n_control, n_treatment, rate_control, rate_treatment, effect, weight`) |

## Layout

| Path | What |
|------|------|
| `src/xp_analysis/` | `sources` (extract readers), `units` (analysis units and outcome), `estimator` (effect, CI, SRM), `report`, `pipeline`, `cli` |
| `config/xp231.toml` | XP-231 readout parameters |
| `data/product.db` | product warehouse extract (read-only; see `docs/data/data_dictionary.md`) |
| `docs/experiments/` | experiment plans (pre-registration) |
| `docs/metrics/` | metric definitions |
| `docs/platform/` | experimentation platform: assignment, exposure logging, analysis guidance |
| `docs/ops/` | incident reports |
| `reports/experiments/` | readouts produced so far |
| `notes/`, `logs/` | stakeholder notes, run and deployment logs |
