# Mutation suite — forecast-only reclassification (in-process), Docker suite NOT RUN

The 28 mutations are unchanged. The hash audit (from `tools/g36_v11/mutations_manifest.json`) shows
28 distinct patch hashes, none equal to the unmutated source, all smoke-execute, all emit every
quantity.

They were scored **in-process** against the proposed v1.1 reward (`forecast_sufficiency.json`). The
containerised suite (`run_suite.sh`) was **not** run, because v1.1 was abandoned at the
counterexample stage before any verifier edit or image build.

| class | cases | expected | result |
|---|---|---|---|
| VALID | V00, V01, V02 | 1 | **3/3 = 1** |
| SCIENTIFIC WRONG | M03 M05 M06 M07 M08 M09 M10 M12 M13 M14 M15 M18 M23 M24 M27 M30 M31 | 0 | **17/17 = 0** |
| DECISION WRONG (forecast correct, decision constant) | M20, M21 | 0 | **2/2 = 0** |
| BOOKKEEPING WRONG | M26 (hard-coded households), M32 (CDD mean from history) | 0 | **2/2 = 0** |
| REPORTING WRONG (forecast and decision correct; response field wrong) | M28 (zero), M29 (sign flipped), M33 (household-weighted), M34 (segment-unweighted) | may be 1 | **4/4 = 1**. The forecast is identical to V00 (max err/tol 0.36), and so is the decision. These are reporting-only; they are **not** counted as verifier failures. |

**Semantic duplicates in forecast space** (distinct source hashes, identical forecasts): M07 ≡ M18
(`total·pt/pc`), and M09 ≡ M31 (both weight by enrolled mix; they differed only in the response
field). There are 15 distinct scientific-wrong forecasts, not 17. This is a pre-existing property
of the G36 suite and is recorded here.

**The mutation suite is not where v1.1 fails.** Every pre-registered scientific mutation is
rejected. The failure is a wrong **modelling** route outside the suite, CE06
(`counterexample_search.md`).
