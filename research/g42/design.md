# G42 — trailing-twelve-month recordable incident rate (denominator construction)

Coverage area 7 of FORENSICDS-10: hierarchical aggregation and denominator reconciliation. The first
design for this area (comparable-store sales) was rejected before build; see
`concept_v1_retail_comp_sales.md` for why, and `concept_v2_exposure_denominator.md` for the
pre-registered gate this design was screened against.

## 1. The business setting

Meridian Industrial Services works across client-operated sites. A client's access requirement is
written on the recordable incident rate over the trailing twelve months:

> rate = 200,000 x recordable cases / hours worked; above 1.50 the client suspends new work.

The published report says **1.26 — inside the limit**. The contract rate is **1.72 — outside it**. The
client's auditor has the higher number, which is the situation the instruction puts to the agent.

## 2. Why the published run is wrong, and why it is not stupid

Its arithmetic is right. Both sides of the ratio are *constructed*, and each is constructed from the
wrong rows:

| Published construction | What the standard says |
|---|---|
| hours from the payroll export | hours **worked**: `WORKED` entries only, overtime included; PTO, holiday, training and travel are paid, not worked |
| one row per incident event | one case per **injured person**; `event_id` groups them |
| window on the date the case was entered | window on the date the incident **occurred** |
| agency workers present in the log, absent from the hours | agency hours **and** cases both count: they work under our supervision |
| company figure quoted from a site-level pack | the company figure is the **pooled** rate, not the mean of site rates |
| cases shown against the worker's badged site | hours follow the site **worked**, cases follow the site of the **incident** |

Each rule is stated in `docs/recordable_case_standard.md` or `docs/hours_worked_policy.md`. The
difficulty is that neither side of the ratio exists as a column: the denominator has to be built from
199,935 shift entries and the numerator from a classification, a grain and a date choice.

## 3. Identifiability

Two independent computational routes agree exactly on all four graded extracts: the generator's truth
(`environment/build/world.py`, computed from the in-memory world before it is ever written to SQL) and
the oracle solution (`solution/safety_rate/`, computed from the SQLite extract with pandas). They agree
on hours to the cent, on the case count, on the company rate to four decimals, and on every site rate:

| Extract | hours worked | cases | rate | decision |
|---|---|---|---|---|
| visible  | 1,740,204.95 | 15 | 1.7239 | suspend |
| hidden_a | 1,486,280.38 |  8 | 1.0765 | clear |
| hidden_b | 2,312,157.17 | 20 | 1.7300 | suspend |
| hidden_c | 1,218,337.84 |  3 | 0.4925 | clear |

The decision is two suspend and two clear, so it cannot be guessed, and no extract sits within 0.2 of
the limit, so the call does not turn on the last decimal.

## 4. Pre-build wrong-object panel

Twelve wrong constructions, labelled before any number was read (`tools/g42/panel.py`). Every one moves
the reported rate on at least three of the four graded extracts; eleven move it on all four
(`tools/g42/panel_results.json`). The panel is dominated by numerator and denominator *construction*
rather than by filtering: the largest single error is counting first aid (+0.66 to +1.26), and the
mean-of-site-rates error reaches +1.49 because site sizes are extremely skewed.

W11 (attributing hours and cases to the worker's badged site) leaves the **company** rate untouched and
moves individual **site** rates by 3.8 to 22.9 — which is why the site table is graded as well as the
headline figure.

## 5. Fixture selection, disclosed

The four extracts were chosen deliberately from a larger screened set, before any model was run:

* the regimes vary (a heavy-agency period with more paid non-work time; a large estate with a 110-day
  entry backlog; a quieter smaller estate), so the task is not solvable by fitting one period's shape;
* the decisions are balanced two and two;
* `hidden_b`'s incident frequency was moved (case_rate 1.35 -> 1.55) because at 1.35 its true rate was
  1.470 against a 1.50 limit, a 2 % margin — a knife-edge decision would have tested precision rather
  than reasoning.

Nothing here was tuned against a model: no model had been run on this task at the time these were
fixed, and the tolerances are the ones the output contract states.

## 6. What could still make this a weak task

- The hardest step (recognising which rows are hours worked) is stated plainly in a policy document.
  If a model reads both documents carefully, execution is a filter plus a groupby — the task then
  measures reading discipline rather than construction skill. The counter-evidence is the panel: the
  errors that matter are the ones a careful reader still has to decide (case grain, occurrence versus
  entry date, pooled versus mean), not the ones the documents spell out.
- Small case counts (3 to 20) mean one misclassified case moves the rate by 0.05 to 0.16. That is the
  real operating regime for this metric, but it does make the numerator unforgiving.
