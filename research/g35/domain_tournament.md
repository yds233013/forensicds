# G35 domain tournament

Nine domains scored 1-5 against the brief's criteria, before any incident was written.  Scores are
design judgements recorded in advance; the two finalists were then measured in simulation.

| | domain | natural interference | realistic experiment | clear randomisation unit | clear interference unit | defensible estimand | identifiable truth | operational realism | multiple valid routes | plausible wrong analyses | shortcut resistance | data realism | distinct from G05/G24 | **total** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A** | ride-hailing dispatch / driver incentives | 5 | 4 | 4 | 4 | 4 | 4 | 5 | 4 | 5 | 4 | 4 | 5 | **52** |
| **B** | **food-delivery dispatch priority** | **5** | **5** | **5** | **5** | **5** | **5** | **5** | **5** | **5** | **4** | **5** | **5** | **59** |
| C | marketplace seller/buyer ranking | 5 | 4 | 4 | 3 | 3 | 3 | 4 | 4 | 4 | 3 | 4 | 4 | 45 |
| D | e-commerce inventory allocation | 4 | 3 | 4 | 4 | 4 | 4 | 4 | 3 | 4 | 4 | 4 | 4 | 46 |
| **E** | **advertising auctions** | **5** | **5** | **5** | **4** | **4** | **5** | **4** | **4** | **5** | **4** | **4** | **5** | **54** |
| F | labour marketplace matching | 5 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 4 | 3 | 3 | 4 | 41 |
| G | warehouse / fulfilment routing | 4 | 3 | 3 | 4 | 4 | 4 | 4 | 3 | 3 | 4 | 3 | 4 | 43 |
| H | dynamic pricing | 4 | 3 | 3 | 3 | 3 | 3 | 4 | 3 | 4 | 3 | 4 | 3 | 40 |
| I | social-network feed ranking | 5 | 3 | 3 | 2 | 3 | 2 | 4 | 3 | 4 | 3 | 3 | 4 | 39 |

## Why B wins

**Food-delivery dispatch priority** scores highest on the two criteria that killed earlier candidates:

- **Identifiable truth (G33's failure mode).**  Courier capacity is a hard, countable constraint.  The
  counterfactual "what if every merchant had priority" can be replayed exactly on the same demand and
  capacity draw, so ground truth is not a modelling opinion.
- **Mechanism strength (G34-v1's failure mode).**  Priority under a capacity constraint is *exactly*
  zero-sum in the limit.  At full saturation every merchant has the same dispatch weight, which is the
  same allocation as nobody having priority.  The interference is not a perturbation; it is most of
  the measured effect.  Simulation confirms the naive comparison overstates by 3x to 38x.

It also has the clearest **interference unit**: couriers are pooled within a city on a given day, and
the dispatch pool boundary is an operational fact a real analyst can read off the system, not a
modelling choice.

## Why E (advertising auctions) was the runner-up and not the winner

Auctions have equally natural interference and excellent ground truth.  It was taken into simulation
and measured.  Result (`simulation_results.md` s6): the naive A/B error was **0.6x** the true policy
effect, versus **3x-38x** for dispatch.  In a second-price auction the private gain from bidding
better and the social loss from a higher clearing price partially offset inside the *same* advertiser's
surplus, so the naive estimate is wrong but not dramatically wrong.  Measured mechanism strength, not
taste, selected B.

## Why the losers lost

- **C, I** - the interference unit is a diffuse network neighbourhood.  Ground truth requires a
  modelled graph, so "truth" becomes an artefact of the generator (the G33 failure).
- **D, G** - interference is real but the experiment is hard to make realistic; firms rarely randomise
  allocation policy at a level that identifies the policy effect.
- **F, H** - matching and pricing both entangle interference with equilibrium *selection*, which makes
  the estimand contestable.  The brief forbids ambiguity as the source of difficulty.
