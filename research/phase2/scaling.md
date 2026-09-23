# Phase 2 — the 1,000-task scaling model

## The generative signature

```
task = WORLD × MECHANISM × INCIDENT ARCHITECTURE × EVIDENCE CONFIGURATION
              × DECISION TYPE × DATA-GENERATING REGIME
```

| axis | cardinality | examples |
|---|---|---|
| **world** | 8–12 authored organisations | Meridian Retail · Halcyon Health · Lattice Financial · an industrial OEM · a freight network · an energy retailer · a marketplace · a B2B software company |
| **mechanism** | 30–40 scientific failure opportunities | selective labels · informative censoring · interference · staggered adoption · measurement-system change · vintage/backfill · performative feedback · hierarchical reconciliation · wrong feasible set · non-linear economics · transport to a new population · multi-stage selection · competing risks · denominator/exposure · proxy-outcome validity · position bias · endogenous prices |
| **incident architecture** | 6–8 shapes | a published number is disputed · two teams disagree · a model degraded in production · a gate/threshold decision is due · an external party challenges a certificate · a plan must be committed · a metric moved and nobody knows why · a regulator asks for a restatement |
| **evidence configuration** | 5–8 shapes | warehouse + incumbent pipeline · warehouse + experiment registry + ops logs · landing zone + issued ledger + contract · model registry + decision logs + policy versions · instrument logs + calibration records + retained samples · finance semantic layer + source systems |
| **decision type** | 6–8 | launch/hold · procure/defer · price/hold · extend/stop a programme · certify/remediate · reserve/release capital · hire/overtime · restate/do not restate |
| **DGP regime** | 3–5 per task | effect present/absent/reversed · strong/weak censoring · heavy/light seasonality · tight/loose capacity |

Naive product: 10 × 35 × 7 × 6 × 7 × 4 ≈ 411,000. That is not the claim. The claim is that **~1,000
semantically distinct tasks** are reachable because the binding constraint is *authored mechanism ×
world pairs* — roughly 10 worlds × 35 mechanisms ≈ 350 viable pairings, of which perhaps 250 survive
the admission test, each yielding 3–5 genuinely distinct incidents by varying architecture, evidence
configuration and decision type. The DGP regimes give hidden extracts, **not** new tasks.

## The anti-clone rules

A generated variant is admitted only if it changes at least one of the following relative to every
existing task, and the change alters what the analyst must *think*, not merely what they must type:

1. **the mechanism** (different scientific reason the incumbent number is wrong);
2. **the object class** (population · grain · temporal state · denominator · counterfactual · action
   unit · feasible set · hierarchy · economic mapping · measurement scale);
3. **the discriminating test class** (negative control · placebo period · randomised stratum ·
   dual-instrumented period · retained reference sample · held-out vintage · natural experiment ·
   independent system invariant · synthetic-censoring replay · on-policy anchor);
4. **the decision type**.

Two variants sharing mechanism *and* object class *and* discriminating-test class are clones, however
different their domain skin. This is the rule that a domain-skin-only generator violates, and it is
why "marketplace interference × 20 domains" is one task, not twenty.

## Expert workflow to get there

| stage | who | output | cost model |
|---|---|---|---|
| 1. world authoring | 1 domain operator + 1 data engineer | systems of record, document estate, event calendar, generator skeleton | ~2–3 weeks per world, amortised over 20–80 tasks |
| 2. mechanism specification | methodologist | the estimand, the wrong objects, the discriminating tests, the identification argument | ~1 day per mechanism, reused across worlds |
| 3. incident authoring | domain operator + methodologist | instruction, documents, incumbent pipeline, decision rule and threshold | ~1–2 days per incident once the world exists |
| 4. pre-build gate | automated | separation of ≥10 wrong objects; margin test; discriminating-test inventory; identifiability by two independent routes | hours; **rejects roughly half of well-motivated designs** (phase-1 observed rate) |
| 5. verifier + mutation suite | engineer | graded quantities, tolerance calibration, 10–40 mutations, cheap-solve audit | ~1 day per incident |
| 6. adversarial review | independent reviewer | the single question "is the object stated anywhere?" plus an ambiguity audit | ~2 hours per incident |
| 7. freeze and prospective run | automated | checksum, Oracle=1, Nop=0, then and only then the target model | ~$1–3 per task |

Measured phase-1 evidence for the cost model: engineering cost per task fell from ≈3,500 to ≈1,000
Python lines once the harness was reusable, and target-model trials cost $0.04–0.30 each. The scarce
input is not compute; it is **mechanism specification and adversarial review**, which is exactly why
the world layer is worth building: it amortises everything except stages 3, 5 and 6.
