# Store KPI handbook (extract)

Owner: Retail Finance. All store KPIs are reported in trading weeks that run **Monday to Sunday**; a week is labelled by
its Monday (`week_start`).

| KPI | Definition | Source |
|---|---|---|
| Net sales | merchandise sales net of returns and promotional markdowns, excluding VAT, lottery and the pharmacy counter | `kpi_store_week.net_sales` |
| Customer transactions | completed checkout transactions (staffed lanes and self-checkout) | `kpi_store_week.customer_txns` |
| Basket size | net sales / customer transactions | derived |
| SCO share | share of customer transactions completed at self-checkout | `kpi_store_week.sco_txn_share` |
| Pharmacy sales | pharmacy counter sales, reported separately (stores with a pharmacy only) | `kpi_store_week.pharmacy_sales` |

## Comparable trading weeks

A **comparable trading week** is a week in which the store traded its full hours on all seven days. A store-week with
any record in `store_closures` (install works, weather, refrigeration, power, flooring) is not a comparable trading
week. Like-for-like reporting and programme evaluations use comparable trading weeks only; partial weeks are kept in the
ledger for completeness.

## Notes

- Transactions and basket size move in opposite directions when shoppers consolidate trips; net sales is the figure
  the P&L uses.
