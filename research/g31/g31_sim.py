"""G31 Phase-0 pilot: data-generating process (research only; no task files, no model).

World: one payments processor, `n_days` of authorization attempts across three merchant segments.

Latent
------
z      latent fraud propensity index (pre-decision)
Y*     would this authorization incur a fraud chargeback if it were allowed to settle (binary)
v      transaction value (loss if Y*=1 and allowed)

Scores (both computed from pre-decision features only)
-----------------------------------------------------
s6     incumbent model, drove the historical policy
s7     challenger model, scored offline on the same pre-decision features

Historical policy (per segment, from the v6 score)
-------------------------------------------------
s6 >= t_block    -> BLOCK                      (never settles; Y* never observable)
t_rev <= s6 < t_block -> REVIEW queue
s6 <  t_rev      -> ALLOW                      (settles; chargeback after a delay if Y*=1)

Two mechanisms break the naive "labelled rows" population:

1. bypass holdout: each BLOCK/REVIEW row is allowed anyway with logged probability q_g.
   This is the only source of labels in the BLOCK band, and the only *unselected* source
   in the REVIEW band.
2. review capacity: within the REVIEW band the queue is worked top-down by s6, so verified
   labels are selected on the incumbent score. Unworked rows are auto-declined at SLA and
   never produce a label at all.

Delay: chargebacks arrive after a segment-specific lag; the extract right-censors them.
"""
from __future__ import annotations

import copy

import numpy as np

SEGMENTS = ["ecom_cnp", "marketplace", "travel"]

BASE = {
    "name": "visible",
    "n_days": 365,
    "extract_day": 365,
    "txn_per_day": 1200,          # per segment
    "seg_share": {"ecom_cnp": 1.0, "marketplace": 1.0, "travel": 1.0},
    # latent fraud propensity -> P(Y*=1) = sigmoid(a_g + b * z)
    "a": {"ecom_cnp": -6.6, "marketplace": -6.2, "travel": -7.0},
    "b": 3.4,
    "log_value_mu": {"ecom_cnp": 4.1, "marketplace": 4.5, "travel": 5.3},
    "log_value_sd": 0.8,
    "fraud_value_mult": {"ecom_cnp": 1.25, "marketplace": 1.9, "travel": 1.3},
    # model score noise: rank index = z + N(0, sigma) + gamma * w   (w is a nuisance feature)
    "sigma6": {"ecom_cnp": 0.80, "marketplace": 0.75, "travel": 0.90},
    "sigma7": {"ecom_cnp": 0.42, "marketplace": 0.72, "travel": 0.50},
    "gamma7": {"ecom_cnp": 0.10, "marketplace": 0.95, "travel": 0.15},
    "gamma6": {"ecom_cnp": 0.10, "marketplace": 0.12, "travel": 0.10},
    # historical policy: block the top 1%, review the next 3%
    "block_rate": {"ecom_cnp": 0.010, "marketplace": 0.012, "travel": 0.008},
    "review_rate": {"ecom_cnp": 0.030, "marketplace": 0.038, "travel": 0.024},
    # logged bypass-holdout probability, higher on the block band than the review band
    "q_block": {"ecom_cnp": 0.25, "marketplace": 0.25, "travel": 0.25},
    "q_review": {"ecom_cnp": 0.12, "marketplace": 0.12, "travel": 0.12},
    "review_capacity": {"ecom_cnp": 0.55, "marketplace": 0.40, "travel": 0.70},
    "delay_mu": {"ecom_cnp": 2.6, "marketplace": 3.3, "travel": 2.9},
    "delay_sd": {"ecom_cnp": 0.50, "marketplace": 0.50, "travel": 0.55},
    "delay_cap": 120,
    # the comparison holds the total intervention budget (block + review) fixed at today's level
    "eval_block_rate": {"ecom_cnp": 0.040, "marketplace": 0.050, "travel": 0.032},
    "adopt_bar": 0.010,
}

REGIMES = {
    "visible": {},
    "high_prev": {"a": {"ecom_cnp": -5.9, "marketplace": -5.5, "travel": -6.3}},
    "slow_cb_big_holdout": {
        "delay_mu": {"ecom_cnp": 3.2, "marketplace": 3.8, "travel": 3.5},
        "q_block": {"ecom_cnp": 0.35, "marketplace": 0.35, "travel": 0.35},
        "q_review": {"ecom_cnp": 0.18, "marketplace": 0.18, "travel": 0.18},
    },
    "tight_capacity": {
        "review_capacity": {"ecom_cnp": 0.30, "marketplace": 0.20, "travel": 0.45},
        "seg_share": {"ecom_cnp": 1.5, "marketplace": 0.7, "travel": 0.8},
    },
    "v7_wins_everywhere": {
        "gamma7": {"ecom_cnp": 0.10, "marketplace": 0.15, "travel": 0.15},
        "sigma7": {"ecom_cnp": 0.42, "marketplace": 0.48, "travel": 0.50},
    },
}


def regime(name: str) -> dict:
    s = copy.deepcopy(BASE)
    s.update(copy.deepcopy(REGIMES[name]))
    s["name"] = name
    return s


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _rank01(x, rng):
    """Map to (0,1) by rank, with ties broken randomly - mimics a calibrated score column."""
    n = len(x)
    order = np.argsort(x + rng.normal(0, 1e-9, n))
    r = np.empty(n)
    r[order] = (np.arange(n) + 0.5) / n
    return r


def draw_world(spec: dict, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    parts = []
    for g in SEGMENTS:
        n = int(spec["n_days"] * spec["txn_per_day"] * spec["seg_share"][g])
        day = rng.integers(1, spec["n_days"] + 1, n)
        z = rng.normal(0, 1, n)
        w = rng.normal(0, 1, n)                                   # nuisance feature
        p = _sigmoid(spec["a"][g] + spec["b"] * z)
        y = (rng.random(n) < p).astype(np.int8)                    # latent Y*
        v = np.exp(rng.normal(spec["log_value_mu"][g], spec["log_value_sd"], n))
        v = np.where(y == 1, v * spec["fraud_value_mult"][g], v)

        r6 = z + rng.normal(0, spec["sigma6"][g], n) + spec["gamma6"][g] * w
        r7 = z + rng.normal(0, spec["sigma7"][g], n) + spec["gamma7"][g] * w
        s6 = _rank01(r6, rng)
        s7 = _rank01(r7, rng)

        # historical policy thresholds from v6 score rates
        t_block = np.quantile(s6, 1 - spec["block_rate"][g])
        t_rev = np.quantile(s6, 1 - spec["block_rate"][g] - spec["review_rate"][g])
        band = np.where(s6 >= t_block, 2, np.where(s6 >= t_rev, 1, 0))   # 0 allow, 1 review, 2 block

        # bypass holdout on BLOCK and REVIEW rows
        qrow = np.where(band == 2, spec["q_block"][g], spec["q_review"][g])
        holdout = (band > 0) & (rng.random(n) < qrow)

        # review capacity: worked top-down by s6 among non-holdout review rows
        reviewed = np.zeros(n, bool)
        idx = np.flatnonzero((band == 1) & ~holdout)
        if idx.size:
            k = int(round(spec["review_capacity"][g] * idx.size))
            if k > 0:
                take = idx[np.argsort(-s6[idx])[:k]]
                reviewed[take] = True

        # settlement: allow band, holdout rows, and reviewed-and-released rows
        released = reviewed & (y == 0)          # analysts release what they judge legitimate
        settles = (band == 0) | holdout | released

        # chargeback delay and right-censoring at the extract
        delay = np.clip(
            np.round(np.exp(rng.normal(spec["delay_mu"][g], spec["delay_sd"][g], n))),
            1, spec["delay_cap"],
        ).astype(int)
        cb = settles & (y == 1)
        cb_day = np.where(cb, day + delay, -1)
        cb_seen = cb & (cb_day <= spec["extract_day"])

        parts.append(dict(
            seg=np.full(n, g), day=day, z=z, w=w, y=y, v=v, s6=s6, s7=s7,
            band=band, holdout=holdout, reviewed=reviewed, settles=settles,
            delay=delay, cb=cb, cb_day=cb_day, cb_seen=cb_seen,
        ))

    world = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    world["spec"] = spec
    world["seed"] = seed
    return world


# ----------------------------------------------------------------- truth
def _value_recall(y, v, score, keep, rate):
    """Value-weighted fraud recall when the top `rate` of `score` (within `keep`) is blocked."""
    if keep.sum() == 0:
        return float("nan")
    s, yy, vv = score[keep], y[keep], v[keep]
    thr = np.quantile(s, 1 - rate)
    denom = float((yy * vv).sum())
    if denom <= 0:
        return float("nan")
    return float(((yy * vv) * (s >= thr)).sum() / denom)


def truth(world: dict) -> dict:
    """Value-weighted recall at the fixed evaluation block rate, on the FULL eligible population."""
    spec = world["spec"]
    out = {}
    for g in SEGMENTS:
        keep = world["seg"] == g
        rate = spec["eval_block_rate"][g]
        r6 = _value_recall(world["y"], world["v"], world["s6"], keep, rate)
        r7 = _value_recall(world["y"], world["v"], world["s7"], keep, rate)
        out[f"recall_v6.{g}"] = r6
        out[f"recall_v7.{g}"] = r7
        out[f"delta.{g}"] = r7 - r6
        out[f"adopt.{g}"] = "v7" if (r7 - r6) >= spec["adopt_bar"] else "v6"
    out["decision"] = "|".join(f"{g}:{out[f'adopt.{g}']}" for g in SEGMENTS)
    return out


def observed(world: dict) -> dict:
    """The analyst-visible view: no y, no z/w, no cb_day beyond the extract."""
    spec = world["spec"]
    mature_ok = world["cb_seen"]
    masks = {g: (world["seg"] == g) for g in SEGMENTS}
    seg_i = np.zeros(len(world["day"]), dtype=np.int8)
    for i, g in enumerate(SEGMENTS):
        seg_i[masks[g]] = i
    return dict(
        _mask=masks, seg_i=seg_i,
        seg=world["seg"], day=world["day"], v=world["v"], s6=world["s6"], s7=world["s7"],
        band=world["band"],                      # from the decisions table
        holdout=world["holdout"],                # logged bypass flag
        reviewed=world["reviewed"],              # review queue table
        review_fraud=np.where(world["reviewed"], world["y"], -1),   # verified determination
        settled=world["settles"],
        chargeback=mature_ok,                    # only chargebacks visible by the extract
        cb_day=np.where(mature_ok, world["cb_day"], -1),
        spec=spec,
    )
