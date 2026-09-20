# G36 correct-data-table gate

## What was handed over

Every analysis in the panel operates on **perfect inputs**. There is no ETL difficulty anywhere in
the simulation:

- segment membership for every household, exact and complete;
- the full flat-tariff history, all households, all three summers, no missingness;
- the pilot enrolment log, the randomisation assignment, and the control arm, all correct;
- daily cooling-degree-days for history, pilot and the target forecast;
- no joins to get wrong, no timestamps to misinterpret, no entity resolution, no schema ambiguity.

The only mistake available is **choosing the wrong statistical object or transporting it wrongly**.

## Result — **PASS**

| | worst error | in sd |
|---|---|---|
| accepted estimator | 0.0130 | 0.9 |
| best *wrong* analysis (W16, right response wrong level) | 0.299 | 21 |
| incumbent historical model | 0.638 | 45 |
| selection-fixed-only | 0.165 | 12 |
| temperature-fixed-only | 0.151 | 11 |

Separation is **not** coming from data hygiene. A team that assembles a flawless analysis table and
then runs its production model is wrong by 45 sd and recommends the wrong capacity decision on two
of five regimes.

## Why this matters for implementation

It licenses a deliberately **clean** workspace. The eventual task should not manufacture difficulty
through messy joins or ambiguous columns - kill criterion K21 - because the measurement above shows
the science carries the task on its own. Any ETL friction added later would be decoration, and would
make the failure analysis harder to interpret rather than easier.
