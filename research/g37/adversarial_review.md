# Adversarial review (hostile reviewer), C1

| attack | result |
|---|---|
| estimand ambiguous | **Repelled.** Ppk vs Cpk, the reference scale and the window are pinned by drawing/contract (`estimand_audit.md`). Fraction nonconforming is deliberately not graded. |
| correction obvious | **Partly succeeds.** After H2/H3, "Deming + subtract variance" captures essentially all numerically visible difficulty (`recognition_execution.md`). |
| bridge study hands over the answer | **Repelled.** The vendor blocks are non-commutable, and OLS on the bridge is attenuated 6–12 SE_REF. |
| wrong methods too close | **SUCCEEDS.** X01/X02 are at ≈ 0 SE_REF; W09, W11, W17, X06 and X08 are < 3.5 on ≥ 3 fixtures; W07 is rejected on 1/5. |
| one fixture carries the difficulty | **Succeeds in part.** hidden_b rejects 18/32, the others 13–14; second-order routes rely on hidden_b alone. |
| threshold tuned | **Repelled.** 1.33 was fixed before the generator (`threshold_provenance.md`). |
| target is generator-only | **Repelled.** Every graded fact is identifiable (`graded_fact_evidence.md`). |
| natural edit solves it | **Repelled** (`natural_path_audit.md`). |
| valid families not independent | **Repelled**, with a caveat: a just-identified MLE ≡ F3 and is not counted. |
| latent assumptions unrealistic | **Partly succeeds.** D3 needed unrealistic gauges and still failed. The realistic regimes (D1/D2) have second-order effects below the noise. |
| decision guessable | **Repelled** (`cheap_solve.md`). |

**Two attacks succeed outright** (wrong methods too close; the correction is obvious once hinted),
**and two partly succeed.** Any one of the first two is disqualifying under the pre-build gates.
