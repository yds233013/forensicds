# 01 — The assignment, and the slice of data science we chose

## First, a provenance warning about the assignment itself

**The original Abundant assignment text is not in this repository.** This is not an oversight in the
dossier; it is a documented fact recorded at the time. `research/audit/abundant_requirements.md`, dated
2026-09-23, opens with:

> **Caveat recorded first: the original assignment text is not in the repository.** `grep -ril
> "abundant\|take-home"` over all tracked Markdown returns nothing. This audit therefore checks the
> requirements as restated by the project owner in the audit brief, and flags that the wording of the
> source document could not be re-read.

I re-ran that search. The string now appears only in documents *this project wrote* (the handoffs, the
final report, that audit file) — never in a source brief. **Therefore every requirement below is a
RESTATEMENT, not a quotation.** Nothing in this chapter should be read as the assignment's own words.

### The requirements as restated, and an inconsistency between two phases

| # | restated requirement | source |
|---|---|---|
| 1 | **5–10 tasks** | `research/audit/abundant_requirements.md` (phase: five-task submission) |
| 1′ | **exactly 10 final tasks** | `HANDOFF_2026-09-28_ABUNDANT_RESUME.md`, `HANDOFF_ABUNDANT_FINAL_SUBMISSION.md` (phase: final ten) |
| 2 | Harbor task format | both |
| 3 | ≥3 target-model trials per task | both |
| 4 | **<30% pass@3** headroom target on `google/gemini-3-flash-preview` | both |
| 5 | Oracle = 1, Nop = 0 | both |
| 6 | `harbor check` task-quality rubric | the earlier restatement |
| 7-8 | logs and a report shipped | both |
| 9 | distribution justification — tasks representative of real DS work | both |
| 10-18 | difficulty profile, research awareness, 10→1000 scale plan, trajectory-derived failure analysis, automation disclosure, piloting-and-curating | the earlier restatement |

**The two restatements disagree on the task count** (5–10 versus exactly 10). **INFERENCE:** there were two
briefs, an initial one and a later final-ten brief. The repository contains neither. This matters because
the five-task submission (`submission_5task_fallback.zip`, unchanged since 2026-09-22) was audited as
compliant against the *first* restatement, and the final ten against the *second*.

### What was required versus optional versus chosen

- **Required** (on both restatements): Harbor format, ≥3 trials per task, Oracle/Nop validation, logs, a
  report, a distribution justification.
- **A target, not a hard gate:** `<30% pass@3`. It is a headroom *goal*; the project treated it as
  something to measure honestly rather than to engineer toward, and chapter 10 reports that it holds for
  the flash-tier model and **fails** for frontier Claude.
- **Chosen by us:** the slice (below), the ten specific mechanisms, criterion-level grading (nothing in
  any restatement asked for it), hidden sibling worlds, and the adversarial validation suites.

## The slice: decision-grade production data science

**Definition.** Work in which *an analysis feeds a named business decision with money attached, the
evidence is operational exhaust rather than a curated dataset, and a plausible analysis is already in the
room.* The agent inherits another analyst's work.

Three clauses, each doing real work:

1. **"Named decision with money attached."** Every final task ends in a specific action: release a capital
   tranche, position on a £1.8m claim, raise a supplier nonconformance, procure capacity, retire a
   forecast model, roll out a courier incentive. The decision rule is written in a document the agent is
   given — a contract, a regulator's reserve requirement, a model-risk standard, a break-even memo. **The
   agent does not get to choose the objective.**
2. **"Operational exhaust."** SQLite warehouses with orders, shifts, assignments, configuration tables,
   event logs and ledgers — joined, grainy and incomplete. Not a feature matrix.
3. **"A plausible analysis already in the room."** The incumbent analysis runs, is documented, and is a
   *correct computation of the wrong quantity*. This is the clause that distinguishes the slice from
   ordinary data-analysis benchmarking.

### Relationship to real job families

| job family | what overlaps | what does not |
|---|---|---|
| **Data scientist / decision scientist** | heavy overlap: estimand choice, identification, population definition, mapping a number to a decision | no stakeholder negotiation, no experiment *design*, no modelling of novel phenomena |
| **Data analyst** | metric reconstruction, definitional reconciliation (`p31` is almost pure analyst work) | less dashboarding, no self-serve enablement |
| **ML engineer / MLOps** | `02` and `p20` are squarely here: point-in-time correctness, training-serving skew, monitoring under governance | no serving infrastructure, no latency or cost engineering |
| **Analytics engineer** | `g08` is a semantic/temporal-modelling task (data vintages, as-of joins) | no dbt-style transformation layer, no lineage tooling |
| **Quality / process engineer** | `p22` is measurement-system analysis under a contract | no physical experimentation |

### What this slice is **not**

- **Not generic business reasoning.** Every task requires a specific statistical object to be recovered
  correctly, and reward depends on a number landing within a tolerance on worlds the agent has not seen.
  A well-argued memo with the wrong quantity fails — and chapter 08 documents 7 trials where exactly that
  happened while the *decision* was right.
- **Not a comprehensive evaluation of data science.** Deliberately absent: model training and tuning at
  scale, feature engineering for predictive performance, deep learning, time-series forecasting *method*
  selection, experiment **design** (as opposed to re-analysis), data engineering at scale, visualisation,
  stakeholder communication, and anything requiring novel method development. **Ten tasks sample one
  capability; they do not cover a profession.**
- **Not a test of tool use or coding ability.** The incumbent code runs. Chapter 08 records that no valid
  trial produced non-executing work.

## Provenance for each final task

Each final task carries `REAL_DISTRIBUTION_PROVENANCE.md` with ten fields including public sources.
**All ten files exist** (VERIFIED FROM ARTIFACT, `MACHINE_READABLE_INVENTORY.csv`).

### Documented provenance — mechanism attested in public sources

| task | mechanism | source type |
|---|---|---|
| `p22` | calibration corrects bias, Gauge R&R addresses consistency; a control chart on an unvalidated gauge shows false out-of-control signals | MSA / Gauge R&R practice literature |
| `p31` | no universal OTIF standard; disputes turn on order vs line vs case level and on request vs promise date; a supplier reporting 97% fill rate can see OTIF in the 80s and chargebacks arrive | supply-chain practice sources, incl. a documented 98% OTIF threshold with 3%-of-COGS charges |
| `g10` | sales understate demand at stockout; models trained on censored sales underestimate demand, lowering reorders and recurring stockouts — a documented self-reinforcing cycle | censored-demand forecasting literature, incl. a stockout-annotated public dataset |
| `g50` | interference is a documented SUTVA violation with large measured magnitudes — an auction experiment's estimate wrong by a factor of two; a marketplace search experiment overestimating by 50% | two-sided marketplace experimentation literature |
| `02`, `p20` | without point-in-time joins models leak future information and produce metrics that collapse in production; training-serving skew is named as the first thing to suspect | feature-store / point-in-time-correctness practice |
| `g24` | offline evaluation is an imperfect proxy for online performance; recommendation data are biased by the exposure process; flaws in offline setups are widespread | off-policy-evaluation literature |
| `g08` | using revised rather than as-of data exaggerates apparent forecast performance; scoring a day-one forecast against current values is named the commonest reason a backtest overstates accuracy | real-time-data / revision-risk econometrics |

### Plausible but **not** independently attested in a cited source

| task | the claim | status |
|---|---|---|
| `g05` | wave-based store rollout with readiness-ordered sequencing and a tranche gate is standard retail capital practice | **plausible, not sourced.** The *statistical* content (staggered-adoption identification) is well attested; the *operational* pattern is asserted from practice knowledge. Its provenance file says so. |
| `g36` | AMI interval data with phased or opt-in TOU enrolment and coincident-peak capacity obligations under a regulator-set reserve | **plausible, not sourced.** Same split: the mechanism is standard, the specific operational configuration is asserted. |

I checked both provenance files: neither claims a citation it does not have. **That honesty is itself
verified** — the files say "the operational pattern … is standard practice and is the direct reference
point", which is an appeal to practice, not to a document.

### What is synthetic in every case

The company, the people, every row of data, and all generator parameters. No real company data is used
anywhere. The DGP mechanisms are *modelling choices*: `g50`'s mean-preserving queue, `g10`'s censoring
process and `p22`'s gauge offset are literature-grounded but not measured from any real system. **Every
conclusion is conditional on them.**

## A discrepancy to record

`README.md` line 26 still describes the **five-task** suite — "gemini-3-flash-preview: 2/15 successful
trials; task-level pass@3 = 1/5 (20%)" — and lists the final suite as Task02, G05, G10, G24, G34. That is
the superseded submission. The final ten replaced it, G34 is **not** in the final ten, and the figures are
1/31 and 10%. **The README is stale relative to the final-ten submission and was never updated.**
Flagged in `OPEN_QUESTIONS.md`.
