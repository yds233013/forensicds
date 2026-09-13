# Revenue Recognition Policy - Management Reporting

Owner: Corporate Controller. Version 4.2, effective 2025-09-01 (billing platform go-live).

This policy defines *recognized revenue* for all management and executive
reporting. Statutory reporting follows the same principles; differences are
handled by the Technical Accounting team and are out of scope here.

## 1. Sources of truth

| Question | System of record |
|----------|------------------|
| What was invoiced or credited, to which billing account, for how much, in which currency | Billing (`billing.db`: `invoices`, `invoice_lines`, `credit_notes`) |
| Service period of each charge | Billing (`invoice_lines.service_period_start/_end`) |
| Currency conversion rates | Billing `fx_rates` (Treasury feed, monthly average) |
| Which accounting periods are reportable | Billing `accounting_periods` |

Billing records are never adjusted in reporting. Any management report of
recognized revenue must tie to Billing's recognized revenue report for every
reportable period, to the cent (rounding of at most $0.01 per reported figure).

## 2. What is revenue

Only lines on invoices with status `posted` are recognized. `draft` and `void`
invoices carry no revenue (a voided invoice is re-issued as a new posted invoice).

| `line_type` | Revenue? | Timing |
|-------------|----------|--------|
| `subscription` | yes | ratably over the service period |
| `discount` | yes (negative) | ratably over the service period of the discount line |
| `usage` | yes | over the usage period stated on the line |
| `onboarding` | yes | on delivery (service period is the delivery date) |
| `tax` | **no** - pass-through liability | - |

## 3. Timing: ratable daily allocation

A line with service period `[start, end]` (both dates inclusive) and amount `A`
recognizes, in calendar month `m`:

    A x (days of [start, end] falling in m) / (days in [start, end])

Every invoice line is therefore represented once per calendar month its service
period touches. Multiple lines on the same invoice are independent charges, even
when their descriptions and amounts are identical (for example, two seat blocks
bought on the same plan).

## 4. Credit notes

Credit notes (`credit_notes`, status `issued`) reduce recognized revenue by their
full amount in the calendar month of `issued_date`, regardless of the service
period of the credited line.

## 5. Currency

Amounts are recognized in the document currency and converted to USD at the
`fx_rates` monthly average rate for the revenue month (`rate_month`).

## 6. Periods

Reportable periods are accounting periods with status `closed` or `closing`.
Revenue falling in `open` periods is not reported (it remains deferred).

## 7. Customer, segment and region reporting

Revenue by customer, segment or region uses the attribution rules in
`docs/data/account_identity_standard.md`. Attribution only decides *whose*
revenue an amount is; it never changes amounts or the number of recognized
charges, so customer, segment and region views always sum to the company total.
