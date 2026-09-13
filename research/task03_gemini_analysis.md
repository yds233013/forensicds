# Task 03 — Gemini 3 Flash baseline (diagnosis condition)

| Item | Value |
|------|-------|
| Task | `candidates/03-lead-score-evaluation`, frozen at commit 4ba24ca (file checksum `a8443d183fe160e6`, unchanged before and after the runs) |
| Command | `harbor run -p candidates/03-lead-score-evaluation -a gemini-cli -m google/gemini-3-flash-preview -k 3 -n 3 -o jobs --job-name task03-gemini3flash-diagnosis --artifact /workspace -y` |
| Agent | gemini-cli 0.59.0, `gemini-3-flash-preview` |
| Trials | 3 valid (no infrastructure or API failures; `exception_info` null for all) |
| Job runtime | 8 m 45 s wall clock (agent phases 2.3–3.0 min each) |
| Cost | $0.482 total (Harbor-reported: $0.139, $0.155, $0.187) |
| Raw artifacts | `jobs/task03-gemini3flash-diagnosis/` (git-ignored): ATIF trajectories, gemini-cli logs, verifier outputs, final `/workspace` |
| Per-trial table | `research/task03_trials.csv` |

Method:
- Objective evidence came from `tools/analysis/trial_evidence.py`: verifier results, code diffs against the frozen workspace, cost, and greps for reward hacking.
- Step-cited trajectory reading came from `tools/analysis/atif_timeline.py` timelines, cross-checked against the raw trajectory JSON.
- Membership counts quoted below were re-computed read-only on a trial's final `revops.db` (identical to the pristine extract).

## 1. Outcome

| Trial | Reward | Verifier | Steps / tool calls | Agent min | Cost |
|-------|-------:|----------|-------------------:|----------:|-----:|
| PQASiat | **1** | 14/14 (incl. 3 hidden fixtures) | 62 / 37 | 2.6 | $0.139 |
| Ug5BWo4 | **1** | 14/14 | 68 / 45 | 2.3 | $0.155 |
| r2pMM9b | **1** | 14/14 | 76 / 41 | 3.0 | $0.187 |

- **Empirical success rate: 3/3 = 1.00.** This is an estimate of per-attempt success from n = 3, not an exact pass@1.
- **pass@3 = 1.**

**Reward hacking: none.** No tool call in any trial touched `/tests`, verifier or reference files, reward files, `/solution`, Harbor, the interpreter, site-packages or root-level paths. This was checked by grep over all tool-call arguments and by reading every command. The verifier sandbox was never tested by an attempt.

## 2. What all three did (common repair)

All three made one change: a block in `src/lead_eval/cohort.py` restricting accepted leads to those whose **first routing event** was `exploration_holdout`.
- PQASiat first filtered to the three router policies, then took the earliest event.
- Neither of the others touched labels, window, scores, config, metrics or source data.
- Each produced the reference cohort (n = 920, AUC 0.7541).
- None hard-coded IDs, dates or router versions.
- **Every code comment paraphrases or quotes the population sentence** in `docs/monitoring/lead_score_evaluation.md` ("…whose treatment … was not determined by the score being evaluated").

## 3. Research-question checklist

| Question | PQASiat | Ug5BWo4 | r2pMM9b |
|----------|---------|---------|---------|
| Identified selection / evaluation bias | yes (step 18; confirmed 40) | yes (10; 20) | yes (6/12) |
| Understood router behaviour depends on score | yes (18, 24) | yes (10, 20) | yes (6) |
| Intake holdout as the evaluation population | yes | yes | yes |
| Intake assignment rather than later holdout events | yes | yes, taken from doc wording; never inspected a release event | yes, after opening a release re-draw (L-0028254524, steps 22–24) and first leaning toward "any holdout event" (26) |
| Investigated router release / reassignment behaviour | partial (restated rule 24; counted multi-event leads 28–30) | no (opened only a manual-claim example) | partial (opened a release re-draw; reason given was "8 days in nurture would bias"; score-dependence of re-evaluation never stated) |
| Kept leads SDRs never worked (ITT) | yes, **by omission** (queue-order worry raised at 24, unresolved) | yes, by omission (per-protocol never raised) | yes, by omission (speed-of-follow-up worry at 34, unresolved) |
| Any-channel conversions | inherited lifecycle label, never examined | same | same |
| Inclusive 60-day boundary / evaluation window | inherited code, never examined; its own script used string dates and got 919 vs 920 without noticing | inherited, never examined | inherited; its script got 8,727 vs 8,733 (exactly the window-end boundary leads), dismissed as "close" (34) |
| Validated membership directly | no: event-level counts (974 events vs 920 leads) never reconciled | no | partial: distinct-lead counts; n = 790 matched the 1.4.2 report (48); 973 vs 920 unreconciled |
| Or only a plausible AUC | mostly AUC + n (38, 42) | AUC / lift / threshold (44, 48) | AUC trend across 9 as-of dates (46) |
| Modified model / scores / config | no | no | no |
| Hard-coded IDs, dates, router versions | no (scratch scripts had literal dates; deleted) | no | no |
| Hidden fixtures exposed an overfit | no (all hidden checks pass) | no | no |

None of the three opened the CHANGELOG, RA-512 note, model card, `sdr_activities`, `conversions` or `router_config_log`. So none established *when* or *why* the population changed (lead_eval 2.0.0).

## 4. Investigation timelines

**PQASiat**
- SYMPTOM: August/September AUC jump.
- Evidence inspected:
  - README and monitoring doc (4); both notes (6)
  - `cohort.py` (10, 20); `sources.py` (12); baseline run (14)
  - `routing_events` queries (16, 22–32, 36); router doc (18); `metrics.py` (34)
- Hypotheses: holdout vs score-routed populations (18); queue prioritisation bias (24); first vs later event (28–34).
- Root cause: 18, confirmed 40 (all-lead AUC 0.8458 vs holdout 0.7544).
- Repair: 40. Validation: pipeline runs and report reads (42–60).
- Outcome: reward 1.
- Final write-up attributes timing to "leads routed after the threshold change in June", which is a distractor. It also silently overwrote the 1.4.2 historical reports by re-running all months.

**Ug5BWo4**
- Evidence inspected:
  - README and monitoring doc (2), quoted in step 4 reasoning; notes (4)
  - config, `cohort.py`, `sources.py` (6); router doc (8)
  - `routing_events` (10, 24–32); `lead_lifecycle` join with per-policy conversion (16–18: nurture 0.86%, threshold 19.2%, holdout 11.0%)
  - `metrics.py` / `report.py` (20–22)
- Root cause: 10/20. Repair: 50.
- Validation: `test_fix.py` AUC / lift / threshold (44, 48); pipeline run and `head` of cohort (52–54).
- Outcome: reward 1.
- This was the most mechanical path: from the doc sentence to the holdout with little data work. The final message misattributes the "low 0.7s" quote.

**r2pMM9b**
- Evidence inspected:
  - README, monitoring doc and proposal note (2); router doc (4)
  - `cohort.py` (8); `sources.py` (10); baseline run (14)
  - `routing_events` including a release re-evaluation example (12, 16–24, 30, 34, 52)
  - `pipeline.py` / `metrics.py` (26–28); scripts on `lead_lifecycle` (36–46)
  - original 1.4.2 and 2.0.3 reports (48, 50)
- Hypotheses: first vs any holdout event (26 → 36); queue prioritisation (34); discarding 90% of data (34).
- Root cause: 12. Repair: 54. Validation: 46, 48, 56–66.
- Outcome: reward 1.
- The final message wrongly credits the June threshold change for when the bias "became dominant", although its own step-46 output shows all-lead AUC ≈ 0.84 at every as-of date. It also overwrote the 1.4.2 history.

## 5. Behaviour dimensions

| Dimension | PQASiat | Ug5BWo4 | r2pMM9b |
|-----------|---------|---------|---------|
| Breadth of evidence gathering | low | low | medium (only one to read history) |
| Reading business definitions | medium | medium | medium |
| Checking data directly | medium | medium | medium–high |
| Considering alternative hypotheses | low | low | medium |
| Reasoning at the correct grain | medium | low | medium |
| Validating intermediate state | low | low | medium–low |
| Reliance on aggregate metrics | high | high | medium–high |
| Stopping after a plausible number | high | high | medium–high |

No failed trials, so success and failure cannot be contrasted on this task.

## 6. Interpretation

- **Recognition was easy.** The monitoring doc's population sentence plus the router table leave one score-independent population. That sentence was added before the baseline so that harbor check's `behavior_in_task_description` would pass. All three agents found and cited it within a few steps.
- **The designed traps were passed by default, not by reasoning.**
  - Per-protocol, sales-led labels and exclusive boundaries are only traps for an agent that rewrites the working label, window or activity logic. None did, and none examined those parts.
  - The one trap that required an active choice (intake vs any/latest holdout event) was resolved correctly by all three. Only r2pMM9b looked at the data for it, and it gave an incomplete reason.
- **Validation was aggregate-level in all three.** Membership mismatches visible in their own scripts (974 vs 920, 919 vs 920, 8,727 vs 8,733) were not reconciled. The verifier cannot distinguish this shallow process from a careful one when the final cohort is right.
- **Final write-ups contained wrong causal stories.** Two of three blamed the June threshold change, and none reported overwriting historical reports. Grading is behavioural, so these errors carry no penalty.

## 7. Difficulty verdict

**TOO EASY.** It went 3/3 in about 2.5 minutes per trial with a Flash-tier model. Investigation quality was low to medium, and the finer invariants were preserved by inheritance rather than reasoning. Its research value is as an easy anchor for "can the agent map an estimand statement to an operational population". It does not provide headroom. Consistent with the frozen-task decision, the task was not modified.
