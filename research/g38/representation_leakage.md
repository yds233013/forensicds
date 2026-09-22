# Representation leakage (design audit; nothing was built)

| channel | risk | design mitigation (not needed; the task is dropped) |
|---|---|---|
| treatment IDs / threshold flags | an enrolment table reveals t0, which is legitimate and needed | fine |
| precomputed dashboards | the dashboard ppm change would be *the natural wrong answer*, not a leak | include as a lure |
| future columns / post-treatment metadata | SDP close-out ratings could encode the effect | exclude |
| row order | generation order | shuffle |
| fixture dimensions / sample sizes | enrolment counts vary by regime (84–118) | not monotone in the decision, but would need fixing to a constant |
| missingness | none | — |

No leakage channel would have handed over the answer. Moot, because the task is dropped.
