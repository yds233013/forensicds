# G34 audits E–H — IGQA, counterexample search, decision/tolerance, fixture coverage

Deterministic and read-only. Tool: `tools/g34_audit/counterexamples.py`, output `counterexamples.json`.
It replicates the frozen verifier's numeric checks in-process: five quantities within 5 × SE_REF on
4 extracts, sum to one, recommendation, and the visible-only two-objects gap. Bookkeeping fields are
filled correctly so that each method is judged on its interpretation alone. No Gemini, no Harbor, no
container. Each method's legitimacy was fixed **before scoring**.

## E. IGQA — every reward-bearing quantity
| quantity | (A) semantic | (B) computational | class |
|---|---|---|---|
| `unplanned_failure_rate_36m` (Q1) | pinned: contract "mutually exclusive outcomes … proportions of the installed base … by 36 months"; memo defines the business meaning | two independent derivations (AJ; crude share in the complete-follow-up cohort) agree with latent truth (`semantic_audit_verifier.md` §C); truth is generator-latent, not a helper | **PASS** |
| `overhaul_rate_36m`, `retirement_rate_36m` | pinned, same sentence | AJ + complete cohort | **PASS** |
| `still_original_assembly_36m` | pinned | AJ survival + cohort; also algebraically forced (1 − the three CIFs) | **PASS** |
| `assembly_failure_rate_36m` (Q2) | pinned **by prose** (engineering note), every alternative reading excluded by wording (`semantic_audit_engineering_quantity.md`) | KM, Weibull MLE, Nelson–Aalen, complete-cohort KM all agree | **PASS** (minor documentation risk: prose, not formula) |
| `recommendation` | memo rule, strict > 28 % | algebraically forced by Q1 | **PASS** |
| `installed_base_units`, `event_counts` | counts defined in contract | exact SQL recount | **PASS** |
| `units_at_risk` | defined in contract (still in service and inside window at age a) | recount; ±2 absorbs the > / ≥ boundary | **PASS** |
| sum-to-one, two-objects gap | consistency (B-type) | algebraic | n/a (no truth) |

**No quantity is AMBIGUOUS or FAIL.**

## F. Counterexample search (reward under the frozen verifier)
| method | kind (pre-fixed) | reward | rejected by | most-detectable err/tol |
|---|---|---|---|---|
| V00 AJ + KM (contract-derived) | legitimate | **1** | 0/4 | 0.35 |
| C05 complete-follow-up cohort | legitimate | **1** | 0/4 | 0.84 (hidden_a Q1) |
| C06 actuarial monthly life table | legitimate | **1** | 0/4 | 0.36 |
| C07 stratified by model, share-weighted | legitimate | **1** | 0/4 | 0.35 |
| E05 Nelson–Aalen (Q2) | legitimate | **1** | 0/4 | 0.35 |
| E06 Weibull MLE (Q2) | legitimate | **1** | 0/4 | 0.40 |
| E10 KM on complete cohort (Q2) | legitimate | **1** | 0/4 | 0.35 |
| C08 stratified by model, **equal** weights | ambiguous | 1 | 0/4 | 0.38 |
| C09 stratified by site, **equal** weights | ambiguous | 1 | 0/4 | 0.38 |
| C10 "today's running units" forward Q1 (prose reading of the memo) | ambiguous | **0** | 4/4 | 5.18 (and sum-to-one) |
| C01 crude, any age | wrong | 0 | 4/4 | 30.61 |
| C02 admin-censored counted as surviving | wrong | 0 | 4/4 | 32.60 |
| C03 incumbent: competing events as censoring (published method) | wrong | 0 | 4/4 | 67.85 |
| C04 competing as censoring, forced to sum to one | wrong | 0 | 4/4 | 23.84 |
| C11 telemetry gap = failure | wrong | 0 | 4/4 | 6.37 |
| C12 telemetry gap = censoring | wrong | 0 | 4/4 | 16.00 |
| E02 Q2 = CIF | wrong | 0 | 4/4 | 5.55 |
| E03 retired as never failing | wrong | 0 | 4/4 | 4.80 |
| E04 overhauled as never failing | wrong | 0 | 4/4 | 3.84 |
| E07 F / (F + S) | wrong | 0 | 4/4 | 7.87 |
| E08 horizon 24 | wrong | 0 | 4/4 | 7.47 |
| E09 complete-case denominator | wrong | 0 | 4/4 | 8.86 |
| E11 1 − all-cause survival | wrong | 0 | 4/4 | 11.27 |
| E12 crude failures / N | wrong | 0 | 4/4 | 8.73 |

**No wrong method passes. No legitimate method fails.**

- **Equal-weighting alternatives (C08/C09) pass**, and this is **not a G36-type failure**. In the
  generator, model and site are assigned at random and carry no effect, so every stratum has the
  same latent risks and any weighting of strata estimates the same quantity. There is no
  heterogeneity for a wrong weighting to get wrong. The contract pins installed-base proportions
  regardless.
- **C10 is rejected.** The contract excludes this prose reading: "proportions of the installed base
  in the extract", four mutually exclusive outcomes including retirement, and a register "whatever
  their current status".

**Identifiability window (lesson 11):** the worst legitimate route sits at 0.84 × tolerance (4.2
SE_REF); the hardest wrong route (E04) is caught at a minimum of 3.84 × tolerance on its most
detectable fixture, and ≥ 1.76 × on every fixture. That is a ratio of ≈ 4.6. **Adequate.**

## G. Decision / tolerance compatibility (Q1 vs the 28 % trigger)
| extract | truth Q1 | \|truth − 0.28\| | tolerance | distance / tolerance | flag |
|---|---|---|---|---|---|
| visible | 0.3598 | 0.0798 | 0.0138 | 5.79 | ok |
| hidden_a | 0.2523 | 0.0277 | 0.0130 | 2.13 | ok |
| hidden_b | 0.2526 | 0.0274 | 0.0124 | 2.21 | ok |
| hidden_c | 0.5484 | 0.2684 | 0.0150 | 17.93 | ok |

Tolerance < distance on every extract, so **no numerically accepted Q1 can imply the wrong
decision.** The closest are hidden_a and hidden_b, with 2.1× headroom. (Contrast G36: visible and
hidden_c were flagged.)

## H. Fixture coverage
Every one of the 14 wrong methods is rejected **numerically** (err/tol > 1) on **all four** extracts,
and each extract rejects 14/14. No single fixture carries disproportionate power. The recommendation
check adds hidden_a/hidden_b rejections for C03, C04 and C11, but is never the sole reason. The
gap test and sum-to-one are never the sole reason for any wrong method's reward of 0.
