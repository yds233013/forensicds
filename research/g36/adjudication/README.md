# G36 adjudication

**Status: adjudication and redesign research only.** No candidate was modified, no model was called,
no `harbor check` was run, and nothing was built.

Original frozen G36 (`85197582fa38141d`, commit `a2196df`, verifier `776c3e59326665c1`) is permanently
unchanged. Its baseline result, **0/3**, is recorded as **contaminated by an F8 benchmark definition
defect** and is not rewritten.

| file | question it answers |
|---|---|
| `response_estimand.md` | what the response *should* be, from the planning problem and contract text alone |
| `submission_replay.md` | what the three saved submissions score under each candidate definition |
| `graded_quantity_independence.md` | why K9 missed it; the new IGQA rule; retrospective risk for G05/G10/G24/G34/G35 |
| `selection_transport_postmortem.md` | which artefacts handed over the selection transport |
| `selection_redesign_options.md` | seven ways selection could be made live, scored |
| `contamination_analysis.md` | which proposed changes survive "would I have proposed this without the trajectories?" |
| `recommendation.md` | **A - minimal adjudicated revision**, not built, and what the numbers mean |
| `definition_se.py`, `definition_se.json` | sampling SE for each candidate definition, from the frozen generator |

## The two general lessons

**1. Independent estimator validation is not enough if the estimators share a definition.** K9 proved
three families agreed on the forecast. They also shared one helper for the response, so they agreed on
the response by construction - including on its wrong definition. A verifier can be statistically
robust about its main estimand and semantically wrong about an intermediate one. The remedy is IGQA:
computational independence **and** a derivation written from the contract text alone.

**2. Convergence of a model on an alternative reading is a signal, not a verdict.** Three trials
independently computing a load-weighted response was worth investigating. It did not prove the
benchmark wrong. The benchmark was adjudicated from domain semantics, and the adjudication would reach
the same conclusion had every trial used the verifier's definition.
