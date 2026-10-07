# Output contract

Write `out/readout.json` and `out/market_week_panel.csv`.

## `out/market_week_panel.csv`

One row per market-week over the whole warehouse window. Columns, in this order:

`market_id`, `week_start`, `orders`, `late_orders`, `late_rate_pct`, `boost_share`, `courier_hours`

`orders` and `late_orders` follow the programme metric population in `docs/metric_definitions.md`.
`boost_share` is the share of that market-week's metric-population orders that carried Boost.
`courier_hours` is defined in `docs/metric_definitions.md`.

## `out/readout.json`

A single JSON object with exactly these keys:

| key | type | |
|---|---|---|
| `orders_analysed` | int | orders in the programme metric population, phase 2, enrolled markets |
| `order_arm_contrast_pp` | number | the difference in late-delivery rate between the phase-2 arms, in percentage points |
| `programme_effect_pp` | number | the quantity named in `docs/rollout_decision_memo.md` |
| `programme_effect_ci_low_pp` | number | 95 % interval on that quantity, lower bound |
| `programme_effect_ci_high_pp` | number | 95 % interval, upper bound |
| `inference_unit_n` | int | how many independent units your interval is computed over |
| `courier_hours_response_pct` | number | the percentage change in courier hours per order attributable to Boost being on rather than off |
| `decision` | string | `roll_out` or `do_not_roll_out` |

Percentage-point fields are signed: negative means the late-delivery rate falls.
