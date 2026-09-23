# Audit 2026-09-23 — where the answer is stated in the workspace ("object leakage")

The single most consequential design finding. For each task, the question is: **is the correct
scientific object derivable only from how the data came to exist, or is it written down somewhere the
agent reads anyway?**

| task | result | where the object is stated | verdict |
|---|---|---|---|
| Task03 | 3/3 | the **task instruction itself** names the population ("retiring the exploration holdout"); `docs/monitoring/lead_score_evaluation.md` states the selective-labels rule in one sentence; the router doc states the intake-draw rule | **stated** |
| Task05 | 3/3 | `docs/experiments/XP-231_plan.md` states all seven required properties (unit of randomisation, ITT, first-assignment rule, window anchor, eligibility, maturity, activation), and the instruction names the file | **stated** |
| Task06 | 3/3 | the contract excerpt states attribution, close semantics and adjustment rules; the vendor doc states revision/void semantics; the issued ledger contains **worked examples** of the target output; the close cutoff is already in the faulty code | **mostly stated**, but 3–4 modules of real assembly remain |
| G35 | 3/3 | `docs/outputs/analysis_contract.md` names all three estimands and defines the spillover arms verbatim; the design note states why 0 % and 100 % pools exist; demand-weighting and assignment-vs-activation are both stated | **stated** (the output contract performs the estimand selection) |
| G42 | 3/3 | `docs/recordable_case_standard.md` and `docs/hours_worked_policy.md` state every inclusion rule | **stated** |
| Task01 | 2/3 | `docs/data/account_identity_standard.md` §2–§5 is a step-by-step procedure for the canonical-account algorithm | **stated**; the discriminator was whether the agent opened that one file (0 references in the failing trial, 4 and 6 in the passes) |
| G44 | 2/3 | the sampling design and the contract population are stated; the *consequences* (weighting a 1-in-N sample; precision depends on the base rate) are not | **partly stated** — and the model derived the unstated part in 3/3 |
| Task04 | 1/3 | the handbook states "customer on D = ARR > 0 on D"; what is **not** stated is that the published workbook is a differently-vintaged artifact that must not be reconciled to | **partly stated**; difficulty lives in the unstated part |
| G08 | 1/3 | the KPI doc defines the target by economic consequence; the settlement doc states the IS/reconciliation distinction; **which clock** (`recorded_at` vs `effective_from`) and **which grain** are not stated together anywhere | **partly stated**, spread across ~10 documents |
| G41 | 1/3 | the availability policy states the feasible set; **no document solves the optimisation** | **execution-hard, object stated** |
| Task02 | **0/3** | no document states the reconstruction rule; the ingredients (load-schedule table, INC-1874, partner weekly batch) are scattered and must be combined | **not stated** |
| G05 | **0/3** | no document states that identification is conditional on format, or that the kit must be transported | **not stated** |
| G10 | **0/3** | no document states the latent-demand construction (exposure-aware, within-day profile, overdispersion) | **not stated** |
| G24 | **0/3** | no document states the eligible-set propensity, the TTL decision unit or slot-level credit as a set | **not stated** |
| G34 | 2/3 | the SOP states the operational codes; **that they are competing events rather than censoring is not stated** | **not stated**, yet solved 2/3 in ~20 steps |

**The association is near-perfect and it is the strongest empirical regularity in the project:**
every task whose object is stated in the workspace was solved (3/3 or 2/3); every task whose object is
not stated was unsolved (0/3), with **G34 the single exception** — and G34 is also the cheapest task in
the pool (median 20 steps, $0.04/trial), which suggests its object is recoverable from a single
well-known textbook substitution (Kaplan–Meier → cumulative incidence) rather than from a genuine
reconstruction.

Caveat: 15 tasks, no randomisation, and "stated" is a judgement made after the results were known,
though it is checkable against the shipped documents. This is an association and a design rule for
future authoring, not a causal claim.
