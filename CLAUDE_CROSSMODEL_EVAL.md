# Claude cross-model evaluation on the frozen ForensicDS final ten

**Status: BLOCKED BEFORE ANY TRIAL WAS RUN.** No Claude trial has been executed. The blocker is
credential integrity, not infrastructure — see §2. Everything that does not require the credential is
complete, and the coding rules in §6 are **pre-registered here before any Claude data exists**, which is
the control Step 11 requires.

| | |
|---|---|
| timestamp (UTC) | 2026-09-30 |
| repository HEAD | `7e6d4d760995c7bd3729a8cbba31e5a31a8801fe` |
| Harbor version | 0.21.0 |
| benchmark modified? | **No. Nothing was touched.** |

---

## 1. The frozen final ten, verified

**Verification method.** Recorded per-task freeze manifests exist for only 4 of the 10 tasks
(`scripts/frozen_checksums.txt` covers `02`, `g05`, `g10`, `g24`; `g50` has its own five-group
`FREEZE_MANIFEST_V23.txt`). The authoritative record of the versions Gemini was actually evaluated on is
therefore the delivered submission archive, whose `samples/<task>/` trees were built from them:

```
submission_final10.zip
sha256 629476cd886bd16eeb206e952c26be41370f9f79b149fa21cda0ecdf7779af7e   [verified intact]
```

Each task directory was diffed against its copy inside that archive. **All ten are byte-identical**
(excluding `__pycache__`). No task differs from its evaluated version, so no stop condition was triggered
at Step 1.

| # | task | version | files | aggregate sha256 | matches evaluated version |
|---|---|---|---|---|---|
| 1 | `02-renewal-risk-regression` | v1 (exposed) | 55 | `b31eb4fe580477cf08a453a38ffaa8b545da19e5f7e9fc4096910f25f665cf88` | ✔ |
| 2 | `g05-sco-rollout-gate` | v1 | 39 | `7525ddb2ff902b42ad20a51c92f0fb392abd484a218ae6cf5d2c9bbb1c23bcc3` | ✔ |
| 3 | `g10-censored-demand` | v1 | 40 | `7c72dd098ce3bfcd3f1283adadf926837ef5969399d44f6b3fa33a6161802194` | ✔ |
| 4 | `g24-recommender-ope` | v1 | 43 | `505e59ccf71f93da82752cc73ba0546998ef41b72c0a8f9277e31ca820c5cce5` | ✔ |
| 5 | `g36-tou-capacity-gate` | v1 | 37 | `6cb3dd64e37a12864354194f836e2e9dbdf70a072af415abe4c15d9e68554512` | ✔ |
| 6 | `p20-noshow-monitoring` | v1 (exposed) | 43 | `62943714d631e6a9466b309a183f038ecd3628eed0fd0eed15225101552833eb` | ✔ |
| 7 | `p22-gauge-recalibration` | v1 | 41 | `8da6ed0e70dff9aaa459e1dbab019d37e998f534f6bdc128901233e97cef6a03` | ✔ |
| 8 | `p31-fill-rate-dispute` | v1 | 40 | `67fb8e658f8a468c8021263e4546f22213ce46c8b1fd8fda47185ea7eaa764e3` | ✔ |
| 9 | `g50-courier-boost-rollout` | **v2.3** (five worlds) | 43 | `656a5a166d37962f2bf867818876bf1b544c81895c886ae25d4ac7da687390e9` | ✔ |
| 10 | `g08-forecast-accuracy-vintages` | v1 | 39 | `a7f073a3402b1bc18ec3ba8278c0b1d79fbd0bfe7a936743f6d4f8da4da15e12` | ✔ |

The aggregate is `sha256` over each file's relative path and content, walked in sorted order, excluding
`__pycache__`. Recomputable with the snippet in §7.

`g50`'s own five-group freeze (`FREEZE_MANIFEST_V23.txt`) also still holds: group A (target-visible)
`ba92e8ccdcecdb58`, B (generator) `49ad4801be5a7e99`, C (verifier) `61f28c84be5de2aa`,
D (oracle) `23a5fa730ee9dacc`.

## 2. Gemini baseline (the comparison arm)

| task | valid trials | passes | pass@1 | pass@3 |
|---|---|---|---|---|
| `02-renewal-risk-regression` | 3 | 0 | 0.0% | 0 |
| `g05-sco-rollout-gate` | 4 | 0 | 0.0% | 0 |
| `g10-censored-demand` | 3 | 0 | 0.0% | 0 |
| `g24-recommender-ope` | 3 | 0 | 0.0% | 0 |
| `g36-tou-capacity-gate` | 3 | 0 | 0.0% | 0 |
| `p20-noshow-monitoring` | 3 | 0 | 0.0% | 0 |
| `p22-gauge-recalibration` | 3 | 0 | 0.0% | 0 |
| `p31-fill-rate-dispute` | 3 | 0 | 0.0% | 0 |
| `g50-courier-boost-rollout` | 3 | 0 | 0.0% | 0 |
| `g08-forecast-accuracy-vintages` | 3 | 1 | 33.3% | 1 |
| **suite** | **31** | **1** | **3.2%** | **10%** |

Model `google/gemini-3-flash-preview`, agent `gemini-cli`.

## 3. THE BLOCKER — credential integrity

**Step 2 of the assignment states: "The previously exposed Anthropic key should NOT be used if it has not
been rotated."**

The key was printed in plaintext in the working transcript during the previous session. Checked without
printing any secret:

| check | result |
|---|---|
| `ANTHROPIC_API_KEY` present in profile | yes, length 108 |
| still carries the distinctive prefix of the exposed key | **YES — NOT ROTATED** |
| sha256 fingerprint (first 12) | `10b97de263f9` |
| `CLAUDE_CODE_OAUTH_TOKEN` | absent |
| `ANTHROPIC_AUTH_TOKEN` | absent |
| `CLAUDE_CODE_USE_BEDROCK` / AWS credentials | absent |
| `CLAUDE_CODE_USE_VERTEX` / `ANTHROPIC_VERTEX_PROJECT_ID` / `GOOGLE_APPLICATION_CREDENTIALS` | absent |
| `~/.claude/.credentials.json` | absent |
| distinct `ANTHROPIC_API_KEY` entries in the profile | 1 |

**There is exactly one Anthropic credential on this machine and it is the compromised one.** No secret was
printed to obtain this: the rotation test compared a prefix and emitted only a boolean, and the fingerprint
is a hash.

I did not run the trials. Reasons, in order:

1. The assignment prohibits it explicitly.
2. It would drive roughly 30 agent sessions of billable usage through a credential that is readable by
   anyone with access to the previous transcript.
3. This session's own `ANTHROPIC_BASE_URL` and `CLAUDE_CODE_MESSAGING_TOKEN` are the harness's internal
   credentials. Repurposing them to drive a benchmark evaluation would be misusing session infrastructure,
   so I did not consider them an alternative.

**What unblocks it:** rotate the key at <https://console.anthropic.com/settings/keys>, revoke the old one,
put the new value in the profile, and re-run §5. The whole experiment is one command.

## 4. Claude configuration, determined not guessed

Read from the installed Harbor at
`/opt/anaconda3/lib/python3.13/site-packages/harbor/agents/installed/claude_code.py`:

| item | value | evidence |
|---|---|---|
| agent | **`claude-code`** | `AgentName.CLAUDE_CODE = "claude-code"` in `harbor/models/agent/name.py` |
| credentials forwarded | `ANTHROPIC_API_KEY` (falling back to `ANTHROPIC_AUTH_TOKEN`), `ANTHROPIC_BASE_URL`, `CLAUDE_CODE_OAUTH_TOKEN` | `claude_code.py` lines 1024-1029 |
| model handling | no whitelist; `model_name` is passed through as `ANTHROPIC_MODEL` (provider prefix stripped for the official API) | `claude_code.py` lines 1074-1090 |
| model chosen | **`claude-opus-5-5`** | see below |

**Why `claude-opus-5-5`.** The repository does **not** designate a Claude comparison model. Its only prior
`claude-code` usage is `claude-sonnet-4-6`, and that was for `harbor check` — task *quality* checking, a
different purpose. The assignment therefore directs the strongest appropriate model, which is also the
right choice for the research question: if the strongest Claude fails in the same place Gemini does, the gap
is cross-model rather than an artefact of model scale.

**Tier-mismatch caveat, flagged now rather than after seeing results.** The Gemini arm is
`gemini-3-flash-preview`, a fast-tier model. Comparing it against a frontier Opus is not a matched-capability
comparison, and a Claude win would be partly attributable to tier. The clean design is **two Claude arms**:
`claude-opus-5-5` (strongest, answers "is the gap cross-model?") and `claude-haiku-4-5-20251001`
(tier-matched, answers "is the gap Gemini-specific at equal tier?"). §5 is written to run either.

## 5. Execution plan (ready to run)

```bash
# 3 valid trials per task, strictly sequential (this host has 8 CPUs; concurrency caused
# every agent-setup timeout observed in the Gemini campaign)
./scripts/run_claude_crossmodel.sh claude-opus-5-5 3
```

Logs are written to `crossmodel_logs/claude/<job-name>/`, entirely separate from `jobs/`. **No Gemini
trajectory is touched.** Invalid trials are renamed with an `__INVALID-<reason>` suffix and replaced, never
counted as model failures — the same rule applied to the Gemini arm, which accumulated 8 invalid
directories.

## 6. Pre-registered coding rules (fixed before any Claude data exists)

To satisfy Step 11, the trajectory coding applied to Claude is **the identical machinery** applied to
Gemini: `scripts/extract_trajectories.py` computes seventeen signal counts by regular expression over the
agent's own reasoning and messages, and `scripts/compute_metrics.py` derives every rate. The signal
patterns are frozen in that script and are not re-tuned for Claude.

Two measures are subjective and their rules are fixed here in advance:

1. **"Correct mechanism recognised."** A per-task regular expression over the agent's own reasoning, with
   the patterns exactly as used for Gemini: `02`/`g08` point-in-time / vintage / restatement language;
   `g05` staggered / wave / cohort; `g10` censoring / stockout / latent demand; `g24` logging policy /
   propensity / exposure / selection bias; `g36` tariff / TOU / enrolment / migration; `p20` feedback /
   vintage / as-served / feature feed; `p22` calibration / gauge / measurement system / offset; `p31`
   denominator / aggregation / definition / line-item / substitution. Measured on the same truncated
   reasoning excerpts (first, middle and last 1,200 characters). **It is a lower bound for both arms and a
   keyword match is not proof of understanding.**
2. **"Revision propagated downstream."** Coded as propagated only if a criterion *downstream* of the
   revised quantity also passes. For binary-reward tasks this is not observable and is recorded as
   `unobservable`, not as a failure — for both arms.

Borderline classifications will be flagged individually in `CLAUDE_TRAJECTORY_ANALYSIS.csv` via a
`borderline` column.

**Known asymmetry to report, not to correct away:** six of the ten tasks emit a binary reward only, so
criterion-level comparison is available on four tasks (`p20`, `p22`, `p31`, `g50`) for both arms. The Gemini
arm has 15 criterion-instrumented trials; a completed Claude arm would have 12.

## 7. Recomputing the hashes in §1

```python
import hashlib, os
def agg(root):
    h = hashlib.sha256()
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ("__pycache__", ".ipynb_checkpoints")]
        for f in sorted(fns):
            p = os.path.join(dp, f)
            h.update(os.path.relpath(p, root).encode())
            h.update(hashlib.sha256(open(p, "rb").read()).digest())
    return h.hexdigest()
```

## 8. What was NOT done, and why

| step | status |
|---|---|
| 1 verify the frozen ten | **done** — all ten byte-identical |
| 2 verify Anthropic auth | **done** — credential is the unrotated exposed key; **this is the blocker** |
| 3 determine Harbor Claude configuration | **done** — `claude-code` + `claude-opus-5-5` |
| 4 smoke test | **not run** — requires the credential |
| 5 run all ten | **not run** |
| 6-11 results, trajectory analysis, comparison | **not run** — no Claude data exists |
| 12 artefacts | scaffolded: this file, `CLAUDE_CROSSMODEL_RESULTS.json`, `CLAUDE_VS_GEMINI.md`, `scripts/run_claude_crossmodel.sh` |

**No results are reported, and none are estimated, simulated or inferred.** Producing a Claude number
without having run Claude would be fabricating evidence, which is the one thing a cross-model integrity
experiment cannot survive.
