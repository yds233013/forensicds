# G45 concept screen — the cost of a fee-relief policy, replayed

Coverage area 10 of FORENSICDS-10: the policy object. Built against principles 17 and 18: the object
must be one the workspace does not state (derivation), and computing it must be real work once stated
(execution).

## Setting

A card issuer is about to adopt a fee-relief policy: the first late fee in any rolling twelve months is
waived for accounts that meet stated conditions. Finance must certify the annual cost of the policy
against a budget before it goes to the regulator-facing committee, and the committee's threshold is a
hard number in the policy brief.

The published estimate takes the historical fee ledger, marks the fees the rule would have waived, and
sums them.

## Why that is the wrong object

Waiving a fee changes the account's balance, and the balance drives what happens next:

- interest accrues on a lower balance, so the following cycle's finance charge is smaller;
- the minimum payment is a function of the balance, so a waiver can move an account from **below** its
  minimum payment to **at or above** it, which means the account is not delinquent that cycle;
- delinquency state drives the *next* late fee, the penalty APR, and eligibility for relief under the
  policy's own once-per-twelve-months condition.

So the policy's cost cannot be read off the historical ledger: the ledger records what happened under
the policy that was in force. The cost is the difference between two **replays** of the same accounts —
one under the current rules, one under the proposed rules — with payments held at what customers
actually paid, which is the convention the policy brief fixes. Each replay is path dependent, and a
waiver in one cycle can suppress or create fees several cycles later.

## Candidate wrong objects (labelled before any number is read)

W01 sum the historical fees the rule marks as waivable (static marking) · W02 static marking, but net of
the interest on the waived fee only for the following cycle · W03 replay without the minimum-payment
interaction (delinquency state taken as historical) · W04 replay without the once-per-twelve-months
condition, so every eligible fee is waived · W05 the condition applied on a calendar year rather than a
rolling twelve months · W06 replay under the proposed rules only, compared against the historical
ledger rather than against a baseline replay · W07 penalty APR left at its historical trigger dates ·
W08 fees waived for accounts the policy excludes (over-limit, charged-off, in hardship) · W09 the cost
measured as fees waived rather than as the difference in total fees and finance charges · W10 the
replay run on statement dates rather than the cycle the fee posts in · W11 accounts closed mid-year
dropped rather than replayed to closure.

## Gate (must pass before any build)

1. the budget decision must not be constant across the graded extracts;
2. each wrong object must move the certified cost by more than the reporting precision on at least
   three of four extracts, and at least half must flip the budget decision somewhere;
3. two independent computational routes must agree on the truth exactly;
4. **principle 17 check**: no workspace document may state that the policy has to be replayed, or that
   a waiver changes later delinquency; the documents state the policy, the fee schedule, the
   minimum-payment formula and the modelling convention on payments;
5. **principle 18 check**: the baseline replay must be non-trivial — a static calculation must not
   coincide with it on any graded extract.
