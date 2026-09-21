# IGQA (C1) — before build

| quantity | semantic (from the business question) | computational #1 | computational #2 | shared helpers | weighting | units | population | window | result |
|---|---|---|---|---|---|---|---|---|---|
| latent_mean_post | mean true thickness of parts shipped post-change, reference-method scale (`estimand_audit.md`) | F1 map | F3 map | the mapping formula (definitional) | per part | mm | post parts | post | **PASS** |
| latent_sd_post | overall SD, reference scale | F1 | F3 (no external repeatability) | the deconvolution formula (definitional) | per part | mm | post parts | post | **PASS** (identifiable) / **FAIL gradability**: no window |
| latent_ppk_post | Ppk per the supply agreement | forced | forced | — | — | — | post | post | forced; inherits the σ₁ gradability failure |
| latent_sd_pre | overall SD pre | check repeats | parallel-run structure | — | per part | mm | pre parts | pre | PASS |
| notification | Ppk < 1.33 | forced | forced | — | — | — | — | — | PASS |

**IGQA passes on meaning and computation. The quantities are nonetheless not gradable, because no
tolerance window exists** (principle 11). Identifiability alone is not enough.
