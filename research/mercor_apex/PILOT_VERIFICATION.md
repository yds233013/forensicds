# Verified pilot arithmetic: visible-instance grading vs world-family grading

Source: the frozen verifiers' own `criteria_notes.txt` for the nine prospective trials, which record
each failure with the extract it occurred on. Recomputed here; nothing re-run, nothing re-graded.

| task | trial | visible-instance grading | world-family grading | criteria failing on visible | criteria failing anywhere |
|---|---|---|---|---|---|
| p22 | 1 | PASS | FAIL | (none) | decision, quantitative_results |
| p22 | 2 | PASS | FAIL | (none) | decision, quantitative_results |
| p22 | 3 | PASS | FAIL | (none) | decision, quantitative_results |
| p20 | 1 | FAIL | FAIL | quantitative_results | quantitative_results |
| p20 | 2 | FAIL | FAIL | quantitative_results | identification, quantitative_results |
| p20 | 3 | FAIL | FAIL | quantitative_results | decision, identification, quantitative_results |
| p31 | 1 | FAIL | FAIL | decision, estimator_implementation, evidence_reconstruction, identification, independent_validation, quantitative_results, scientific_object | decision, estimator_implementation, evidence_reconstruction, identification, independent_validation, quantitative_results, scientific_object |
| p31 | 2 | PASS | FAIL | (none) | decision, identification |
| p31 | 3 | FAIL | FAIL | decision, identification | decision, identification |

## Per-task totals

| task | visible-instance | world-family |
|---|---|---|
| p22 | **3/3** | 0/3 |
| p20 | **0/3** | 0/3 |
| p31 | **1/3** | 0/3 |
| **all** | **4/9** | **0/9** |

---

## The claim as stated to me, and the correction

**Claimed:** "P22 and P20 would each appear 3/3 successful if only their visible incidents were graded, but both
score 0/3 when the same agent outputs are tested against the controlled hidden variants."

**Verified:** true for P22, **false for P20**.

| task | visible-instance | world-family | does the world family change the verdict? |
|---|---|---|---|
| **P22** | **3/3** | **0/3** | **yes — this is the clean case** |
| **P20** | **0/3** | 0/3 | **no.** All three trials already failed on the visible instance |
| **P31** | 1/3 | 0/3 | yes, for one trial of three |
| **all nine** | **4/9** | **0/9** | — |

P20's three trials failed `quantitative_results` **on the visible extract**: trial 1 reported the programme
effect as −10.59 pp against a truth of +10.85 (a sign inversion), and trials 2 and 3 reported feed-defect shares
of 51.15 % and 63.80 % where the visible truth is 0.00 %. The hidden variants added nothing for P20 — the visible
instance was already sufficient to fail it.

**This correction matters for the proposal, and it helps rather than hurts.** It shows the method does not
manufacture failures: on one task the extra worlds changed the verdict completely, on another they changed
nothing, and on a third they changed it for one trial in three. A method that flipped every verdict would be
suspect.

**The honest headline is therefore:** across nine trials, visible-instance grading would have recorded **4
successes**; grading the same agent outputs across the world family records **0**. The single cleanest case is
P22, where the same submitted procedure passes 3/3 on the observed world and 0/3 across the family.

## Why visible-only grading passed P22, precisely

The frozen truth for the tooling component of the attribution is **0.167 pp on the visible extract** and
**3.083 pp on hidden_c**, where the insert-change interval was extended and a faster-wearing insert grade fitted.
All three trials wrote `"tooling": 0.0` as a literal in their final `attribution.py`; two also retained the
incumbent pipeline's own docstring asserting *"Tooling was on schedule and no operator or shift effect reaches
significance, so those are reported as zero."*

Against a frozen tolerance of ±0.8 pp, a hard-coded zero is **correct on the visible world** (|0 − 0.167| = 0.167)
and **wrong by 3.08 pp on hidden_c**, which pushes the material-attributable rate above the supply agreement's
5.5 % limit and flips the supplier decision from `no_supplier_action` to `raise_supplier_nonconformance`.

The token `wear` appears **zero times** in all three trajectories; `tool_hours` and `tool_changes` appear 2–4
times each, always inside documentation the agent was reading rather than in a query or a computation. Trial 1
closed at step 48 with *"I'm confirming there are no other significant factors."*

So the omission is not a bookkeeping slip. A step of the professional procedure — estimate the wear contribution
before attributing the residual — was **never performed**, and the observed world could not reveal that because
the quantity it omitted happens to be near zero there.

## What the variants exposed, stated narrowly

They exposed an **untested auxiliary assumption inside an otherwise correct analysis**. On the visible world the
agent recovered the headline object correctly — the instrument offset to 7.81 µm against a design value of
8.20 µm, and the corrected nonconforming rate to 3.81 % against 3.83 % — and reached the right decision. The
variant did not test whether it could find the gauge problem; it tested whether the *procedure it submitted*
still produced the right decision when a different latent mechanism carried the weight.

## The cost property that makes this practical

The nine trials cost **$1.4667** in total model spend. Each trial was graded on **four** worlds, because the
verifier re-executes the agent's own submitted pipeline against each regenerated extract. The whole P22 Oracle
trial, including generating and grading four worlds, took **32 seconds** of wall clock.

**Robustness across the family cost one agent rollout plus seconds of CPU, and zero additional model spend.**
The marginal cost of the Nth world is compute, not inference. This is a property of evaluating the *procedure*
rather than re-querying the model, and it is the main reason the method is affordable at benchmark scale.

---

# Model-free calibration: how much does the family add over the visible instance?

The nine-trial result above is nine trials of one model. The stronger and cheaper measurement is model-free:
take the expert reference procedure, inject exactly one defect, and ask **which world the defect becomes visible
on**. That is what the 45 frozen mutation suites already are. Recomputed with
`tools/bench/visible_vs_family.py` → `research/mercor_apex/mutation_visible_vs_family.json`.

Each mutant's numeric readout is compared against frozen truth on the visible extract and on the three hidden
siblings, at the frozen tolerances.

| | count | share of defective mutants |
|---|---|---|
| defective mutants (`want=0`) | 42 | — |
| numerically caught **on the visible world** | 30 | 71.4 %, CI [56.4 %, 82.8 %] |
| numerically **invisible on the visible world, caught by a sibling** | **10** | **23.8 %**, Wilson 95 % CI [13.5 %, 38.5 %] |
| numerically invisible on all four worlds | 2 | 4.8 %, CI [1.3 %, 15.8 %] |
| reference procedures (`want=1`) passing all four worlds | 3/3 | — |

The ten defects that only a sibling world exposes:

| task | defect | first sibling that exposes it |
|---|---|---|
| p22 | `M10_decision_on_corrected_rate` — decision keyed to the wrong rate | hidden_c |
| p20 | `M03_basis_feature_store_current` — as-of features read from the current store | hidden_c |
| p20 | `M07_feed_audit_decile_only` — feed audit restricted to one decile | hidden_b |
| p20 | `M08_decision_skips_feed_clause` — decision omits the feed-integrity clause | hidden_b |
| p31 | `M03_null_confirmation_excluded` — null confirmations dropped from the denominator | hidden_a |
| p31 | `M05_window_on_despatch` — window keyed to despatch rather than the contract event | hidden_a |
| p31 | `M09_always_accept` — accepts the incumbent verdict unconditionally | hidden_a |
| p31 | `M10_ignore_schedule_four` — ignores the amending schedule | hidden_c |
| p31 | `M11_amended_basis_preferred` — prefers the amended basis where it does not govern | hidden_c |
| p31 | `M12_consequences_from_point_estimate` — consequences read off a point estimate | hidden_c |

## Three caveats that must travel with this number

1. **This measures numeric-readout detection only, not the full verifier.** The two mutants invisible on all
   four worlds (`p22 M12_corrected_on_cmm1_only`, `p22 M13_window_off_by_one`) *are* caught by the frozen
   verifier — on `estimator_implementation` and `evidence_reconstruction`, criteria that inspect the submitted
   procedure rather than its output. So the family is not a substitute for procedure-level criteria; the honest
   claim is that the two are complementary, and that 24 % of defects are reachable by the family and *not* by
   the visible instance's numbers.
2. **Family-pass is a subset of visible-pass by construction**, so a non-negative gap is guaranteed. The
   informative quantities are the *magnitude* (23.8 %, CI [13.5 %, 38.5 %] — and clustered in three self-authored
   worlds, so the true interval is wider) and the *composition* of the gap — every one of the ten is
   a substantive analytical choice (basis, window, denominator, governing document, decision rule), not a
   rounding artefact. The three reference procedures passing 4/4 is the control that shows the siblings are not
   simply harder.
3. **45 mutants over three tasks in one domain.** The defects were written by the same author as the tasks, which
   is a real bias: a defect I thought to write is a defect I designed the worlds to be able to see. Independent
   defect authoring is a design requirement for the full study, not an afterthought.
