# G36 graded-fact evidence audit

For every quantity a future verifier might grade: what visible evidence supports it, could a real
analyst infer it, and does it require future outcomes or generator knowledge?

| candidate graded fact | visible evidence | needs future outcomes? | verdict |
|---|---|---|---|
| target-summer peak load forecast | stable curve from history + response from pilot + published weather forecast | **no** | **GRADE** |
| capacity decision | the numeric gate is in the procurement memo | no | **GRADE** |
| per-segment weather-load slope | three summers of flat-tariff history, all households | no | **GRADE** |
| per-segment TOU response at a stated CDD | the randomised pilot, using its control arm | no | **GRADE** |
| population segment mix | the customer master | no | **GRADE** |
| opt-in segment mix | the pilot enrolment log | no | **GRADE** |
| household / pilot counts | countable | no | **GRADE** (bookkeeping) |
| **true response parameters `resp0`** | none - generator internals | n/a | **DO NOT GRADE** |
| **heat-damping coefficient as a parameter** | not observable as such; only its *consequence* is estimable | n/a | **DO NOT GRADE** as a parameter; the response *at a stated CDD* is gradeable |
| **regime label** | a generator concept | n/a | **DO NOT GRADE** |
| **actual target-summer load** | does not exist at decision time | **yes** | **DO NOT GRADE** |
| **per-household response** | not identified by any experiment | n/a | **DO NOT GRADE** |
| **response outside the pilot's CDD range** | extrapolation beyond support | n/a | **DO NOT GRADE** |

## Explicit confirmation

**No proposed graded check requires generator-only truth, and none requires outcomes that do not
exist at decision time.** The target forecast is graded against the latent expectation of the
generator - which is a *property of evidence the analyst holds*, not a secret - exactly as G34 graded
cumulative incidence and G35 graded the rollout contrast.

## The line this audit draws

The task may ask "what will peak load be next summer" **only because** the pilot identifies the
response and the weather forecast is published. Remove either and the honest answer becomes "not
identified", and asking anyway would be grading clairvoyance. This is the single most important
constraint on any implementation.
