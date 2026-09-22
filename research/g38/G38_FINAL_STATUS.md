# G38 — FINAL STATUS: CLOSED, DROP / RESEARCH-ONLY (2026-09-21)

| | |
|---|---|
| direction | regression to the mean under threshold-triggered intervention |
| status | **DROP / RESEARCH-ONLY** (external review decision) |
| candidate built | **NO** |
| Gemini | **NONE** |
| Harbor | **NONE** |
| model spend | **$0** |
| primary blocker | **NO VALID/WRONG TOLERANCE WINDOW**: R1 5.67 / 0.02, R2 9.16 / 0.02, R3 7.89 / 0.03 (ratio ≈ 0.00; required ≥ 3) |
| secondary finding | the intended RTM mechanism is **genuine and distinct from G05**: under exogenous timing the naive bias collapses to ≈ 0 |
| operational-policy finding | a 1-month trigger would create separation (≈ 7.3 SE_REF RTM bias) but is unrealistic for supplier-quality practice, and is therefore **rejected** |
| final recommendation | **DO NOT BUILD** |
| benchmark arithmetic | **not counted** |

## Raw evidence (preserved unchanged; not regenerated or reformatted)
| file | sha256 |
|---|---|
| `sim/g38_R1_supplier.json` | `848e840b727dc8fde20d78c27c7c3e092dd7e0a5e8bab00fe5c0f5e67bd19eb1` |
| `sim/g38_R2_warehouse.json` | `c50828b8fb83e1f7e332d490db5edbe774d31c4c4b3e19ffcb648fca030eea05` |
| `sim/g38_R3_depot.json` | `7b8be806116c2d6c5dbf802c346e611dcb23aa4c0a8ef6c4f2932af5970d8da0` |
| `sim/aux_audits.json` | `7355044cb0ae558d3414e6c2c762a15cd45a8eaa1c042971b8cd65a263a0d069` |

`sim/*_window.json` files are derived by `analyze_g38.py`, a read-only pass over the raw files.
