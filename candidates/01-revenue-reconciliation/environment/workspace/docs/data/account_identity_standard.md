# Account Identity Standard for Reporting

Owner: Data Governance Council (Revenue Analytics, Billing Ops, Sales Ops, Finance).
Version 2.1, approved 2026-07-30.

Revision history: 1.0 (2025-09) initial; 2.0 (2026-01) migration register as lineage
system of record; 2.1 (2026-07) restatement rules and staged cutovers, ahead of the
Enterprise contract migration waves.

## 1. Entities

**CRM account** - a customer relationship managed by Sales (id `ACC-nnnnnn`).
Carries reporting attributes: name, segment, region, owner.

**Billing account** - the container Billing invoices against (id `BA-nnnnnn`).
Each billing account has a legal entity, country and currency. A CRM account
can have more than one billing account (e.g. one per contracting entity).

**Migration** - a change of contracting entity for a customer, recorded by Billing
Ops in the migration register. Types:
- `entity_transfer`: one legacy account moves to one successor account.
- `entity_consolidation`: several legacy accounts move to one successor account.

A legacy account has at most one successor. A successor may itself be migrated
later, forming a chain.

## 2. System of record for each fact

| Fact | System of record |
|------|------------------|
| Invoiced amounts, credits, service periods | Billing |
| Which CRM account owns a billing account | Billing: `billing_accounts.crm_account_id`, set when the billing account is created and never changed |
| Account lineage (legacy -> successor), effective dates, status | Billing Ops migration register (`account_migrations.csv`) |
| Account name, segment, region, owner | CRM (current record) |

Migrations never move or rewrite billing history: invoices and credit notes stay
on the billing account they were issued to. New contracts after a migration are
issued on new billing accounts owned by the successor.

## 3. Canonical account

Customer-level reporting uses the **canonical account**:

1. Start from the CRM account that owns the billing account (section 2).
2. If that account has an effective migration in the register, move to its
   successor. Repeat until the account has no effective migration.
3. The account reached is the canonical account.

A migration is effective once its register status is `cutover_in_progress` or
`completed`. Register rows with status `scheduled` are plans and do not change
attribution.

## 4. Restatement

Canonical attribution applies to **all periods**, including periods before the
migration took effect. When a migration becomes effective, customer-level history
is restated under the canonical account at the next run. This applies as soon as a
migration is effective, even if its effective date falls after the last reportable
period. Company, segment and region totals are unchanged by restatement.

## 5. Reporting attributes

Name, segment and region reported for a customer are those of the canonical
account's current CRM record.
