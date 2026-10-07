# Review checklist

For an auditor who wants to check this dossier without trusting it.

## Reproduce the numbers (no model calls, ~2 minutes)

```bash
cd /Users/yashshah2311/forensicds
python research_review/build_inventory.py     # -> the three CSVs
python research_review/build_results.py       # -> chapters 05, 06
python research_review/build_trajectories.py  # -> trajectories/ (58 files)
```

Expect: 24 task rows · 139 trial records (94 valid, 45 invalid) · 32 instrumented records ·
58 case studies. Gemini 31 valid / 1 pass on the final ten; Claude 27 valid / 13 passes on 9 tasks.

## Verify the benchmark was not touched

```bash
shasum -a 256 -c SUBMISSION_SHA256.txt                  # expect OK
shasum -a 256 submission_5task_fallback.zip             # expect c8561aad8300df6c8329…
rm -rf /tmp/zc && mkdir -p /tmp/zc
unzip -q submission_final10.zip 'samples/*' -d /tmp/zc
for t in 02-renewal-risk-regression g05-sco-rollout-gate g10-censored-demand \
         g24-recommender-ope g36-tou-capacity-gate p20-noshow-monitoring \
         p22-gauge-recalibration p31-fill-rate-dispute g50-courier-boost-rollout \
         g08-forecast-accuracy-vintages; do
  diff -rq --exclude=__pycache__ "/tmp/zc/samples/$t" "candidates/$t" >/dev/null \
    && echo "OK   $t" || echo "DRIFT $t"
done
```

**Extract the reference fresh.** A stale `/tmp` copy caused a false DRIFT report during this project
(chapter 09, D7).

## Spot-check the load-bearing claims

| claim | command |
|---|---|
| `p22` Gemini trials are byte-identical and `tooling` is always 0.0 | `cat jobs/p22-prospective-*/*/verifier/criteria_notes.txt` |
| `g50` Gemini reported the arm contrast as the decision quantity | `grep -A8 "=== visible" jobs/g50-gemini3flash-v23-1/*/verifier/test-stdout.txt` |
| Claude `p20` sign flips | `grep programme_effect_pp crossmodel_logs/claude/claude-p20-*/*/verifier/criteria_notes.txt` |
| `p31` implements justified deferral | `grep -rn not_determinable candidates/p31-fill-rate-dispute/tests/ candidates/p31-fill-rate-dispute/environment/workspace/docs/` |
| the one full pass | `cat crossmodel_logs/claude/claude-p22-gauge-recalibration-2/*/verifier/criteria.json` |
| scaffold reasoning asymmetry | recompute median `reasoning_content` length per arm from the trajectories |

## Audit items I checked before declaring completion

| check | result |
|---|---|
| broken internal links | all `tasks/*.md` and `trajectories/*.md` targets exist; verified by generation |
| all ten tasks have a chapter | 10 chapters + `INDEX.md` |
| one case study per valid final-ten trial | 58 written, 58 expected — **reconciled** |
| duplicated trials | **found and fixed**: the first generation collided jobs with multiple trials into one filename (48 files for 58 trials); slugs now include the trial id |
| incorrect denominators | Claude's pass@3 is over **9** measured tasks, not 10; the joint comparison uses 9 tasks; both stated explicitly |
| invalid trials counted as failures | none — 45 isolated in the register, excluded before any rate |
| fabricated zeros in criterion data | none — `CRITERION_RESULTS.csv` leaves missing values empty |
| unsupported causal claims | chapter 08 states the multi-mechanism reading and explicitly declines a shared-cause claim |
| secrets in generated documents | scanned (below) |
| prior reports contradicted | 4 contradictions recorded in `OPEN_QUESTIONS.md` (items 12-13) and chapter 09 |

## Known weaknesses of the dossier itself

1. **Trajectory case studies are generated from a template.** They are accurate and complete on observable
   fields, but they are not individually hand-narrated. The hand analysis lives in chapters 07 and 08.
2. **Several `artifacts/workspace/out/` directories are empty in the archives**, so the agents' produced
   numbers are recoverable only from verifier notes. The case studies say "not observable" where that holds.
3. **Docker was unavailable**, so every dynamic re-verification is marked REPORTED BUT NOT REVERIFIED.
4. **Chapter 08 rests on 4 of 10 tasks.** Stated in that chapter and in `OPEN_QUESTIONS.md`.
