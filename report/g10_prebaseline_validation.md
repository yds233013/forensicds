# G10 pre-baseline validation: unconstrained demand under informative stockout censoring

- **Task:** `candidates/g10-censored-demand`.
- **Design:** `research/g10/G10_build_design.md` (§0 as-built deltas).
- **Tolerances:** `research/g10/recal/`.
- **No model (Gemini or otherwise) has been run as a solver against this task** before its baseline.
- **Cost accounting, corrected 2026-09-18.** The line above originally read "No model (Gemini or otherwise) has been
  run against this task", which was incorrect: `harbor check` invokes an evaluator agent (`claude-code` /
  `claude-sonnet-4-6`). `g10-check-prebaseline` cost **$0.322628**. That is a validation run, not a solver run, so
  the G10 baseline remains uncontaminated. See `research/harbor_check_protocol.md`.

## 1. Summary

| Gate | Result |
|---|---|
| Tolerance / identifiability pilot (hard gate before building) | passed (`research/g10/G10_tolerance_pilot.md`) |
| Recalibration on the task generator (pre-registered; round 1 failed its gate → documented deviation; round 2) | **passed** (`recal/RESULT_ROUND2.md`) |
| Clean-checkout build (fresh clone of 3efed5c, image rebuilt, real `test.sh`) | oracle **1**, nop **0** |
| Harbor oracle | **1.0** (`jobs/g10-oracle-prebaseline`) |
| Harbor nop | **0.0** (`jobs/g10-nop-prebaseline`) |
| `harbor check` | **11/11 pass** (`jobs/g10-check-prebaseline`) |
| Mutation suite in the task image with the real `test.sh` | **33/33 as expected** (`research/g10/shortcuts_report.json`) |
| Correct implementations on the graded extracts | **11/11 pass**, worst error/tolerance ratio 0.68 |
| Wrong methods on the graded extracts | faulty code and 14/14 wrong methods fail |
| Independent adversarial review | done; 4 major and 6 minor findings, all fixed or recorded (§7) |
| Independent statistical-validity review | done; verdict "valid with caveats"; caveats addressed or recorded (§8) |
| Answer-key audit | pass (§9) |
| Frozen checksums (Tasks 01–06, G08) | unchanged (§10) |
| Secret scan | clean (§10) |

## 2. Graded extracts

| Extract | Store-SKU-days | Fully in stock | Go-live | Lost share, LEAN post / holdout post | v4 bias vs demand |
|---|---|---|---|---|---|
| visible (seed 101013) | 171,968 | 69.8% | 2026-06-29 | 21.1% / 6.8% | −17.9 pp |
| hidden_a | 157,632 | 64.3% | 2025-12-15 | 28.6% / 10.3% | −22.1 pp |
| hidden_b (weak-censoring control) | 186,368 | 87.4% | 2026-04-06 | 7.2% / 3.5% | −12.1 pp |
| hidden_c | 171,904 | 67.7% | 2026-07-20 | 23.8% / 6.5% | −23.7 pp |

**Visible truth: category baseline change.**

| Category | Change | Action |
|---|---|---|
| Soups | −14.1% | reduce |
| Hot beverages | −12.7% | reduce |
| Ice cream | +16.2% | increase |
| Breakfast cereals | −2.4% | maintain |
| Household cleaning | −0.1% | maintain |
| Pasta & sauces | −1.7% | maintain |
| Snacks & crisps | −0.8% | maintain |
| Soft drinks | −1.9% | maintain |

**The deployed review on visible:**
- all eight categories `reduce` (−16% to −38%), including ice cream at −5.3% while its sales are +4.6%;
- lost units 0;
- bias v3 +2.0 pp and v4 +4.1 pp (against sales).

## 3. Tolerances (`tests/tolerances.json`)

| Family | Tolerance |
|---|---|
| Demand totals, period × arm × promo | 1.5% (one stratum 1.63%) |
| Lost units: before go-live all stores and × promo; from go-live × arm and × promo | 6.0% (pre × promo 7.1%) |
| Post-go-live lost share by arm | same keys as lost units |
| Category baseline change | 1.5–1.79 pp |
| Forecast bias | 1.0 pp |

Protocol:
- Tolerance = max(floor, 1.5 × worst error of nine correct NB specifications over 20 calibration worlds).
- Validated on 20 fresh worlds: every correct specification passed 20/20, worst ratio 0.86.
- Actions are graded where truth is ≥ 2 pp from ±5%. The action must also follow the rule for the reported change.

## 4. Error/tolerance ratios on the graded extracts (worst family per extract; > 1 fails)

| Implementation / method | visible | hidden_a | hidden_b | hidden_c | Reward |
|---|---|---|---|---|---|
| **Oracle** (pandas, joint NB MLE, L-BFGS) | 0.36 | 0.55 | 0.23 | 0.36 | 1 |
| **Gibbs** data augmentation (independent loader) | 0.38 | 0.58 | 0.26 | 0.35 | 1 |
| nb (numpy IPF) | 0.36 | 0.45 | 0.34 | 0.33 | 1 |
| em | 0.36 | 0.57 | 0.29 | 0.33 | 1 |
| nb_4week | 0.36 | 0.46 | 0.26 | 0.35 | 1 |
| store_week | 0.39 | 0.46 | 0.31 | 0.34 | 1 |
| sep_cat (separate fit per category) | 0.68 | 0.60 | 0.40 | 0.42 | 1 |
| alpha_sku | 0.36 | 0.49 | 0.28 | 0.36 | 1 |
| promo_common | 0.46 | 0.45 | 0.45 | 0.33 | 1 |
| cat_period_only | 0.35 | 0.46 | 0.26 | 0.33 | 1 |
| store_only | 0.39 | 0.44 | 0.32 | 0.33 | 1 |
| faulty deployed review | 22.0 | 31.1 | 16.7 | 23.9 | 0 |
| sales = demand | 22.0 | 31.1 | 16.7 | 23.9 | 0 |
| drop censored days | 20.2 | 27.4 | 15.5 | 21.4 | 0 |
| forecast imputation | 18.9 | 24.1 | 15.4 | 20.7 | 0 |
| mean-rate imputation | 11.9 | 18.5 | 9.7 | 12.2 | 0 |
| per-day traffic scaling | 13.0 | 8.4 | 14.9 | 11.1 | 0 |
| daily censored Poisson | 8.0 | 10.8 | 9.6 | 9.5 | 0 |
| Poisson offset | 6.2 | 10.1 | 7.3 | 6.5 | 0 |
| NB plug-in imputation | 5.9 | 7.6 | 7.0 | 5.7 | 0 |
| uniform time scaling | 5.9 | 6.6 | 7.6 | 2.7 | 0 |
| forecast as prior | 2.9 | 4.8 | 2.2 | 4.8 | 0 |
| NB without promotions | 3.4 | 4.3 | 2.9 | 3.0 | 0 |
| v3 as prior | 2.1 | 3.9 | 1.4 | 2.0 | 0 |
| traffic profile from all days | 1.8 | 1.7 | 1.1 | 2.4 | 0 |
| holdout transfer | 22.0 | 31.1 | 16.7 | 23.9 | 0 |
| *probe:* common dispersion | 0.97 | **1.59** | 0.48 | 0.82 | 0 |
| *probe:* Poisson-lognormal shock | **1.23** | **1.03** | 0.95 | 0.72 | 0 |
| *probe:* fixed-effects traffic profile | **1.51** | **1.23** | 0.62 | **1.48** | 0 |

## 5. Mutation suite (Docker, real `test.sh`, `tools/g10/shortcuts.py`)

| Group | Cases | Expected | Result |
|---|---|---|---|
| **Controls** | nop | 0 | 0 |
| | oracle; alt numpy IPF; alt EM; alt Gibbs; alt separate category fits | 1 | 1 (15/15 tests each) |
| **Natural wrong corrections** | sales-as-demand (all days), drop censored days, per-day traffic scaling, uniform time scaling, mean-rate imputation, Poisson offset, daily censored Poisson, forecast imputation, profile from all days, NB without promotions, holdout transfer, forecast as prior, v3 as prior, NB plug-in, fixed-effects profile | 0 | 0 |
| **Partial repairs** | correct demand + clean-day baselines (fails trends only); spec baselines + sales demand | 0 | 0 |
| **Patches / cheats** | output-only patch; warehouse edit (fails `test_warehouse_unmodified` only); import verifier generator | 0 | 0 |
| | stdlib exit hook | 0 | refused: "interpreter, standard library or sandbox tools differ" |
| | shadow `pytest` in stdlib | 0 | refused: "files were added to … the standard library" |
| **Overfits** (visible passes, only hidden tests fail) | hard-coded traffic profile; hard-coded dispersion; hard-coded go-live; hard-coded holdout stores; hard-coded actions | visible pass, hidden fail | as expected |

## 6. Hidden regimes

| Regime | Change | Wrong methods it separates most |
|---|---|---|
| hidden_a | Oct–Mar window with reversed seasons (soups and hot drinks up, ice cream down); α × 0.6; lean multiplier 1.15; 9 afternoon-slot stores; flat weekday traffic; other go-live, holiday and closure | Poisson offset, dispersion overfit, common dispersion |
| hidden_b | weak-censoring control: multipliers 2.4 / 2.0 / 2.4; 8 holdout stores; no promo cut; no competitor; breakfast down, soft drinks up | upward-biased imputation (per-day scaling 14.9×); action overfit |
| hidden_c | May–Oct window (soups up, ice cream down); promotions 20% / 15%; v4 promo under-reaction 0.7; strong evening peak; Sunday 11–17; two closures | uniform-time scaling, profile from all days, profile overfit |

## 7. Independent adversarial review: findings and disposition

| # | Finding | Disposition |
|---|---|---|
| M1 | v4 built from realised pre-period arrivals: truth leak for pre lost strata | **Fixed.** v4 is trained on observed clean-day sales before go-live, then frozen. |
| M2 | v3 = true mean × noise: the `rate = v3 / E_full` posterior passed all extracts | **Fixed.** v3 is a 28-day moving average of observed non-promotional sales. `v3_prior` / `forecast_prior` now fail at 3.9× / 4.8×. |
| M3 | Verifier trusts a root-modifiable interpreter | **Mitigated.** Base image pinned by digest; sha256 manifest of the interpreter, stdlib, setpriv, bash, env, sha256sum and find; stdlib file list must match; stdlib `__pycache__` removed; `/etc/ld.so.preload` refused; pytest run with `-I -B`. Mutation cases confirm refusal. |
| M4 | `/tests` hiding fails open | **Fixed.** Grading is refused if uid 65534 can read `/tests/world.py`. |
| m1 | Warehouse digest skipped 3-column tables | **Fixed.** Rows sorted in Python. |
| m2 | Pipeline runs share `/workspace` / `/tmp` state | **Recorded** (§11): no truth gain; only weakens the determinism test. |
| m3 | Event timestamp rounded to closing time | **Fixed.** Timestamps truncated. |
| m4 | Docs hard-code visible hours, traffic, programme counts | **Fixed.** Calendar is authoritative; shape "differs between regions"; programme counts generic. |
| m5 | Unrealistic hidden seasons | **Fixed.** hidden_a and hidden_c seasons reversed. |
| m6 | Action checked only against truth | **Fixed.** The action must also follow the rule for the reported change. |

## 8. Independent statistical-validity review: findings and disposition
- **Estimand, identifiability, realised-sum grading: valid.**
  - A Bayes oracle with true parameters scored 0.05–0.46.
  - Realised-vs-expected lost noise is ≤ 1.6% per stratum.
  - The competitor is immaterial.
  - The oracle's model contains the generator.
- **Gamma tail dependence (lognormal shock fails narrowly).**
  - The data favour NB decisively: log-likelihood +280 to +751 per extract (`tools/g10/lrtest_dispersion.py`).
  - Recorded as a data-checkable discriminator with thin separation: 1.03–1.23× on graded extracts, 8/20 fresh worlds
    pass. See §11.
- **v4 bias tolerance silently binding (0.5 pp).** Floor raised to 1.0 pp in the pre-registration.
- **Category tolerances above the action margin.** Capped at 2.0 pp; all final values ≤ 1.79.
- **Tolerances not recalibrated on the final generator.** Recalibrated twice under pre-registration.
- **hidden_b is not a null.** Renamed "weak-censoring control"; recorded.
- **Docs issues** ("three lines" purchase hint; hard-coded programme facts; within-day shape independent of level):
  fixed.
- **Suggested additions** (plug-in imputation, fixed-effects profile, lognormal): all added to validation and
  mutation.

## 9. Answer-key audit (agent-visible artifacts vs visible truth)

| Artifact | States | Truth | Verdict |
|---|---|---|---|
| `reports/category_review_2026-09.md` | baselines −16% to −38% (all reduce) | −14% to +16% | far |
| `notebooks/lost_sales_quick_estimate.ipynb` | lost 1.9% (LEAN, 4 weeks) | 21.1% (LEAN post) | far |
| `reports/lean26_week8_readout.md` | sales −21% / −6%; shelf stock −58% / −5%; stockout days 20% → 47% | not graded | no key |
| `out/review/programme_impact.json` (faulty) | lost 0; bias +2.0 / +4.1 pp | lost share 6.8–21.1%; bias −5.2 / −17.9 pp | far |
| `reports/availability_weekly.csv` | in-stock rate by week × arm | not graded | no key |
| Forecast tables | built from observed sales only; no latent quantity | — | leak closed (M1/M2) |
| Docs | business definitions; no estimator named; no distribution named | — | pass |

## 10. Git and security
- **Frozen checksums unchanged:**

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

- **Secret scan:** clean for `candidates/g10-censored-demand`, `tools/g10`, `research/g10` and `report`. The API key was
  loaded only via `eval` from `~/.zshrc` for `harbor check` and never printed.
- **Image:** multi-stage; the generator, tests and solution are not in the image (`harbor check` confirms).

## 11. Unresolved validity risks
1. **Common dispersion is not robustly separated.** It passes 19/20 fresh worlds; on the graded extracts only hidden_a
   (category change, 1.59×) fails it. Its assumption is rejected by the data (LR ≥ 1,130 on 7 df), but whether an
   agent's common-α model scores 0 depends on implementation details.
2. **Thin separation for two data-checkable near-misses:**
   - lognormal day shock: fails 1.03–1.23× on two extracts;
   - fixed-effects traffic profile: 1.23–1.51× on three.
3. **Some wrong methods pass hidden_b on fresh seeds.** Profile-from-all-days (4/5) and v3-as-prior (2/5) do; on the
   graded hidden_b the profile method fails at 1.10×. Their reward 0 rests on the other three extracts, where they fail
   at ≥ 1.7× in every seed.
4. **Calibration base is NB-family only.** Nine specifications, all Gamma-Poisson with exposure offset. A
   non-parametric but correct approach (e.g. a flexible mixing distribution) has not been tried.
5. **Parametric generator.** It is Gamma-Poisson with day-type traffic; real demand has more structure. The task rewards
   recovering this generator's estimand, which the docs support through observable facts only.
6. **Shared pipeline state across verifier runs** (`/workspace`, `/tmp`) can make the determinism check pass
   trivially. No grading gain.
7. **In-container integrity checks** cannot defeat a tampered libc or kernel. The manifest raises the bar; it does not
   make tampering impossible.
8. **hidden_b is a weak-censoring control, not a no-effect null.**
