#!/usr/bin/env python3
"""G24 Phase-0 estimator panel: correct estimators, alternatives and natural wrong methods.

Every estimator sees only observable quantities: stream, device, pool item ids, per-candidate eligibility flag and
model scores, served slate, decision-level clicks (and per-serve attribution where a method uses serves), the logged
propensity field, K and m.
"""
from __future__ import annotations

import numpy as np

POLICIES = ("v6", "v7", "v7_pd")
SLOTS = 5


# ------------------------------------------------------------------ helpers (observable reconstructions)


def target_slates(w, prefilter=False):
    """Counterfactual slate per policy: top 5 by model score among eligible items (or ignoring eligibility)."""
    out = {}
    for p in POLICIES:
        mask = w["in_pool"] if prefilter else w["eligible"]
        masked = np.where(mask, w["scores"][p], -np.inf)
        out[p] = np.argsort(-masked, axis=1)[:, :SLOTS]
    return out


def theta_hat(w, idx, pooled=False):
    """Examination curve estimated from the randomized stream: click rate by slot, normalised to slot 1."""
    c = w["clicks"][idx]
    dev = w["dev"][idx]
    if pooled:
        rate = c.mean(0)
        t = rate / rate[0]
        return np.repeat(t[None, :], 3, axis=0)
    out = np.zeros((3, SLOTS))
    for d in range(3):
        rate = c[dev == d].mean(0)
        out[d] = rate / rate[0]
    return out


def reward_model(w, idx, th):
    """Per-item relevance estimated from the randomized stream: clicks / examination exposure (shrunk)."""
    items = np.take_along_axis(w["item"][idx], w["served"][idx], 1).ravel()
    expo = th[w["dev"][idx]].ravel()
    clk = w["clicks"][idx].ravel().astype(float)
    n_items = w["n_items"]
    num = np.bincount(items, weights=clk, minlength=n_items)
    den = np.bincount(items, weights=expo, minlength=n_items)
    prior = clk.sum() / expo.sum()
    return (num + 8.0 * prior) / (den + 8.0)          # shrink towards the global mean


def paired(values_per_decision):
    """Mean, SE and paired lift SEs from per-decision contributions."""
    n = len(next(iter(values_per_decision.values())))
    val = {p: float(v.mean()) for p, v in values_per_decision.items()}
    se = {p: float(v.std(ddof=1) / np.sqrt(n)) for p, v in values_per_decision.items()}
    lift, lift_se = {}, {}
    for p in ("v7", "v7_pd"):
        d = values_per_decision[p] - values_per_decision["v6"]
        lift[p] = float(d.mean())
        lift_se[p] = float(d.std(ddof=1) / np.sqrt(n))
    return dict(value=val, se=se, lift=lift, lift_se=lift_se)


def decision_from(res):
    lo = {p: res["lift"][p] - 1.96 * res["lift_se"][p] for p in ("v7", "v7_pd")}
    ok = [p for p in ("v7", "v7_pd") if lo[p] > 0]
    return max(ok, key=lambda p: res["value"][p]) if ok else "v6"


# ------------------------------------------------------------------ correct estimators


def slot_ips(w, weight="m", clip=None, target_prefilter=False, clicks="decision"):
    """Item-in-slot IPS on exploration decisions: weight = eligible pool size m (1 / (1/m))."""
    idx = np.flatnonzero(w["stream"] == 0)
    tgt = target_slates(w, prefilter=target_prefilter)
    wt = (w["K"] if weight == "K" else w["m"])[idx].astype(float)
    if clip is not None:
        wt = np.minimum(wt, clip)
    if clicks == "decision":
        c = w["clicks"][idx]
    elif clicks == "first_serve":
        c = w["clicks"][idx] * (w["click_serve"][idx] == 0)
    contrib = {}
    for p in POLICIES:
        match = (w["served"][idx] == tgt[p][idx]).astype(float)
        contrib[p] = wt * (c * match).sum(1)
    return paired(contrib)


def pbm_ips(w, pooled_theta=False):
    """Item-anywhere IPS with position transfer: weight m/5, credit theta_target / theta_logged."""
    idx = np.flatnonzero(w["stream"] == 0)
    th = theta_hat(w, idx, pooled=pooled_theta)
    tgt = target_slates(w)
    dev = w["dev"][idx]
    served = w["served"][idx]
    c = w["clicks"][idx]
    wt = w["m"][idx] / SLOTS
    contrib = {}
    for p in POLICIES:
        t = tgt[p][idx]
        # position of each served item inside the target slate (-1 if absent)
        pos = np.full(served.shape, -1)
        for k in range(SLOTS):
            hit = served == t[:, [k]]
            pos = np.where(hit, k, pos)
        ratio = np.where(pos >= 0, th[dev][np.arange(len(idx))[:, None], np.clip(pos, 0, SLOTS - 1)], 0.0)
        logged = th[dev]
        contrib[p] = wt * (c * ratio / logged).sum(1)
    return paired(contrib)


def doubly_robust(w):
    """DR: per-item reward model plus a slot-exact IPS correction on the randomized stream."""
    idx = np.flatnonzero(w["stream"] == 0)
    th = theta_hat(w, idx)
    rhat = reward_model(w, idx, th)
    tgt = target_slates(w)
    dev = w["dev"][idx]
    served = w["served"][idx]
    c = w["clicks"][idx]
    m = w["m"][idx].astype(float)
    contrib = {}
    for p in POLICIES:
        t = tgt[p][idx]
        dm = (th[dev] * rhat[np.take_along_axis(w["item"][idx], t, 1)]).sum(1)
        resid = c - th[dev] * rhat[np.take_along_axis(w["item"][idx], served, 1)]
        match = (served == t).astype(float)
        contrib[p] = dm + m * (resid * match).sum(1)
    return paired(contrib)


def snips(w):
    """Self-normalised slot-exact IPS (correct weights)."""
    idx = np.flatnonzero(w["stream"] == 0)
    tgt = target_slates(w)
    m = w["m"][idx].astype(float)
    c = w["clicks"][idx]
    contrib = {}
    for p in POLICIES:
        match = (w["served"][idx] == tgt[p][idx]).astype(float)
        num = m * (c * match).sum(1)
        den = (m[:, None] * match).sum(1) / SLOTS         # mean is 1 in expectation
        contrib[p] = num / max(den.mean(), 1e-9)
    return paired(contrib)


def onpolicy_mix(w):
    """On-policy means where a stream exists (v6 production, v7 A/B arm), slot-exact IPS for v7_pd."""
    res = slot_ips(w)
    ip = np.flatnonzero(w["stream"] == 1)
    ia = np.flatnonzero(w["stream"] == 2)
    for p, idx in (("v6", ip), ("v7", ia)):
        y = w["clicks"][idx].sum(1).astype(float)
        res["value"][p] = float(y.mean())
        res["se"][p] = float(y.std(ddof=1) / np.sqrt(len(idx)))
    return res          # lifts stay paired (computed on the randomized stream by slot_ips above)


# ------------------------------------------------------------------ natural wrong methods


def replay_gate(w):
    """Production-log replay: match target items anywhere in the logged slate; CTR over matched impressions x 5."""
    idx = np.flatnonzero(w["stream"] == 1)
    tgt = target_slates(w)
    served, c = w["served"][idx], w["clicks"][idx]
    out, se = {}, {}
    for p in POLICIES:
        t = tgt[p][idx]
        match = np.zeros(served.shape, bool)
        for k in range(SLOTS):
            match |= served == t[:, [k]]
        ctr = c[match].mean() if match.any() else 0.0
        out[p] = float(SLOTS * ctr)
        se[p] = float(SLOTS * c[match].std(ddof=1) / np.sqrt(match.sum()))
    lift = {p: out[p] - out["v6"] for p in ("v7", "v7_pd")}
    lift_se = {p: float(np.sqrt(se[p] ** 2 + se["v6"] ** 2)) for p in ("v7", "v7_pd")}
    return dict(value=out, se=se, lift=lift, lift_se=lift_se)


def logged_propensity_snips(w, floor=1e-5):
    """The notebook path: IPS with the logged (pre-filter, slate-level) propensity, clipped, self-normalised,
    item-anywhere matching."""
    idx = np.flatnonzero(w["stream"] == 0)
    tgt = target_slates(w)
    wt = 1.0 / np.maximum(w["logged_propensity"][idx], floor)
    served, c = w["served"][idx], w["clicks"][idx]
    contrib = {}
    for p in POLICIES:
        t = tgt[p][idx]
        match = np.zeros(served.shape, bool)
        for k in range(SLOTS):
            match |= served == t[:, [k]]
        contrib[p] = SLOTS * wt * (c * match).sum(1) / wt.mean()
    return paired(contrib)


def item_anywhere_unaware(w):
    """Exploration, item-anywhere match, weight m/5, no position transfer."""
    idx = np.flatnonzero(w["stream"] == 0)
    tgt = target_slates(w)
    served, c = w["served"][idx], w["clicks"][idx]
    wt = w["m"][idx] / SLOTS
    contrib = {}
    for p in POLICIES:
        t = tgt[p][idx]
        match = np.zeros(served.shape, bool)
        for k in range(SLOTS):
            match |= served == t[:, [k]]
        contrib[p] = wt * (c * match).sum(1)
    return paired(contrib)


def serves_as_units(w):
    """Correct weights and matching, but every serve is treated as an independent decision."""
    idx = np.flatnonzero(w["stream"] == 0)
    tgt = target_slates(w)
    served, c, ns = w["served"][idx], w["clicks"][idx], w["n_serves"][idx]
    cs = w["click_serve"][idx]
    m = w["m"][idx].astype(float)
    rows, contrib = [], {p: [] for p in POLICIES}
    max_s = int(ns.max())
    for s in range(max_s):
        sel = ns > s
        rows.append(sel.sum())
        cc = (c * (cs == s))[sel]
        for p in POLICIES:
            match = (served[sel] == tgt[p][idx][sel]).astype(float)
            contrib[p].append(m[sel] * (cc * match).sum(1))
    return paired({p: np.concatenate(v) for p, v in contrib.items()})


def slate_match_replay(w):
    """Exploration replay restricted to decisions where the target slate was served exactly (no weights)."""
    idx = np.flatnonzero(w["stream"] == 0)
    tgt = target_slates(w)
    served, c = w["served"][idx], w["clicks"][idx]
    out, se = {}, {}
    for p in POLICIES:
        hit = (served == tgt[p][idx]).all(1)
        y = c[hit].sum(1).astype(float)
        out[p] = float(y.mean()) if hit.sum() > 1 else 0.0
        se[p] = float(y.std(ddof=1) / np.sqrt(hit.sum())) if hit.sum() > 1 else float("inf")
    lift = {p: out[p] - out["v6"] for p in ("v7", "v7_pd")}
    lift_se = {p: float(np.sqrt(se[p] ** 2 + se["v6"] ** 2)) for p in ("v7", "v7_pd")}
    return dict(value=out, se=se, lift=lift, lift_se=lift_se)


def direct_method(w):
    """Reward model only: plug estimated per-item relevance into target slates."""
    idx = np.flatnonzero(w["stream"] == 0)
    th = theta_hat(w, idx)
    rhat = reward_model(w, idx, th)
    tgt = target_slates(w)
    dev = w["dev"][idx]
    contrib = {p: (th[dev] * rhat[np.take_along_axis(w["item"][idx], tgt[p][idx], 1)]).sum(1) for p in POLICIES}
    return paired(contrib)


PANEL_CORRECT = {
    "slot_ips": lambda w: slot_ips(w),
    "pbm_ips": pbm_ips,
    "doubly_robust": doubly_robust,
    "snips": snips,
    "onpolicy_mix": onpolicy_mix,
    "pooled_theta": lambda w: pbm_ips(w, pooled_theta=True),   # empirically unbiased here: accepted, not a trap
}

PANEL_WRONG = {
    "replay_gate": replay_gate,
    "logged_propensity_snips": logged_propensity_snips,
    "weight_K_prefilter": lambda w: slot_ips(w, weight="K"),
    "serves_as_units": serves_as_units,
    "item_anywhere_unaware": item_anywhere_unaware,
    "keep_first_serve": lambda w: slot_ips(w, clicks="first_serve"),
    "target_prefilter": lambda w: slot_ips(w, target_prefilter=True),
    "clipped_weights": lambda w: slot_ips(w, clip=10.0),
    "direct_method": direct_method,
    "slate_match_replay": slate_match_replay,
}
