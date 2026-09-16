"""Home-row serving path (extract of the production service).

    retrieve -> rank -> log -> business rules -> respond

The ranker logs what it produced. The rules layer runs afterwards and can change the response.
"""
from __future__ import annotations

import math
import random

from platform_sdk import cache, rules, telemetry

SLATE_SIZE = 5


def serve_home_row(request, config):
    cached = cache.get(key=(request.session_id, request.surface))
    if cached is not None:
        telemetry.log_serve(request, cached.slate, propensity=cached.propensity,
                            candidate_count=cached.candidate_count, stream=cached.stream)
        return cached.slate

    pool = retrieve(request, config)                      # candidates, ranked by the retrieval score
    stream = "explore_shuffle" if in_exploration(request, config) else "prod_rank"

    if stream == "explore_shuffle":
        ordered = list(pool)
        random.shuffle(ordered)                           # uniform ordering of the retrieved pool
        propensity = math.exp(-sum(math.log(len(pool) - k) for k in range(SLATE_SIZE)))
    else:
        ordered = sorted(pool, key=lambda c: -c.score_production)
        propensity = 1.0

    if stream == "explore_shuffle" or telemetry.sampled(request, "candidates"):
        telemetry.log_candidates(request, pool)           # one row per retrieved title, with the model scores
    telemetry.log_propensity(request, propensity)         # probability of the ordering the ranker produced

    ordered, suppressed = rules.apply(ordered, request)   # drops titles the rules layer suppresses
    telemetry.log_rules(request, suppressed)              # reason per suppressed title
    slate = ordered[:SLATE_SIZE]

    cache.put(key=(request.session_id, request.surface), slate=slate, propensity=propensity,
              candidate_count=len(pool), stream=stream, ttl=config["cache"]["ttl_seconds"])
    telemetry.log_serve(request, slate, propensity=propensity, candidate_count=len(pool), stream=stream)
    return slate
