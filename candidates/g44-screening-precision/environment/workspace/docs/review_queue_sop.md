# Review queue SOP (Fraud Operations)

## 1. What reaches the queue

| `reviews.review_source` | How the case is selected | Coverage |
|---|---|---|
| `QUEUE_FLAGGED` | every transaction the screen flags | all flagged transactions |
| `QUALITY_SAMPLE` | the quality programme takes a **systematic one-in-N sample of passed transactions**, N = `quality_sample_one_in` in `contract_terms` | a known fraction of passed transactions |
| `AD_HOC` | raised outside the programme: a chargeback arrives, or the merchant escalates a transaction | no defined selection rule |

The quality sample is what makes it possible to see what the screen let through. `AD_HOC` cases are
worked because they have to be, not because they were selected: they arrive because something already
went wrong, so they are not part of the quality programme's sample and are excluded from its counts.

## 2. Outcomes

`FRAUD` and `LEGITIMATE` are adjudications. `PENDING` means the analyst has not finished: the case is
open at extract time and has no determination. Roughly one case in thirty is open at any extract, more
after a chargeback backlog.

## 3. Standing instructions

- A reviewer never sees the screen's decision before adjudicating.
- The one-in-N counter runs over passed transactions in authorisation order and is reset only when the
  programme's sampling fraction changes; the fraction in force for an extract is in `contract_terms`.
- Do not re-review a case to change an adjudication; raise a new `AD_HOC` case instead.
