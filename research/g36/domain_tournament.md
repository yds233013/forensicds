# G36 domain tournament

Twelve domains scored 1-5. **Criterion 5 - execution difficulty AFTER shift recognition - is
weighted x3**, because that is precisely what G35 failed.

| | domain | 1 realism | 2 consequence | 3 shift strength | **5 exec-after-recognition (x3)** | 4 identifiability | 6 multiple valid | 7 regimes | 8 shortcut resist | 9 verifier | 10 distinct | **total** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | retail demand after pricing-policy change | 5 | 5 | 5 | 4 (12) | 4 | 4 | 4 | 3 | 4 | 4 | **50** |
| **B** | **energy load after tariff change** | **5** | **5** | **5** | **5 (15)** | **5** | **4** | **5** | **4** | **5** | **5** | **58** |
| C | cloud capacity after scheduler change | 4 | 4 | 4 | 4 (12) | 3 | 3 | 4 | 4 | 4 | 4 | 46 |
| D | staffing after routing-policy change | 4 | 4 | 4 | 3 (9) | 3 | 3 | 3 | 3 | 4 | 4 | 41 |
| E | subscription renewal after contract change | 4 | 4 | 3 | 3 (9) | 2 | 3 | 3 | 3 | 4 | 3 | 38 |
| F | supplier lead time after procurement change | 4 | 4 | 4 | 2 (6) | 4 | 3 | 3 | 2 | 4 | 4 | 36 |
| G | marketplace demand after fee/ranking change | 4 | 4 | 4 | 3 (9) | 3 | 3 | 4 | 3 | 3 | 2 | 37 |
| H | manufacturing throughput after maintenance change | 4 | 4 | 4 | 3 (9) | 3 | 3 | 4 | 4 | 4 | 3 | 41 |
| I | call-centre handle time after IVR change | 4 | 3 | 4 | 3 (9) | 3 | 3 | 3 | 3 | 4 | 3 | 38 |
| J | insurance claim severity after policy-wording change | 4 | 4 | 3 | 3 (9) | 2 | 3 | 3 | 3 | 3 | 4 | 36 |
| K | water demand after conservation programme | 4 | 3 | 4 | 4 (12) | 4 | 3 | 4 | 3 | 4 | 4 | 45 |
| L | freight transit time after carrier-mix change | 3 | 3 | 3 | 2 (6) | 4 | 3 | 3 | 2 | 4 | 4 | 34 |

## Top 3

**B (energy load after tariff change) — 58**, A (retail pricing) — 50, C (cloud scheduler) — 46.

## Why B wins

B is the only domain scoring 5 on execution-after-recognition, and it does so for a structural
reason rather than by being complicated:

- The **stable** mechanism is physics. Air-conditioning load responds to temperature, and that
  relationship is untouched by a tariff. History identifies it and it transports.
- The **unstable** mechanism is behaviour. Only a tariff pilot observes it.
- **Two independent transport problems arise naturally and are both realistic.** Tariff pilots are
  almost always opt-in, so pilot households are more responsive than the population. And demand
  response saturates in extreme heat - an air conditioner running flat out cannot be shifted - so a
  response measured in a mild pilot summer overstates what a hot target summer will deliver.

Neither problem is contrived, and **neither implies the other**. That is the property the tournament
was weighted to find.

## Why the losers lost

- **F, L** score 2 on execution-after-recognition: once you notice the supplier or carrier mix
  changed, reweighting by the new mix is the whole answer. That is covariate shift (K6).
- **E, J**: identifiability is weak. The target behaviour under a new contract wording is not
  estimable from anything the analyst can see without assuming the answer.
- **G**: overlaps G35's marketplace framing.
- **C, H, I, K** are viable but each scores 3-4 on the decisive criterion; A and C were carried into
  incident design and A into simulation as the runner-up.
