# data/service.sqlite — table dictionary

## order_lines
One row per order line.

| column | meaning |
|---|---|
| line_id, order_id, account_id, sku | keys |
| requested_qty | the quantity on the customer's purchase order line |
| confirmed_qty | the quantity the supplier confirmed against the line; **null where no confirmation was recorded** |
| delivered_qty | the quantity despatched against the line |
| requested_delivery_date | the date the customer asked for |
| despatch_date | the date the supplier despatched; null for cancelled lines |
| cancelled_by_customer | 1 where the customer cancelled before despatch |
| amended_qty | where the customer amended the quantity after the supplier confirmed, the amended quantity; null otherwise |

## returns
Returns and rejections against a line, with quantity, reason code and date. A line may have more than one row.

## goods_receipts
The customers' own goods-receipt confirmations: the quantity each account recorded as received. An independent
system; it is not derived from `order_lines`.

## shortfall_tickets
Tickets raised by accounts, each pointing at the line complained of, with a claim type.

## published_metrics
The figures that have been published for the period, with their source: MRG's demand-science team and the
supplier's own report.

## accounts
Account reference data, including the contractual per-account floor.
