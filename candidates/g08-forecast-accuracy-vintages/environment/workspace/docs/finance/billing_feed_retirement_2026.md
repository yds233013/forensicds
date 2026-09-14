# Billing platform consolidation: retired feeds (effective 1 August 2026)

Owner: Billing Systems.

The following feeds stop with the move to the consolidated billing platform. The warehouse settlement tables
(`settlement_runs`, `settlement_volumes`, `run_status_history`) carry every run published by the settlement agent and
replace them for analytical use.

| Feed | Contents | Notes |
|---|---|---|
| `billing.charge_basis_snapshot` | By snapshot month, region, portfolio and delivery day: the settlement volume the day's imbalance charge was calculated on | Produced on request (Trading Analytics requested one per month). The last snapshot delivered was for delivery month June 2026; historical snapshots were not migrated. |
| `billing.imbalance_invoice_lines` | Invoice lines to Trading | Available in the finance ledger. |

Trading system feeds retired with the trading system upgrade (Trading Technology, cut-over 20 July 2026) are listed in
the trading system release notes; `trading.locked_forecasts` was one of them.
