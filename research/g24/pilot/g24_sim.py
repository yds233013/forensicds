#!/usr/bin/env python3
"""G24 Phase-0 simulator: recommender off-policy evaluation world (no task files, no model).

Pipeline per slate decision:
    retrieval pool (K items by v6 score)  ->  logging policy orders the pool
    -> post-ranking eligibility filter removes ineligible items from the ordered list
    -> first five survivors are served    -> position-based clicks
    -> cache: reloads re-serve the stored slate (more reloads after a poor slate)

Streams: prod_v6 (deterministic top-5 eligible), explore_shuffle (uniform ordering of the pool),
ab_v7 (deterministic top-5 eligible by v7, bounded window).

Logged propensity (as the serving stack computes it) is the ordered-slate probability over the PRE-filter pool:
1/(K(K-1)(K-2)(K-3)(K-4)).  The served ordering is uniform over orderings of the m eligible items, so the
item-in-slot marginal is 1/m and the slate probability is (m-5)!/m!.
"""
from __future__ import annotations

import numpy as np

THETA = {  # examination probability by slot, per device
    "web": np.array([1.00, 0.70, 0.54, 0.43, 0.35]),
    "mobile": np.array([1.00, 0.62, 0.45, 0.33, 0.26]),
    "tv": np.array([1.00, 0.52, 0.33, 0.22, 0.15]),
}
DEVICES = ("web", "mobile", "tv")
SLOTS = 5

BASE = dict(
    name="visible",
    n_decisions=160_000,          # decisions in the extract (all streams)
    explore_share=0.45,           # share of extract decisions from the exploration stream (extract is stratified)
    ab_share=0.10,                # share from the A/B arm (v7 on-policy)
    device_mix=(0.45, 0.30, 0.25),
    theta=THETA,
    n_items=4000,
    pool_k=(8, 14),               # retrieved pool size K (uniform over the range)
    filter_rate=(0.10, 0.45),     # share of the pool filtered out per decision, min eligible enforced
    min_eligible=6,
    r_scale=0.30,                 # relevance in (0, r_scale)
    v6_pop_weight=0.90, v6_noise=0.090,
    v7_novelty=0.60, v7_anti=2.40, v7_noise=0.012,   # better set, ordering anti-correlated with relevance
    v7pd_noise=0.045,                  # slightly weaker set, correct ordering
    reload_lambda=dict(web=0.15, mobile=0.25, tv=0.55),
    reload_quality=1.2,           # worse slates cause more reloads
)


def draw_world(spec: dict, seed: int) -> dict:
    """One extract: per-decision pools, relevances, policy scores, streams, served slates, clicks, serves."""
    rng = np.random.default_rng(seed)
    n = spec["n_decisions"]
    kmin, kmax = spec["pool_k"]
    K = rng.integers(kmin, kmax + 1, n)
    kmax_pad = kmax
    dev = rng.choice(len(DEVICES), n, p=spec["device_mix"])
    theta = np.stack([spec["theta"][d] for d in DEVICES])          # (3, 5)

    # catalogue: global items with a quality level, a popularity signal and a novelty signal
    n_items = spec["n_items"]
    q_item = rng.normal(0.0, 1.0, n_items)
    pop_item = 0.35 * q_item + rng.normal(0.0, 1.0, n_items)
    nov_item = rng.normal(0.0, 1.0, n_items)
    item = rng.integers(0, n_items, (n, kmax_pad))                  # retrieved pool membership
    u_user = rng.normal(0.0, 0.6, (n, 1))                           # user-level taste level
    z = q_item[item] + u_user + rng.normal(0.0, 0.9, (n, kmax_pad))  # user x item affinity
    r = spec["r_scale"] / (1.0 + np.exp(-(z - 0.9)))
    pop = pop_item[item]
    nov = nov_item[item]
    in_pool = np.arange(kmax_pad)[None, :] < K[:, None]

    # eligibility: already-watched / licence filtering, correlated with relevance (watched titles are relevant ones)
    share = rng.beta(2.0, 6.0, n) * (spec["filter_rate"][1] - spec["filter_rate"][0]) + spec["filter_rate"][0]
    elig_score = rng.random((n, kmax_pad)) + 0.45 * (r / spec["r_scale"])     # relevant items filtered more often
    m = np.maximum(spec["min_eligible"], K - np.floor(share * K).astype(int))  # eligible pool size
    keep_rank = np.argsort(np.argsort(np.where(in_pool, elig_score, np.inf), axis=1), axis=1)
    eligible = in_pool & (keep_rank < m[:, None])                             # the m least-filtered pool items

    # policy scores over the pool
    s_v6 = r + spec["v6_pop_weight"] * 0.1 * pop + rng.normal(0, spec["v6_noise"], (n, kmax_pad))
    s_v7pd = r + rng.normal(0, spec["v7pd_noise"], (n, kmax_pad))
    # v7: selects a good set (relevance-driven) but orders it by novelty -> good set, bad order
    sel_v7 = r + rng.normal(0, spec["v7_noise"], (n, kmax_pad))
    rank_sel = np.argsort(-np.where(eligible, sel_v7, -np.inf), axis=1)
    top_set = np.zeros((n, kmax_pad), bool)
    np.put_along_axis(top_set, rank_sel[:, :SLOTS], True, axis=1)
    order_v7 = spec["v7_novelty"] * nov - spec["v7_anti"] * (r / spec["r_scale"])   # novelty first, relevance last
    s_v7 = np.where(top_set, 10.0 + order_v7, sel_v7)

    def slate_of(score):
        masked = np.where(eligible, score, -np.inf)
        order = np.argsort(-masked, axis=1)[:, :SLOTS]
        return order

    slate = {"v6": slate_of(s_v6), "v7": slate_of(s_v7), "v7_pd": slate_of(s_v7pd)}
    value = {p: (np.take_along_axis(r, s, 1) * theta[dev]).sum(1) for p, s in slate.items()}

    # streams
    u = rng.random(n)
    stream = np.where(u < spec["explore_share"], 0, np.where(u < spec["explore_share"] + spec["ab_share"], 2, 1))

    # served slate per stream
    served = np.zeros((n, SLOTS), int)
    shuffle_key = np.where(eligible, rng.random((n, kmax_pad)), np.inf)
    perm = np.argsort(shuffle_key, axis=1)[:, :SLOTS]                        # uniform ordering of eligible items
    served = np.where((stream == 0)[:, None], perm,
                      np.where((stream == 2)[:, None], slate["v7"], slate["v6"]))

    r_served = np.take_along_axis(r, served, 1)
    p_click = r_served * theta[dev]
    clicks = (rng.random((n, SLOTS)) < p_click).astype(np.int8)

    # cache reloads: extra serves of the stored slate; poor slates cause more reloads
    slate_val = (r_served * theta[dev]).sum(1)
    lam = np.array([spec["reload_lambda"][d] for d in DEVICES])[dev]
    lam = lam * (1.0 + spec["reload_quality"] * (spec["r_scale"] - slate_val) / spec["r_scale"])
    extra = rng.poisson(np.clip(lam, 0.01, None))
    n_serves = 1 + extra
    click_serve = (rng.random((n, SLOTS)) * n_serves[:, None]).astype(int)   # which render carried each click

    logged_propensity = np.exp(-(np.log(K) + np.log(K - 1) + np.log(K - 2) + np.log(K - 3) + np.log(K - 4)))
    return dict(spec=spec, seed=seed, n=n, K=K, m=m, dev=dev, theta=theta, r=r, eligible=eligible, in_pool=in_pool,
                item=item, n_items=n_items,
                scores={"v6": s_v6, "v7": s_v7, "v7_pd": s_v7pd}, slate=slate, value=value, stream=stream,
                served=served, clicks=clicks, n_serves=n_serves, click_serve=click_serve,
                logged_propensity=logged_propensity, r_served=r_served)


def truth(w: dict) -> dict:
    """Exact policy values over all decisions in the extract (expectations, not click draws)."""
    return {p: float(v.mean()) for p, v in w["value"].items()}


def launch_decision(values: dict, lo: dict) -> str:
    """Launch rule: candidate whose lift lower bound is above zero; if both, the larger estimate."""
    ok = [p for p in ("v7", "v7_pd") if lo[p] > 0]
    if not ok:
        return "v6"
    return max(ok, key=lambda p: values[p])


def true_decision(w: dict) -> str:
    t = truth(w)
    ok = [p for p in ("v7", "v7_pd") if t[p] > t["v6"]]
    return max(ok, key=lambda p: t[p]) if ok else "v6"


# ---------------------------------------------------------------- regimes (hidden fixtures change the policy world)

def regime(name: str) -> dict:
    import copy
    sp = copy.deepcopy(BASE)
    sp["name"] = name
    if name == "visible":
        return sp
    if name == "tv_heavy":                       # device-heavy tail: pooled examination curves must fail
        sp.update(device_mix=(0.25, 0.30, 0.45), explore_share=0.35,
                  theta={**THETA, "tv": np.array([1.00, 0.45, 0.27, 0.17, 0.11])})
        return sp
    if name == "no_launch":                      # neither candidate beats production; wider pools
        sp.update(pool_k=(6, 20), filter_rate=(0.05, 0.35), v7pd_noise=0.30, v7_anti=4.20, v7_noise=0.05,
                  explore_share=0.50)
        return sp
    if name == "v7_wins":                        # v7 orders its good set correctly: launching v7 is right
        sp.update(v7_anti=0.0, v7_novelty=0.0, v7_noise=0.010, v7pd_noise=0.16,
                  v6_pop_weight=1.50, v6_noise=0.150,
                  device_mix=(0.35, 0.45, 0.20), reload_lambda=dict(web=0.20, mobile=0.35, tv=0.55))
        return sp
    raise ValueError(name)


REGIMES = ("visible", "tv_heavy", "no_launch", "v7_wins")
