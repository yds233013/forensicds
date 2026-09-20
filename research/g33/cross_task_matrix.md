# Cross-task placement — where G33 would have sat

Stages S0–S9 as defined in `research/g31/cross_task_matrix.md`.

| | S0 | S1 | S2 | S3 | S4 | S5 | S6 | S7 | S8 | S9 |
|---|---|---|---|---|---|---|---|---|---|---|
| **Task 01** entity grain / identity | ✓ | ~ | **✗** | ~ | ✗ | — | ~ | ✗ | — | — |
| **Task 02** point-in-time state | ✓ | ~ | **✗** | ~ | ~ | — | ~ | ✗ | — | — |
| **G08** forecast vintages | ✓ | **✗** | ✗ | ~ | ~ | — | ~ | ✗ | — | ~ |
| **G10** censored demand | ✓ | ✓ | ✓ | ~ | **✗** | ✗ | ~ | ✗ | ✗ | ~ |
| **G24** off-policy evaluation | ✓ | ✓ | ~ | ✓ | **✗** | ~ | ✓ | ✗ | ~ | ✓ |
| **G05** staggered rollout | ✓ | ~ | ✓ | ~ | ✗ | **✗** | ✓ | ✗ | ✗ | ~ |
| **G31** (rejected) | — | — | — | intended **S3–S5** | | | | | | |
| **G33** (rejected) | — | — | — | intended **S3–S4** | | | | | | |

**Intended placement:** S3–S4 — "what is the object being measured?" — with S2 (reconstruction) as the
supporting work.

**Measured placement:** S3 alone, and only one bit of it. Once the grain is chosen, S4 is decided; the S2
reconstruction work contributes 0.6–8% relative error and is dominated by the grain choice. A task that
tests one bit of S3 is not worth a build.

**Relation to Task 01.** The claimed distinction — Task 01 repairs a documented mapping, G33 reconstructs the
entity from heterogeneous evidence — is real in the *design* but does not survive into the *measurement*,
because in G33 the reconstruction does not change the answer. Task 01's does, because revenue attribution is
a within-vs-between decomposition. That is the structural reason, and it generalises (see
`build_recommendation.md` §2).
