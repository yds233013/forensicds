"""G25 Phase-0 pilot: the statistical step only (research only).

Identity, scale, product-grain and supersession errors are deterministic and are caught by the exact resolved-qrels
table; they need no simulation. What needs calibration is the estimate of the unjudged slots' contribution and the
frame restriction, so this pilot models:

  per gate query: two ranked lists of 10 slots, each slot with a true gate grade (0/1/2);
  resolution state per slot: labelled after correct resolution, or genuinely unlabelled;
  the harness frame: slots the broken harness saw as unlabelled (a superset: it also contains 3P offers of judged
  products, which correct resolution labels);
  an audit round (R09): a uniform sample of the harness frame.
"""
from __future__ import annotations

import copy

import numpy as np

GAIN = np.array([0.0, 1.0, 3.0])          # 2^g - 1 for g = 0, 1, 2

BASE = {
    "name": "visible",
    "n_queries": 2000,
    "k": 10,
    "audit_size": 1500,
    "threshold": -0.005,
    # share of slots that correct resolution leaves unlabelled, per ranker
    "unlabelled_share": {"A": 0.04, "B": 0.15},
    # extra share of slots the harness saw as unlabelled but resolution labels (3P offers of judged products)
    "harness_extra_share": {"A": 0.05, "B": 0.31},
    # true grade distribution (P(g=0), P(g=1), P(g=2))
    "grade_labelled": {"A": (0.32, 0.34, 0.34), "B": (0.24, 0.32, 0.44)},
    "grade_unlabelled": {"A": (0.62, 0.26, 0.12), "B": (0.62, 0.26, 0.12)},
    "grade_harness_extra": {"A": (0.30, 0.34, 0.36), "B": (0.26, 0.32, 0.42)},
    "ideal_pool_extra": 6,                 # judged products beyond the two lists, for IDCG
    "ideal_pool_grades": (0.45, 0.33, 0.22),
    "rank_gain_tilt": 0.10,                # mild rank dependence of unlabelled gain
    # semantic retrieval places new/3P products high: unlabelled share is concentrated at top ranks
    "unlabelled_rank_weight": (2.2, 2.0, 1.8, 1.4, 1.1, 0.8, 0.6, 0.5, 0.4, 0.3),
}

REGIMES = {
    "visible": {},
    # B genuinely worse: its unlabelled new products are poor and its labelled slots are weaker
    "b_worse": {"grade_labelled": {"A": (0.30, 0.33, 0.37), "B": (0.33, 0.33, 0.34)},
                "grade_unlabelled": {"A": (0.62, 0.26, 0.12), "B": (0.72, 0.22, 0.06)},
                "unlabelled_share": {"A": 0.04, "B": 0.22}},
    # tail-heavy: more unlabelled, better unlabelled products, bigger audit
    "tail_heavy": {"unlabelled_share": {"A": 0.06, "B": 0.25}, "audit_size": 2500,
                   "grade_unlabelled": {"A": (0.50, 0.30, 0.20), "B": (0.50, 0.30, 0.20)}},
    # thin audit: the estimate is noisier
    "thin_audit": {"audit_size": 800},
}


def regime(name):
    s = copy.deepcopy(BASE)
    s.update(REGIMES[name])
    s["name"] = name
    return s


def _draw_grades(rng, probs, size):
    return rng.choice(3, size=size, p=np.array(probs) / np.sum(probs))


def draw_world(spec, seed):
    rng = np.random.default_rng(seed)
    Q, k = spec["n_queries"], spec["k"]
    out = {}
    for r in ("A", "B"):
        rw = np.array(spec["unlabelled_rank_weight"][:k], float)
        rw = rw / rw.mean()
        u = rng.random((Q, k)) < np.clip(spec["unlabelled_share"][r] * rw[None, :], 0, 0.95)
        extra = (~u) & (rng.random((Q, k)) < spec["harness_extra_share"][r])    # harness-unlabelled but resolvable
        g = np.where(u, _draw_grades(rng, spec["grade_unlabelled"][r], (Q, k)),
                     np.where(extra, _draw_grades(rng, spec["grade_harness_extra"][r], (Q, k)),
                              _draw_grades(rng, spec["grade_labelled"][r], (Q, k))))
        # mild rank tilt for unlabelled slots: later ranks slightly worse
        tilt = rng.random((Q, k)) < spec["rank_gain_tilt"] * (np.arange(k) / k)[None, :]
        g = np.where(u & tilt & (g > 0), g - 1, g)
        out[r] = {"grade": g, "unlabelled": u, "harness_unlabelled": u | extra}
    ideal = _draw_grades(rng, spec["ideal_pool_grades"], (Q, spec["ideal_pool_extra"]))
    # audit: uniform sample of the harness frame over B's slots (the design's R09)
    frame = np.argwhere(out["B"]["harness_unlabelled"])
    idx = rng.choice(len(frame), size=min(spec["audit_size"], len(frame)), replace=False)
    audit = frame[idx]
    return dict(spec=spec, seed=seed, Q=Q, k=k, A=out["A"], B=out["B"], ideal=ideal, audit=audit)


def _dcg(gain_matrix):
    disc = 1.0 / np.log2(np.arange(2, gain_matrix.shape[1] + 2))
    return (gain_matrix * disc[None, :]).sum(1)


def _idcg(w, extra_gains=None):
    """Ideal DCG per query from the union of both lists' true grades and the historical judged pool."""
    pool = np.concatenate([GAIN[w["A"]["grade"]], GAIN[w["B"]["grade"]], GAIN[w["ideal"]]], axis=1)
    if extra_gains is not None:
        pool = np.concatenate([pool, extra_gains], axis=1)
    pool = -np.sort(-pool, axis=1)[:, : w["k"]]
    return _dcg(pool)


def truth(w):
    """NDCG@10 under complete judgments: every slot's true gate grade counts."""
    idcg = _idcg(w)
    out = {}
    for r in ("A", "B"):
        out[r] = float(np.mean(_dcg(GAIN[w[r]["grade"]]) / idcg))
    out["delta"] = out["B"] - out["A"]
    out["decision"] = "pass" if out["delta"] >= w["spec"]["threshold"] else "block"
    return out
