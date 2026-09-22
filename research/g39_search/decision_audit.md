# Business-decision provenance and correct-decision / wrong-science

Candidate decisions (with independent provenance, written before simulation):

| id | decision | provenance |
|---|---|---|
| A1 | renegotiate or keep take-or-pay contracts | contract economics |
| A2 | expedite purchase iff shortfall > SLA allowance | service contract |
| A4 | buy Q* cores | cost minimisation (argmin, no threshold) |
| B3 | build a new hall iff pipeline (1.2 MW, from the sales plan) > headroom | sales plan |
| B1 | capacity investment iff effective capacity < demand | demand plan |
| C2 | switch forecast vendor iff accuracy < contractual 85 % | vendor contract |
| C4 | deploy iff expected recall ≥ contracted level | network rule |

**Not simulated.** The minimal simulations measured the continuous objects only, because the
separation gate failed first. Correct-decision / wrong-science rates therefore **were not measured**.

**Qualitative expectation:** conditional traps imply many wrong objects give the right decision
whenever the trap is inactive, so decision-only grading would be weak everywhere.
