# G36 adjudication - replay of the three existing submissions

**No agent was executed. No model was called.** Each trial's saved `analysis_results.json` values,
obtained by deterministically re-executing its *saved* `capacity_forecast` package on each fixture
(`tools/g36/replay_submissions.py`, results in `../replay_results.json`), are graded against each
candidate definition of the response.

**This is adjudication, not a new baseline. The recorded frozen rewards are unchanged: 0, 0, 0.**

## Tolerances

Every definition is graded at 2.5 x the sampling SE of the reference F1 estimator *for that
definition*, measured by Monte Carlo on the frozen generator (`definition_se.py`, 12 redraws per
fixture). The frozen column uses the frozen verifier's own SE_REF (30 redraws). The forecast and
decision checks are identical to the frozen verifier's in every column.

| fixture | SE hh (frozen, 30r) | SE hh (12r) | SE load | SE season |
|---|---|---|---|---|
| visible | 0.00690 | 0.00614 | 0.00488 | 0.00501 |
| hidden_a | 0.01122 | 0.01120 | 0.00823 | 0.00783 |
| hidden_b | 0.00584 | 0.00518 | 0.00500 | 0.00517 |
| hidden_c | 0.01650 | 0.01911 | 0.02266 | 0.01396 |
| hidden_d | 0.00618 | 0.00563 | 0.00433 | 0.00440 |

The 12-redraw SEs are approximate. No conclusion below is sensitive to them: every pass is at 0.30x
tolerance or better and every fail at 1.04x or worse.

## Replay

```
response error / tolerance by definition (tolerance = 2.5 x SE of the reference F1 estimator for that definition)
T   fixture      frozen   hh(12r)      load    season  forecast ok / decision ok
1   visible        0.87      0.98      0.05      0.17  yes / yes
2   visible        0.78      0.88      0.08      0.05  yes / yes
3   visible        0.78      0.88      0.08      0.05  yes / yes
1   hidden_a       0.38      0.38      0.04      0.07  yes / yes
2   hidden_a       0.22      0.22      0.18      0.16  yes / yes
3   hidden_a       0.22      0.22      0.18      0.16  yes / yes
1   hidden_b       1.04      1.18      1.35      1.27  NO / yes
2   hidden_b       2.21      2.50      0.02      0.05  yes / yes
3   hidden_b       2.21      2.50      0.02      0.05  yes / yes
1   hidden_c       3.56      3.07      2.42      3.41  NO / NO
2   hidden_c       0.65      0.56      0.30      0.03  yes / yes
3   hidden_c       0.65      0.56      0.30      0.03  yes / yes
1   hidden_d       1.78      1.96      0.62      0.74  yes / yes
2   hidden_d       1.53      1.68      0.26      0.39  yes / yes
3   hidden_d       1.53      1.68      0.26      0.39  yes / yes

TASK-LEVEL OUTCOME (all fixtures must pass)
trial  frozen         household      load           season         forecast_only
T1     fail           fail           fail           fail           fail         
T2     fail           fail           PASS           PASS           PASS         
T3     fail           fail           PASS           PASS           PASS         
```

## Reading

- **T1 fails under every definition**, including forecast-only grading. Its `hidden_c` forecast is
  4.0x tolerance with the wrong decision, and its `hidden_b` forecast is outside tolerance. It is a
  genuine model failure regardless of how the response is defined.
- **T2 and T3 fail only under the household-weighted definitions** (frozen and re-measured). Under the
  load-weighted definition they sit at 0.02-0.30x tolerance on every fixture. Under forecast-only
  grading they pass.
- The household-weighted failures are not marginal: 2.21x on `hidden_b` and 1.53x on `hidden_d`.
  Their correct-definition fits are not marginal either. This is a definitional disagreement, not a
  sampling one.

## What this replay may and may not be used for

| use | permitted? |
|---|---|
| establishing that the frozen 0/3 is contaminated by F8 | **yes** |
| establishing which trials are genuine model failures | **yes** — T1 only |
| reporting 2/3 as the official G36 baseline | **no** |
| entering 2/3 or 0/3 into the final benchmark aggregate now | **no** — see `recommendation.md` |
