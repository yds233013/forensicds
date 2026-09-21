# Response K9 under R_load — PASS

Families F1 stratified, F2 joint nonlinear and F3 hierarchical, run on 5 fixtures × 4 draws
(`response_validation.json`).

- Pairwise paired-difference \|t\|: F1–F2 1.08, F1–F3 0.04, F2–F3 1.11 (all < 3).
- Decisions: unanimous and correct.
- Biases vs truth: F1 +0.00359, F2 +0.00234, F3 +0.00354 (t 3.68). The F3 bias is attributed to
  hierarchical shrinkage and is shared in sign with F1 and F2.
- Response SE_REF (30 redraws, seeds `base + 10007(k+1)`): visible 0.00566, hidden_a 0.008221,
  hidden_b 0.005185, hidden_c 0.019631, hidden_d 0.004921.
- The forecast SE_REF recomputed under the same procedure reproduces v1 (diff about 4e-9), which
  confirms the harness is unchanged.

K9 passing establishes that the valid estimators agree. It does **not** establish that a tolerance
exists which separates them from wrong analyses. That is where v1.1 failed.
