# Ranker launch policy

Owner: Personalisation leadership.

1. A candidate ranker may be launched only if its estimated improvement over the production ranker on
   **home-row clicks per slate decision** (`docs/metrics/home_row.md`) has a two-sided 95% confidence interval whose lower bound is above zero.
2. If more than one candidate qualifies, launch the one with the higher estimate.
3. If none qualifies, keep the production ranker.

The estimate must cover the whole evaluation window and all devices.
