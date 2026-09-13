# Revenue metrics handbook (excerpt: ARR and retention)

Owner: FP&A. Approved by the CFO for board reporting. Version 3.2 (2025-01).

## ARR

- **ARR on a date D** for an account is the sum of `arr_usd` of its recurring subscription lines in effect on D
  (`start_date <= D < end_date`). One-time lines (onboarding, services) are not ARR. USD, to the cent.
- An account is a **customer on D** if its ARR on D is greater than zero.
- ARR does not depend on how Sales Ops categorises the contract document a line came from.

## Reporting periods

Calendar quarters. For a quarter Q, `S` is the first day of the quarter and `E` the first day of the next quarter.
"Starting ARR" is ARR on S; "ending ARR" is ARR on E.

## Retention metrics (per quarter)

Retention measures what happened to the recurring revenue of the customers the company had at the start of the
quarter.

| Metric | Definition |
|--------|------------|
| Retention cohort | customers on S |
| Net revenue retention (NRR) | ending ARR of the cohort / starting ARR of the cohort |
| Gross revenue retention (GRR) | sum over the cohort of min(ending ARR, starting ARR) / starting ARR of the cohort |
| Logo churn rate | cohort accounts with zero ending ARR / cohort accounts |

Revenue from accounts that are not customers on S does not enter retention metrics.

## ARR bridge (per quarter)

Every account with ARR on S or on E is in exactly one bridge category:

| Category | Accounts | ARR in the bridge |
|----------|----------|-------------------|
| New | not a customer on S, customer on E, never a customer before S | + ending ARR |
| Reactivated | not a customer on S, customer on E, a customer on some day before S | + ending ARR |
| Expanded | customer on S, ending ARR > starting ARR | + (ending - starting) |
| Contracted | customer on S, 0 < ending ARR < starting ARR | - (starting - ending) |
| Churned | customer on S, ending ARR = 0 | - starting ARR |
| Retained | customer on S, ending ARR = starting ARR | 0 |

Starting ARR (all customers) + new + reactivated + expansion - contraction - churned = ending ARR (all customers).

## Customer segments

Segments for retention reporting are set by the customer's starting ARR in the quarter: SMB below 25,000;
Mid-Market 25,000 to below 100,000; Enterprise 100,000 and above. Segment retention metrics apply the retention
definitions to the cohort customers in each segment.
