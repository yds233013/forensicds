# G36 pre-freeze gates A1-A30

Evidence for every gate. "All pass" is not an answer.

| | gate | evidence | verdict |
|---|---|---|---|
| **A1** | DGP matches the research design | stable weather-load mechanism, unstable tariff response, opt-in selection and heat damping all present and measured; two orthogonal transports preserved | **PASS** |
| **A2** | target quantity identified | `E[peak kW \| whole estate on tariff, forecast weather]`; four observable ingredients, no future outcome | **PASS** |
| **A3** | solver-visible evidence sufficient | history, pilot enrolment log with randomised arms, customer master, published weather outlook - all in the extract | **PASS** |
| **A4** | selection transport necessary | `M09_temperature_fixed_only` fails 8 checks; enrolment over-representation 0.32x-2.49x (0.07x-2.90x on hidden_a) | **PASS** |
| **A5** | CDD-dependent response necessary | `M08_selection_fixed_only` fails 3 checks; `M14_response_at_midpoint_cdd` fails 2 | **PASS** |
| **A6** | recognition != execution preserved | H1 alone 37.1 sd / 1-of-5 wrong; H2 alone 70.8 sd / 3-of-5; both 1.3 sd / 0-of-5 | **PASS** |
| **A7** | correct-table gate passes | every panel method ran on a perfect table; worst valid 0.0187, incumbent wrong by up to 0.562 | **PASS** |
| **A8** | >=2 genuinely independent valid estimators agree | F1 closed-form two-stage, F2 Gauss-Newton joint nonlinear, F3 empirical-Bayes shrinkage; pairwise \|t\| <= 1.82 | **PASS** |
| **A9** | valid decisions agree on all fixtures | unanimous and correct on 20 of 20 draws; all three correct on all 5 frozen fixtures | **PASS** |
| **A10** | coherent historical analysis fails | incumbent holds out at R2 0.748-0.753, bias <= 0.006, reconciles - wrong by 0.174-0.562, reward 0 | **PASS** |
| **A11** | selection-only sophisticated analysis fails | `M08` reward 0 | **PASS** |
| **A12** | same-history / different-future preserved | hidden_b vs hidden_c: holdout RMSE 0.7573 vs 0.7528 (0.6 % apart), truths 2.7274 vs 3.1366, opposite decisions | **PASS** |
| **A13** | cheap-solve panel rejected | 13 shortcuts carried into the suite, none above reward 0 | **PASS** |
| **A14** | constant decision rejected | `M20_constant_procure` and `M21_constant_defer` both reward 0; fixture split 3 defer / 2 procure | **PASS** |
| **A15** | wrong-method panel rejected | 23 wrong mutations, all reward 0; 24-method local panel, all >= 1 wrong decision | **PASS** |
| **A16** | mutation hashes valid | 25 distinct hashes, `source_sha256` recorded per case; one genuine duplicate caught and replaced | **PASS** |
| **A17** | mutation outcomes as expected | 27 cases, 0 mismatches, 0 ERRORs | **PASS** |
| **A18** | no generator-only graded facts | 7 graded facts audited, 8 candidates explicitly refused | **PASS** |
| **A19** | no future-outcome graded facts | target-season outcomes do not exist in any fixture; decision made on forecast | **PASS** |
| **A20** | representation leakage clean | row order \|r\| <= 0.031; enrolled counts overlap 553-629; backtest R2 range 0.005 | **PASS** |
| **A21** | tolerance calibration defensible | measured window 0.91-6.88 SE_REF, chosen 2.5; 30 redraws per fixture; no model involved | **PASS** |
| **A22** | Oracle = 1 | 13/13 local; **1.000 under real Harbor** | **PASS** |
| **A23** | Nop = 0 | 7 failed / 6 passed local; **0.000 under real Harbor**; passes bookkeeping and reconciliation and still scores 0 | **PASS** |
| **A24** | clean rebuild reproducible | two independent `--no-cache` builds plus the dev image: `b6e5787096a111e3` three times | **PASS** |
| **A25** | tamper controls pass | 5/5 fire: pytest.ini, conftest.py, stdlib injection all refuse to grade; warehouse edit fails 8 checks; `/tests` and `/solution` absent | **PASS** |
| **A26** | Harbor check clean | `jobs/2026-09-20__19-03-35`, **11/11 pass**, $0.4688, single invocation, no reruns | **PASS** |
| **A27** | G35 checksum unchanged | `3b7c6a4bd0f403a7` | **PASS** |
| **A28** | G34 checksum unchanged | `f14dd0c0dbcd763c` | **PASS** |
| **A29** | G05 checksum unchanged | `77a6e432d9d2cba2` | **PASS** |
| **A30** | secret scan clean | no key-like strings in candidate, tools or research | **PASS** |

## The gate that required the most work

**A8** was the blocking condition and it failed three times before passing, each failure exposing a
real defect: a truth that returned the median rather than the mean, an F2 that was misspecified
rather than independent, and an F1 carrying a ratio-estimator bias. See `development_defect_log.md`.

## The weakest gate

**A9 holds, but with less headroom than G35.** Decision margins are 2.0 to 18.5 SE_REF, with three
fixtures between 2.0 and 3.1. All three independent families decide all five frozen fixtures
correctly, and were unanimous and correct on 20 of 20 fresh draws - but this is the number a
reviewer should scrutinise first.
