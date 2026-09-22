# Identification (R1)

**Target:** the untreated counterfactual Σ_h E λ⁰ for each enrollee over its six SDP months.

**Key fact.** Enrolment is a deterministic function of **observed** history (D, E). Conditional on
the full observed pre-enrolment history, selection is ignorable. The predictive distribution of
future untreated outcomes given that history is the same whether or not the unit was selected. This
is what makes the counterfactual identifiable **without** any contemporaneous untreated unit at the
same trigger value. There is none: every supplier above 1,500 ppm is enrolled.

| component | learned from (visible) | used by |
|---|---|---|
| seasonal profile | fleet totals by calendar month, pre-programme era (months 0–23) | V1 (ratio of totals), V2 (mean log-rate by month): computed independently |
| variance of α, variance and persistence ρ of u | autocovariances of supplier log-rates in the pre-programme era, net of Poisson variance 1/(D + 0.5) | V2 |
| each enrollee's α and current shock | its own 24+ months of pre-enrolment history (Kalman filter) | V2 |
| E[post-6 rate \| trigger rate, prior-6-month rate] among rule-selected episodes | **pseudo-episodes**: the same rule applied in months 11–16 before the programme existed (untreated by construction), 12 months earlier, so the calendar is aligned | V1 |

**Assumptions** (stated, checkable):
- stationarity of the untreated process across the two years;
- the SDP does not change the behaviour of non-enrolled suppliers;
- for V2, the log-normal state-space form;
- for V1, a log-linear conditional mean in (log S*, log H*).

Nothing requires generator-only knowledge.
