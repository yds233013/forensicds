# Required outputs

`service.fill` must write two files into `out/` when run as

    python -m service fill --db data/service.sqlite --out out

## out/readout.json

| field | type | meaning |
|---|---|---|
| `period` | [string, string] | the reporting period, inclusive start and exclusive end, as ISO dates |
| `fill_rate_contract_pct` | number | the category fill rate on the basis the customer supply agreement defines |
| `fill_rate_contract_low_pct` | number | the lowest value that basis can take across readings the agreement admits |
| `fill_rate_contract_high_pct` | number | the highest such value |
| `fill_rate_supplier_definition_pct` | number | the figure on the basis the supplier's methodology appendix defines |
| `published_rate_pct` | number | the figure MRG's demand-science team published for the period |
| `bridge_pp` | object | the difference between the two definitions, decomposed (see below) |
| `account_fill_pct` | object | the contractual fill rate per account, keyed by `account_id` |
| `accounts_below_floor` | integer | how many accounts fall below the agreement's per-account floor |
| `returns_driven_ticket_share_pct` | number | share of shortfall tickets whose line carries a return |
| `governing_definition` | string | `contract_line_fill_confirmed` or `supplier_order_fill_requested` |
| `incumbent_verdict` | string | see below |
| `bonus_gate_met` | string | `yes`, `no` or `not_determinable` |
| `supplier_claim_payable` | string | `yes`, `no` or `not_determinable` |

### `bridge_pp`

Exactly these five keys, summing to
`fill_rate_supplier_definition_pct - fill_rate_contract_pct` within 0.2 pp:

    aggregation · denominator · returns_treatment · date_window · other

Each is the change in the figure from applying that one difference between the two definitions. Any key may be
zero or negative.

### `incumbent_verdict`

Exactly one of:

* `incumbent_correct` — the published figure is the figure the agreement defines;
* `incumbent_incorrect` — it is not;
* `not_determinable_from_available_evidence` — the evidence available does not settle it.

Where the verdict is `not_determinable_from_available_evidence`, `bonus_gate_met` and
`supplier_claim_payable` shall also be `not_determinable`, and the low/high fields shall bracket the readings
that cannot be chosen between.

### The two decisions

The bonus gate is met where the category figure on the governing definition is at least **96.0 %**. The
supplier claim is payable where that figure is **below** the agreement's per-account floor of 95.0 % for the
category as a whole.

## out/account_fill.csv

Header `account_id,lines,lines_filled,fill_rate_pct,below_floor`, one row per account.

## Rules

* Do not modify `data/service.sqlite`.
* The command must be re-runnable and produce the same outputs for the same database.
* Report rates as percentages to two decimals.
