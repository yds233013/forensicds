# Output contract - FY27 residential capacity readout

`python -m capacity_forecast analyse --warehouse <db> --out <dir>` writes `analysis_results.json`.
Numbers are written unrounded.

```json
{
  "n_households": <int>,
  "estate_segment_shares": {"APT_ELECTRIC": <float>, ...},
  "target_cdd_mean": <float>,
  "segment_target_peak_kw": {"APT_ELECTRIC": <float>, ...},
  "estate_tou_response_at_target_cdd": <float>,
  "target_peak_kw": <float>,
  "procurement_decision": "procure" | "defer"
}
```

- `n_households` - residential premises in the extract.
- `estate_segment_shares` - share of the estate in each segment.
- `target_cdd_mean` - mean forecast cooling degree days across the target season.
- `segment_target_peak_kw` - per-segment mean peak-window kW expected in the target season, with
  every customer on the time-of-use tariff.
- `estate_tou_response_at_target_cdd` - the estate-wide fractional reduction in peak-window load
  attributable to the tariff, at the target season's mean cooling degree days. A proportion, so
  0.08 means eight per cent.
- `target_peak_kw` - **the headline figure.** Mean peak-window kW per residential customer expected
  in the target season, with every customer on the tariff, under the forecast weather.
- `procurement_decision` - from the capacity ceiling in `reports/fy27_capacity_memo.md`.
