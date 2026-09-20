# G34 adversarial review

By reasoning and code only — **no model call, no LLM critique**, per the brief. Every attack was
executed; numbers are in `simulation_results.md`.

**Verdict: BLOCK the design as specified. The crude-risk variant is not blocked and was not fully tested.**

## The killer objection

**The two mechanisms that make this a *survival* task are the two that do not work.**

Left truncation moves the answer by 7–10% against a correct-estimator sd of 2.3% — 1.2 to 3.5 sd,
and it plateaus regardless of fleet age, so it cannot be strengthened by making the fleet older.
Competing risks, in the informative (condition-based) form that would have made it interesting,
destroys identification of the estimand: every method including the correct one lands 80% low.

What is left separating is the **time origin** (−48%), **removal-reason classification** (+148%) and
**mature-cohort filtering** (−67%). Those are, respectively, a timestamp-semantics error (Task 02's
shape), a status-code semantics error (G08's shape) and a population-eligibility error (Task 03 /
G31's shape). Once they are fixed, the statistics are a one-line Kaplan-Meier. So the task would
measure operational-state reconstruction with a survival estimator bolted on — **K12** (duplicates
an existing capability) and **K14** (textbook terminology rather than reasoning).

## Attacks and outcomes

| Attack | Outcome |
|---|---|
| "use KM" solves it immediately | **Partly.** Correct KM needs the right clock, the right event indicator and delayed entry. But `C_km_default_no_thought` (one-line KM, no thought) still gets the *decision* right 7/7 while being +145% wrong on the number |
| mature-cohort filtering is effectively correct | **No** — −67%, wrong decision. This attack fails, and that is a genuine strength |
| wrong time origin barely matters | **No** — −48%, 8.2 sd. Fails |
| censoring barely matters | **No** — treating overhaul as the event is +148% |
| **left truncation barely matters** | **YES — attack succeeds.** 7–10%, 1.2–3.5 sd, non-scalable |
| **competing risks barely matter (as designed)** | **YES — attack succeeds.** With age-based overhaul, treating it as independent censoring is *correct*, so there is no competing-risks content at all in the net-risk design |
| one mechanism dominates | **Yes** — removal-reason classification at 25 sd dwarfs everything else |
| the final decision is constant | Partly: 80% pooled for "hold", but unanimous per regime, so fixture selection defeats it |
| a visible aggregate leaks truth | No — unit_id, sensor_gap uncorrelated with outcome |
| hidden truth is unavailable | No — every graded fact has observable evidence (audit in `cheap_solve_results.md`) |
| legitimate estimators disagree | **Was true, now fixed.** Spread was 15.6–18.7% until the actuarial correction; now 5.3–5.7%. Recorded because the first version would have failed K11 |
| duplicates Task 02 / G08 | **Yes, for the parts that separate** — see the killer objection |
| unrealistic event rates | No — 2351 failures / 5526 overhauls / 119 decommissions out of 14,290 units over 24 months is plausible for an 18-month overhaul policy |
| solver can just use the oldest cohorts | **Yes, and it works** (−0.5%) — but it is a *valid* subsample estimator, not a bypass |

## What the design got right

Recorded so a redesign does not rediscover it: the **removal-reason taxonomy** is genuinely good.
Four reasons mapping onto four different statistical roles — target event, censoring, censoring,
and *not an exit at all* — is operationally real, and the sensor-dropout case (a monitoring gap that
looks like a disappearance but is not a removal) is the kind of distinction that separates an
analyst who reads the work-order system from one who does not. It survives into any redesign.
