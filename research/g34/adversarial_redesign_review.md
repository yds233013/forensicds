# G34 redesign — adversarial review

By reasoning and code only; **no model call**, per the brief. Every attack was executed.

**Verdict: the redesign survives. Three findings must be fixed before a build; none is structural.**

| Attack | Outcome |
|---|---|
| "textbook competing-risks exercise; use AJ and you're done" | **Fails.** The one-line mapping (overhaul competing, everything else censoring) is wrong by 6–38%, up to **65 sd**, worst where retirement is common. Recognising competing risks is necessary and not sufficient |
| "event semantics are given away" | **Fails.** No code names a statistical role. Each role is supported by a distinct operational fact, and two codes (`PM_OVHL`, `ASSET_RET`) have **different roles for the two questions** |
| "competing-event definition is arbitrary" | **Fails.** An overhaul replaces the assembly, so the original assembly cannot subsequently fail — that is a physical fact, not a modelling choice. Retirement removes future demand, which is what the spares question is about |
| "net-vs-crude wording gives the answer" | **Partly lands.** The incident says Engineering's question is different. That is realistic framing, but a build must not go further and name the estimators |
| "raw rates are nearly sufficient" | **Fails.** −17% to −25%, 11–24 sd, and the decision is wrong in `visible` |
| "oldest/mature cohorts sufficient" | **Fails.** +4% to +10%, 5–9 sd |
| "business decision is constant" | **Fails on fixtures.** Best constant is right in 3 of 5 regimes; a 2-vs-2 fixture set defeats it. Decisions are unanimous within regime, so not knife-edge |
| "one event dominates" | **Partly lands.** Overhaul is the largest competing event; but `retirement_heavy` is precisely the regime where the one-line mapping fails worst (65 sd), so the second competing event is load-bearing |
| "valid estimators disagree" | **Fails.** Three implementations within 0.5% of truth |
| "CIF truth mismatched" | **Fails.** R1: AJ within ±0.11% of latent truth in all five regimes |
| "hidden regimes change the estimand" | **Fails.** Same invariant throughout; regimes vary failure scale, overhaul interval, retirement scale |
| "unrealistic rates" | **Fails.** 6401 failures / 8444 overhauls / 3470 retirements / 6685 still in service, 24-month overhaul interval, 36-month horizon — ordinary for rotating equipment |
| "status codes leak the role" | **Fails**, by construction |
| "Task 02 / G08 semantics still dominate" | **Fails — this is the key result.** R7 hands over the entire correct event table and separation is still 3.6–171 sd |
| "no survival reasoning remains after reconstruction" | **Fails**, same test |

## Findings that must be fixed before a build

1. **Row ordering.** Records are emitted in `unit_id` order. Shuffle.
2. **The pilot ships the regime name.** `observed()` passes `spec`, which contains `name`, to
   estimators. Convenient for the pilot; a build must not expose it.
3. **Transfers are still decorative.** The telemetry-gap fix (informative gaps) was tested and works
   at 51 sd, but `SITE_XFER` remains independent of failure and therefore harmless. Either give it a
   real consequence (a transferred unit enters harsher service) or **drop the code** rather than
   ship a mechanism that does nothing. Shipping it as-is would repeat the G31 error.

## Residual risk, stated plainly

The strongest remaining objection is that **`W7` — the one-line mapping — gets the business decision
right in all four regimes tested** while being 6–38% wrong. The task's discrimination therefore
rests on grading the quantities, not the decision. That is already the benchmark's policy after G24
and G05, and the graded set includes Q1, Q2, the per-cause incidence and the risk-set counts — but
it means a decision-only reading of a future baseline would badly overstate performance. This must
be stated explicitly in the task's own validation report.
