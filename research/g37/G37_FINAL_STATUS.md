# G37 — FINAL STATUS: CLOSED, DROP / RESEARCH-ONLY (2026-09-21)

| | |
|---|---|
| direction | measurement-system change / errors-in-variables |
| status | **DROP / RESEARCH-ONLY** (external review decision) |
| candidate built | **NO** |
| Gemini trials | **NONE** |
| model spend | **$0** |
| Harbor | **NONE** |
| research record | commit `81ed909`, preserved unchanged; this note is the only addition |
| primary blocker | **no scientific tolerance window**: VALID_BOUND 5.57, WRONG_BOUND 0.04, ratio ≈ 0.01 |
| secondary blocker | recognition/execution collapses once both measurement-error insights are given; the remaining subtle mistakes cannot be distinguished statistically |
| benchmark arithmetic | **not counted** |

**Structural finding.** When measurement error is large enough for the correction to matter
materially, the uncertainty of legitimate latent-variable estimators also becomes large. Once
first-order mistakes are removed, realistic second-order wrong methods lie inside that legitimate
uncertainty. The design therefore cannot sharply grade the subtle execution failures it was meant to
study.

**Not to be pursued** (review decision):
- relaxing the ≥ 3 criterion;
- the tail-fraction variant;
- other domains within measurement error;
- any measurement-error candidate.
