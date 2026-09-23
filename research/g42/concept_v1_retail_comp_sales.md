# G42 concept screen — comparable-store sales for a covenant test

Coverage area 7 of FORENSICDS-10: hierarchical aggregation and denominator reconciliation.

## Setting

A retail chain (stores -> districts -> regions) must report **comparable-store sales growth** to its
lender each quarter. The credit agreement sets a covenant: growth below a stated floor triggers a
cash-sweep. The published run divides this period's total sales by last period's total sales.

## The object the covenant is written on

Growth on a **comparable basket**: stores trading for the whole of both periods, on a **week-aligned**
retail calendar (52/53-week year; a date-aligned prior period misaligns the trading weeks), with
non-comparable revenue excluded (wholesale, and orders fulfilled from a dark store that is not in the
basket), and remodelled / relocated / franchise-converted stores excluded for the periods the estate
rules say they are non-comparable.

Two aggregation traps sit on top of the population question:

1. **ratio of sums vs mean of ratios** — averaging store-level growth rates is a different number, and
   is what a store-level dashboard naturally shows;
2. **rollup double counting** — a relocated store appears under two store ids, and a district-level
   sum that treats them as separate stores counts one trading history twice.

## Candidate wrong objects (labelled before any number is read)

W01 total chain growth (no basket) · W02 basket = stores open at period end · W03 date-aligned prior
period · W04 remodels included · W05 relocation counted as a close plus an open · W06 franchise
conversions included · W07 wholesale revenue included · W08 dark-store fulfilment attributed to the
receiving store · W09 mean of store growth rates · W10 district rollup double counting the relocated
pair · W11 basket fixed on the prior period only · W12 growth on transactions rather than sales.

## Screen (must pass before any build)

1. the covenant decision must not be constant across the graded extracts;
2. each wrong object must change the reported growth by more than the reporting precision on at
   least three of four extracts, and flip the covenant decision on at least one;
3. the correct basket must be derivable from the estate rules and the credit agreement alone
   (identifiability), with two independent computational routes agreeing.

---

## Screen result (2026-09-22): REJECTED pre-build

`tools/g42/sim.py`, 8 worlds. Gate 1 passed only after the estate was made heterogeneous and seasonal
(both realistic, both chosen before any build). Gate 2 failed on substance rather than on arithmetic:

| Wrong object | typical |growth error| | decisions flipped (of 8) |
|---|---|---|
| basket open at period end | 0.08-0.24 | 4 |
| basket from the prior period only | 0.03-0.12 | 4 |
| total chain growth | 0.005-0.09 | 4 |
| franchise conversions included | 0.01-0.09 | 2 |
| remodels included | 0.000-0.023 | 1 |
| date-aligned prior period | 0.001-0.006 | 0 |
| relocation as a close plus an open | 0.000-0.003 | 0 |
| wholesale included | 0.000-0.005 | 1 |
| dark-store fulfilment included | 0.000-0.001 | 0 |
| mean of store growth rates | 0.001-0.011 | 1 |

The mechanisms that carry the task are all **population filters** (which stores are in the basket).
The mechanisms that would have made it a *hierarchical aggregation* task - calendar alignment,
relocation identity, mean-of-ratios, channel attribution - move the number by less than a basis point
or two and flip no decisions. Grading them exactly would be a precision trap, not a reasoning test
(design principle 13: the graded difference has to be the difference that changes the decision).

What remains is "select the right population", which the suite already covers (G05, task03), and
which is recognition-complete: once the estate rules are read, execution is a filter (principle 15,
recognition must not equal execution). Rejected before build; replaced by a design where the
denominator has to be **constructed** rather than filtered (`concept_v2_exposure_denominator.md`).
