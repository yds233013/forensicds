# P22 — MAN-4471 yield step (gauge recalibration)

First of the three prospective-validation tasks from `research/phase2/HANDOFF_2026-09-23.md`. Scientific
specification: `research/phase3/spec_p22.md`. Evidence register: `research/phase3/register_p22.md`.

**Mechanism.** A measurement-system change. The pass/fail outcome is produced by an instrument whose bias
moved at a recalibration, while the drawing tolerance did not change, so "yield" is not comparable across the
step. The week-19 recalibration coincides with a genuine heat-family changeover, which makes a correct SPC and
capability study — control charts, Cp/Cpk, a significant ANOVA on heat family — reach the wrong conclusion
without any of its own checks failing.

**What is graded.** The offset on the feature for each measuring machine; the nonconforming rate against the
drawing's conformance reference; the population's strata; a five-way attribution of the change over a neutral
vocabulary (material, measurement system, tooling, operator, other); and the supplier decision under
Schedule 3 §3.2. `reward.json` carries one criterion per stage of the scientific chain beside the binary reward.

**Anti-pattern insurance.** The four graded extracts differ in which cause is active: one is almost pure
measurement, one has a genuinely bad heat family and **reverses the supplier decision**, and one has a real
tool-wear contribution from an extended insert-change interval. A constant answer cannot pass.
