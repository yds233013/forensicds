# Decision / tolerance compatibility (C1)

Truth Ppk per fixture (D2, finite population over the 40 realised coils; spread across redraws):

| fixture | E[truth] | range over redraws | \|E truth − 1.33\| | SE_REF(Ppk) | dashboard Ppk | truth decision |
|---|---|---|---|---|---|---|
| visible | 1.565 | 1.358 – 1.721 | 0.235 | 0.030 | 0.991 | no notification |
| hidden_a | 1.075 | 0.912 – 1.260 | 0.255 | 0.019 | 1.306 | notify |
| hidden_b | 1.720 | 1.525 – 1.926 | 0.390 | 0.040 | 1.011 | no notification |
| hidden_c | 1.179 | 1.002 – 1.303 | 0.151 | 0.039 | 0.753 | notify |
| hidden_d | 1.120 | 0.951 – 1.269 | 0.210 | 0.021 | 1.140 | notify |

- **Expected-truth distances** are 4–13 SE_REF, so compatibility would hold for most realisations.
- **But** realised truths approach 1.33 within 0.03 (visible min 1.358; hidden_c max 1.303), because
  coil-to-coil variation over 40 coils moves the finite-population truth.
- A built task would need either more coils or a fixture-seed rule. Choosing seeds for distance is
  fixture engineering and would need to be preregistered.
- **Moot, because no tolerance exists** (`tolerance_window.md`). The threshold was never moved.
