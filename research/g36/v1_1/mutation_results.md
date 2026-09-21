# Mutation suite vs v1.1 — NOT RUN

28 mutations were generated (`tools/g36_v11/mutations/`): 28 distinct hashes, all smoke-execute, all
emit every graded quantity. New ones: `V02_response_as_load_ratio` (valid), `M33_household_weighted_response`
(wrong) and `M34_segment_unweighted_mean_response` (wrong).

The suite was **not executed**, because the verifier has no response tolerance. Calibration predicts
that at any usable multiplier `M34` would PASS the verifier, and so would `M33` on hidden_c. That is the
"behaves unexpectedly" STOP condition, found before execution.
