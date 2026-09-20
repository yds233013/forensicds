# G35 incident tournament

Five concrete incidents written and paper-reviewed; two taken into simulation.

## The five

### I1 - Dispatch priority for premium merchants  (domain B)  **-> SIMULATED, SELECTED**
A delivery platform tests giving selected merchants priority in courier assignment.  The experiment
dashboard shows a large lift in order fulfilment for treated merchants.  Operations object that
couriers are a fixed pool: priority given to one store is priority taken from another, so the lift may
be displacement rather than gain.  Finance must size an FY27 commitment on the effect **after full
rollout**, when everybody has priority and priority is therefore worth nothing except for whatever
genuine routing efficiency the new algorithm adds.

*Strength:* the zero-sum limit is exact and the residual (routing efficiency) is a clean scalar.
*Risk:* interference here is a famous idea; recognition may be easy.

### I2 - Sponsored-listing bid optimiser  (domain E)  **-> SIMULATED, runner-up**
Advertisers randomised to an automated bidder.  Treated advertisers win more impressions; at full
rollout the clearing price rises and most of the private advantage cancels.
*Strength:* genuinely equilibrium interference.  *Weakness:* measured mechanism strength only 0.6x.

### I3 - Courier sign-on bonus in a shared supply pool  (domain A)
Bonuses randomised to couriers; treated couriers take more trips, leaving fewer for controls.
*Rejected:* the outcome unit (courier earnings) and the business estimand (platform trips) diverge in a
way that needs a second modelling layer, and the randomisation unit is the supply side while the
business cares about the demand side.  Two moving parts, against the brief's "do not stack mechanisms".

### I4 - Search-ranking boost for a seller cohort  (domain C)
Treated sellers ranked higher, taking impressions from controls.
*Rejected:* pure demand cannibalisation with a soft constraint.  Ground truth depends on an assumed
demand model rather than a countable resource, which is the G33 trap.

### I5 - Regional promotion with cross-border shopping  (domain F/G)
Promotion in one region draws demand from neighbours.
*Rejected:* the interference group is a fuzzy geographic neighbourhood, so the exposure mapping is a
modelling choice rather than an operational fact.  K13.

## Paper review summary

| | identifiable truth | mechanism strength (prior) | estimand clarity | exposure mapping is an operational fact | verdict |
|---|---|---|---|---|---|
| I1 | exact counterfactual replay | expected large | crisp | yes - the city/day dispatch pool | **simulate** |
| I2 | exact auction replay | expected moderate | crisp | yes - the auction | **simulate** |
| I3 | needs a second model | large | muddy | partly | reject |
| I4 | needs a demand model | unknown | crisp | no | reject |
| I5 | needs a spatial model | unknown | muddy | no | reject |

Measured outcome: I1 mechanism strength 3x-38x, I2 0.6x.  **I1 selected.**
