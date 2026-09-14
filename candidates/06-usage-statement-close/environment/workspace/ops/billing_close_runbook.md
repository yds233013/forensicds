# Runbook: monthly usage statement close

Owner: Billing Operations.

1. **Close.** The statement for month M closes at 00:00 UTC on the 4th of month M+1, 72 hours after the end of the
   month. The close is the cutoff for the statement; the run itself may start later.
2. **Run.** `bin/close_month M` on the metering host. It rebuilds the usage mart and writes the statement to
   `out/statements/M/`.
3. **Review.** Finance ties out statement quantity with collector volume (`finance/tieout_*.ipynb`) and spot-checks
   large customers.
4. **Issue.** Billing Ops exports the statement to the billing system, which issues the invoices. The billing system's
   issued statement is exported to `ledger/issued/`. Issued statements are never regenerated or re-issued.
5. **Disputes.** Route to Billing Ops with the customer's usage console export. Credits go on a later statement.
