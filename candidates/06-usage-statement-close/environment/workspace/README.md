# cobalt-metering

Usage metering for the Cobalt data platform. Owner: Platform Billing Engineering (#billing-eng).

The pipeline reads meter records delivered by the `meterd` edge collectors, maintains the usage mart that the customer
usage console and capacity dashboards read, and assembles the monthly usage statements that are exported to the
billing system.

```
python -m jobs.close_month --month 2026-09     # or: bin/close_month 2026-09
```

| Path | Contents |
|------|----------|
| `raw/landing/` | collector deliveries as received (`received_date=YYYY-MM-DD/*.jsonl.gz`), read-only |
| `config/` | pipeline settings, customer registry, rate cards |
| `metering/` | landing reader, normalisation, usage mart |
| `statements/` | statement calendar, rate cards, rating, assembly, export |
| `jobs/` | entry points |
| `out/` | pipeline outputs (usage mart, statements) |
| `ledger/issued/` | statements as issued by the billing system (export, read-only) |
| `docs/` | data catalog, architecture decisions |
| `contracts/`, `vendor/`, `ops/` | customer terms, collector documentation, billing operations |
| `finance/`, `exports/`, `dashboards/`, `inbox/` | material from Finance, Support and Operations |

Release notes: `RELEASES.md`.
