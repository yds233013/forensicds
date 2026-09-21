# G36 - FY27 residential capacity gate under a mandatory time-of-use tariff

**Research commit `5f99972` (design, recommendation A). This directory now also carries the
implementation-phase records.**

No model of any kind has seen this task: no Gemini, no Claude, no target-model call, at any stage.

## The design in one paragraph

A utility must decide whether to procure peaking capacity for next summer. Two flat-tariff seasons
identify the **stable** mechanism - cooling degree days drive peak-window load, and a tariff cannot
change building physics. A mandatory time-of-use tariff changes the **unstable** mechanism,
behaviour, observed only in a voluntary pilot that randomised the tariff *inside* its opt-in group.
Two independent facts stop the pilot's answer transporting to the estate: the customers who
volunteered are far more responsive than the estate (enrolment over-representation 0.32x to 2.49x by
segment), and the response fades as cooling demand rises while the pilot season was milder than the
target is forecast to be. **Fixing either one alone still gives the wrong capacity decision.**

## Implementation-phase documents

| file | contents |
|---|---|
| `threshold_provenance.md` | **why the decision threshold is 3.057 kW**, and the explicit rejection of a margin-maximising choice |
| `development_defect_log.md` | **seven defects found during construction**, five of them in my own measurement apparatus |
| `estimator_independence.md` | why F1/F2/F3 are genuinely independent, and the corrected K9 acceptance test |
| `graded_fact_evidence_implementation.md` | one row per verifier check; every row confirmed not generator-only and not future-dependent |

## Design-phase documents

`concept_map.md`, `domain_tournament.md`, `incident_tournament.md`, `formal_designs.md`,
`identification.md`, `recognition_execution_gate.md`, `wrong_methods.md`, `valid_methods.md`,
`simulation.py`, `gates.py`, `f2_repricing.py`, `simulation_results.md`, `correct_table_gate.md`,
`coherent_wrong_gate.md`, `cheap_solve_gate.md`, `falsification_design.md`,
`representation_leakage.md`, `graded_fact_evidence.md`, `distinctness_matrix.md`,
`model_failure_predictions.md`, `build_recommendation.md`.

## The two findings worth carrying forward

**Threshold provenance is a scientific property, not a tuning knob.** I initially selected 2.825 kW because it maximised the minimum decision margin across fixtures. That is
threshold-hacking: it makes the difficulty an artefact of where the line was drawn. The adopted
threshold follows from the utility's capacity position (1,900 MW firm, 10 % reserve, 565,000
customers) using the historical record only, and the fixture outcomes were accepted as they fell.

**Five of seven construction defects were in the measurement apparatus, not the task.** A truth that
returned the median instead of the mean, an estimator mislabelled as independent, a ratio bias, a
confounded negative control, and a wrong statistic in a leakage probe. Each would have produced a
confident, internally consistent, wrong conclusion - the exact failure mode this benchmark exists to
detect, occurring in its own construction. The defence each time was an independent measurement that
disagreed, taken seriously rather than explained away.
