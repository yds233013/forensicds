# 12 — Next experiments, prioritised

Ordered by **uncertainty reduced per unit cost**. Nothing here was executed. Costs are grounded in
measured values where one exists (Claude: $0.80 median per trial, ~4 min, `06_CLAUDE_RESULTS.md`) and
marked as estimates otherwise.

**Recommended first move: Experiment A.** It is free, needs no model calls, and it is the only experiment
that can distinguish the several candidate mechanisms chapter 08 leaves open.

---

## A. Manual trajectory adjudication of the four jointly failed tasks — **DO THIS FIRST**

| | |
|---|---|
| **Question** | On `g10`, `g36`, `p20` and `p31` — the four tasks both models failed on every trial — *where* does the analysis break, and is it the same place across models? |
| **Hypothesis** | Different tasks break at different stages (chapter 08 finds 4 shapes on instrumented tasks); the two binary-reward tasks (`g10`, `g36`) will break at different stages from each other. |
| **Intervention** | Read the 12 valid trajectories for these tasks plus the agents' submitted code in `artifacts/workspace`, and hand-code each against the stage taxonomy: evidence · population · estimand · identification · implementation · number · uncertainty · validation · decision. |
| **Controls** | Two independent coders, blind to arm and reward, on a fixed codebook. Report inter-coder agreement. Include the 4 `g08` **passing** trials as positive controls — a codebook that cannot distinguish a pass is not measuring anything. |
| **Success measure** | Inter-coder agreement ≥ 0.7; a stage assignment for ≥ 10 of 12 trials. |
| **Cost** | **$0 in model spend.** ~6-10 hours of analyst time. |
| **What outcomes mean** | *Same stage across tasks* → supports a single mechanism, strengthening chapter 08's regularity into a cause. *Different stages* → confirms the multi-mechanism reading and tells us which stage to instrument first. *Cannot code it* → the trajectories are too thin, and the real finding is that final-state verification plus these scaffolds cannot answer the question. |

---

## B. Instrument the six binary-reward tasks as new versions

| | |
|---|---|
| **Question** | Where do failures sit on `g10`, `g36`, `g05`, `02`, `g24`, `g08`? |
| **Hypothesis** | `quantitative_results` remains the modal failure, but `g10`/`g36` break earlier (population/evidence) than the attribution-family tasks do. |
| **Intervention** | Add criterion emission to each — the `atexit` pattern at `p22/tests/test_gauge.py:50-59` is ~20 lines. **New versions only**; the frozen originals are never edited. Then 3 trials per arm per task. |
| **Controls** | Verify the new version's oracle still scores 1 and nop 0; verify the agent-visible workspace hashes **identically** to the original, as was done for `02-v1.1` (`c26939cde7cc…`), so the capability measurement is comparable to the frozen version's. |
| **Success measure** | Criterion data on 10/10 tasks; chapter 08's selection-bias limitation removed. |
| **Cost** | Engineering ~2 days. Trials: 6 tasks × 3 trials × 2 arms = 36 trials ≈ **$29 for the Claude arm** at the measured $0.80 median; Gemini comparable or cheaper. |
| **What outcomes mean** | This is the single change that would let the dossier's central claim rest on ten tasks instead of four. If the pattern holds, the finding generalises; if `g10` breaks at evidence reconstruction, chapter 08's regularity is an artifact of the attribution family. |

---

## C. Controlled scaffolding intervention

| | |
|---|---|
| **Question** | How much of the measured failure is the model and how much is the scaffold stopping early? |
| **Hypothesis** | A non-trivial share. `g36` is the signal: Claude used **13-15 steps** where Gemini used 40-54, and both failed. Several trajectories end with confident completion language. |
| **Intervention** | Re-run `g36` and `g10` with (i) the default scaffold, (ii) a raised step/turn budget, (iii) an added "before finishing, verify each reported quantity against an independent recomputation" instruction **delivered through the scaffold's system prompt, not by editing the frozen task**. |
| **Controls** | Identical frozen tasks; the instruction must not name the mechanism. Confirm by diff that `candidates/` is untouched. |
| **Success measure** | Any arm where pass rate moves materially with budget alone. |
| **Cost** | 2 tasks × 3 conditions × 3 trials × 1 arm = 18 trials ≈ **$15**. |
| **What outcomes mean** | *Pass rate rises with budget* → part of what we called a capability gap is a scaffold artifact, and the headline numbers need re-stating. *No movement* → strengthens the capability reading considerably. **This is the cheapest threat-to-validity test available.** |

---

## D. A `g50` version compatible with both scaffolds

| | |
|---|---|
| **Question** | Does Claude fail `g50`'s interference mechanism, which is the suite's flagship? Currently **unmeasured**. |
| **Hypothesis** | Given Claude's 100% `scientific_object` rate on instrumented tasks, it is more likely than Gemini to separate the arm contrast from the rollout quantity — the step all three Gemini trials failed. |
| **Intervention** | `g50-v2.4`: replace the runtime hash-pin with the resolution check already prototyped in `tests/test.sh:102`, or narrow the manifest to what the generator actually imports. **Diagnose first** — chapter 09 D5 records that *which* pinned file `claude-code` trips is UNKNOWN, because `test.sh:76` discards the filename. Reproduce the installer in the frozen image and rerun the check with output shown. |
| **Controls** | Oracle 1 / nop 0 on five worlds; agent-visible group-A hash unchanged from `ba92e8ccdcecdb58`; **a scaffolded-agent smoke test for each scaffold before any graded trial** — the gate whose absence caused D4 and D5. |
| **Success measure** | Both scaffolds graded; 3 valid trials per arm. |
| **Cost** | Diagnosis ~1 hour (free, needs Docker). Engineering ~0.5 day. 6 trials ≈ **$5**. |
| **What outcomes mean** | *Claude separates the objects* → the `g50` failure is tier-specific. *Claude also reports the arm contrast* → a frontier model walks into the designed trap, which would be the strongest single result the benchmark could produce. |

---

## E. Tier-matched Claude arm (`claude-haiku-4-5`)

| | |
|---|---|
| **Question** | Is Claude's advantage architecture or tier? Chapter 10 cannot separate them. |
| **Hypothesis** | A tier-matched model lands much closer to Gemini Flash than to Opus. |
| **Intervention** | 3 trials × 9 gradable tasks with `-a claude-code -m claude-haiku-4-5-20251001`. Identical frozen tasks and command. |
| **Controls** | Same scaffold as the Opus arm, so scaffold is held constant and only tier varies — the clean contrast the Opus-vs-Flash comparison lacks. |
| **Success measure** | Per-task and suite pass rates against both existing arms. |
| **Cost** | 27 trials. Haiku is materially cheaper per token than Opus; **estimated $5-10**, not measured. |
| **What outcomes mean** | *Haiku ≈ Flash* → the benchmark measures a tier-sensitive capability and the "frontier gap" framing is wrong. *Haiku ≈ Opus* → the gap is Gemini- or scaffold-specific. Either answer materially rewrites chapter 10. |

---

## F. Analyse the justified-deferral world we already have

| | |
|---|---|
| **Question** | Do agents decline when the evidence does not settle the question? |
| **Status correction** | The project's own documents (`report/FINAL_REPORT.md:982`, `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md:794`) state that **no** task tests justified deferral. **That is wrong.** `p31-fill-rate-dispute` implements it: `tests/scenarios.py:13` designs a world where the evidence does not settle it, `tests/world.py:300` returns `not_determinable_from_available_evidence`, the reference returns it (`solution/service/adjudicate.py:20`), the verifier accepts it (`tests/test_fill.py:285`), and **it is in the agent-visible contract** (`readout_contract.md:42`). **VERIFIED FROM ARTIFACT.** |
| **What the existing data already show** | Both arms **failed** to produce the deferral. `p31-prospective-2` reported `incumbent_correct` where `not_determinable_from_available_evidence` was expected. So the question is **partly answered already**: agents did not defer. |
| **Intervention** | Re-read the 6 `p31` trajectories specifically for deferral behaviour (free, part of Experiment A), then build deferral worlds for 2-3 further tasks as new versions. |
| **Cost** | $0 for the re-read; ~1 day engineering plus ~$15 of trials for new worlds. |
| **What outcomes mean** | If no agent ever defers across tasks, that is an economically important and publishable finding on its own — production analytics needs "the evidence does not support a conclusion" far more than it needs a confident wrong number. |

---

## Recommended sequence

1. **A** — free, and it is the only way to resolve the multi-mechanism question (plus F's re-read).
2. **C** — ~$15, and it tests the largest threat to the validity of every number in the dossier.
3. **B** — ~$29, and it removes the dossier's biggest stated limitation.
4. **D**, then **E**.

**Smallest experiment that most reduces uncertainty: A combined with F's re-read.** Zero model spend,
no new engineering, and it either converts chapter 08's statistical regularity into a mechanism or shows
that these trajectories cannot support the claim at all. Either result is worth more than another 30 trials.

## Explicitly not recommended

- **More trials on the existing instrumentation.** Going from 3 to 5 trials per task narrows confidence
  intervals and answers no mechanistic question.
- **Building new tasks before B.** The suite's limitation is measurement density, not task count.
- **Tuning any frozen task's tolerances in response to these results.** Both arms are now exposed; any
  such change would invalidate the comparison.
