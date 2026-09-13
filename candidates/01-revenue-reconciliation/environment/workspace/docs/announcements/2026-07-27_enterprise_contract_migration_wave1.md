# Enterprise Contract Migration - Wave 1 (August 2026)

From: Billing Operations and Revenue Operations - 2026-07-27

As part of moving enterprise customers to our new regional contracting entities,
the first wave of Enterprise accounts (plus one Mid-Market account that is
completing a second move) migrates during **August 2026**. Wave 2 is scheduled
for September.

Earlier entity transfers (February-April) used **immediate cutover**: the legacy
account was closed on the effective date. Enterprise contracts include prepaid
annual terms, so wave 1 uses a **staged cutover**:

1. On the effective date Billing Ops creates the successor CRM account and a new
   billing account for it. Usage from the effective date and new services are
   invoiced on the new billing account; monthly items move to it from the next
   monthly billing date.
2. Prepaid annual terms already invoiced on the legacy billing account run to the
   end of their term there; they are not re-invoiced. Final usage up to the
   effective date is also invoiced on the legacy billing account.
3. The legacy CRM account stays open with lifecycle status `Migrated` until Billing
   Ops signs off the cutover (final usage invoiced and open credits settled), so
   account teams can manage the remaining legacy invoices and credits. Prepaid terms
   still running on the legacy billing account after sign-off continue to recognize
   there and are managed from the successor account.
4. With CRM migration tool 2.1.0, successor accounts show the billing accounts of
   their predecessors (link type `legacy`) so account teams can see full billing
   history in one place.
5. The migration register (`account_migrations.csv`) is updated on the effective
   date (`cutover_in_progress`) and at sign-off (`completed`).

Finance reporting follows the Account Identity Standard: customer-level revenue is
reported under the successor account for all periods. Company totals are not
affected by migrations.

Contacts: Billing Ops (#billing-ops), RevOps (#revops)
