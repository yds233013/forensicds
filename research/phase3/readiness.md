# Prospective readiness report — P22, P20, P31

Every gate below is model-free. `harbor check` was **not** run: it invokes an LLM judge.

| gate | P22 | P20 | P31 | evidence |
|---|---|---|---|---|
| scientific specification frozen before build | **PASS** | **PASS** | **PASS** | `spec_p22.md`, `spec_p20.md`, `spec_p31.md`, written before any code |
| independent scientific ground truth | **PASS** | **PASS** | **PASS** | truth from the generator's objects; the reference solution from the shipped SQLite by a separate path |
| identifiability reviewed; unidentifiable quantities not graded | **PASS** | **PASS** | **PASS** | P22 operator contrast only; P20 no agent-trained model; P31 a range where Schedule 4 is unexecuted |
| workspace frozen + checksum | **PASS** | **PASS** | **PASS** | `proposed_freeze_manifest.txt`: `a0570585c3927b53`, `2c3c374b07f233fa`, `e18bf13d6080f987` |
| the two generator copies identical | **PASS** | **PASS** | **PASS** | `validate_phase3.sh` §3 |
| **Oracle = 1** on all four extracts | **PASS** | **PASS** | **PASS** | 7/7 criteria and `reward: 1` in every case |
| **Nop = 0** | **PASS** | **PASS** | **PASS** | 0/7 criteria and `reward: 0` in every case |
| wrong-analysis mutation suite (≥10) | **PASS** 15/15 | **PASS** 15/15 | **PASS** 15/15 | `tools/p*/mutation_results.txt`; one behaviour-preserving mutant scores 1 in each |
| separation margin | **PASS** | **PASS** | **PASS** | every graded mutant fails on at least one extract; the criterion breakdown records which |
| decision-margin test | **PASS** | **CONDITIONAL** | **PASS** | P22 ≥1.65 pp from the 5.5 % limit on all four; P31 ≥0.57 pp on the decisive threshold; **P20's hidden_a is 0.036 AUC from the floor against a 0.02 tolerance (1.8×)**, the thinnest margin in the suite |
| discriminating-test inventory (≥2 routes, outcomes recorded) | **PASS** 3 | **PASS** 3 | **PASS** 3 | `audits.md`, with predicted and actual outcomes |
| cheap-solve audit, each shortcut implemented and run | **PASS** | **PASS** | **PASS** | `audits.md` table; exploit probes E00/E01 rejected on all three |
| stated-object audit | **PASS** | **CONDITIONAL** | **PASS** | no document states the object; P20's contract does reveal that the population is a choice (disclosed as residual weakness 2) |
| ambiguity audit (two independent readers) | **CONDITIONAL** | **CONDITIONAL** | **CONDITIONAL** | met only in the weak sense: verifier and reference solution derived separately from the written spec. **Single author throughout** |
| multiple-valid-method audit | **PASS** 4 routes | **PASS** 2 routes | **PASS** 2 routes | measured spreads recorded; tolerances set from them |
| hidden extracts: 3 regimes, decisions not constant | **PASS** | **PASS** | **PASS** | P22 escalate on 1 of 4; P20 three distinct actions; P31 three distinct verdicts |
| no extract within tolerance of a threshold | **PASS** | **CONDITIONAL** | **PASS** | see decision-margin |
| grading evidence map | **PASS** | **PASS** | **PASS** | `grading_maps.md`, each criterion mapped to the mutation that breaks it |
| environment reproducibility and isolation | **PASS** | **PASS** | **PASS** | `environment_and_redteam.md` |
| resource limits do not bind | **PASS** | **PASS** | **PASS** | 32 s / 1 m 42 s / 34 s against 5,400 s |
| secret and leakage scan | **PASS** | **PASS** | **PASS** | no credentials; no generator internals, hidden specs or truth in any workspace |
| **adversarial exploit agent** | **BLOCKED** | **BLOCKED** | **BLOCKED** | no non-target-model agent available; target models forbidden this phase. Hand-written probes substituted and labelled |
| **independent human re-solve / expert baseline** | **BLOCKED** | **BLOCKED** | **BLOCKED** | not attempted; needs a second person |

## Overall

**P22: READY, conditional on the two BLOCKED gates.**
**P20: READY, conditional on the two BLOCKED gates and on accepting a 1.8× decision margin on hidden_a.**
**P31: READY, conditional on the two BLOCKED gates.**

No task is blocked on a scientific defect. The two blocked gates are both "a second party is required" gates, and
neither can be closed by me in this phase.

## What must not happen next without authorisation

Freezing. The manifest in `proposed_freeze_manifest.txt` is a **proposal**: the checksums record the current
content so that a later freeze can be shown to be of the reviewed artefact. Nothing has been frozen, no target
model has been run, and the exposure procedure in the phase-2 handoff §29 has not been started.

## Validation script result (2026-09-24)

`bash scripts/validate_phase3.sh` → **phase 3 validation: PASS**, all 24 checks. The decisions it prints per
task confirm the anti-constant property:

```
p22: visible=no_supplier_action  hidden_a=no_supplier_action  hidden_b=raise_supplier_nonconformance  hidden_c=no_supplier_action
p20: visible=retain_model        hidden_a=replace_with_v4     hidden_b=remediate_feature_pipeline     hidden_c=retain_model
p31: visible=incumbent_correct   hidden_a=incumbent_incorrect hidden_b=incumbent_correct              hidden_c=not_determinable_from_available_evidence
```
