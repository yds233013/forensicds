# G34 cheap-solve gate and leakage audit

Panel written alongside the generator, per the G31/G33 rule. 20,000 units, 7 worlds, visible regime,
truth = 0.4010.

| Heuristic | mean p | rel. err | decision correct |
|---|---|---|---|
| `C_constant_hold` | — | — | **7/7** (but 0/12 in `robust_units`) |
| `C_constant_extend` | — | — | 0/7 |
| `C_followup_length_proxy` (median follow-up > 12m) | — | — | 7/7 — a coin flip with no content |
| `C_failure_share_of_removals` | 0.2906 | −27.5% | 0/7 |
| `C_median_age_at_failure` | 0.9961 | **+148%** | **7/7** |
| `C_km_default_no_thought` (one-line KM, no truncation, every removal an event) | 0.9834 | **+145%** | **7/7** |
| `C_oldest_cohort` | 0.3991 | −0.5% | 7/7 |

**Two findings.**

1. **`C_oldest_cohort` is not a cheap solve — my panel mislabelled it.** It restricts to the oldest
   quartile by commissioning date but still uses the age clock and left-truncated KM, so it is a
   *valid estimator on a subsample*, and it lands within 0.5%. Recorded rather than quietly
   dropped: a panel entry that turns out to be legitimate is as informative as one that turns out
   to be a shortcut.
2. **Two genuine decision-correct / analysis-wrong cases exist** (`C_median_age_at_failure`,
   `C_km_default_no_thought`): both are off by ~+148% on the graded quantity and still reach the
   right business decision 7/7. This is the property G24 and G05 showed is necessary — the decision
   alone cannot carry the grade.

## Constant-decision attack

Constant "hold" is correct **48/60 pooled (80%)**, but unanimously wrong (0/12) in `robust_units`.
Because each regime's decision is unanimous rather than seed-dependent, a frozen fixture set of two
"hold" and two "extend" extracts defeats a constant answer outright. Manageable, not a kill.

## Representation-leakage audit

| Check | Result |
|---|---|
| `unit_id` vs observed age | corr **+0.0015** — no leak |
| `sensor_gap` vs failure | corr **+0.0010** — the dropout flag is genuinely uninformative |
| `commissioned_month` vs observed age | corr −0.836 — **mechanical and correct**: later-commissioned units are younger. This is the truncation structure itself, not an artefact, and an analyst must reason about it rather than be protected from it |
| **row order** | records are emitted in `unit_id` order — **would need shuffling in a build** |
| removal-reason frequencies | overhaul 5526 / failure 2351 / decommission 119 / still in service 6294 — operationally plausible for an 18-month overhaul policy |

## Graded-fact evidence audit

For every quantity the design would grade, the question "what evidence would a real analyst have?":

| Graded fact | Evidence | Verdict |
|---|---|---|
| age at entry | commissioning date (asset register) + monitoring go-live | observable |
| event indicator | work-order removal reason | observable |
| risk-set membership | removal record absent ⇒ still in service | observable |
| whether a sensor gap is a removal | no work-order record exists | observable |
| net vs crude estimand | maintenance policy document states the overhaul interval and its basis | observable |
| the overhaul policy is age-based, not condition-based (I2) | policy document + checkable by regressing overhaul age on condition indicators | observable |

No graded fact depends on a convention only the generator knows. This is the check that G33 failed
and that caught the `exit < entry` generator bug here.
