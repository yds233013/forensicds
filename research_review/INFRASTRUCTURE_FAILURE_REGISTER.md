# Infrastructure-failure register

Every attempt that did **not** produce a graded model result. **None of these is counted as a model
failure** anywhere in the dossier. Each row is reproducible from the raw path.

**Total invalid attempts: 45** across both arms.

## By cause

| cause | count | what it means |
|---|---|---|
| `credit-balance-too-low` | 20 | Anthropic account credit exhausted mid-run. Agent returned `billing_error` / HTTP 400 after 2 steps, $0.00 spend, empty workspace. Verifier then graded an empty submission, which is why the criteria read all-zero. |
| `verifier-refused` | 6 | `g50`'s frozen verifier hash-pins the runtime; a scaffold that installs its own tooling changes a pinned file and the verifier refuses rather than grading. |
| `agent-setup-timeout` | 3 | Harbor agent setup exceeded its timeout (host contention). |
| `verifier-refused-ldsocache` | 3 | First `g50` exposure. `/etc/ld.so.cache` was hash-pinned; `apt-get` runs `ldconfig`, which regenerates it. |
| `api-key-rejected` | 3 | Provider rejected the credential. |
| `free-tier-quota` | 3 | Free-tier quota exhausted. |
| `free-tier-rpm-stopped` | 3 | Free-tier rate limit halted the run. |
| `session-interrupted-during-agent-setup` | 3 | Operator session interrupted during setup. |
| `verifier-refused-agent-did-run` | 1 | Same refusal, but with the agent demonstrably funded and active (16 steps, $0.66) — this is the de-confounded confirmation. |

## Full register

| arm | task | job | trial | cause | steps | cost | raw path |
|---|---|---|---|---|---|---|---|
| claude | `g08-forecast-accuracy-vintages` | `claude-g08-forecast-accuracy-vintages-1__INVALID-credit-balance-too-low` | `g08-forecast-accuracy-vintages__e3KqGBF` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g08-forecast-accuracy-vintages-1__INVALID-credit-balance-too-low/g08-forecast-accuracy-vintages__e3KqGBF` |
| claude | `g08-forecast-accuracy-vintages` | `claude-g08-forecast-accuracy-vintages-2__INVALID-credit-balance-too-low` | `g08-forecast-accuracy-vintages__oV2yYFj` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g08-forecast-accuracy-vintages-2__INVALID-credit-balance-too-low/g08-forecast-accuracy-vintages__oV2yYFj` |
| claude | `g08-forecast-accuracy-vintages` | `claude-g08-forecast-accuracy-vintages-3__INVALID-credit-balance-too-low` | `g08-forecast-accuracy-vintages__n6N9fyt` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g08-forecast-accuracy-vintages-3__INVALID-credit-balance-too-low/g08-forecast-accuracy-vintages__n6N9fyt` |
| claude | `g24-recommender-ope` | `claude-g24-recommender-ope-1__INVALID-credit-balance-too-low` | `g24-recommender-ope__qP3oeYt` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g24-recommender-ope-1__INVALID-credit-balance-too-low/g24-recommender-ope__qP3oeYt` |
| claude | `g24-recommender-ope` | `claude-g24-recommender-ope-2__INVALID-credit-balance-too-low` | `g24-recommender-ope__2GQAcaH` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g24-recommender-ope-2__INVALID-credit-balance-too-low/g24-recommender-ope__2GQAcaH` |
| claude | `g24-recommender-ope` | `claude-g24-recommender-ope-3__INVALID-credit-balance-too-low` | `g24-recommender-ope__jYX6kuF` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g24-recommender-ope-3__INVALID-credit-balance-too-low/g24-recommender-ope__jYX6kuF` |
| claude | `g36-tou-capacity-gate` | `claude-g36-tou-capacity-gate-1__INVALID-credit-balance-too-low` | `g36-tou-capacity-gate__nPeAo59` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g36-tou-capacity-gate-1__INVALID-credit-balance-too-low/g36-tou-capacity-gate__nPeAo59` |
| claude | `g36-tou-capacity-gate` | `claude-g36-tou-capacity-gate-2__INVALID-credit-balance-too-low` | `g36-tou-capacity-gate__uKBELHi` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g36-tou-capacity-gate-2__INVALID-credit-balance-too-low/g36-tou-capacity-gate__uKBELHi` |
| claude | `g36-tou-capacity-gate` | `claude-g36-tou-capacity-gate-3__INVALID-credit-balance-too-low` | `g36-tou-capacity-gate__ScHsj2y` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g36-tou-capacity-gate-3__INVALID-credit-balance-too-low/g36-tou-capacity-gate__ScHsj2y` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-1__INVALID-credit-balance-too-low` | `g50-courier-boost-rollout__GfQTCRY` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-1__INVALID-credit-balance-too-low/g50-courier-boost-rollout__GfQTCRY` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-1__INVALID-verifier-refused` | `claude-g50-courier-boost-rollout-1` | `verifier-refused` | — | — | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-1__INVALID-verifier-refused/claude-g50-courier-boost-rollout-1` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-1__INVALID-verifier-refused` | `g50-courier-boost-rollout__A5bPR5U` | `verifier-refused` | 2 | 0.0 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-1__INVALID-verifier-refused/g50-courier-boost-rollout__A5bPR5U` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-1__INVALID-verifier-refused-agent-did-run` | `g50-courier-boost-rollout__6pHEtw7` | `verifier-refused-agent-did-run` | 16 | 0.6593851999999999 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-1__INVALID-verifier-refused-agent-did-run/g50-courier-boost-rollout__6pHEtw7` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-2__INVALID-credit-balance-too-low` | `g50-courier-boost-rollout__oDoYNbL` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-2__INVALID-credit-balance-too-low/g50-courier-boost-rollout__oDoYNbL` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-2__INVALID-verifier-refused` | `claude-g50-courier-boost-rollout-2` | `verifier-refused` | — | — | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-2__INVALID-verifier-refused/claude-g50-courier-boost-rollout-2` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-2__INVALID-verifier-refused` | `g50-courier-boost-rollout__qGycs8G` | `verifier-refused` | 2 | 0.0 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-2__INVALID-verifier-refused/g50-courier-boost-rollout__qGycs8G` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-3__INVALID-credit-balance-too-low` | `g50-courier-boost-rollout__2HZJVRL` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-3__INVALID-credit-balance-too-low/g50-courier-boost-rollout__2HZJVRL` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-3__INVALID-verifier-refused` | `claude-g50-courier-boost-rollout-3` | `verifier-refused` | — | — | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-3__INVALID-verifier-refused/claude-g50-courier-boost-rollout-3` |
| claude | `g50-courier-boost-rollout` | `claude-g50-courier-boost-rollout-3__INVALID-verifier-refused` | `g50-courier-boost-rollout__tgY6hWE` | `verifier-refused` | 2 | 0.0 | `crossmodel_logs/claude/claude-g50-courier-boost-rollout-3__INVALID-verifier-refused/g50-courier-boost-rollout__tgY6hWE` |
| claude | `p20-noshow-monitoring` | `claude-p20-noshow-monitoring-1__INVALID-credit-balance-too-low` | `p20-noshow-monitoring__PMcSqMB` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p20-noshow-monitoring-1__INVALID-credit-balance-too-low/p20-noshow-monitoring__PMcSqMB` |
| claude | `p20-noshow-monitoring` | `claude-p20-noshow-monitoring-2__INVALID-credit-balance-too-low` | `p20-noshow-monitoring__8KA3gUX` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p20-noshow-monitoring-2__INVALID-credit-balance-too-low/p20-noshow-monitoring__8KA3gUX` |
| claude | `p20-noshow-monitoring` | `claude-p20-noshow-monitoring-3__INVALID-credit-balance-too-low` | `p20-noshow-monitoring__HWJivHD` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p20-noshow-monitoring-3__INVALID-credit-balance-too-low/p20-noshow-monitoring__HWJivHD` |
| claude | `p22-gauge-recalibration` | `claude-p22-gauge-recalibration-2__INVALID-credit-balance-too-low` | `p22-gauge-recalibration__kuUVv69` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p22-gauge-recalibration-2__INVALID-credit-balance-too-low/p22-gauge-recalibration__kuUVv69` |
| claude | `p22-gauge-recalibration` | `claude-p22-gauge-recalibration-3__INVALID-credit-balance-too-low` | `p22-gauge-recalibration__wZe47bz` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p22-gauge-recalibration-3__INVALID-credit-balance-too-low/p22-gauge-recalibration__wZe47bz` |
| claude | `p31-fill-rate-dispute` | `claude-p31-fill-rate-dispute-1__INVALID-credit-balance-too-low` | `p31-fill-rate-dispute__YKQcaym` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p31-fill-rate-dispute-1__INVALID-credit-balance-too-low/p31-fill-rate-dispute__YKQcaym` |
| claude | `p31-fill-rate-dispute` | `claude-p31-fill-rate-dispute-2__INVALID-credit-balance-too-low` | `p31-fill-rate-dispute__FsxbpBV` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p31-fill-rate-dispute-2__INVALID-credit-balance-too-low/p31-fill-rate-dispute__FsxbpBV` |
| claude | `p31-fill-rate-dispute` | `claude-p31-fill-rate-dispute-3__INVALID-credit-balance-too-low` | `p31-fill-rate-dispute__Rzuodrc` | `credit-balance-too-low` | 2 | 0.0 | `crossmodel_logs/claude/claude-p31-fill-rate-dispute-3__INVALID-credit-balance-too-low/p31-fill-rate-dispute__Rzuodrc` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-api-key-rejected` | `01-revenue-reconciliation__EFJtarZ` | `api-key-rejected` | 1 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-api-key-rejected/01-revenue-reconciliation__EFJtarZ` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-api-key-rejected` | `01-revenue-reconciliation__YLz8Tfi` | `api-key-rejected` | 1 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-api-key-rejected/01-revenue-reconciliation__YLz8Tfi` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-api-key-rejected` | `01-revenue-reconciliation__vuSqLhS` | `api-key-rejected` | 1 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-api-key-rejected/01-revenue-reconciliation__vuSqLhS` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-free-tier-quota` | `01-revenue-reconciliation__FaaYr8C` | `free-tier-quota` | 9 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-free-tier-quota/01-revenue-reconciliation__FaaYr8C` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-free-tier-quota` | `01-revenue-reconciliation__kTv9yzy` | `free-tier-quota` | 17 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-free-tier-quota/01-revenue-reconciliation__kTv9yzy` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-free-tier-quota` | `01-revenue-reconciliation__kWjeaHh` | `free-tier-quota` | 15 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-free-tier-quota/01-revenue-reconciliation__kWjeaHh` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped` | `01-revenue-reconciliation__5rCytnc` | `free-tier-rpm-stopped` | 3 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped/01-revenue-reconciliation__5rCytnc` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped` | `01-revenue-reconciliation__L976rTV` | `free-tier-rpm-stopped` | 3 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped/01-revenue-reconciliation__L976rTV` |
| gemini | `01-revenue-reconciliation` | `task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped` | `01-revenue-reconciliation__oBwDoNf` | `free-tier-rpm-stopped` | 13 | — | `jobs/task01-gemini3flash-diagnosis__INVALID-free-tier-rpm-stopped/01-revenue-reconciliation__oBwDoNf` |
| gemini | `02-renewal-risk-regression__explicit-invariant` | `task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup` | `02-renewal-risk-regression__expl__XqMDsHt` | `session-interrupted-during-agent-setup` | — | — | `jobs/task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup/02-renewal-risk-regression__expl__XqMDsHt` |
| gemini | `02-renewal-risk-regression__explicit-invariant` | `task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup` | `02-renewal-risk-regression__expl__ZXkWu4v` | `session-interrupted-during-agent-setup` | — | — | `jobs/task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup/02-renewal-risk-regression__expl__ZXkWu4v` |
| gemini | `02-renewal-risk-regression__explicit-invariant` | `task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup` | `02-renewal-risk-regression__expl__zmti9PZ` | `session-interrupted-during-agent-setup` | — | — | `jobs/task02-gemini3flash-explicit-invariant__INVALID-session-interrupted-during-agent-setup/02-renewal-risk-regression__expl__zmti9PZ` |
| gemini | `g08-forecast-accuracy-vintages` | `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | `g08-forecast-accuracy-vintages__YGnxp6B` | `agent-setup-timeout` | — | — | `jobs/g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout/g08-forecast-accuracy-vintages__YGnxp6B` |
| gemini | `g08-forecast-accuracy-vintages` | `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | `g08-forecast-accuracy-vintages__fPfGQX3` | `agent-setup-timeout` | — | — | `jobs/g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout/g08-forecast-accuracy-vintages__fPfGQX3` |
| gemini | `g08-forecast-accuracy-vintages` | `g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout` | `g08-forecast-accuracy-vintages__hd7ACNA` | `agent-setup-timeout` | — | — | `jobs/g08-gemini3flash-baseline-1__INVALID-agent-setup-timeout/g08-forecast-accuracy-vintages__hd7ACNA` |
| gemini | `g50-courier-boost-rollout` | `g50-gemini3flash-baseline-1__INVALID-verifier-refused-ldsocache` | `g50-courier-boost-rollout__oi5LLwQ` | `verifier-refused-ldsocache` | 38 | — | `jobs/g50-gemini3flash-baseline-1__INVALID-verifier-refused-ldsocache/g50-courier-boost-rollout__oi5LLwQ` |
| gemini | `g50-courier-boost-rollout` | `g50-gemini3flash-baseline-2__INVALID-verifier-refused-ldsocache` | `g50-courier-boost-rollout__5zpVc4k` | `verifier-refused-ldsocache` | 28 | — | `jobs/g50-gemini3flash-baseline-2__INVALID-verifier-refused-ldsocache/g50-courier-boost-rollout__5zpVc4k` |
| gemini | `g50-courier-boost-rollout` | `g50-gemini3flash-baseline-3__INVALID-verifier-refused-ldsocache` | `g50-courier-boost-rollout__BNSAPAD` | `verifier-refused-ldsocache` | 48 | — | `jobs/g50-gemini3flash-baseline-3__INVALID-verifier-refused-ldsocache/g50-courier-boost-rollout__BNSAPAD` |

## Why this register exists

An ungraded attempt carries no information about model capability. Two of the causes above were
**our own defects**, not provider problems:

- the `g50` verifier refusals (a runtime hash-pin incompatible with any real agent scaffold), and
- the all-zero criteria produced when the verifier graded an empty workspace after a billing failure,
  which would have looked like a catastrophic model failure if read from `reward.json` alone.

The second is the reason this dossier derives validity from the **trajectory** (did the agent act?) and
the **verifier stdout** (did it refuse?), not from the reward value.
