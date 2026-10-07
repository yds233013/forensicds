# P20 — no-show model monitoring (deployment feedback)

Second of the three prospective-validation tasks from `research/phase2/HANDOFF_2026-09-23.md`. Scientific
specification: `research/phase3/spec_p20.md`. Evidence register: `research/phase3/register_p20.md`.

**Mechanism.** Policy feedback on the evaluation population. The model's output drives reminder calls, the
calls change attendance, and the monitored metric is computed on the population those calls acted upon - so the
model's own successes destroy its measured discrimination. A textbook MLOps response (drift metrics, temporal
validation, adopt the retrained candidate) is available, reconciles with the dashboard, and is wrong.

**What is graded.** The dashboard figure and the registry figure; the population MRM-04 requires; the model's
discrimination under four scoring bases on that population; the feature-feed defect share; the programme's
effect; a five-way decomposition of the gap; and the action MRM-04 requires. `reward.json` carries one
criterion per stage of the scientific chain beside the binary reward.

**Anti-pattern insurance.** The four graded extracts require three different actions. One is
policy-feedback-dominant (retain), one has a genuine new driver of attendance the model cannot see so the
candidate legitimately wins (replace), one has a failed feature-enrichment join so the remedy is the feed and
not the model (remediate), and one is vintage-dominant (retain). Neither "never retrain" nor "adopt the
retrain" passes.
