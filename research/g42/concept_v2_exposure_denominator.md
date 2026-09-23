# G42 concept (v2) — recordable injury rate for a client access requirement

Coverage area 7 of FORENSICDS-10: hierarchical aggregation and denominator reconciliation. Replaces
the rejected comparable-store design (`concept_v1_retail_comp_sales.md`), whose mechanisms all
collapsed to a population filter.

## Setting

An industrial services contractor works across sites for client operators. A client's access
requirement is written on the **recordable incident rate**:

> rate = 200,000 x recordable cases / hours worked, over the trailing twelve months.

Above the contractual limit the client suspends new work and requires a corrective plan. The published
safety report computes the rate from payroll hours and the incident log as recorded.

## Why the denominator has to be built, not filtered

Neither the numerator nor the denominator exists in the warehouse as a column.

* **Hours worked** come from shift records, not payroll totals: paid time off, holiday, training and
  travel are paid but are not hours worked; overtime is; a shift crossing midnight splits across days;
  a worker assigned to two sites in a week splits hours by where the shift was worked, not by their
  home site.
* **Agency workers** are supervised day to day by us, so the standard puts both their hours and their
  cases on our rate. They are in a different source table from employees, at a different grain.
* **Recordable cases** are a classification, not a row count: first-aid-only cases are not recordable,
  a case still under review is not recordable until it is, one incident can produce several case rows
  (two workers hurt in one event is two cases; one worker with two body parts is one), and a case
  recorded in the window but *occurring* before it belongs to the earlier window.

## The aggregation layer

The same rate is reported per site, per region and company-wide. The company rate is the **pooled**
rate (total cases over total hours), not the average of site rates - and site sizes are extremely
skewed, so the two differ materially. A multi-site worker's hours belong to the site where the hours
were worked, while their case belongs to the site of the incident; a naive join puts both at the
worker's home site, which moves small sites a long way.

## Candidate wrong objects (labelled before any number is read)

W01 payroll hours as the denominator (PTO, holiday, training included) · W02 scheduled hours instead
of worked · W03 agency hours excluded but agency cases kept · W04 agency workers excluded entirely ·
W05 first-aid cases counted · W06 cases still under review counted · W07 cases counted by record date
rather than occurrence date · W08 one case per incident event (multi-worker events undercounted) ·
W09 headcount x 2,000 hours · W10 mean of site rates instead of the pooled rate · W11 multi-site
hours and cases attributed to the worker's home site · W12 a 12-month window taken as calendar months
rather than the trailing period · W13 rate per 100 workers instead of per 200,000 hours.

## Gate (must pass before any build)

1. the access decision must not be constant across the graded extracts;
2. each wrong object must move the company rate by more than the reporting precision (0.01) on at
   least three of four extracts, and at least half the panel must flip the access decision somewhere;
3. two independent computational routes must agree on the truth;
4. the correct construction must be derivable from the recordability standard and the contract alone.
