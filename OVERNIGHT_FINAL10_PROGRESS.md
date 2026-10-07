# OVERNIGHT FINAL10 PROGRESS LOG (append-only)

Never rewrite earlier entries. Each entry: timestamp / task / action / scientific decision /
validation result / target-exposure state / Gemini result / cost / next action.

---

## 2026-09-30T09:53:53Z
- **task**: ALL
- **action**: Confirmed Gemini auth path: GEMINI_API_KEY present in ~/.zshrc (len 53, prefix <redacted>), forwarded into the container by harbor/agents/installed/gemini_cli.py. harbor auth status = NOT authenticated, which affects only 'harbor check' (Claude scaffold agent) and 'harbor upload', not 'harbor run'.
- **scientific decision**: Gemini trials are runnable; harbor check is not. Proceed.
- **validation**: harbor run -a oracle/-a nop confirmed working on g50 earlier this session.
- **exposure**: no task exposed yet
- **gemini**: none yet
- **next**: audit the existing candidate pool

## 2026-09-30T10:10:02Z
- **task**: ALL
- **action**: Built exposure ledger (61 valid Gemini trials, 21 tasks) and structured trajectory dataset (report/analysis/trajectories.json).
- **scientific decision**: Aggregate 'failing trials do more work' is a TASK-DIFFICULTY CONFOUND: within the 6 mixed-outcome tasks, effort is pass-higher in 3/6 and fail-higher in 3/6. Do not claim effort predicts failure.
- **validation**: 61/61 trajectories parsed; 9 trials carry criterion-level detail.
- **exposure**: 21 tasks already exposed; g50 unexposed
- **gemini**: aggregate pass@1 = 24/61 = 39.3%; 9 tasks at pass@3 = 0
- **next**: sign-convention audit of every criterion failure

## 2026-09-30T10:10:02Z
- **task**: p20-noshow-monitoring
- **action**: Audited every criterion failure for sign/unit artifacts.
- **scientific decision**: FOUND A GENUINE BENCHMARK DEFECT: readout_contract.md does not state the sign convention for programme_effect_pp; the reference computes control-minus-programme (positive = programme helps) and no agent-visible artifact disambiguates it. 7 sign-flip failures across 2 of 3 trials. HOWEVER all three p20 trials also fail on independent genuine grounds, so the 0/3 is not manufactured by the defect. p22 and p31 show zero sign artifacts.
- **validation**: sign-flip confined to p20 programme_effect_pp; 42 genuine magnitude failures elsewhere
- **exposure**: p20 v1 EXPOSED - will be preserved, not edited
- **gemini**: p20 v1 remains 0/3
- **next**: create p20 v1.1 with the sign convention stated; re-expose; preserve v1 record

## 2026-09-30T11:33:02Z
- **task**: g50-courier-boost-rollout
- **action**: Calibrated and added a fifth world (hidden_d, beta_supply=0.100) so the memo's break-even is binding for the first time; re-ran the mutation suite on five worlds.
- **scientific decision**: Effect -0.3049 pp: memo says do_not_roll_out, 'any reduction' says roll_out. Every accepted route still lands correctly (0.129-1.000 pp). Side effect: the unadjusted estimator now misses by 18.6 pp on hidden_d, strengthening the pre-period-adjustment invariant.
- **validation**: oracle=1 nop=0 M_threshold_ignored=0 (gap CLOSED) D_mu=1 H_post=1 R2_boostshare=1 P_ow_unadjusted=0; 5 mutations still running
- **exposure**: still unexposed at time of fix, so the change was legitimate
- **gemini**: none yet
- **next**: freeze then expose 3 trials

## 2026-09-30T11:33:02Z
- **task**: p20-noshow-monitoring-v1.1
- **action**: Ran 3 Gemini trials on the contract-fixed fork.
- **scientific decision**: The fix removed the artifact and the task remains hard for genuine reasons: 0/3, zero programme_effect_pp sign failures (v1 had 7). Trial 2 passed SIX of seven criteria and failed only quantitative_results - the cleanest single instance of the failure mode in the dataset.
- **validation**: oracle=1 nop=0
- **exposure**: v1 preserved untouched; v1.1 newly exposed
- **gemini**: 0/3 (rewards 0,0,0)
- **next**: audit remaining tasks for leakage

## 2026-09-30T11:33:02Z
- **task**: 02-renewal-risk-regression
- **action**: Leakage audit across all ten tasks; found and empirically confirmed a single-stage Dockerfile defect.
- **scientific decision**: COPY build/ then rm -rf only whiteouts the layer: docker save recovers tmp/build/world.py (34,538 B) AND tmp/build/pit_reference.py (10,301 B, the reference implementation). Verified the agent CANNOT reach it at runtime (ls /tmp/build -> No such file), so the 6 existing trials remain valid. Built 02-renewal-risk-regression-v1.1 with a two-stage build: zero generator artefacts in any layer, and the agent-visible workspace hashes IDENTICALLY to v1 (c26939cd...).
- **validation**: leak removed; agent-visible surface provably unchanged
- **exposure**: v1 exposed and preserved; v1.1 is a packaging-only remediation
- **gemini**: v1 remains 0/3
- **next**: finish g50 exposure, then package

## 2026-09-30T11:57:22Z
- **task**: g50-courier-boost-rollout
- **action**: First G50 exposure produced 3 trials that all scored 0 with NO criterion keys. Diagnosed: the verifier REFUSED TO GRADE - 'interpreter, library tree or sandbox tools differ from the pinned image'.
- **scientific decision**: MY OWN DEFECT, introduced earlier this session. I pinned /etc/ld.so.cache to close a loader-redirection path; apt-get runs ldconfig, which regenerates it, and a real agent scaffold installs its own tooling. Pre-exposure validation used oracle/nop and my docker harness, none of which install anything, so the path was never exercised. Reproduced deterministically: apt-get install curl -> 'etc/ld.so.cache: FAILED'.
- **validation**: 3 trials marked __INVALID-verifier-refused-ldsocache. NOT counted as model failures (assignment Part XXI: infrastructure failures are invalid trials).
- **exposure**: g50 exposed but ungraded; artefacts preserved
- **gemini**: INVALID x3 - verifier never graded the work
- **next**: fix, re-validate oracle, re-freeze, re-expose

## 2026-09-30T11:57:22Z
- **task**: g50-courier-boost-rollout
- **action**: Replaced the ld.so.cache hash pin with a RESOLUTION check: every shared object the verifier's interpreter and sandbox tools actually load must resolve to a manifest-pinned path.
- **scientific decision**: An inventory check on the loader search dirs fails for the same reason as the cache hash (a scaffold's apt-get adds libraries). Resolution is the property a redirection attack must break, and it is immune to unrelated installs. First attempt at an inventory guard was wrong - it compared the directory against the ldd closure and flagged every unrelated .so - and was discarded.
- **validation**: verified in-container: hash PASS + resolution PASS both before and after apt-get install curl
- **exposure**: pending re-exposure
- **gemini**: n/a
- **next**: oracle re-check, re-freeze, 3 fresh trials

## 2026-09-30T12:33:17Z
- **task**: g50-courier-boost-rollout
- **action**: Re-froze as v2.3 with the resolution-check fix and ran 3 fresh Gemini trials.
- **scientific decision**: 0/3, properly graded this time. All three reported programme_effect_pp IDENTICAL to the arm contrast (within 0.000 pp), an order-level interval 1.882 pp wide, courier_hours_response_pct +0.366 (the incumbent's zero-power capacity identity), and decision roll_out. They reproduced the incumbent and walked into every designed trap. evidence_reconstruction passed 3/3; nothing downstream did. G50's failure is at the ESTIMAND step, unlike p22 (generalisation) and p20 (quantity) - the bottleneck localises by mechanism class.
- **validation**: criterion keys present, zero refusals; oracle=1 on the fixed verifier
- **exposure**: v2.3 exposed, 3 valid trials
- **gemini**: 0,0,0
- **next**: package and finalise

## 2026-09-30T12:33:17Z
- **task**: ALL
- **action**: Built and validated the submission ZIP; recorded SHA-256 externally to avoid the self-reference (the handoff is inside the archive).
- **scientific decision**: Final-10 metrics: 31 valid trials, 1 pass, aggregate pass@1 3.2%, task-level pass@3 10% - target <30% met with margin. 8 invalid trial directories preserved with reasons, none counted as model failures.
- **validation**: unzip -t PASS; 4,517 files; 131 MiB; 12 task dirs in samples (10 final + 2 forks + 1 ablation); 88 job dirs in logs; fallback hash c8561aad... UNCHANGED
- **exposure**: all 10 final tasks exposed with >=3 valid trials
- **gemini**: 1 pass in 31 trials
- **next**: none - submission complete
