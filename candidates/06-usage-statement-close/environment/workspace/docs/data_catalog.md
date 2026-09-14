# Data catalog: cobalt-metering

## Sources

### Collector deliveries: `raw/landing/received_date=YYYY-MM-DD/part-*.jsonl.gz`

One JSON object per line, partitioned by the UTC date on which the landing service received it.

| Field | Meaning |
|-------|---------|
| `delivery_id` | unique per delivery |
| `received_at` | UTC time the landing service received the delivery |
| `collector` | edge collector that sent it |
| `record.event_id` | the meter record's identifier (one per customer, meter and usage window) |
| `record.rev` | record revision, see `vendor/meterd/DELIVERY.md` |
| `record.customer_id`, `record.meter` | customer and meter |
| `record.window_start`, `record.window_end` | usage window, UTC |
| `record.quantity` | metered quantity, decimal string with 3 decimals |

### Customer registry: `config/customers.csv`
`customer_id, name, region, currency`. The region's edge collector sends the customer's records.

### Rate cards: `config/rate_cards.csv`
`customer_id, meter, effective_month, included_units, tier1_units, tier1_rate, tier2_rate`. A rate card applies from
its effective month until the next effective month for the same customer and meter.

### Issued statements: `ledger/issued/statement_YYYY-MM.csv`
Export from the billing system. One file per issued statement, one row per statement line:
`statement_id, statement_month, customer_id, meter, line_type, service_month, quantity, amount, issued_at`.
A line bills the customer for the month in its `service_month` column. Issued statements are final.

## Outputs (`out/`)

### Usage mart: `out/usage_mart/usage_by_service_month.csv`
`customer_id, meter, service_month, quantity` (3 decimals). One row for every customer, meter and service month
(`YYYY-MM`) for which any usage record is known, with usage as currently known. The customer usage console and
capacity dashboards read this table.

### Statement lines: `out/statements/<statement_month>/statement_lines.csv`
`statement_month, customer_id, meter, line_type, service_month, quantity, amount`. The same line conventions as issued
statements: `line_type` is `usage` or `adjustment`; quantity has 3 decimals, amount 2 decimals (USD).

### Statement summary: `out/statements/<statement_month>/summary.json`
`{"statement_month", "close_at", "customers": [{"customer_id", "usage_amount", "adjustment_amount", "total_amount"}]}`
(`close_at` is an ISO 8601 UTC timestamp; amounts are decimal strings)
with one entry for every customer that has a line on the statement.
