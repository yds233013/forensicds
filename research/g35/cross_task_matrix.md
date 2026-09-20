# G35 cross-task distinctness

| | core object | what makes it hard | randomisation | why G35 is different |
|---|---|---|---|---|
| **Task 02** | point-in-time feature state | using a feature value that did not exist at prediction time | none | G35's features and timestamps are clean by construction; the correct-table gate hands them over perfectly and separation survives |
| **G08** | forecast accuracy across vintages | reconstructing what was known when | none | no temporal reconstruction in G35; the assignment log is complete and pre-dated |
| **G10** | latent censored demand | a deterministic censoring process with no randomised device | none | G35's treatment is randomised and its estimands are identified nonparametrically by arm contrasts |
| **G24** | policy value under a logged policy | reconstructing the logging propensity and the action grain | logged, stochastic, **unknown** | G35's assignment probabilities are **known by design**; no propensity is estimated and no OPE estimator appears among the valid families |
| **G05** | treatment effect of a staggered rollout | the identifying assumption for a counterfactual trend; format sequencing; transport | quasi-experimental | G35's treatment **is** randomised; there is no parallel-trends assumption and no control group to construct. The naive comparison is *internally valid for its own estimand* - it is simply the wrong estimand |
| **G31** | value-weighted fraud recall under three missingness mechanisms | the outcome is missing for three different reasons | partly randomised bypass | G31 is a missing-outcome problem; G35's outcomes are fully observed for every unit |
| **G33** | entity resolution / measurement error | *(dropped: the mechanism proved statistically irrelevant to the final quantity)* | n/a | G35's mechanism strength was measured first: 4x-39x, not a perturbation |
| **G34** | competing risks: crude vs net risk | one analyst must produce two statistical objects from one set of histories and keep them apart | none | same **shape** - multiple objects, one dataset - but a different science: G34 is about which events remove a unit from a risk set, G35 about whether units are independent at all. G34 has no randomisation and no interference; G35 has no censoring |

## The sharpest distinction, G35 vs G05

Both are "an experiment-shaped question with a wrong obvious answer", so the line matters.

- **G05**: the treated and control groups are *not* comparable, and the work is constructing a credible
  counterfactual.  Randomisation is absent; identification is the battleground.
- **G35**: the treated and control groups **are** perfectly comparable, randomisation is airtight, and
  the naive comparison is an unbiased estimate **of a real quantity**.  That quantity just is not the
  one the deployment decision is written on.

An agent that solves G35 with G05's toolkit - worrying about balance, trends and confounding - fixes
nothing, because nothing is broken there.  The measured proof: the correct-data-table gate hands over
a perfect table and the naive analysis is still wrong by 4x-39x.

## The sharpest distinction, G35 vs G34

G34's two objects are separated by **which events count as removals**.  G35's three objects are
separated by **which treatment regime the population is under**.  Neither mechanism appears in the
other: G34 has no interference and no randomisation; G35 has no censoring and no competing events.
The structural similarity - grade several objects so that confusing them is detectable - is a
deliberate carry-forward of what worked.
