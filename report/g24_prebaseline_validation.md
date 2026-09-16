# G24 recommender off-policy evaluation: pre-baseline validation

**Task:** `candidates/g24-recommender-ope/`

**Status:** validated. Ready for a baseline, which has **not** been run: no Gemini and no other model.

**Task commit:** 2e21788. **Task checksum:** `2c9cc2055ef796a5`, computed with
`git ls-files candidates/g24-recommender-ope | xargs shasum -a 256 | shasum -a 256 | cut -c1-16`.

**Related documents:**
- Research audit: `research/g24/G24_research_audit.md`
- Phase-0 simulation gate: `research/g24/G24_phase0_gate.md`. It passed before any build. §7 records the as-built
  deviations.
- Fixture audit: `research/g24/fixture_audit.json`
- Mutation suite report: `research/g24/shortcuts_report.json`

## 1. Summary

| Check | Result |
|---|---|
| Harbor oracle (`-k 1 -n 1`, job `g24-oracle-prebaseline`) | **reward 1**, 15 passed, pytest 308 s |
| Harbor Nop (`-k 1 -n 1`, job `g24-nop-prebaseline`) | **reward 0**, 8 failed / 7 passed |
| `harbor check` (job `g24-check-prebaseline`) | **11/11 pass** |
| Clean checkout: clone at 2e21788, `docker build`, Harbor oracle and Nop | oracle **reward 1** (15 passed); Nop **reward 0** (the same 8 failures). The log extract is byte-identical to the dev image (sha256 `2f93fbc257a069fa…`). |
| Mutation suite in the task image with the real `test.sh` (`tools/g24/shortcuts.py`) | **30/30 as expected** |
| Re-smoke of the tamper cases and oracle with the final `test.sh` (after the Harbor process fix) | **8/8 as expected** (oracle, logs_edit, five tamper cases, hard-coded launch overfit) |
| Fixture audit: launch-boundary margin ≥ 3 SE_ref on every frozen extract | met on all 4 |
| Frozen checksums: 01–06, 02-explicit-invariant, G08, G10 | all unchanged (§8) |
| Secret scan (task, tools, research, report) | clean |

## 2. Frozen extracts and truth (build-time generator, exact expectations)

- **Values:** expected clicks per slate decision.
- **Launch rule:** `docs/launch_policy.md` (two-sided 95%).
- **SE_ref:** the analytic standard error of slot-exact IPS.
- **Distance:** lift / SE_lift − 1.96.

| Extract | Decisions (exploration) | v6 | v7 | v7_pd | Lift v7 (dist.) | Lift v7_pd (dist.) | Launch |
|---|---|---|---|---|---|---|---|
| visible | 130 000 (58 647) | 0.3827 | 0.3695 | 0.4665 | −0.0132 (−3.05) | +0.0838 (+4.52) | v7_pd |
| hidden_a (TV-heavy, steep TV examination) | 150 000 (52 782) | 0.3481 | 0.3253 | 0.4246 | −0.0228 (−3.91) | +0.0765 (+4.19) | v7_pd |
| hidden_b (wider pools, strong v7 anti-ordering, weak v7_pd) | 130 000 (64 803) | 0.3902 | 0.3472 | 0.3301 | −0.0430 (−5.48) | −0.0601 (−6.75) | v6 |
| hidden_c (v7 relevance-ordered, mobile-heavy) | 130 000 (54 174) | 0.3803 | 0.4659 | 0.3443 | +0.0855 (+4.47) | −0.0361 (−4.75) | v7 |

- The three hidden extracts require three different launch decisions: v7_pd, v6 and v7.
- The deployed gate reports v7 ≈ +12% and v7_pd ≈ +18% on the visible extract. The truth is v7 −3.5% and
  v7_pd +21.9%. The gate therefore gets the sign of the v7 lift wrong and understates v7_pd.

## 3. Verifier

**What it checks.** `tests/test_ope.py` runs the agent's command on the visible extract and on three hidden extracts
that are generated at grading time. Each run is graded immediately, keeping peak memory at 1.7 GB. It checks:
- the logs are unmodified, and the run succeeds within 20 min;
- the decision table exactly: `decision_id` = the `serve_id` of the response that created the decision;
- the target slates exactly (eligible titles in each policy's order);
- values and lifts within **3.5 × SE_ref**;
- intervals: width between 0.10× and 3× the reference width, and covering the truth at a widened multiple;
- the launch decision exactly;
- determinism: a byte-identical rerun.

**Hardening in `test.sh`:**
- **Fail-closed:** reward 0 unless every check completes.
- **Pinned base image:** runtime manifest (sha256) of the interpreter, the standard library and the sandbox tools.
  The file list of the standard library must match exactly; `__pycache__` is purged; `/etc/ld.so.preload` is
  refused.
- **Pytest configuration:** refused at `/pytest.ini`, `/conftest.py`, `/tox.ini`, `/setup.cfg`, `/pyproject.toml`
  and in `/tests`.
- **Verifier environment:**
  - the venv is created with `python -I -S`, so no `.pth` or site hooks run;
  - pinned wheels are installed with `--require-hashes --no-index --isolated`, `PIP_CONFIG_FILE=/dev/null` and
    `env -i`;
  - pytest runs with `-I -B --noconftest -c /dev/null --rootdir=/tests`.
- **Agent pipeline:** runs as uid 65534. `/tests` is mode 700 and verified unreadable to that user.
- **Stray processes:** any process started before the verifier's own process tree is killed, except the container's
  init-era processes.
  - *First version:* killed Harbor's container main command, which ended the container. The job came back as reward
    0 in 0.8 s with an empty `test-stdout`.
  - *Fix:* processes started within 3 s of PID 1 are kept.
  - *Verification:* after the fix, a `--init` container with a detached `sleep` survived grading, and both Harbor jobs
    ran to completion.

## 4. Mutation suite (30 cases, task image, real `test.sh`)

**Accepted implementations** (reward 1). Error/tolerance ratios are from `tools/g24/quickcheck.py`, as the worst
value ratio across the 4 extracts.

| Implementation | Structure | Worst ratio |
|---|---|---|
| oracle (`solution/`) | TTL grouping, slot-exact IPS (weight m), paired analytic SEs | 0.43 |
| variant `slot_ips` | independent control flow | 0.43 |
| variant `pbm_ips` | item-in-slate marginal 5/m + per-device examination curve from exploration | 0.26 |
| variant `dr` | per-title reward model + slot-exact correction | 0.47 |
| variant `snips` | self-normalised slot-exact | 0.42 |
| variant `onpolicy_mix` | on-policy means for v6/v7, paired IPS lifts | 0.25 |
| variant `pooled_theta` | position transfer with a pooled curve | 0.30 |
| `alt_pandas_pbm.py` | pandas, vectorised grouping, seeded paired bootstrap | 0.26 |

**Natural wrong methods** (reward 0). The failing layer is the first check that separates the method.

| Wrong method | Fails on | Worst ratio (values) |
|---|---|---|
| deployed gate (Nop) / production replay from scratch | values, intervals, hidden launch | 2.2–2.4 |
| IPS with the logged propensity (clipped SNIPS; the June notebook) | values | 9.8–12.6 |
| per-slot replay on exploration, no propensity | values | 1.5–2.3 |
| weight = pre-filter pool K (`candidate_count`) | values | 1.1–2.0 |
| serves treated as decisions | decision table, values | 1.0–1.6 |
| keep first serve only | values on 3 of 4 extracts | 1.2–1.6 |
| item-anywhere credit, no position transfer | values/intervals | 1.1–1.3 |
| target slates ignoring the rules layer | target slates, values | 0.9–1.6 |
| clipped weights (cap 10) | values | 2.2–3.4 |
| direct method only | values | 0.9–2.7 |
| merge identical consecutive slates across TTL | decision table, target slates | — |
| session-only grouping | decision table, values | 4.4–5.8 |

**Cheats and tampering** (reward 0):
- output-only patch;
- editing the logs;
- importing the verifier's generator;
- a stdlib `site.py` exit hook;
- a shadow `pytest` in the stdlib;
- root `pytest.ini`/`conftest.py`;
- a `.pth` in site-packages;
- a pip config pointing at a fake pytest.

**Visible-pass / hidden-fail overfits** (reward 0; each passes every visible-extract check):

| Overfit | Fails on |
|---|---|
| hard-coded launch | hidden_b, hidden_c |
| hard-coded eligible pool size m = 12 | hidden_a |
| hard-coded examination curve | hidden_a |

## 5. Cheap-solve audit

| Cheap path | Outcome |
|---|---|
| `grep propensity` then standard IPS with the logged column | Fails at 10–13 τ. The column is a pre-filter slate probability (≈1e-7). |
| Run the June notebook (`notebooks/2026-06-12_ips_spike.ipynb`) | Clipped SNIPS with item-anywhere credit. Plausible scale, wrong ranking of v7, fails values. |
| Trust one schema (`docs/data/logging_schema.md`) | The schema says the propensity is "probability with which the ranker produced this response". True of the ranker, not of the response after the rules layer. Using it as the weight fails. |
| Trust one dashboard (gate reports, AB readout) | Gate = Nop, reward 0. The A/B gives v7's online value only; there is no v7_pd arm, so v7_pd must be estimated. |
| Copy a helper (`recs_eval/replay.py`) | It is the deployed gate; reward 0. |
| Exploration slice only (replay, K-weights, first serve) | Each fails (see §4). |
| Correct weights, no decision reconstruction | Fails the decision table and the values. |

**Answer-key audit** (built image, clean checkout):
- **No stated recipe.** No agent-visible file states the marginal 1/m, "eligible count", "item-in-slot" or any
  estimator recipe.
- **No leaked truth.** No file references truth, the hidden extracts, the generator or the oracle.
- **No verifier or solution files.** `/tests` and `/solution` are absent from the image; the generator runs in a
  build stage that is discarded.
- **Pre-generated outputs.** `out/ope/*` in the image are the deployed gate's outputs.
- **Wrong gate numbers.** The gate and notebook numbers are far from truth, so copying them fails.

**Residual cheap-solve risks** (accepted; each still requires the full reasoning chain):
1. `serving/ranker/serve.py` is close to a recipe. It shows the propensity is logged *before* `rules.apply`, and the
   module docstring says the rules layer "can change the response". An agent must still infer that the shuffle is
   uniform over the eligible subset (so the marginal is 1/m, not 1/K). It must also rebuild decisions across cache
   re-serves and handle position.
2. Candidates are logged at the creating serve for every exploration decision, but only for a sample of production
   decisions. The candidate table therefore identifies exploration decisions. This reflects real logging and does not
   by itself give the weights.
3. The extract is 45% exploration, while `serving.yaml` says `traffic_share: 0.05`. The extract composition is
   documented in `logging_schema.md`, and the enrichment is realistic for an OPE extract.

## 6. Statistical validity

1. **Identifiability.** Every target item-slot pair has logging probability 1/m, with m ≥ 6 (`min_eligible`), so the weights are bounded. The estimand (expected clicks per slate decision over all extract
   decisions) is a mean over decision contexts. Exploration decisions are a hash-random subset, so exploration-only
   IPS is unbiased for the full extract.
2. **Tolerance.** The tolerance is 3.5 × SE_ref per quantity, with the exact m/(m−1) pair factor in SE_ref.
   - Across 20 graded quantities, an unbiased slot-IPS fails ≈1% of the time in expectation.
   - Seed screening placed the realised error of all 8 accepted implementations at ≤0.47 τ on the frozen extracts.
3. **Decision margins.** Every lift is at least 3 SE_ref from the launch-rule boundary, so correct estimators with
   their own SEs reach the same decision.
4. **Accepted family.** The accepted family includes position-transfer variants (per-device and pooled curves),
   doubly robust, SNIPS, bootstrap intervals and on-policy anchors. No arbitrary modelling choice inside it decides
   pass/fail.
5. **Independent statistical review.** Recommendations (hidden_c regime, margin definition, width floor, SE factor)
   were all applied; see gate §7.

## 7. Residual validity risks

1. **Thin separations.** Several wrong methods fail values by only 1.1–1.6 τ on their worst extract (item-anywhere,
   weight K, keep-first-serve, target slates without rules). They are still rejected deterministically on the frozen
   extracts, and each fails at least 3 extracts or a table check. A differently tuned variant (for example a
   different clip or smoothing) could land inside tolerance on some extracts, but not on all four simultaneously in
   any variant tested.
2. **Interval width floor (0.10× reference).** This is permissive; a very narrow but covering interval passes.
   Coverage at a widened multiple still binds.
3. **Runtime.** A 20-minute limit per run. The oracle takes 10–35 s per extract; the pandas bootstrap 50–110 s. A naïve
   Python loop over 130–150k decisions × 3 policies is still well inside the limit.
4. **Stray-process defence depends on start times.** A process the agent starts within 3 s of container boot would
   survive into grading. Agents start well after boot, so this is a Harbor-level residual risk, not a practical
   bypass. Everything the grade depends on is also checked independently: manifest, tamper refusals, uid separation.
5. **Host memory under parallel runs.** The first clean-checkout Nop was OOM-killed mid-pytest. It shared an 8 GB
   Docker VM with four other heavy containers. It was rerun alone and completed normally.
   - The task's own peak is 1.7 GB of its 4 GB limit.
   - Baselines should not be run alongside other heavy jobs on this host; `-n 3` Harbor trials use 3 × 4 GB of
     limits.
6. **G08/G10 frozen verifiers.** They share the weaknesses found in G24's adversarial review (not modified, per
   instruction):
   - no refusal of root-level `pytest.ini`/`conftest.py` and no `--noconftest -c /dev/null`;
   - a venv created without `-S`, so a `.pth` in system site-packages runs;
   - `pip install` from the network without `PIP_CONFIG_FILE=/dev/null`/`--isolated`/hashes.

   G08 additionally runs pytest without `-I`. These should be considered before comparing G24 results with G08/G10,
   and fixed in any future revision of those tasks.

## 8. Integrity

**Frozen checksums** (recomputed after the G24 commit):

| Task | Checksum |
|---|---|
| 01 | 67259f9d0d438f7c |
| 02 | f696367794c1a25f |
| 02 explicit-invariant | 0e8200bd6d99c77b |
| 03 | a8443d183fe160e6 |
| 04 | 885b541eb480a020 |
| 05 | 8daa31d646dfcb59 |
| 06 | cd572b17bd537b4d |
| G08 | b1f0fa1304fb88f5 |
| G10 | 047195e7a12d34cd |

All match, and there are no working-tree changes under any frozen directory.

**Secret scan:** `sk-ant-`, `AIza`, `ghp_`, `AKIA` and private-key patterns over the task, tools, research and
report: no matches. API keys were loaded only via `eval "$(grep … ~/.zshrc)"` and never printed.

**Clean `__pycache__`:** purged before commit.

## 9. Proposed baseline (not run)

```
harbor run -p candidates/g24-recommender-ope -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs \
  --job-name g24-gemini3flash-baseline-1 --artifact /workspace --agent-setup-timeout-multiplier 3 -y
```
