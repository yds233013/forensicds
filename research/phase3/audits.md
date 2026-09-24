# Falsification-route, multiple-valid-method and cheap-solve audits

Every route below was implemented and run, not reasoned about. The commands are in
`scripts/validate_phase3.sh`; the recorded outputs are in `tools/p22|p20|p31/`.

## Falsification routes

A route counts only if the evidence is in the **agent's** workspace, if the competing hypotheses predict
different outcomes, and if the outcome in the generated world is recorded. A coherence check does not count;
neither does a robustness check that cannot come out differently.

### P22 — three routes

| route | hypothesis A (material) predicts | hypothesis B (measurement) predicts | actual, visible extract | why it discriminates |
|---|---|---|---|---|
| retained reference artefacts, pre vs post adjustment, CMM-1 | 0 µm paired difference — the artefacts are unchanged metal | ≈ the offset | **+8.95 µm** (design value 8.20; two-machine route 7.97) | the artefacts' geometry cannot have changed, so any movement is the instrument |
| the second, un-adjusted machine | its nonconforming rate rises too | its rate is flat across week 19 | CMM-2 pre **2.82 %** vs post **3.43 %**; CMM-1 post **7.2 %** | the rota assigns parts to machines independently of geometry |
| functional leak test (no CMM) | leak-fail rate rises roughly in proportion | rises only by the material component | tracks the corrected rate, not the reported one | the rig is a pressure test |

The corrected rate from the bridge (3.90 %) and the un-adjusted machine's own rate (3.43 %) agree to 0.47 pp,
inside the 0.7 pp tolerance — the verifier requires that agreement as `independent_validation`.

### P20 — three routes

| route | hypothesis A (drift) predicts | hypothesis B (policy feedback) predicts | actual, visible extract |
|---|---|---|---|
| evaluate on the clinics outside the programme | AUC has fallen there too | AUC is unchanged there | **0.790** against a validation figure of **0.770** — no degradation at all |
| evaluate the candidate on that same population | the candidate is better | the candidate is **worse**, having learned the programme's footprint | candidate **0.764** vs incumbent **0.790** |
| replay the feature vintage from the event log | no gap between vintages | a measurable gap | as-served **0.790** vs current feature store **0.764** |

On hidden_a the first route comes out the other way (0.695 against a floor of 0.730) and the second favours the
candidate by +0.15, which is why `replace_with_v4` is correct there. That is the point of the route: it can come
out either way.

### P31 — three routes

| route | hypothesis A (report wrong) predicts | hypothesis B (definitional) predicts | actual, visible extract |
|---|---|---|---|
| the agreement's definition clause | the denominator is requested quantity | it is confirmed quantity | §7.2 states confirmed quantity explicitly, and the supplier's own appendix §A2 states it uses requested |
| ticket reconciliation | tickets map to short deliveries | a large share carry return reason codes, which §7.4 excludes | **42 %** of tickets point at a line carrying a return |
| the customers' own goods-receipt confirmations | reproduce the supplier's figure | reproduce the contractual figure | **97.65 %**, the contractual figure, from a different system |

## Multiple-valid-method audit

| task | accepted routes | status |
|---|---|---|
| P22 | (a) paired retained-artefact bridge; (b) departure of the post-adjustment artefact readings from the NML certified values; (c) two-machine difference in differences; (d) the un-adjusted machine's own rate as the corrected rate | all four implemented in `world.routes()`; worst spread from the design value **0.75 µm** on the offset and **0.47 pp** on the corrected rate, both inside tolerance. (b) is mutation **M00** and scores **1** |
| P20 | (a) twelve-week window; (b) ten-week window; (c) `bisect` or linear reconstruction of the as-of feature | (b) is mutation **M00** and scores **1**. Not accepted, and documented as a limitation: a model the agent trains itself, because its AUC is model-class dependent and therefore not identifiable |
| P31 | (a) `delivered >= target`; (b) the same test as "no shortfall against target"; (c) either reading of Schedule 4, provided both are reported and the consequences settled only where they agree | (b) is mutation **M00** and scores **1**. (c) is the graded structure, not an alternative to it |

**Where two routes could disagree materially, the disagreement is the graded object rather than a tolerance
problem**: P31's Schedule 4 range, and P22's observational-vs-bridge offset spread which sets the tolerance.

## Cheap-solve and exploit audit

Each shortcut was implemented and run through the real verifier.

| shortcut | P22 | P20 | P31 |
|---|---|---|---|
| documentation lookup only | no output → schema failure | same | same |
| reproduce the incumbent report | **Nop = 0**, 0 of 7 criteria | **Nop = 0**, 0 of 7 | **Nop = 0** (see readiness) |
| one obvious filter | M12 (one machine's stratum) → 0 | M01/M02 (wrong population) → 0 | M06 (cancelled lines) → 0 |
| one obvious join | M02 (certificate figure) → 0 on 3 of 4 extracts | M04 (candidate scores as served) → 0 | M01 (reproduce the supplier) → 0 |
| one doc lookup for the answer | the certificate does not give the feature offset (QP-07 §4, and the numbers) | the standard names no population | the agreement's clause must be read against the code |
| decision-only guess | **E01** → 0 (fails hidden_b) | **E01** → 0 (fails hidden_a, hidden_b) | **E01** → 0 (fails hidden_a, hidden_c) |
| hardcoded visible answers | **E00** → 0 | **E00** → 0 | **E00** → 0 |
| always reject the incumbent | n/a | n/a | **M07** → 0 |
| always accept the incumbent | n/a | n/a | **M09** → 0 |
| always defer | n/a | n/a | **M08** → 0 |
| hedge across every cause | **M14** → 0 | **M13** → 0 | **M12** → 0 |
| exploit exposed fixture values | `scenarios.py` and `truth()` are in `/tests` only; `/tests` is mode 700 and the verifier **refuses to grade** if the pipeline user can read it |
| exploit predictable seeds | the generator is not in the shipped image (multi-stage build; the final stage copies only `/workspace`) and the hidden specs are not in the build context at all |
| exploit the scoring implementation | same as above; the verifier also checks the interpreter, standard library and sandbox tools against `runtime_manifest.sha256` and refuses on any difference |

**Adversarial exploit agent: not run.** No non-target-model agent was available in this environment, and running
a target model is forbidden this phase. The exploit probes above are hand-written equivalents and are labelled as
such; this is recorded as an open gate in the readiness report rather than claimed as an agent audit.
