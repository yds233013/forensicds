# G35 representation-leakage audit

Probes run on the simulated experiment for all four regimes.  The question is whether assigned
saturation - the variable the whole analysis turns on - can be recovered from an artefact in a way
that makes the statistical work unnecessary, or whether any regime label is inferable.

## Probes and results

| probe | visible | hidden_a | hidden_b | hidden_c |
|---|---|---|---|---|
| corr(block demand, saturation) | -0.015 | -0.015 | -0.023 | -0.026 |
| corr(day index, saturation) | +0.007 | +0.001 | +0.011 | -0.026 |
| corr(city index, saturation) | +0.059 | -0.005 | -0.025 | -0.021 |
| AUC separating the 100% arm from the 0% arm using block size alone | 0.537 | 0.527 | 0.504 | 0.548 |

All correlations are below 0.06 and every AUC is within 0.05 of chance.  Saturation is not recoverable
from block size, city, or calendar position.

## Arm balance (visible)

| saturation | blocks |
|---|---|
| 0.00 | 335 |
| 0.25 | 318 |
| 0.50 | 318 |
| 0.75 | 359 |
| 1.00 | 350 |

No arm is degenerate; each has ample support.

## Assigned versus realised exposure

| assigned saturation | mean realised adoption share |
|---|---|
| 0.00 | 0.000 |
| 0.25 | 0.214 |
| 0.50 | 0.429 |
| 0.75 | 0.647 |
| 1.00 | 0.866 |

Realised adoption is systematically below assigned saturation and is tilted toward larger merchants.
The two are therefore genuinely different quantities, which is what makes W10 a real (if weak) error
rather than a distinction without a difference.

## Requirements for any future build

Recorded now so they are designed in rather than patched later:

1. The assignment log must be a **first-class artefact** with pre-dated timestamps, because A1/A2/A5
   identification rests on it.  It must not encode the regime, the seed, or the truth.
2. Row order must be shuffled before serialisation, and block/merchant identifiers must be label-
   shuffled, exactly as in G34's generator.
3. City names must be synthetic and carry no tightness signal - no "Metro-Tight-01".
4. The hidden regimes must not be distinguishable by dataset size, arm counts or file layout.
5. No artefact may contain the realised courier capacity `S_b`, which would let an analyst compute
   the answer mechanically rather than estimate it.
