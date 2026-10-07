"""One chapter per final task. Structural sections are generated from artifacts; the analytical
sections (A-D, N, O) are authored content keyed by task id. Labels: VERIFIED FROM ARTIFACT /
REPORTED BUT NOT REVERIFIED / INFERENCE / UNKNOWN."""
import csv, glob, json, os, collections
ROOT="/Users/yashshah2311/forensicds"; os.chdir(ROOT)
FA=json.load(open("research_review/_task_facts.json"))
T=list(csv.DictReader(open("research_review/ALL_TRIALS.csv")))
CR=list(csv.DictReader(open("research_review/CRITERION_RESULTS.csv")))
OUT="research_review/tasks"; os.makedirs(OUT,exist_ok=True)

A = {
"02-renewal-risk-regression": dict(
 story="""**Northwind-style B2B SaaS, Revenue Data Science.** A model called `renewal-risk v2.4` predicts which
customer accounts will fail to renew. It was trained in February, scored far better offline than the
previous `v2.3`, and has been scoring live renewals since March. Sales and Customer Success now say the
scores are unusable, and the monitoring dashboards do not resemble the model that was approved. The Q3
retrain is frozen pending an explanation.""",
 question="Is `v2.4` fit to keep scoring renewals, and can the Q3 retrain be released?",
 ds="""Churn/renewal risk scoring is one of the highest-volume applications of applied ML in B2B software. The
work here — rebuild the training pipeline, re-derive the evaluation, explain an offline/online gap — is
the daily job of a revenue data scientist, not a puzzle.""",
 wrong="""The inherited pipeline computes account 'health' features as **time-windowed aggregates** read from the
current state of the warehouse, then joins them to renewal outcomes. Offline AUC looks excellent. The
analysis is internally coherent and the code runs.""",
 plain="""Some of the features are computed from data that did not exist yet when the prediction would have been
made. The model is effectively being told part of the answer. Offline it looks brilliant; in production,
where the future is genuinely unavailable, it does not.""",
 tech="""**Point-in-time correctness.** A training row for account *a* with label observed at time *t* must carry
feature values **as of** *t*, i.e. the most recent value with timestamp ≤ *t*. The inherited pipeline reads
feature values from a mutable store whose rows are overwritten, so a feature for a row labelled in January
can reflect a March value. This is *label leakage via non-point-in-time features*. It inflates offline
metrics and vanishes in production, where the serving path has no future data. The fix is a temporal
('as-of') join, and the evaluation must be recomputed on the corrected matrix.""",
 isolates="""**Partially.** It tests evidence reconstruction and estimand/population repair, and the fix must survive
sibling worlds. It does *not* isolate the 'recognises-but-cannot-quantify' phenomenon, because the task's
reward is binary: a trial that diagnosed leakage but mis-measured the corrected AUC is indistinguishable
from one that never diagnosed it. **UNKNOWN** which of those happened in the Gemini failures.""",
 improve="""Instrument it. A v2 should emit separate criteria for (i) metric population rebuilt as-of, (ii) leaked
features identified, (iii) corrected offline metric within tolerance, (iv) decision. That single change
would let this task contribute to the central failure-mode question instead of only to the pass rate."""),
"g05-sco-rollout-gate": dict(
 story="""**A grocery/general-merchandise retailer, Decision Science in FP&A.** 'SCO 2.0' is a self-checkout
conversion programme deployed store-by-store in waves. The Capital Committee decides in October whether to
release tranche 2 (waves 5-6). The business case defines a specific 'gate figure' the decision turns on.""",
 question="Does the gate figure clear the threshold in the business case, so tranche 2 should be released?",
 ds="""Phased capital rollouts are how retailers actually deploy estate changes, and the gate number is computed
by an analyst from store-week operational data. Getting the estimator wrong here moves real capital.""",
 wrong="""A before/after comparison, or a two-way fixed-effects regression across all store-weeks. Both run, both
produce a signed and precise number, and both are the conventional first thing an analyst reaches for.""",
 plain="""Stores did not all convert at the same time, and the early waves were chosen because they were ready, not
at random. So 'stores that have converted' and 'stores that have not' are not comparable groups, and the
usual regression quietly averages together comparisons that should not be averaged.""",
 tech="""**Identification under staggered adoption.** With treatment timing varying across units and effects varying
with exposure length, the two-way fixed-effects estimator is a weighted average of 2×2 difference-in-
differences comparisons in which *already-treated* units serve as controls for *later-treated* ones, and
some weights can be negative. The gate quantity must be built from comparisons whose control group is
genuinely not-yet-treated, on the exposure window the business case specifies.""",
 isolates="""**Partly, and differently from how we first framed it.** Claude passes 3/3 and Gemini 0/4, so the task
discriminates sharply by model capability. That makes it a good *difficulty* instrument and a poor
*mechanism* instrument: with a binary reward we cannot see whether Gemini's failures were identification
errors or arithmetic ones. **UNKNOWN.**""",
 improve="Criterion-level instrumentation, plus a sibling world in which the naive estimator happens to be right, so that passing for the wrong reason becomes visible."),
"g10-censored-demand": dict(
 story="""**A multi-category retailer, Demand Science.** An inventory-reduction programme called 'LEAN-26' went live.
The Q3 category review now shows baselines down in all eight categories and proposes cutting every buy —
including ice cream, in summer, while ice cream sales are up. The review feeds both the Q3 buy plan and the
decision whether to extend LEAN-26.""",
 question="What is the demand baseline per category, and should the buy plan be cut and LEAN-26 extended?",
 ds="""Demand planning under imperfect availability is a core supply-chain analytics problem, and the artefacts
(sales, inventory snapshots, stockout records, programme configuration) are exactly what a planner holds.""",
 wrong="""Compute baselines from observed sales, and — in the most seductive version — restrict to 'clean'
stockout-free days to remove contamination. That filtering sounds like good hygiene.""",
 plain="""When a product is out of stock you cannot sell it, so sales understate what customers actually wanted.
LEAN-26 *caused* more stock-outs. So the programme has depressed the very numbers being used to judge it,
and keeping only in-stock days throws away exactly the periods that carry the information.""",
 tech="""**Informative censoring, endogenous to the intervention.** Observed sales are `min(demand, availability)`.
Censoring is not random: it is induced by the programme under evaluation, so selecting on availability
selects on the outcome. Latent demand must be reconstructed using inventory and stockout records, and the
baseline re-estimated on that reconstruction. Conditioning on stockout-free days is a collider-style
selection that biases the trend.""",
 isolates="""**Yes, and it is one of the strongest instruments in the suite.** Both models fail every trial (0/3 and
0/3). Gemini's trajectories show heavy, correct engagement with censoring — 29-36 recorded mentions,
one trial recomputing the ice-cream baseline from -5.3% to +9.96% — and still 0/3. That is a direct
observation of correct mechanism engagement with a failing final quantity. **VERIFIED FROM ARTIFACT**
(see the trajectory chapters); the *cause* of the shortfall is **UNKNOWN** without criterion data.""",
 improve="Instrument the per-category baselines and the decision separately. This is the highest-value instrumentation target in the suite, because it is the task where behavioural evidence and outcome most clearly diverge."),
"g24-recommender-ope": dict(
 story="""**A consumer-internet retailer, Personalisation Analytics.** Three rankers are in play for the home row:
the deployed `v6`, a candidate `v7`, and `v7_pd`. The offline gate scored `v7` well above `v6` and `v7_pd`
higher still. But experiment AB-1182 measured `v7` **below** `v6` online, with no sample-ratio mismatch.
`v7_pd` has never been tested online and its number comes from the same gate.""",
 question="Which ranker should serve the home row next quarter?",
 ds="""Choosing a ranker from logged data is the central measurement problem of industrial recommendation, and
the offline/online disagreement here is the canonical symptom.""",
 wrong="""Trust the offline gate's ranking metric. It is the team's established process, it ranks the candidates
confidently, and it is computed correctly on the data it is given.""",
 plain="""The logs only record what the *currently deployed* ranker chose to show. A new ranker that would have shown
different items has no data about them, so scoring it on these logs measures something other than how it
would actually perform.""",
 tech="""**Off-policy evaluation under a logging policy.** Logged bandit feedback gives rewards only for actions the
logging policy π₀ took. Estimating the value of a target policy π requires correcting for the exposure
process — e.g. inverse-propensity weighting `E[(π(a|x)/π₀(a|x))·r]`, with variance control — on the
evaluable population where π₀ had support. A ranking metric computed on raw logs is not an estimate of
π's online value, and the AB-1182 sign flip is the observable evidence of that.""",
 isolates="""**Partly.** Claude 3/3, Gemini 0/3, so again a sharp difficulty split with no mechanism visibility.
Gemini's trajectories do record identifying the gate's 'Direct Match' estimator as biased, and one trial
diagnosed the bias in its *own* first correction — then still failed. **VERIFIED FROM ARTIFACT**;
cause **UNKNOWN**.""",
 improve="Instrument policy-value estimate, evaluable-population definition, and decision separately; add a sibling world where the offline gate and the online result agree, so that trusting the gate is right for once."),
"g36-tou-capacity-gate": dict(
 story="""**A regulated electric utility, Resource Planning Analytics.** The utility holds 1,900 MW of firm capacity
for the residential block, and the regulator requires a 10% reserve. Across 565,000 customers that caps
mean peak-window demand at **3.057 kW per customer**. A planning memo contains the arithmetic.""",
 question="Does FY27 residential peak demand breach the cap, so additional capacity must be procured?",
 ds="""Capacity procurement is a high-consequence regulated decision resting on one scalar derived from interval
(AMI) meter data. All the weight falls on how that scalar is defined and on which population.""",
 wrong="""Compute mean peak-window kW over the observed customer population and compare it with 3.057. The
arithmetic in the memo is correct given its inputs.""",
 plain="""Customers have been moving onto time-of-use tariffs, which changes both when they use power and which
customers are on which plan. Enrolment was not random. So the 'average customer' in the data is not the
population the regulator's cap applies to.""",
 tech="""**Population and exposure definition under non-random tariff migration.** The per-customer peak figure
depends on the tariff mix during the measurement window, and migration is correlated with consumption.
The quantity the reserve applies to must be reconstructed on the specified population and window rather
than on whoever happens to appear in the extract.""",
 isolates="""**Yes on difficulty, no on mechanism.** Both models 0/3. It carries four hidden worlds
(`hidden_a..d` — **VERIFIED FROM ARTIFACT**, `tests/scenarios.py`), the most of any task except `g50`, so
generalisation is tested. But it is binary-reward, so we cannot say where either model broke.""",
 improve="Instrument population definition, the scalar, and the procure/do-not-procure decision; and record whether the agent ever examined the tariff-switch history."),
"p20-noshow-monitoring": dict(
 story="""**Halcyon Health Partners, clinical operations ML.** The model owner for `noshow-v3.1` must file a
monitoring submission under the written model-risk standard **MRM-04**. The vendor's review reports AUC
falling 0.77 → 0.71 and recommends adopting their retrained `noshow-v4.0`. Clinical Operations need a
decision before the winter capacity plan.""",
 question="Retain `v3.1`, remediate the feature pipeline, retrain, or replace with `v4.0` — whichever MRM-04 §4.3-§4.4 requires?",
 ds="""Model monitoring under a governance standard, with a vendor holding a commercial interest in the outcome,
is routine regulated-healthcare analytics.""",
 wrong="""Accept the AUC decline at face value and adopt the vendor's retrained model. The vendor's review is
competent and its recommendation follows from its own numbers.""",
 plain="""Four different things could make the number fall: the patient mix changed; the served feature values
disagree with the source records; the features are stale relative to scoring time; or the reminder
programme the model drives has itself changed who shows up. Each implies a *different* remedy, and only
one of them is 'buy the vendor's new model'.""",
 tech="""**Decomposing a monitored-performance decline into four candidate causes** — population drift, feature-feed
defect, feature vintage, and policy feedback — evaluated on the population MRM-04 §4.1 specifies, with
several scoring bases available in the evidence (`as_served`, `record_features_asof_window`,
`feature_store_current`, `candidate_v4`). Policy feedback is the subtle one: a model that triggers
interventions changes its own outcome distribution, so monitored AUC is not a clean measure of model
quality.""",
 isolates="""**Yes — this is the single best instrument in the suite for the central claim.** It is criterion-
instrumented (7 criteria, **VERIFIED FROM ARTIFACT**: `tests/test_monitoring.py` lines 7, 56) and both
models fail 0/3. The decisive observation: **all three Claude trials pass `decision` and fail
`quantitative_results`** — correct action, wrong number, three times out of three. Gemini shows the same
pattern on 2 of 3. This is *correct decisions supported by incorrect quantities*, measured rather than
inferred.""",
 improve="Add a sibling world in which the vendor's recommendation is in fact correct, so that 'retain the model' cannot be a safe default. Also split `quantitative_results` into the four attribution components so the failing component is identifiable."),
"p22-gauge-recalibration": dict(
 story="""**Kelvin Works, Building 2 — precision machining.** First-pass yield on the MAN-4471 bore has fallen from
97.0% to 92.8% since week 19. Purchasing has drafted a supplier nonconformance against the bar-stock
supplier and wants to escalate to a change of supplier. The supplier has declined the draft, so the claim
must be restated in the form Schedule 3 §3.2 of the supply quality agreement requires.""",
 question="Does the agreement's threshold support raising a supplier nonconformance, and how does the yield loss divide across causes?",
 ds="""Attributing a quality step across candidate causes, on a stratified population, under a contractual
definition, is the core of applied quality engineering.""",
 wrong="""Compute the nonconforming rate from the CMM measurements and attribute the step to the material, because
the step coincides with new heat lots. The measurements are real, the rate step is real, the published
report is arithmetically correct.""",
 plain="""One of the measuring machines was re-zeroed in week 19. A gauge that reads slightly differently will fail
parts that are actually in tolerance. So some of the 'bad parts' are a measurement artefact, not a supplier
problem — and blaming the supplier would be an expensive mistake.""",
 tech="""**Measurement-system bias presenting as a process shift.** Calibration corrects instrument *bias* against a
traceable standard; Gauge R&R addresses *consistency*; a gauge can be perfectly calibrated and still fail
R&R. The conformance-referenced rate must remove the gauge offset — identifiable because the offset appears
in *reference-artefact* measurements, which the supplier's material cannot have affected — and the residual
must then be attributed across material, tooling and operator before the contractual threshold is applied.""",
 isolates="""**Yes, and it produced the dossier's sharpest single observation.** All three Gemini trials produced
**byte-identical, correct** visible-world output (measurement_system 2.88 pp, material 1.06 pp, corrected
rate 3.81%, `no_supplier_action`) and all three scored 0, failing only the sibling world where tooling is
the true driver, reporting `attribution_pp[tooling] = 0.0` against an expected 3.083.
**VERIFIED FROM ARTIFACT** (`verifier/criteria_notes.txt`). Their attribution code had no path that could
assign the change to tooling. Claude reaches 1/3 here — so the generalisation is achievable, which means
the Gemini result is a capability observation and not a design artefact.""",
 improve="Keep it as is; it is the best-designed task in the suite. If versioned, add a fourth cause (operator) as the driver in a further world, and split `quantitative_results` per cause."),
"p31-fill-rate-dispute": dict(
 story="""**Meridian Retail Group, demand science supporting Commercial and Legal.** The published ambient-grocery
service-level report shows a 97.7% fill rate for the quarter. The supplier's own quarterly report shows
91.5% for the same category and period. Three key accounts have logged shortfall tickets. The Commercial
Director wants the metric rebuilt, the team's bonus gate reviewed, and a position on a £1.8m claim that
turns on whether a contractual account floor was breached.""",
 question="What is the contractually correct fill rate, was the account floor breached, and does the £1.8m claim stand?",
 ds="""Reconciling two defensible computations of the same KPI, where a contract selects one of them, is ordinary
and consequential commercial analytics.""",
 wrong="""Recompute the fill rate at the aggregation level the reporting code already uses and defend 97.7%. It is a
correct computation of *a* fill rate.""",
 plain="""There is no single definition of 'fill rate'. Whether you count at order, line or case level, whether you
use the requested or the promised date, and how you treat partial shipments and returns all change the
answer — and the contract fixes one of those choices, not the one the report used.""",
 tech="""**Metric reconciliation against a contractual definition.** The bridge between 97.7% and 91.5% decomposes
into aggregation level, denominator definition, and treatment of returns/substitutions
(`bridge_pp[aggregation]`, `bridge_pp[denominator]`, `bridge_pp[returns_treatment]` — **VERIFIED FROM
ARTIFACT**, these appear in the verifier notes). The contractual floor must then be applied at the
contractual unit, which is not the reporting unit.""",
 isolates="""**Yes, and it shows a *different* failure shape.** Both models 0/3. Two Gemini trials produced the right
numbers (`quantitative_results` PASS) and still failed `identification` and `decision` — the mirror image of
`p20`. One Gemini trial failed all seven criteria outright. **VERIFIED FROM ARTIFACT**
(`CRITERION_RESULTS.csv`). So the suite contains at least two distinct failure shapes, which is evidence
*against* a single-mechanism story.""",
 improve="Add a world in which the published number is the contractually correct one, so that 'the report is wrong' cannot be assumed. Instrument the three bridge components individually."),
"g50-courier-boost-rollout": dict(
 story="""**Northline, an on-demand delivery marketplace.** 'Boost' is a guaranteed minimum courier payout attached
to an individual delivery offer, piloted in spring. The programme readout says it cuts late deliveries by
4.0 points across 120,671 orders and recommends national rollout. The July investment committee decides.
The Finance director wants the recommendation re-derived from the warehouse.""",
 question="Should Boost be rolled out nationally, given £0.19 incentive per boosted order and £12.70 per late delivery — a 1.4961 pp break-even?",
 ds="""Re-deriving an experiment readout before a capital decision, where the experiment was run correctly but
answers a different question, is exactly the marketplace-experimentation problem.""",
 wrong="""Report the phase-2 arm contrast. It is the **correct** estimate of the arm contrast: assignment is clean,
realised share tracks the configured target in every market-week, arms were balanced pre-programme, the
effect appears in all sixteen markets, and the interval is four tenths of a point wide. Its capacity check
compares courier hours available to each arm and finds them identical to within 0.08%.""",
 plain="""A boosted offer jumps the queue ahead of an unboosted one, and the same couriers serve both. So the
measured gain is mostly one order winning at another's expense. Turn Boost on for everyone and there is no
queue position left to win. The capacity check cannot fail, because both arms share the same couriers —
that is the trap.""",
 tech="""**Interference / unit of intervention.** Phase-2 randomises per order, violating SUTVA through a shared
market-hour courier queue. Because the priority reordering is **mean-preserving** within a market-hour, the
arm contrast is largely redistribution and collapses at full rollout. The rollout estimand is
`τ = Σ_m w_m [r_m(1) − r_m(0)]` with `w_m` the pre-programme share of estate orders; it is identified by
the market-level phase-1 soak — the design the incumbent analyst rejected as underpowered.""",
 isolates="""**For Gemini, yes — decisively. For Claude, not measured.** All three valid Gemini trials reported
`programme_effect_pp` **identical to the arm contrast** (within 0.000 pp), an order-level interval 1.882 pp
wide, `courier_hours_response_pct` +0.366 (the zero-power identity check), and `decision: roll_out` — the
expensive wrong answer. **VERIFIED FROM ARTIFACT** (`verifier/test-stdout.txt`). This is failure at the
*estimand* step, a different location from `p22` and `p20`. Claude received **no valid grade** (chapter 09).""",
 improve="""The verifier's runtime hash-pin must be replaced by the resolution check already prototyped, so that a
scaffolded agent can be graded at all. That is a **verifier** fix in a new version, never in the frozen
original. Also retire or narrow the three documented blind spots (`H_post`, `R2`, `M_holdout_as_control`)."""),
"g08-forecast-accuracy-vintages": dict(
 story="""**An energy/commodity trading desk, Trading Analytics engineering.** In July an 'accuracy mart' replaced
the notebook that produced the monthly forecast-accuracy packs. The September review built from the mart
puts `v4`'s WAPE 29.7% below `v3`'s and recommends retiring `v3`. The model board will act on it.""",
 question="Is `v4` genuinely more accurate than `v3`, and should `v3` be retired?",
 ds="""Measuring forecast accuracy against a restated actuals series is a real and widely mis-handled
analytics-engineering problem.""",
 wrong="""Compute WAPE of each model's forecasts against the current actuals table. The mart is well engineered and
its numbers reconcile internally.""",
 plain="""The 'actuals' get revised after the fact. If you score an old forecast against today's revised numbers you
are mixing up how good the forecast was with how much the truth later changed — and the two models made
their forecasts at different times, so the comparison is not fair.""",
 tech="""**Vintage-correct accuracy measurement.** A forecast made at origin *t* must be scored against the actuals
*as of* a consistently defined vintage, not against the latest restated series. Using revised data
exaggerates apparent performance and makes models with different forecast origins incomparable; the
accuracy statistic otherwise reflects both forecast error and revision history.""",
 isolates="""**Weakly.** Gemini 1/3 and Claude 3/3, so it is the easiest of the ten. It earns its place on mechanism
uniqueness — no other final task's defect lives in the *temporal semantics of the evidence table* — rather
than on headroom. Its single `artifacts` criterion is not a capability decomposition.""",
 improve="Instrument it properly, and make the restatement pattern adversarial (e.g. revisions correlated with forecast error) so that a vintage-naive computation is wrong by more than it is here."),
}

def rows_for(task):
    g=[r for r in T if r["task"]==task and r["arm"]=="gemini"]
    c=[r for r in T if r["task"]==task and r["arm"]=="claude"]
    return g,c

for t,a in A.items():
    f=FA[t]; g,c=rows_for(t)
    gv=[r for r in g if r["valid"]=="True"]; cv=[r for r in c if r["valid"]=="True"]
    crit=[r for r in CR if r["task"]==t]
    ckeys=sorted({k for r in crit for k,v in r.items() if v!="" and k not in
        ("arm","model","task","job","valid","invalid_reason","reward")})
    L=[f"# Task chapter — `{t}`","",
    f"**Harbor task name** `{f['toml_name']}` · **difficulty** `{f['difficulty']}` · "
    f"**agent timeout** {f['agent_timeout']}s · **verifier timeout** {f['verifier_timeout']}s · "
    f"**network** `{f['network']}`  ",
    f"**Directory** `candidates/{t}` — verified byte-identical to `submission_final10.zip`. "
    f"**VERIFIED FROM ARTIFACT.**","",
    "## A. The company story and business question","", a["story"],"",
    f"**The question:** {a['question']}","",
    "## B. Why this is genuinely a data-science problem","", a["ds"],"",
    "## C. The tempting but incorrect inherited analysis","", a["wrong"],"",
    "## D. The actual scientific issue","","**In everyday language.**","", a["plain"],"",
    "**Technically.**","", a["tech"],"",
    "## E. Map of task files","",
    f"| area | contents |","|---|---|",
    f"| agent-visible workspace | **{f['n_workspace']} files** |",
    f"| generator (never in the final image) | `environment/build/`: {', '.join('`'+x+'`' for x in f['build'] if x!='__pycache__')} |",
    f"| verifier | `tests/`: {', '.join('`'+x+'`' for x in f['tests'])} |",
    f"| reference solution | `solution/`: {', '.join('`'+x+'`' for x in f['solution'][:8])}{' …' if len(f['solution'])>8 else ''} |",
    f"| instruction | `instruction.md`, {f['instruction_lines']} lines |",
    f"| provenance | {'`REAL_DISTRIBUTION_PROVENANCE.md` present' if f['has_provenance'] else 'absent'} |","",
    "Agent-visible workspace inventory:","","```"]
    L += ["  "+x for x in f["workspace"]]
    L += ["```","",
    "## F. How the data was generated","",
    f"**Entirely synthetic.** `environment/build/world.py` is a seeded generator run at Docker **build time**",
    f"in a stage whose layers are not copied into the final image, so the data-generating process is absent",
    f"from everything the agent can reach. Hidden sibling worlds are declared in `tests/scenarios.py`: "
    f"**{', '.join('`'+h+'`' for h in f['hidden']) if f['hidden'] else 'none declared'}**. "
    f"**VERIFIED FROM ARTIFACT.**","",
    "What is synthetic: the company, the people, every row of data, and all generator parameters. What is",
    "preserved from real practice: the artefact surface, the governing document, and the fact that the",
    "inherited analysis is a correct computation of the wrong quantity.","",
    "## G. The agent's tools and instructions","",
    f"The agent receives `instruction.md` ({f['instruction_lines']} lines) and a populated `/workspace`. It has",
    "the scaffold's full tool set (shell, file read/write, search) inside the container. It is **not** told the",
    "mechanism, is **not** shown `tests/`, `solution/` or `environment/build/`, and has no access to the",
    "hidden worlds.","",
    "## H. Dependency map","",
    f"See `../TASK_DEPENDENCY_MAPS.md` for this task's graph. Chains are stated at the depth the artefacts",
    "support; where a task is genuinely short this is said rather than padded.","",
    "## I. The reference solution","",
    f"`solution/solve.sh` installs the reference implementation over the incumbent package and re-runs the",
    f"pipeline. Reference modules: {', '.join('`'+x+'`' for x in f['solution'][:6])}.",
    "Oracle result: **reward 1** (`ALL_TRIALS.csv`, arm-independent oracle runs recorded in `jobs/`).",
    "**VERIFIED FROM ARTIFACT** for every final task.","",
    "## J. What the verifier checks","",
    (f"This task emits **criterion-level rewards**: {', '.join('`'+k+'`' for k in ckeys)}. "
     f"**VERIFIED FROM ARTIFACT** (`tests/{[x for x in f['tests'] if x.startswith('test_')][0]}`)."
     if ckeys else
     "This task emits a **single binary reward** only. Criterion-level attribution of its failures is "
     "therefore **UNKNOWN** — not zero. This is the dossier's main instrumentation gap."),"",
    "It does **not** check reasoning, method identity, or any intermediate state the agent does not write",
    "to disk. Legitimate alternative implementations pass as long as the graded outputs fall within",
    "tolerance on every world.","",
    "## K. Hidden worlds and adversarial validation","",
    f"Sibling worlds: {', '.join('`'+h+'`' for h in f['hidden']) if f['hidden'] else '**none declared**'}. "
    "The same submitted procedure is graded on each, so an analysis that encodes the mechanism it happened to",
    "find in the visible world is distinguishable from one that recovers whichever mechanism holds.","",
    "## L. Known defects, limitations and exposure integrity","",
    "See `../09_BENCHMARK_INTEGRITY.md` for the audited defect register. Exposure: this task version is the",
    "one both arms were graded on, and it was **not** modified after exposure.","",
    "## M. Every trial outcome","",
    "| arm | job | trial | valid | reward | case study |","|---|---|---|---|---|---|"]
    for r in g+c:
        slug=f"{r['arm']}--{r['task']}--{r['job']}--{r['trial']}"
        cs=f"[case study](../trajectories/{slug}.md)" if r["valid"]=="True" else "— (invalid)"
        L.append(f"| {r['arm']} | `{r['job']}` | `{r['trial']}` | {'yes' if r['valid']=='True' else '**no**'} "
                 f"| {r['reward'] or '—'} | {cs} |")
    L+=["",f"**Gemini: {sum(int(r['passed']) for r in gv)}/{len(gv)} valid trials passed. "
         f"Claude: {sum(int(r['passed']) for r in cv)}/{len(cv)} valid trials passed.** "
         f"Invalid attempts are in `../INFRASTRUCTURE_FAILURE_REGISTER.md` and are not model failures.","",
    "## N. Does this task isolate the proposed failure mode?","", a["isolates"],"",
    "## O. What a future *separately versioned* task should change","", a["improve"],"",
    "---","",
    "*The frozen original is never edited. Every improvement above belongs in a new version with its own",
    "exposure record.*"]
    open(f"{OUT}/{t}.md","w").write("\n".join(L)+"\n")
print(f"wrote {len(A)} task chapters")
# index
L=["# Task chapters — the final ten","",
"| # | task | mechanism | Gemini | Claude | instrumented |","|---|---|---|---|---|---|"]
MECH={"02-renewal-risk-regression":"point-in-time correctness","g05-sco-rollout-gate":"staggered adoption",
"g10-censored-demand":"informative censoring","g24-recommender-ope":"off-policy evaluation",
"g36-tou-capacity-gate":"population definition","p20-noshow-monitoring":"policy feedback + vintage",
"p22-gauge-recalibration":"measurement-system bias","p31-fill-rate-dispute":"contractual definition",
"g50-courier-boost-rollout":"interference","g08-forecast-accuracy-vintages":"data vintage"}
for i,t in enumerate(["02-renewal-risk-regression","g05-sco-rollout-gate","g10-censored-demand",
 "g24-recommender-ope","g36-tou-capacity-gate","p20-noshow-monitoring","p22-gauge-recalibration",
 "p31-fill-rate-dispute","g50-courier-boost-rollout","g08-forecast-accuracy-vintages"],1):
    g,c=rows_for(t); gv=[r for r in g if r["valid"]=="True"]; cv=[r for r in c if r["valid"]=="True"]
    inst = t in {r["task"] for r in CR}
    L.append(f"| {i} | [`{t}`]({t}.md) | {MECH[t]} | {sum(int(r['passed']) for r in gv)}/{len(gv)} | "
             f"{sum(int(r['passed']) for r in cv)}/{len(cv)} | {'yes' if inst else 'no — binary only'} |")
open(f"{OUT}/INDEX.md","w").write("\n".join(L)+"\n")
print("wrote tasks/INDEX.md")
