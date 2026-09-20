# G36 distinctness matrix

| task | core object | why G36 is different |
|---|---|---|
| **Task02** | point-in-time feature state | G36's features and timestamps are clean by construction; the correct-table gate hands them over perfectly and 45 sd of separation survives |
| **G05** | treatment effect of a staggered rollout | G36 **uses** a causal ingredient but its graded object is an operational **level** under a named future policy. The causal step (pilot response) is one of four ingredients; the others are a stable weather curve, a population mix and a weather forecast. An agent that produces only a treatment effect has not answered the question |
| **G08** | historical forecast vintages / what was known when | **the closest neighbour, and the one to watch.** G08 is about reconstructing historical semantic state. G36 has no vintage problem at all: every artefact is current and complete. The difficulty is that a mechanism *did not exist* in the training period, not that the analyst mis-reads what was known |
| **G10** | latent demand under censoring | no censoring in G36; outcomes are fully observed in every period that exists |
| **G24** | policy value under a logged policy | G36's pilot assignment probability is known by design; no propensity is reconstructed and no OPE estimator appears among the valid routes |
| **G31** | value-weighted recall under three missingness mechanisms | G36 has no missing outcomes |
| **G33** | entity resolution / measurement error (dropped) | G36's mechanism strength was measured first: 45 sd, not a perturbation |
| **G34** | competing risks: crude vs net risk | shares the multi-object shape deliberately. Different science: G34 is about which events remove a unit from a risk set; G36 is about which conditional relationships survive an intervention |
| **G35** | interference / recognition of shared capacity | **the reason G36 exists.** G35's recognition handed over the estimator (`mean(pi=1) - mean(pi=0)`) and scored 3/3. G36 is built so that each insight leaves 10-12 sd of error and at least one wrong decision |

## The sharpest distinction: G36 vs G08

Both involve "the past does not tell you what you think it does", so the line must be explicit.

- **G08**: the data is a historical record whose *semantics* are easy to misread - which vintage,
  which as-of date, what was known when. The fix is operational reconstruction (S2).
- **G36**: the data is semantically unambiguous and completely correct. The failure is that a
  **mechanism that will govern the future did not exist during the period the model was trained on**,
  so no amount of historical reconstruction or validation can reveal it. The fix is decomposition and
  transport (S4-S5).

Measured support: G36's correct-table gate hands over a flawless table and the incumbent model is
still wrong by 45 sd. If the difficulty were vintage semantics, that gate would collapse it.

## The sharpest distinction: G36 vs G05

G05 asks *what did the rollout cause*. G36 asks *what will the operational level be*. G36's forecast
requires a causal input, but composing it with a stable non-causal component and a target population
is the work. An analyst who perfectly estimates the pilot's causal effect and reports it has produced
`W7`, wrong by 27 sd.
