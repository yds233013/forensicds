# Experiment design

Design principle: **put the statistical weight where the sample is cheap.** The expensive object is a world family
(expert authoring + expert adjudication); the cheap objects are injected defects (no model calls at all) and
sibling gradings (compute only). So the primary, adequately-powered experiment is model-free, and the model study
is sized to establish existence and ranking rather than to estimate a population rate it cannot estimate with six
families.

Everything below is pre-registered and frozen before any model is run, following the same procedure the pilot used:
a hashed analysis plan committed ahead of exposure, tolerances and criteria frozen, invalid trials preserved.

---

## 1. Questions

**Primary.** Does re-executing a submitted professional analysis against mechanism-flipping siblings detect
decision-relevant defects that (a) single-instance grading and (b) the best expert rubric written for the visible
world both miss — and by how much?

**Secondary.**
- S1. Does conditional correctness reorder a frontier-model ranking relative to single-instance grading?
- S2. How much of family failure is brittleness of the submitted artifact versus failure of the agent's analysis —
  i.e. is cheap replay a valid proxy for expensive re-rollout?
- S3. How many siblings are actually needed? Where does marginal detection flatten?
- S4. What is the cost per resolved reliability question, against single-instance grading and against re-rollout?

## 2. Hypotheses

Stated so each can fail.

- **H1 (incremental detection).** Family grading detects defects that the best visible-world expert rubric misses,
  with incremental detection Δ ≥ 10 percentage points. *Null: Δ < 10 pp, in which case expert rubrics on one world
  are a sufficient instrument and the method's marginal value is small.*
- **H2 (dissociation in real rollouts).** Among rollouts that pass visible-instance grading, a non-trivial fraction
  fail the family, and a majority of those failures are classified by independent experts as
  professional-reasoning failures rather than bookkeeping. *Null: the discordant set is mostly bookkeeping, in which
  case the method measures implementation hygiene, not analysis quality.*
- **H3 (replay validity).** Family failures detected by replay are largely reproduced when the agent is re-run from
  scratch on the sibling world. *Null: fresh rollouts succeed where replay fails, in which case replay measures
  artifact brittleness and must be reported as such — the metric survives, because a deliverable that breaks on next
  month's data is defective, but the claim about professional reasoning goes away.* **This null is pre-committed to
  the abstract (R9)**, not to a limitations paragraph, and it is the most decision-relevant number for anyone
  considering replay as a cheap proxy for re-rollout.
- **H4 (ranking).** Conditional-correctness ranking differs from single-instance ranking (Kendall τ < 1 with a CI
  excluding 1). *Null: the rankings agree, in which case the method is a more expensive way to learn the same thing
  and should be reported as a validation of existing practice.*

H3 exists because of objection E and H1's null exists because of objection G. Both were added by the red team.

## 3. Unit of evaluation

The **world family**. A family is passed by a rollout only if every sibling's pre-registered expectation is met:
conclusions unchanged on invariance siblings, changed to the pre-registered decision on flip siblings, and withheld
with a named identifying requirement on the identification-removed sibling. Per-sibling scores are reported as a
three-part decomposition, never averaged into a single headline (objection D).

For statistical purposes the family is also the **clustering unit**, and with six families that is the binding
constraint on power. This is why H1 is tested on defects rather than on rollouts.

## 4. Materials

**Five to six world families in production data science and analytics** (domain rationale in `METHODOLOGY.md` §8) —
six is the planned ceiling, five the week-6 acceptance floor — each:
- a fixed artifact corpus: data dictionary, the governing contract or policy with its amending schedule, a
  model-governance or quality standard with a written threshold, an incident log, the incumbent analysis and its
  documentation;
- a parameterised generator over decision-relevant latent mechanisms;
- siblings: 1 visible, up to 3 invariance, up to 3 flip, 1 identification-removed — a target of 8, with a **floor of
  two expert-validated flip siblings**. Families ship with however many siblings survive adjudication; the **discard
  rate is a reported finding**, because it prices the construction of decision-flipping variants for anyone building
  this next (R1);
- a frozen verifier with per-criterion rewards and frozen tolerances;
- an expert reference analysis passing all 8.

Mechanisms are drawn from distinct classes so that no two families turn on the same one: measurement-instrument
drift, policy-feedback on an evaluation population, definition change under a governing document, selection into
treatment, delayed-label maturity, aggregation object. This anti-clone rule is inherited from the pilot's world
architecture.

**Defect bank for H1: 150 defects, 25 per family (25 × 6, or 30 × 5 if the study runs on five families), authored by
experts who did not author the world**, each a
single-step modification of the reference analysis with a written rationale for why a practitioner might make it.
Independent authorship is a requirement, not a nicety — the pilot's 45 defects were author-written and that is
its main internal-validity weakness.

**Expert rubrics for the H1 control arm: two independent experts per family**, given the visible sibling, the
corpus and the reference analysis, and asked to write the strongest rubric they can for grading a submitted
analysis. They never see the siblings and are not told the method exists. Their rubrics are applied by the same
judge configuration APEX uses.

**A static-analysis baseline, as a fourth instrument (R2).** A cheap automated check over the submitted artifact:
literals in output fields where an estimate was required, unused inputs, constant returns, and dead branches. This
exists because the single most deflating version of objection G is "a linter would have caught your example". My
prediction, pre-registered: it catches the hard-coded-constant class and reaches at most 2 of the pilot's 10
family-only defects, because the remainder are wrong window, wrong denominator, wrong governing document, wrong
stratification and unconditional acceptance of an incumbent verdict — all idiomatic code. If it does substantially
better than that, the method's marginal value shrinks and the report says so.

## 5. Model sample

Six frontier agents spanning at least four developers, at the configuration each vendor recommends for
long-horizon agentic work, on one harness, with web search off for reproducibility (APEX's own choice). Five
rollouts per (model, family) → **up to 180 primary rollouts** (150 if the study runs on five families). Plus the H3 arm: 3 families × 6 models × 3 siblings × 3
rollouts = **162 fresh-rollout runs**. Total ≈ 342 rollouts.

At the pilot's measured $0.163 per rollout for a flash-class model and an allowance of $3 for frontier
long-horizon agents, the model budget is order $1,000 — inside the fellowship's stated unlimited API credits. The
1,440 sibling gradings (180 × 8) cost compute only; the pilot graded four worlds in 32 seconds of wall clock.

Five rollouts per cell is chosen because the interesting variance is across families, not across repeats; pass^k
style repeat-reliability is APEX's existing axis and is reported but not a hypothesis here.

## 6. Expert baseline

Two experts per family who did not author it solve the visible sibling under the same brief the agent receives,
producing a re-executable deliverable. Their submissions are graded across the family exactly as the agents' are.

This baseline does three jobs: it establishes the human reference point APEX-Agents and APEX-Accounting both use
(20 % of tasks re-solved by uninvolved experts); it tests whether the family is passable by a competent human at
all, which is a validity check on the tasks; and it gives the honest comparison for any claim about the gap being
about professional practice rather than about code generality. **If experts also fail the families at a high rate,
the families are mis-specified and that is a finding to report, not to fix quietly.**

## 7. Construct validity of the siblings

Before any model runs, every flip sibling is shown to two experts who did not author the world. They are asked, blind
to our label, what the correct decision is on the evidence available. A flip sibling is **valid only if both name the
decision we pre-registered, and both differ from the visible sibling's decision.** Invalid siblings are discarded
and the discard rate is reported. Identification-removed siblings are validated the same way, against the question
"is this estimand recoverable from what is here?"

This is the human-vs-model grading-agreement instrument, used for validity rather than as a headline metric, and it
is what answers objection F.

**Realism and detection checks (R6).** Experts additionally rate each sibling on whether it reads as a real
organisation, on the same scale applied to the visible sibling — a sibling that reads as synthetic where the visible
one does not is a construction failure. Independently, all trajectories are scanned for the agent remarking that the
data looks generated or that the task looks like a benchmark. If agents routinely detect the generator, that is a
finding about generative world authoring in general, and it is reported rather than suppressed.

## 8. Metrics

| metric | definition |
|---|---|
| `VP` visible-instance pass | the rollout's artifact passes all criteria on the visible sibling |
| `CC` conditional correctness | the rollout's artifact meets every sibling's pre-registered expectation |
| `d` discordance | P(`VP` ∧ ¬`CC`) — the quantity single-instance grading cannot see |
| profile | (invariance-met, flip-met, deferral-met), reported separately |
| `Δ` incremental detection | family detection rate − best-visible-rubric detection rate, over the 150-defect bank |
| τ | Kendall's τ between the `VP` model ranking and the `CC` model ranking |
| replay validity | P(fresh rollout also fails ∣ replay fails), per sibling type |
| deferral-leg reliability | inter-rater κ on identification-removed expectations, and family results **recomputed with the deferral leg dropped** (R4) |
| cost | $ per family-graded rollout; replay:re-rollout cost ratio; $ per detected defect |

No metric here is invented for sophistication. `VP`, `CC` and `d` are three numbers from one contingency table; Δ is
a difference of two detection rates; τ is a rank correlation; the rest are costs and conditional probabilities.

## 9. Statistical analysis

- **H1.** Per defect, a paired binary outcome (caught by best visible rubric / caught by family). **Exact McNemar**
  on discordant pairs, plus a mixed-effects logistic model with a random intercept per family to respect clustering.
  Δ reported with a 95 % CI from a cluster bootstrap over families (families resampled, not defects).
- **H2.** `d` estimated from the 150–180 rollouts with a family-and-model random-effects logistic model; McNemar for the
  within-rollout `VP`-vs-`CC` contrast. Composition tested against a pre-registered 50 % threshold on the
  expert classification, with inter-rater κ reported.
- **H3.** P(fresh failure ∣ replay failure) with a Clopper–Pearson CI, stratified by sibling type; discordant cases
  read individually.
- **Deferral leg, reported separately (R4).** Inter-rater κ on the identification-removed expectations, and every
  headline result recomputed with the deferral leg removed. If κ is poor the leg is dropped and the
  invariance-plus-flip result stands on its own — the deferral leg is the most contestable part of the design (it is
  what APEX deleted twenty-four tasks to avoid) and the analysis is built so it can be amputated without taking the
  paper with it.
- **H4.** Kendall τ with a bootstrap CI over families; also reported as the number of adjacent-rank inversions,
  because APEX itself cautions that sub-1-point differences should not be over-read.
- **Multiplicity.** Four primary hypotheses, Holm–Bonferroni at family-wise α = 0.05.
- **Power, stated honestly.** With 150 defects clustered in 6 families and an assumed intra-family correlation of
  0.2, the design effect is ≈ 5.8 and the effective n for H1 is ≈ 26 — enough to detect Δ ≈ 25 pp, not Δ ≈ 10 pp.
  **The pre-registered Δ ≥ 10 pp threshold is therefore a decision rule, not a powered test**, and the report will
  say so. If the observed Δ lands between 10 and 25 pp the honest conclusion is "suggestive, needs more families",
  and the deliverable is the generator that makes more families cheap. Six families is what three months buys; more
  families, not more defects per family, is the correct way to spend a follow-on.

## 10. Failure analysis

Every family-only failure is coded by two independent experts into: untested auxiliary assumption; constant
hard-coded where estimation was required; wrong governing document or clause; window, basis or denominator error;
insensitivity on a flip sibling; over-deferral on an identified sibling; bookkeeping or implementation slip. Only
the first five count toward H2's "professional-reasoning" class. Trajectories are read *after* coding, to describe
mechanisms, never to assign the code — the pilot's observation that the token `wear` appeared zero times in three
trajectories is exactly this kind of supporting evidence and exactly not a metric.

## 11. Ablations

- **Sibling-count curve.** Detection as a function of k siblings, averaged over random subsets. Answers S3 and tells
  a benchmark builder how many worlds to pay for. This is the most practically useful number the project can ship.
- **Sibling-type ablation.** Invariance-only, flip-only, identification-only, and all three. Predicts that flip-only
  recovers most of the detection and that invariance-only recovers little — if invariance-only does most of the
  work, the design should be simplified to a robustness eval and the contribution shrinks accordingly.
- **Tolerance sensitivity.** All results recomputed at 0.5×, 1× and 2× the frozen tolerances.
- **Judge-with-trajectory.** The expert rubric arm re-run with the judge shown the trajectory, since that is the
  version of objection H that Mercor could implement next quarter.

## 12. Controls

1. **Reference-procedure control.** The expert reference analysis must pass all 8 siblings in every family. If it
   fails, the family is mis-specified. (Pilot: 3/3 references pass 4/4.)
2. **Degraded-oracle control.** The reference with exactly one professional step removed must pass the visible
   sibling and fail the family. This is the positive control for instrument sensitivity. (Pilot: 10 of 42
   single-defect mutants behave exactly this way.)
3. **Seed-only sibling control.** Siblings that differ only by generator seed, with every mechanism held at its
   visible value, must **not** change any verdict. This is the control that distinguishes "the family detects
   mechanism differences" from "the family is noisy" — and it is the control the pilot lacks.
4. **Leak check.** No sibling's parameter values may be derivable from the visible corpus. Tested adversarially: a
   frontier model is given the visible corpus and asked to predict each sibling's mechanism value; above-chance
   prediction invalidates the family.
5. **Insensitivity control.** A deliberately constant analysis — always the same decision — must fail every family.
   (Pilot: `M07_always_overturn`, `M08_always_defer`, `M09_always_accept` all fail.)
6. **Static-analysis baseline** (R2), above: the instrument that must be beaten for the generator to be worth its
   authoring cost.

## 13. Reproducibility

Generator seeds and parameter vectors frozen and hashed; task digests pinned; verifier wheels hash-pinned and
installed offline; per-criterion rewards emitted as machine-readable JSON; one analysis plan hashed and committed
before the first model call; invalid trials preserved rather than retried; infrastructure-validity adjudication
applied before any scientific reading of a trajectory. The pilot ran under exactly this protocol with 9/9 valid
trials and zero protocol violations, so it is a demonstrated procedure rather than an aspiration.

**Release**: the generator, the five-to-six families with all siblings, the defect bank with independent-author
attributions, the expert rubrics from the control arm, the adjudication records, and a family verifier implemented
against Archipelago's verifier interface — so the result is usable by the benchmark it is aimed at, not only readable.
Nothing released modifies or claims compatibility with any existing APEX dataset.
