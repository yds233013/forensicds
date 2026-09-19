# Cross-task failure matrix

A shared frame for reporting where frontier agents fail across the benchmark. Stages S0–S9 are the brief's; the
mappings for Task 02, G08, G10, G24 and G05 are **tentative** — they are re-readings of existing baseline
analyses under a common vocabulary, not fresh trajectory work, and should be re-derived from the trajectories
before this matrix is used in a final report.

| Stage | Meaning |
|---|---|
| **S0** | incident recognition — does the agent understand what is being claimed and disputed |
| **S1** | evidence discovery — does it open the artefacts that carry the mechanism |
| **S2** | operational-state reconstruction — dates, eligibility, joins, grain, the exact population |
| **S3** | target / estimand specification — what quantity actually answers the question |
| **S4** | statistical object construction — the right unit, weights, population, outcome |
| **S5** | identification / model assumptions — stating and testing what makes the estimate valid |
| **S6** | estimator implementation — does the code do what the plan says |
| **S7** | falsification / scientific validation — testing its own analysis, not the incumbent's |
| **S8** | uncertainty |
| **S9** | business decision |

## Where each task's failures landed

✗ = primary failure stage, ~ = partial/inconsistent, ✓ = done correctly by most trials.

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Task 02** (0/3) | ✓ | ~ | **✗** | ~ | ~ | — | ~ | ✗ | — | — |
| **G08** (1/3) | ✓ | **✗** | ✗ | ~ | ~ | — | ~ | ✗ | — | ~ |
| **G10** (0/3) | ✓ | ✓ | ✓ | ~ | **✗** | ✗ | ~ | ✗ | ✗ | ~ |
| **G24** (0/3) | ✓ | ✓ | ~ | ✓ | **✗** | ~ | ✓ | ✗ | ~ | ✓ |
| **G05** (0/3) | ✓ | ~ | **✓** | ~ | ✗ | **✗** | ✓ | ✗ | ✗ | ~ |
| **G31** (proposed) | — | — | — | — | — | — | — | — | — | — |

Reading the columns rather than the rows is the point:

- **S2 (operational-state reconstruction)** is where the early tasks failed and where the later ones stopped
  failing. G05's three valid trials reconstructed the analysis panel exactly on four extracts. The benchmark has
  measured this capability and, for this model, it is largely solved.
- **S7 (falsification)** is failed by **every task, every trial, without exception.** Across Task 02, G08, G10,
  G24 and G05 there is not one trial that tested its own specification. This is the most robust finding the
  benchmark has produced, and no task currently isolates it.
- **S4 and S5** are where the frontier now sits: the right method applied to the wrong object (G24, G05), or the
  right object with an unstated assumption (G05).
- **S9 is not diagnostic.** G24 got 12/12 decisions right while failing, G05 2/3. Decision-only grading would
  have scored both tasks as successes.

## What G31 would uniquely probe

G31's whole difficulty sits at **S3–S5**, with S2 made deliberately easy:

| Stage | G31's design intent |
|---|---|
| S2 | **deliberately easy.** Scores exist for every row, the policy is stationary and documented, the decision log is clean. There is no point-in-time puzzle. If an agent fails here, the task has a defect |
| **S3** | the estimand is defined over the **full eligible population** including blocked authorisations. An agent that specifies it over the settled or labelled population has already lost — this is `W3`, and it fails while looking rigorous |
| **S4** | the statistical object is the fraud-**value** total over that population, reconstructed from three different label mechanisms. `W10` gets everything else right and counts transactions instead of dollars |
| **S5** | identification rests on the logged bypass being randomised and on a maturity horizon estimated from mature cohorts. Both are checkable in the data. `W7` is the agent that sees selection, reaches for weights, and reconstructs the wrong probability |
| S7 | the artefacts support several direct self-checks — compare holdout and non-holdout covariate distributions within band; compare the fraud rate among reviewed rows against the band's bypass-implied rate; recompute on a fully mature cohort only. **Whether the agent runs any of them is the measurement we most want** |

**The distinct capability claim:** no current task requires the agent to reason about **why a label exists at
all**. Task 02 asks when a feature was knowable; G10 asks what a censored quantity would have been; G24 asks which
action was taken and with what probability; G05 asks what would have happened without treatment. G31 asks: *given
that the incumbent model decided who would ever be measurable, on what population can its successor be judged?*

If G31 is built and the model fails at S7 again — obtaining a coherent number and not testing it — that is the
fifth independent confirmation of the benchmark's strongest finding. If it fails at S3/S5 specifically, it
sharpens the S4/S5 result from G24 and G05. If it passes, the hypothesis is in trouble, which is the point of
running it.
