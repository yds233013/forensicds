# Phase 2 — production failure structures: experimentation, measurement, marketplaces, ads, recsys, metric systems

All items below were verified by fetching the primary source. Findings are given as **paraphrase plus exact
numbers**; numbers and findings are facts, not expression, and every section is named so verbatim quotes can
be lifted at source. Items that could not be verified are marked **UNVERIFIED** and must not be quoted.

**Unreachable sources — cite as pointers only.** All `medium.com` properties return 403 to automated fetch
(Airbnb's *Experiments at Airbnb*, the Airbnb **Minerva** series) and the Netflix interleaving post is absent
from the Wayback Machine. **The widely-repeated Airbnb early-stopping anecdote (p crosses 0.05 around day 7,
effect gone by day 30) is UNVERIFIED and must not appear as a quote.**

## A. Interference, network effects, marketplace spillovers

| # | instance | numbers | why a competent analyst gets it wrong | discriminating test |
|---|---|---|---|---|
| A1 | **LinkedIn Feed** ranking — Gui, Xu, Bhasin, Han, WWW 2015, `hanj.cs.illinois.edu/pdf/www15_hgui.pdf` | direct β=**0.0486**, spillover γ=**0.1252** (≈**2.6×** direct), homophily η=0.0626, all p<e⁻¹⁶ | the t-test is correctly specified *under SUTVA*; no SRM, balance fine, estimate significant and in the hypothesised direction | add treated-neighbour-count and homophily terms; γ≠0 is the tell; add neighbourhood size to rule out popularity |
| A2 | **LinkedIn** BR-vs-CBR meta-experiment — Saveski et al., KDD 2017 | μ̂_br **0.2338** vs μ̂_cbr **0.8123** (≈3.5× smaller), Δ=−0.5785, **p=0.048**; σ̂_cbr 0.9966 vs σ̂_br 0.3414 (≈3× SD) | pre-launch balance checks (connections/activity/premium) and the pre-treatment A/A were **all clean**; experiment 1 failed to reject at all | run BR and CBR arms **simultaneously** and test whether the estimates differ |
| A3 | **Facebook Stories** — Karrer et al., KDD 2021, arXiv:2012.08591 §6.1 | user-randomized: emoji replies −23.8%, text replies +11.1%, **creator metrics flat**. Cluster-randomized: daily active creators **−0.25%**, active creators with feedback −1.2% | creators received feedback from viewers in *both* arms, so the supply-side harm is invisible by construction — a **false negative** | Louvain cluster randomization on the interaction graph (purity ~40%) |
| A3b | **Facebook Jobs**, same paper §6.2 | user-randomized **+71.841% ± 5.087%** vs commuting-zone cluster **+49.652% ± 17.817%**, differing at 5% | **an earlier independent user-randomized test replicated the biased number** — replication gave false assurance, and the effects were hidden in *all* prior user-randomized tests of these features | cluster arm; downstream P(job receives application) +14.069% ± 11.198% |
| A4 | **eBay** — Blake & Coey, EC '14 | 4 weeks, 4.9M users, 10,425,390 auctions. User-level **+0.74%** revenue (SE 0.29); auction-level coefficient **indistinguishable from zero**; implied all-treated **0.35%** → the user-level number **overstates by more than 2×** | with fixed supply, making a test bidder likelier to win mechanically makes a control bidder lose: the contrast measures incremental revenue **plus reassignment** | two tests on the *same* data: (i) compare all-test to all-control auctions holding entrants fixed; (ii) control users win **49.5%** vs test 50.5%, and spend ~**1.3% less** against ≥1 test user, 0.6% less per test user faced |
| A5 | **Airbnb pricing** — Holtz, Lobel, Liskovich, Aral, arXiv:2004.12489 / Mgmt Sci | Bernoulli TATE −0.207 bookings/listing; true TATE −0.139; **32.60% ± 12.93%** of the Bernoulli estimate is interference | — | cluster arm; **but the sign is not fixed**: interference is +15.09% of the Bernoulli TATE in demand-constrained and **−27.41%** in supply-constrained markets |
| A6 | **Lyft** Prime Time subsidy — Chamandy, 2016 (403 to fetchers; read in browser) | 2 passengers/1 driver: true global ATE **33%**, user-randomized naive lift **200%** — a **6×** overestimate | the post explicitly pre-empts the wrong diagnosis: **this is not a small-sample problem**; scaling up tightens the CI around the wrong number | coarser randomization units, at substantial variance cost |

**A7. Switchbacks and their own failure modes (DoorDash).** Randomize per 30-min × region unit *independently*
per window. **A second failure the treatment itself creates:** an assignment algorithm reluctant to take
long-distance deliveries shows faster average completion purely by cherry-picking short deliveries and leaving
long ones to control — diagnose by switching back *less* often to force treatment to absorb them, and by
comparing simple vs delivery-weighted averages. **Variance underestimation:** delivery-level t-tests have the
highest power and a **false-positive rate of 0.62** against simulated A/A data; MLM gives FPR 0.03, power 0.93
— because the regressor is constant within cluster, intra-cluster correlation of the regressor is 1 and the OLS
variance estimator is severely downward biased. Their fix is cluster-robust SEs validated against a cluster
bootstrap. **And an incoherent intermediate they shipped:** the MLM estimator returned a significant treatment
effect of **−0.22** while the raw difference was **+0.26**. Switchbacks structurally **cannot** measure courier
learning or retention. Randomization trilemma: switchback (low interference, moderate power, no learning) vs
supplier A/B (high power + learning, severe interference) vs market A/B (little interference + learning, low
power).

## B. Contamination, noncompliance, exposure vs assignment, triggered analysis

- **B1. The best "correct test, wrong conclusion" case in the corpus.** Airbnb's *price-suggestion* meta-experiment
  ran the same interference diagnostic at essentially the same sample size as the fee experiment and returned a
  **null**: Bernoulli TATE −0.106 (significant), cluster −0.051 (not), implied bias **54.16% ± 65.05%**; they
  estimate a **3.45×** larger sample would be needed. Hosts comply poorly with price tips, so ITT is forced and
  the complier set is endogenous. *An analyst who runs the recommended test and reports "no interference here"
  has followed best practice and is wrong — and behavioural nudges are the common case.*
- **B2. Unequal allocation causes asymmetric contamination** (Kohavi, Deng, Vermeer, *A/B Testing Intuition
  Busters*, KDD 2022, §7): with cookie churn, users in the *smaller* variant are likelier to be re-randomized
  into a larger one; cookie→user mapping via logins then produces SRM. Shared LRU caches give the larger variant
  a performance advantage. A 2%/98% ramp looks like free power.
- **B3. Ads exposure is an endogenous outcome** (Gordon, Zettelmeyer, Bhargava, Chapsky, *Marketing Science*
  38(2) 2019): control compliance is perfect, test exposure is not, giving three observable groups. Ghost-ads
  style control substitutes the **second-place auction ad**. Exposure rates across their 15 studies range
  **6.6%–81%**, which alone sizes the dilution. Report ITT and ATT side by side with the exposure rate.
- **B4. Triggering on a post-treatment condition — the single cleanest scenario in the corpus.** Dmitriev, Gupta,
  Kim, Vaz, *A Dirty Dozen: Twelve Common Metric Interpretation Pitfalls*, KDD 2017, §5.8. Bing ranking
  segmented by whether a user saw a "deeplink": **both segments showed a statistically significant increase in
  Sessions/User — Bing's key metric — while the union showed no significant change.** Truth: the treatment did
  not move Sessions/User at all; it shrank the deeplink segment, and the users who left were below average for
  that segment and above average for the one they joined. **Discriminating test: a per-segment SRM test** — the
  sample ratio differed significantly in *both* segments, which voids all results for that segment variable. It
  is available on every mature platform and is almost never run by default. Note the analyst's instinct on
  seeing both halves agree is to trust the result *more*.
- **B5. Model-derived trigger (LinkedIn, arXiv:1808.00114).** JYMBII targeted at "passive job seekers", an ML
  attribute the treatment itself moves: a **better** model triggered proportionally **fewer** users because it
  removed members from the targeted population. **Effect size and bias are positively coupled — the better the
  treatment, the worse the bias, exactly when you most want to ship.** ~**10% of LinkedIn's triggered analyses**
  carried an SRM.
- Correction to a common mis-citation: **Deng/Lu/Litz WSDM 2017 is about variance estimation / i.i.d.
  violations, not triggering.** The triggering machinery is Deng & Hu, WSDM 2015.

## C. Sample ratio mismatch — real root causes

Fabijan, Gupchup, Gupta, Omhover, Qin, Vermeer, Dmitriev, KDD 2019,
`exp-platform.com/Documents/2019_KDDFabijanGupchupFuptaOmhoverVermeerDmitriev.pdf`. Base rate ~**6% of
Microsoft experiments**; a product running 10,000/year expects one per day. **25 causes** across five lifecycle
stages. Sensitivity: a **50.2/49.8** split (821,588 vs 815,482) is a **p < 1/500,000** event.

- **C1 — bot filtering on post-treatment signals.** MSN carousel 12→16 cards read as a **significant decrease**
  in engagement, with a ready-made UX story (choice overload). Cause: the most engaged treatment users crossed
  the engagement threshold in bot detection and were **deleted from analysis**. Corrected, the **sign flipped**
  and the feature shipped. Booking.com fixes bot status at **first exposure**.
- **C2 — delayed/asynchronous assignment.** Skype adaptive audio buffering read as significantly worse
  distortion and delay, with **30% fewer sessions** collected: a mid-session config refresh mutated the
  in-memory variant ID. They trained a random forest to separate invalidated sessions; top features were all
  session-duration related.
- **C3** redirect-based assignment (only one arm pays the tax) — redirect **both** arms. **C4** performance and
  crashes, where **the SRM and the true effect share a cause**, so the surviving-user regression is genuine even
  though the sample is biased. **C5** an SRM with a *positive* cause: recovering extra users usually means a real
  performance improvement. **C6** assignment-service bugs — an MSN A/A test at **49.9/50** (one bucket in 1000),
  invisible to inspection, systemic across every experiment. **C7** pipeline joins silently dropping rows.
- **C8 — Rule 1:** SRM present in the **triggered** scorecard but absent in the standard one ⇒ **the trigger
  condition is wrong** (Teams first-run: the slower control quit before batched visibility events flushed).
- **C9** human/ramp interference: a search campaign with a misconfigured URL forced users into one variant;
  pausing one variant mid-flight; a telemetry injection attack.
- Rules to encode: **Rule 3** strongest evidence on day 1 ⇒ time-related cause, plot assignments per hour;
  **Rule 6** many disparate experiments with SRM ⇒ systemic; **Rules 9–10** compare intermediate pipeline stages
  and two independent pipelines.
- **C10 — metric-level SRM.** *Dirty Dozen* §5.1: MSN opened links in a new tab; readout **+8.32% Page Load
  Time** for a one-line JS change. Cause: treatment had **7.8% fewer homepage loads** because the back-button
  reload disappeared — and those were the *fast, cached* ones. **Just as an experiment-level SRM invalidates the
  experiment, a metric-level SRM invalidates the metric**, in an arbitrary direction. Test the metric's
  **denominator**.

## D. Simpson's paradox in real readouts

- **D1. The printed worked example** — Crook, Frasca, Kohavi, Longbotham, *Seven Pitfalls to Avoid…*, KDD 2009,
  §6 Table 1. 1M visitors/day; Friday at **99/1**, Saturday at **50/50**. Treatment wins both days (2.30% vs
  2.02%; 1.20% vs 1.00%) yet pooled shows **treatment 1.20% vs control 1.68%** — **−0.48 pp, −29% relative**,
  when the effect is positive every single day. **There is no bug: the arithmetic is correct and the pooled
  number reconciles exactly against total conversions and total sessions, so it survives every reconciliation
  check a data team owns.** Same section: non-uniform sampling by browser (treatment wins overall, loses in
  *every* browser); per-country allocation differences; and holding the top-1%-spend segment at 1% exposure,
  giving an experiment positive overall yet worse for both the most valuable and the non-valuable customers.
- **D2. Bing ads, real counts** — Bottou, Peters et al., JMLR 2013, arXiv:1209.2355 §2.4 Table 2. CTR on the
  second mainline ad: overall **6.2%** (q1 low) vs **7.5%** (q1 high), but split on q2: **5.1% vs 4.8%** and
  **18.1% vs 15.6%** — the sign reverses; the confounder is user intent. Worse than the textbook case because
  **both the segmenting variable and the outcome are outputs of the same model**. **The kicker:** acting on the
  corrected conclusion improves click prediction, which *lowers* second-position estimates on commercial pages,
  pushing those ads below reserve into the sidebar — **the likely net result is a loss of clicks and money
  despite a better model.**
- **D3. Trigger-day mix shift that mimics novelty** (LinkedIn arXiv:1808.00114): cross-day impact blends
  in-trigger and off-trigger behaviour and the mix weight shifts mechanically, producing a clean monotone trend
  that is pure composition change — a pattern that routinely prompts experimenters to suspect a platform bug.
  Decompose into in- and off-trigger deltas.

## E. Novelty, primacy, time-based heterogeneity

Kohavi, Deng, Frasca, Longbotham, Walker, Xu, KDD 2012; Kohavi, Deng, Longbotham, Xu, *Seven Rules of Thumb*,
KDD 2014.

- **The headline inverts the analyst's instinct: most *suspected* primacy and novelty effects are artifacts.**
  Genuine ones are **uncommon**; the named exceptions are recommenders and finite-resource treatments (LinkedIn's
  People You May Know has a finite pool).
- **A real novelty effect that nonetheless held up:** MSN opening Hotmail in a new tab, **+8.9%** clicks/user on
  900k users, replicated on 2.7M, and **+5% on 12M** in 2011. Novelty appeared in **complaints**, not metrics:
  20% of feedback on day one, 4% in week two, 2% by weeks three and four, while the gains persisted.
- **Reversal essentially never observed** across Microsoft's corpus — so extending an experiment that is
  significantly negative after two weeks has little value. Recommended duration two weeks with an explicit look
  for time trends.
- **Two confounders that make naive novelty calls wrong:** weekend activation produces single-day trends that
  closely resemble novelty; and **the magnitude of a novelty effect cannot be estimated from single-day impacts
  alone**, because each day mixes first-time and repeat triggerers — clean identification needs staggered
  exposure of two treatment subpopulations.
- **Experiment length does not always buy power** (KDD 2012 §3.4): for Sessions/user the coefficient of
  variation grows with the window, so CV/√n is roughly flat over 31 days. Poisson is a poor model; negative
  binomial is better. Extending a test to "get more power" on sessions/user gets none.
- **The cumulative-effect chart from an A/A test** (KDD 2012 §3.3): four days rising from negative toward zero
  invites "good feature with primacy", but the true mean is zero; cumulative series are autocorrelated and day 1
  has a **67%** chance of falling outside the final 95% bound, day 2 **55%**. The authors say they were fooled
  themselves multiple times. **The chart type manufactures the artifact.**

## F. Multiple testing, peeking, sequential analysis — four platforms converge

- **Optimizely** (Johari, Koomen, Pekelis, Walsh, KDD 2017): at 10,000 samples the false-positive probability is
  inflated **5–10×**, approaching **100%** with increasing data. **Footnote 2 is the gem:** stopping at p<0.05
  **and** requiring post-hoc power above 0.8 is equivalent to rejecting at a lower α and **also significantly
  inflates the FPR**. *The safeguard a careful team adds is part of the error.*
- **Netflix**: **70%** of A/A simulations declare significance at some point (66 of 100 in the reported figure).
  Because this gates canary deploys, a false positive interrupts a release and sends developers hunting bugs
  that do not exist.
- **Etsy** (archived): with a true null, α=0.1, no peeking, FPR is 10%; after **500 observations** of continuous
  monitoring there is over a **50%** chance of declaring a difference. Their honest counter-argument: fixing n in
  advance means you may miss a setup bug that invalidates the run. Their dashboard prints the state as
  *directionally correct, magnitude possibly inflated* — an excellent grading target.
- **Spotify**: a z-test built for 5% used twice yields ~**10%**; and **GST requires a planned maximum sample
  size — continuing past it inflates the FPR**, so a correct sequential method used incorrectly is still invalid.
- **Multiple testing across metrics/variants/iterations** (Kohavi et al., KDD 2013): hundreds of metrics per
  experiment (LinkedIn 4000+); five treatments turn a 2.5% FPR into **12%**; six iterations of 5-treatment
  experiments give **>50%** chance of a positive significant result. Their alerting uses O'Brien–Fleming: the
  day-1 cutoff in a 7-day test is **5×10⁻⁸**, rising to 0.040 at the final look, **and they additionally require
  material magnitude** — no alert on a 2 ms PLT degradation even at p<1e-10. Daily looks are for debugging;
  there is **one final scorecard**, at a duration that is a multiple of weeks.
- **Underpowered publication** (*Intuition Busters* §2): a published **337%** lift — 82 vs 75 visitors, 3 vs 12
  conversions, p=0.009, **reported observed power 97%**. True pre-experiment power ≈**3%**; false-positive risk
  ≈**63%**; you would need α≈**0.0016**. Across tens of thousands of tests at Airbnb, Booking, Amazon and
  Microsoft the authors have never seen a conversion improvement near that size.

## G. Assignment reuse and carryover

KDD 2012 §3.5. Bucket systems randomize users into buckets once, then assign buckets to successive experiments.
Readout: metrics **unrelated** to the change moved with **high statistical significance**; rerunning on a larger
sample made many effects disappear. Design: 7-day A/A → 47-day A/B → 3+ weeks post-monitoring; the carryover
died out around the **third week**, and in a case where a bug gave users a genuinely bad experience the buckets
had **still not recovered after three months**. Mitigation: two-level bucketing with per-experiment second-level
seeds — **at the documented cost that you can no longer use a shared control**. **Discriminating test:
retrospective A/A** — re-hash and evaluate the days *before* the experiment; if key metrics show **p<0.2**
(deliberately conservative, not 0.05), change the hashing key and retry. Hash-seed collisions: with 365 seeds you
need only ~**23 experiments** for a 50% chance of a shared pair. **Counterintuitive inversion:** when two
experiments' variants interact (the app crashes when a user is in both), *independent* randomization **causes**
SRM via telemetry loss — the fix is **exclusivity**, not independence.

## H. Ads incrementality, attribution, selection

- **H1. eBay brand keywords** — Blake, Nosko, Tadelis, *Econometrica* 2015. Halting brand-keyword paid search on
  Yahoo!/MSN with Google as control: **99.5%** of forgone paid clicks were immediately recaptured by natural
  search on the same platform. For non-brand keywords OLS gives ROI **>4,100%** without controls and **>1,400%**
  with time and geographic controls; **the experiment gives −63%, 95% CI [−124%, −3%]**. *Adding controls reduces
  the bias from 4,100% to 1,400% and thereby makes the wrong answer look robust.*
- **H2. Activity bias** — Lewis, Rao, Reiley, WWW 2011. Exposed-vs-unexposed overstates search lift by **~200×**
  the experimental truth **even after controlling for a rich set of observables including past search
  intensity**; before-vs-during on the exposed group overstates by **~20×**; a before/after read in experiment 2
  overstates by **350%** while the control group is nearly identical. Generative fact: online activities are
  **positively** correlated across unrelated sites — on some days a user does more of everything. The
  identifying assumption that yesterday predicts today is standard, innocuous-sounding, **and untestable without
  the experiment**.
- **H3. Platform-grade covariates are not enough** — Gordon et al. 2019: 15 Facebook RCTs, 435M observations,
  1.4bn impressions. Observational methods generally **overestimate**; in **half** the studies the estimated
  percentage increase is off by a **factor of three** across all methods. Study 4: exposed 0.061% vs unexposed
  0.019% → ATT lift **316%**; true ATT lift **73%** [49,103]; ITT 37.7% — the naive number is **>4×** the truth.
  **They tried to rescue it and could not:** their covariate ladder includes a Facebook match score summarising
  **thousands** of behavioural variables from a production model, and their sensitivity analysis shows some
  studies would need additional covariates **exceeding the explanatory power of their entire observable set**.
- **H4. The precision heuristic — the most portable single diagnostic in ads** (Lewis, Rao, Reiley, NBER w19520):
  across 25 large Yahoo! experiments the **SD of purchases is ~10× the mean**; for a campaign at 25% ROI the
  expected R² on the treatment variable is **0.0000054**. 2M users evenly split gives an expected t of 3.30;
  **200,000 users gives 1.04**, failing to reject a healthy 25% ROI **74%** of the time. **Heuristic: if an
  observational method claims *higher* precision than a feasible experiment, be suspicious** — omitted
  heterogeneity generating a partial R² of only **0.00005** produces bias that swamps plausible ad effects.
  Corollary: for a major retailer the majority of the sales impact was **offline**. And the time-window trap —
  cumulative point estimates rise with the horizon but standard errors rise faster, so a short attribution
  window is a *power* choice masquerading as a measurement choice.
- **H5. Geo experiments** — Vaver & Koehler (Google). Contamination scales down as geos shrink but consumers
  travel and geo-targeting accuracy is finite, so postal-code geos are infeasible; the practical US unit is the
  **210 Nielsen DMAs**, and **that, not the number of users, sets power**. Grouping geos by size before
  assignment cut the ROAS CI by **10%+**. The distortion to guard against: a 20-market matched test presented
  with the false precision of a user-level test.

## I. Delayed conversion and attribution windows

Chapelle, *Modeling Delayed Feedback in Display Advertising*, KDD 2014. On Criteo data **35%** of conversions
occur within one hour, about **50% occur after 24 hours**, and **13% after two weeks**; the industry-standard
window is 30 days. Their solution avoids a window entirely: positive if followed by a conversion, **unlabeled**
otherwise, with a second model for the delay distribution. **The best detail for a scenario:** on the Yahoo RMX
exchange **95.5%** of conversions happened within one hour — so a practitioner who ports a published 2-day window
from one platform to another mislabels a large fraction of conversions, and the diagnostic is simply to plot the
empirical click→conversion CDF **on your own data** before choosing a window. Truncated labels bias the
conversion rate **downward**, worst for the most recent data — exactly the data the model is retrained on — and
the bias is non-stationary with campaign mix. Distorts bidding, campaign kill decisions, and the apparent
"decay" of recent cohorts in any retention or LTV dashboard.

## J. Proxy and surrogate metric validity

- **J1. The model proxy failure** (*Seven Rules of Thumb*, Rule #3): Office Online used clicks on
  revenue-generating links as a revenue proxy; the redesign showed a **64% reduction in clicks per user**. Truth:
  the treatment displayed the **price**, attracting fewer but far better-qualified clicks. **The treatment changed
  the coefficient linking surrogate to outcome** — any treatment that changes *who* proceeds breaks the surrogate.
- **J2. Google ads blindness** — Hohnhold, O'Brien, Tang, KDD 2015. Increased ads load showed **significant
  short-term RPM gains** and was assessed **likely long-term negative**. With learning rate β≈0.012, a **90-day**
  study captures only ~**65%** of the long-run effect and a post-period measured in the first 14 days ~**92%** of
  that, so ~**60%** overall — hence a multiplier Q≥1.54, in practice **2–3** on desktop. Drove launches reducing
  mobile search ad load by **50%**.
- **J3. The counter-result at Bing** — Dmitriev, Frasca, Gupta, Kohavi, Vaz, IEEE Big Data 2016. Sessions/User
  rose when ads were reduced and fell when increased, with **increased abandonment** at higher load, whereas the
  Google paper reported **no** significant learned effect on Users and Tasks/User. **Failure structure:
  survivorship in the holdout** — with differential abandonment the post-period delta blends a population
  difference with the feature effect, and *"the difference is attributed to user learning when the real cause is
  a change in population."* **Under 25%** of cookies survive a two-month longitudinal study. Fix: impute zeros
  for users present during the experiment but absent post-period — **which fails for ratio metrics** because the
  denominator is zero. **Two competent teams, similar designs, opposite conclusions, and the published resolution
  turns on power and on whether abandonment was measured.**
- **J4. Surrogate index** — Athey, Chetty, Imbens, Kang, arXiv:1603.09326: under Prentice surrogacy the ATE on a
  surrogate index equals the ATE on the long-term outcome; six quarters substituted for nine years with a **35%
  reduction in standard errors**. They characterise bias from violating Surrogacy and Comparability, and flag the
  practitioner habit of dropping individually-insignificant short-term outcomes, which distorts the weighting.
- **J5. Choosing the proxy is choosing the product** — Covington, Adams, Sargin, RecSys 2016: YouTube ranks on
  **expected watch time per impression** because CTR ranking promotes clickbait. Same paper: live A/B results are
  **not always correlated with offline experiments**; the choice of surrogate problem has outsized importance and
  is very hard to measure offline; they train on **all** watches, not only those from their own recommendations,
  to avoid biasing toward exploitation; and information must be **withheld** from the classifier to stop it
  exploiting site structure.

## K. Off-policy evaluation, logging policies, position bias

- **K1. The headline production result.** Gilotte, Calauzènes, Nedelec, Abraham, Dollé (Criteo), *Offline A/B
  testing for Recommender Systems*, WSDM 2018, benchmarked against **39 real online A/B tests** over a few
  hundred billion recommendations. Capped importance sampling at cap=100 — **common practice** — achieves
  correlation with online truth **−0.15 ± 0.35**, decision precision **0.28**, **false-negative rate 0.64**.
  NCIS 0.24/0.47/0.33; PieceNCIS 0.36/0.53/0.28; PointNCIS **0.49/0.56/0.16**. Capping makes CIS systematically
  **underestimate**, which is why the correlation is *negative* on a dataset with more genuine wins than losses;
  uncapped IPS/NIS were discarded because their CIs never permit a decision. **Asymmetric cost, stated
  explicitly: a false positive costs one A/B test; a false negative is a real improvement never tested online.**
  An FNR of 0.64 silently discards about two-thirds of genuine improvements. **Discriminating artefact: a
  decision-agreement table of past offline predictions against their online outcomes — correlation, precision and
  FNR — not the point estimate.**
- **K2. Support violations and how to detect them honestly.** Bottou et al. §4.6 randomized Bing mainline reserve
  multipliers (lognormal around 1) and estimated counterfactual outcomes; **a second equal-size bucket with
  reserves reduced ~18% matched the counterfactual estimates with high accuracy**, and a third bucket priced the
  cost of randomization (a small significant increase in mainline ads/page; click yield and revenue differences
  not significant). **The generalisable diagnostic: their *inner* confidence intervals grow sharply once the
  target policy leaves the range actually explored** — a computable signal that an off-policy estimate is
  extrapolating, and the missing safeguard in most replay pipelines.
- **K3. Position bias** — Joachims, Swaminathan, Schnabel, WSDM 2017: treating clicks as relevance is severely
  biased by presentation order, and learners trained on clicked-vs-skipped preferences tend to **reverse the
  presented order**. **Cheap discriminating test:** swap the top-ranked document to a uniformly random rank
  j∈{1…21}; the ratio of its CTR at j to its CTR at 1 estimates p_j/p_1. On a live article search engine
  propensities decayed to **p_min≈0.12** — an identical result at a low rank collects ~1/8 the clicks. Live
  interleaving: Propensity SVM-Rank beat the production ranker **87–48–83** (p=0.001) and Naive SVM-Rank
  **95–60–102** (p=0.006). Complement: Schnabel et al., ICML 2016 — observations are conditioned on the very
  effect you want to optimize, so the data are MNAR. Google's *Rules of ML* #36 warns against positional feedback
  loops.

## L. Feedback loops and performative prediction

- **L1. Algorithmic confounding** — Chaney, Stewart, Engelhardt, RecSys 2018: evaluation on confounded held-out
  data is **biased toward recommenders similar to the deployed one**; the loop homogenizes behaviour at
  population and individual level without utility gains, and losses fall unequally (users with lower relative
  utility homogenize more). **Held-out accuracy is the organisation's actual acceptance gate and it silently
  rewards resembling the incumbent.** Fix: randomized-exposure data or propensity weighting; report the
  *distribution* of impact, not means.
- **L2. Performative prediction** — Perdomo, Zrnic, Mendler-Dünner, Hardt, ICML 2020: a bank predicts elevated
  default risk, assigns a high rate, and thereby raises default risk. **It hides because ignored performativity
  surfaces as ordinary distribution shift, which teams handle by retraining** — so the dashboard shows a
  familiar, benign pattern. Fix: a holdout where the prediction is **not acted upon**. The production-shaped
  instances (churn model triggers retention, ETA changes demand, fraud model changes fraudster behaviour) share
  the self-defeating-prediction structure: **the model looks worse precisely because the intervention worked.**
- **L3. Google Flu Trends** — Lazer, Kennedy, King, Vespignani, *Science* 343 (2014). Overshot 2011–12 flu by
  **more than 50%** and reported too-high prevalence in **100 of 108 weeks** (21 Aug 2011 – 1 Sep 2013), at peak
  **more than double** the CDC. Out-of-sample MAE: GFT **0.486**, a lagged-CDC model with 52-week seasonality
  **0.311**, the combination **0.232**, all differences p<0.05. **Mechanism: "algorithm dynamics"** — Google added
  suggested related searches (Jun 2011) and candidate diagnoses for symptom searches (Feb 2012), and because GFT
  keys off *relative* search volume, **improving the search product degraded the estimator**. Search behaviour is
  not exogenous; it is cultivated by the provider. **It was coherent for years because it validated strongly
  against historical CDC data — and was part flu detector, part winter detector.** Discriminating evidence is
  embarrassingly cheap: compare to a naive lagged baseline, and test the error series for autocorrelation and
  seasonality — last week's errors predicted this week's.

## M. Feature-store point-in-time correctness and training/serving skew

Google's *Rules of ML* defines training–serving skew as a difference between training and serving performance
caused by a discrepancy in data handling, a change in the data between training and serving, or a **feedback loop
between model and algorithm**. **Rule #29: save the feature set actually used at serving time and pipe it to a
log for training** — the "log and wait" pattern; reconstructing features from a warehouse re-introduces the
timing mismatch. **Uber Michelangelo/Palette** shares the same batch pipeline and DSL feature expressions between
training and prediction, and — the monitoring primitive that matters — **logs and optionally holds back a
percentage of predictions and later joins them to observed outcomes**, which is the only way to detect a
point-in-time violation after the fact. **Feast's own docs** state that a value backfilled or corrected *after* an
entity-dataframe timestamp can still be returned for that row (the leakage path), and that TTL windows silently
drop rows.

**Why a competent analyst gets it wrong:** the model validates cleanly on a held-out **random** split, and often
on a held-out time split too if the leakage is short-horizon. The offline metric improves, which **is** the
acceptance criterion. **Naive analysis shows** a step change in AUC on adding a feature, then an online A/B that
shows nothing, or online performance decaying toward the no-leakage baseline. **Discriminating evidence:**
re-derive the training set from **serving logs** rather than the warehouse and compare; audit as-of joins per
feature against label timestamps; ask whether any feature value for a row could have been written after the label
event; and **re-run the backtest with a deliberately widened embargo window — if performance collapses, the
original was leaking.** Canonical structure: Kaufman, Rosset, Perlich, *Leakage in Data Mining*, KDD 2011/TKDD
2012.

## N. Metric definition drift, instrumentation, client-logging asymmetry

- **N1. Client telemetry loss that differs by arm** (*Dirty Dozen* §5.3). Skype changed the iPhone
  push-notification protocol; readout showed **strong significant changes in call metrics**, including the
  fraction of attempted calls connected, for a change that should not touch calls. Cause: under the new protocol
  the app stayed awake a few seconds longer, had more time to find wifi and **flush a telemetry batch**, so
  treatment **lost fewer client events**. **The tell: some metrics moved strongly while closely related ones
  stayed flat — and the split was exactly client-logged vs server-logged.** Fixes: reconcile each client event
  against a near-lossless server counterpart (superior), or use client-assigned sequence numbers and measure gap
  rates; create a loss-rate data-quality metric for **every** client event in a metric. Generalises to the web:
  some browsers cancel click beacons on navigation, so anything keeping the origin page alive improves fidelity.
- **N2. Instrumentation fidelity masquerading as a product win, and the best "internally coherent" case in the
  corpus** (*Seven Rules of Thumb*, Rule #3). Over several months in 2013 Bing migrated its CDN from Akamai to
  Bing Edge, and **several independent teams reported key metrics improving** — homepage CTR up, feature usage up,
  abandonment down. A large portion was **improved click-tracking beacon fidelity**. The discriminating
  experiment: replace beacon tracking with redirect tracking (negligible click loss, a per-click slowdown) —
  click loss for some browsers dropped by **more than 60%**. There was no bug, no SRM, no single suspicious
  number, multiple teams agreeing, and a plausible causal story (a faster CDN).
- **N3. Metric definition drift** — Uber *uMetric*: the **"Shopping Session"** metric returned **6.53M vs 6.20M**
  in two visualization tools for the same city and window; root cause was one tool's static query using **stale
  filters** that missed the current list of rider states. Both numbers are internally consistent and each
  reconciles within its own tool, and 5% is small enough to be waved away as freshness or timezone.
  **Discriminating evidence: diff the filter predicates and dimension value sets, not the aggregates.** Airbnb's
  Minerva covers the same ground but is **unverifiable by automated fetch** — pointer only.
- **N4. Twyman's law** (*Dirty Dozen* §5.12). MSN replaced the Outlook.com button with a mail-app button:
  **+4.7%** overall navigation clicks, **+28%** on the button, **+27% on the adjacent button**. Truth: users
  habituated to outlook.com kept clicking, then clicked neighbours to see if anything worked; clicks declined
  rapidly day over day and satisfaction/retention showed nothing. A second case: a Windows Store reconfiguration
  gave **+10%** page views because the page displayed **no content**, so users retried. **The stated bias:
  surprising negatives are met with scepticism; surprising positives are not.** Microsoft alerts and auto-shuts
  down large unexpected movements **in both directions**.

## O. Time semantics

- **Airflow's logical date** denotes the **start of the data interval**, not execution time; a DAG run is
  scheduled one interval after `start_date` and typically *after* its interval has ended. **The single most common
  off-by-one-day in metric pipelines.**
- **DST:** a `US/Eastern` DAG on `0 0 * * *` runs at 04:00 UTC during DST and 05:00 otherwise; timezone-aware
  cron respects DST, but `timedelta`/`relativedelta` schedules **do not adjust subsequent runs** — so a
  cron-scheduled and a timedelta-scheduled daily job silently diverge twice a year. Airflow stores and displays
  UTC.
- **Late-arriving events are dropped, not queued:** Google Analytics ignores events arriving more than 2 calendar
  days plus today after they were triggered, so any cohort inside that window is provisional and the most recent
  day is structurally understated.
- **History restatement:** Kimball — a **Type-1 overwrite destroys field history**, so reports that constrain or
  group on it **change**, and precomputed aggregates and materialized views must be taken offline at the moment
  of overwrite and recomputed.
- **Why it survives:** the number reconciles perfectly *today*, and the same query re-run last month gave a
  different answer — which reads as a data bug or a genuine trend, not a semantics change. DST effects are
  twice-yearly and are almost always attributed to seasonality. **Tests:** reconcile UTC against local time;
  count events per hour across the DST boundary looking for a 23- or 25-hour day; re-run a historical window and
  diff against the stored snapshot; compare event-time to ingest-time distributions to size the late tail.
  Microsoft requires experiment durations to be a multiple of weeks for exactly this reason.

## P. Semantic layer, denominators, dimension hierarchies

- **P1. Fan-out joins** — Looker symmetric aggregates: joining `orders` to `order_items` makes `SUM(total)`
  return **223.44** instead of **124.84**. The join is correct, the SQL is correct, row counts look plausible,
  nothing errors, and **the inflation factor is the average basket size — so the distortion varies by dimension
  and segment comparisons invert.** Tests: `SUM` over a `SELECT DISTINCT` of the grain; `COUNT(*)` vs
  `COUNT(DISTINCT pk)` after every join; tie back to a single-grain source.
- **P2. Ratio metric whose denominator the treatment moves** (*Dirty Dozen* §5.2). An MSN module moved higher
  showed a **40% decrease in CTR per user** with **no user-level SRM** and a movement genuinely caused by the
  treatment. Decomposed: numerator **+74%**, denominator **+200%**; whole-page CTR flat; **revenue increased**
  because the promoted module monetized better. The experiment was good. **Always ship numerator and denominator
  as separate counts beside every ratio, and prefer average-of-per-user-ratios** — more sensitive, more
  outlier-resilient, and its denominator is the user count, a *controlled* quantity.
- **P3. Randomization unit vs analysis unit** — Deng, Knoblich, Lu, *Applying the Delta Method in Metric
  Analytics*, KDD 2018 §3. When the randomization unit is a **cluster** of analysis units the metric is a ratio of
  two sums, not an average of i.i.d. variables, so the i.i.d. variance formula is wrong. **The purest "internally
  coherent" statistical error: the point estimate is right, the pipeline is right, the dashboard reconciles — only
  the CI is wrong, and anti-conservatively, so you get significance you have not earned.** Also: mixed-effect
  estimates target the cluster-level double average, and with heterogeneous effects can be severely biased. The
  measured consequence of getting it wrong is DoorDash's **FPR 0.62**.
- **P4.** Non-additive measures rolled up as additive; drill-down totals that miss an "Other"/null bucket; and
  **SCD Type-2 joins on the surrogate vs the natural key**, which silently changes which historical attribute
  version a fact row is attributed to.

## Q. Survivorship and funnel selection

*Dirty Dozen* §5.11: Xbox promotion tests produced **large positive click-through impacts to the sale** with **no
corresponding revenue increase even with sufficient power** — the cost being users' wasted time. Prescription:
measure every step; compare success **rates** not raw clicks; report **both conditional** (among users who started
the step) **and unconditional** rates, each adequately powered. Final success rates under 1% are common.
**General shape:** conditioning on a step the treatment itself moves is the same defect as triggering on a
post-treatment condition (B4) and segmenting on a treatment-affected attribute (B4/D1) — and the same cheap
diagnostic applies: **SRM-test the conditioning population.**

## R. Observability metric systems

- **Precomputed quantiles do not aggregate.** Prometheus: you cannot compute a service's overall p90 latency from
  per-worker p90s; histograms permit `histogram_quantile()`. Their own counter-caution: interpolation error is
  bounded by bucket width, and with all observations in the 200–300 ms bucket the estimate can be **295 ms against
  a true 220 ms**.
- **Averages hide the tail.** Google SRE Book: a service averaging 100 ms at 1,000 rps can easily have 1% of
  requests taking 5 seconds; and **one backend's p99 can become the frontend's median**. Separate the latency of
  successful and failed requests.
- **Why it survives:** every monitoring system offers a p99 field, and averaging across instances or re-bucketing
  across windows is a one-line dashboard operation that produces a plausible number with no error. **Distorts SLO
  claims, capacity decisions and — directly relevant here — experiment guardrail metrics on latency.**

---

## Taxonomy of *why* the wrong answer is stable — the most transferable output

1. **The arithmetic is right and reconciles.** Ramp-mixing Simpson's. No bug exists, so validation cannot find it.
2. **The bias and the effect share a cause.** Performance-induced telemetry loss; the JYMBII trigger loop.
   Drill-downs *confirm* rather than refute, because the survivor-only effect is genuine.
3. **The chart type manufactures the pattern.** Cumulative deltas; trigger-day mix shift. Both mimic novelty —
   the exact hypothesis a motivated analyst wants.
4. **The safeguard is itself invalid.** The post-hoc power gate; a GST run past its planned maximum n. The team
   can show its work.
5. **The trusted reference is wrong.** KDD 2009 §8.1.1: Microsoft's audits found serious problems with the
   internal *system of record*, because those systems carry complicated legacy ETL while the experiment logging
   path is simpler and loses less data. Their preferred alternative is validation against **simulated traffic with
   a known expected answer** — which directly attacks the "it matched a trusted figure" heuristic.
6. **Significance is read as mechanism.** Carryover moving unrelated metrics at high significance.
7. **Replication reproduces the bias.** Facebook Jobs; any bias inherent to the default design.

## Ten mechanisms ranked as professional incident scenarios

Ranked by: a real decision at stake; several *genuinely* competing hypotheses a good practitioner would entertain;
and a discriminating test that exists in real practice and is cheap enough that failing to run it is a realistic
error rather than a contrived one.

1. **Segment or trigger defined by a treatment-affected condition** (Bing deeplink, *Dirty Dozen* §5.8) — two
   corroborating significant segment wins, true population effect zero; test = per-segment SRM.
2. **Client-side telemetry loss differing by arm** (Skype; Bing Edge) — tell is client-logged metrics moving while
   server-logged siblings do not.
3. **Ratio metric whose denominator the treatment moves** (MSN PLT +8.32%; module CTR −40% while revenue rose) —
   test = SRM on the denominator, then decompose.
4. **Last-touch/observational attribution vs incrementality** — OLS with controls **+1,400%** vs experiment
   **−63%**; 99.5% organic recapture; tests = switch-off + organic uptake, geo/DMA experiment, precision heuristic.
5. **Marketplace interference on fixed supply** — eBay 2×, Lyft 6×, Airbnb 32.6%, Facebook Stories a complete
   false negative; **bias direction is not fixed** (demand- vs supply-constrained flips the sign).
6. **Off-policy evaluation anti-correlated with online truth** — Criteo FNR **0.64**; artefact = a
   decision-agreement table, plus inner CIs to detect leaving explored support.
7. **Short-term proxy that inverts the long-term sign** — Google ads blindness (Q 2–3) vs Bing's opposite
   conclusion; resolution turns on power and on whether differential abandonment was measured.
8. **Peeking, plus a safeguard that is itself invalid** — 70% of Netflix A/A runs; >50% after 500 Etsy
   observations; audit the **stopping rule**, not just the p-value.
9. **Point-in-time incorrectness / training–serving skew** — model validates on the held-out set, which *is* the
   acceptance gate; tests = re-derive from serving logs, widen the embargo.
10. **Semantic-layer definition mismatch between two coherent dashboards** — Uber 6.53M vs 6.20M; Looker 223.44 vs
    124.84. Highest-frequency incident in the set and the one most likely to be closed as "rounding".

**Just outside:** bucket-reuse carryover (retrospective A/A at p<0.2); delayed conversion labels (plot your own
CDF); randomization- vs analysis-unit variance (delta method; FPR 0.62); incorrectly aggregated p99 as an
experiment guardrail.
