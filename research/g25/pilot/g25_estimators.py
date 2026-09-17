"""G25 Phase-0 estimators: accepted ways to handle unjudged slots, and the natural wrong ones (research only)."""
from __future__ import annotations

import numpy as np

import g25_sim as S

GAIN = S.GAIN


def _audit_gains(w, restrict_to_unlabelled: bool):
    """Gains observed by the audit round, optionally restricted to slots still unlabelled after resolution."""
    q, k = w["audit"][:, 0], w["audit"][:, 1]
    g = GAIN[w["B"]["grade"][q, k]]
    if restrict_to_unlabelled:
        keep = w["B"]["unlabelled"][q, k]
        return g[keep], k[keep]
    return g, k


def _observed_gain(w, r, fill):
    """Gain matrix where labelled slots use their resolved grade and unlabelled slots use `fill` (scalar or per-rank)."""
    g = GAIN[w[r]["grade"]].astype(float)
    u = w[r]["unlabelled"]
    if np.isscalar(fill):
        return np.where(u, fill, g)
    return np.where(u, np.asarray(fill)[None, :], g)


def _score(w, gain_A, gain_B, idcg):
    a = float(np.mean(S._dcg(gain_A) / idcg))
    b = float(np.mean(S._dcg(gain_B) / idcg))
    return {"A": a, "B": b, "delta": b - a,
            "decision": "pass" if b - a >= w["spec"]["threshold"] else "block"}


# ------------------------------------------------------------------ accepted
def accepted_global_mean(w):
    """Expected gain for unjudged slots = mean gain of audit pairs still unlabelled after resolution."""
    g, _ = _audit_gains(w, True)
    m = float(g.mean())
    idcg = S._idcg(w)
    return _score(w, _observed_gain(w, "A", m), _observed_gain(w, "B", m), idcg)


def accepted_rank_bucket(w):
    """Same, stratified into three rank buckets."""
    g, k = _audit_gains(w, True)
    buckets = [(0, 3), (3, 6), (6, 10)]
    fill = np.zeros(w["k"])
    for lo, hi in buckets:
        sel = (k >= lo) & (k < hi)
        fill[lo:hi] = g[sel].mean() if sel.sum() > 20 else g.mean()
    idcg = S._idcg(w)
    return _score(w, _observed_gain(w, "A", fill), _observed_gain(w, "B", fill), idcg)


def accepted_bootstrap(w, draws: int = 200, seed: int = 7):
    """Mean NDCG over bootstrap draws of the restricted audit sample."""
    g, _ = _audit_gains(w, True)
    rng = np.random.default_rng(seed)
    idcg = S._idcg(w)
    accs = []
    for _ in range(draws):
        m = float(g[rng.integers(0, len(g), len(g))].mean())
        accs.append(_score(w, _observed_gain(w, "A", m), _observed_gain(w, "B", m), idcg))
    out = {r: float(np.mean([a[r] for a in accs])) for r in ("A", "B")}
    out["delta"] = out["B"] - out["A"]
    out["decision"] = "pass" if out["delta"] >= w["spec"]["threshold"] else "block"
    return out


def _idcg_with(w, gain_A, gain_B):
    pool = np.concatenate([gain_A, gain_B, GAIN[w["ideal"]].astype(float)], axis=1)
    pool = -np.sort(-pool, axis=1)[:, : w["k"]]
    return S._dcg(pool)


def accepted_expected_idcg(w):
    """Specified convention: expected gain in DCG and in the ideal pool."""
    g, _ = _audit_gains(w, True)
    m = float(g.mean())
    gain_A, gain_B = _observed_gain(w, "A", m), _observed_gain(w, "B", m)
    return _score(w, gain_A, gain_B, _idcg_with(w, gain_A, gain_B))


# ------------------------------------------------------------------ wrong
def wrong_unjudged_zero(w):
    """Unjudged slots count as not relevant."""
    idcg = S._idcg(w)
    return _score(w, _observed_gain(w, "A", 0.0), _observed_gain(w, "B", 0.0), idcg)


def wrong_condensed(w):
    """Condensed lists: drop unjudged slots and promote the rest."""
    idcg = S._idcg(w)
    out = {}
    for r in ("A", "B"):
        g = GAIN[w[r]["grade"]].astype(float)
        keep = ~w[r]["unlabelled"]
        cond = np.zeros_like(g)
        for i in range(g.shape[0]):
            v = g[i][keep[i]]
            cond[i, : len(v)] = v
        out[r] = cond
    return _score(w, out["A"], out["B"], idcg)


def wrong_frame_mean(w):
    """Expected gain estimated from the whole audit frame (includes pairs that resolution labels)."""
    g, _ = _audit_gains(w, False)
    m = float(g.mean())
    idcg = S._idcg(w)
    return _score(w, _observed_gain(w, "A", m), _observed_gain(w, "B", m), idcg)


def wrong_labelled_mean(w):
    """Impute with the mean gain of labelled slots (equivalent to condensing in expectation)."""
    idcg = S._idcg(w)
    fills = {r: float(GAIN[w[r]["grade"]][~w[r]["unlabelled"]].mean()) for r in ("A", "B")}
    return _score(w, _observed_gain(w, "A", fills["A"]), _observed_gain(w, "B", fills["B"]), idcg)


def accepted_rank_bucket_ei(w):
    """Rank-bucket expected gain, specified IDCG convention."""
    g, k = _audit_gains(w, True)
    buckets = [(0, 3), (3, 6), (6, 10)]
    fill = np.zeros(w["k"])
    for lo, hi in buckets:
        sel = (k >= lo) & (k < hi)
        fill[lo:hi] = g[sel].mean() if sel.sum() > 20 else g.mean()
    gain_A, gain_B = _observed_gain(w, "A", fill), _observed_gain(w, "B", fill)
    idcg = _idcg_with(w, gain_A, gain_B)
    return _score(w, gain_A, gain_B, idcg)


def accepted_bootstrap_ei(w, draws: int = 100, seed: int = 7):
    """Bootstrap over the restricted audit sample, specified IDCG convention."""
    g, _ = _audit_gains(w, True)
    rng = np.random.default_rng(seed)
    accs = []
    for _ in range(draws):
        m = float(g[rng.integers(0, len(g), len(g))].mean())
        gain_A, gain_B = _observed_gain(w, "A", m), _observed_gain(w, "B", m)
        accs.append(_score(w, gain_A, gain_B, _idcg_with(w, gain_A, gain_B)))
    out = {r: float(np.mean([a[r] for a in accs])) for r in ("A", "B")}
    out["delta"] = out["B"] - out["A"]
    out["decision"] = "pass" if out["delta"] >= w["spec"]["threshold"] else "block"
    return out


def wrong_plugin_idcg(w):
    """Ideal pool built from determined grades only (the other IDCG convention; the gate doc specifies otherwise)."""
    g, _ = _audit_gains(w, True)
    m = float(g.mean())
    idcg = S._idcg(w)
    return _score(w, _observed_gain(w, "A", m), _observed_gain(w, "B", m), idcg)


def wrong_idcg_excludes_imputed(w):
    """Imputed gains in DCG but the ideal pool built only from labelled slots."""
    g, _ = _audit_gains(w, True)
    m = float(g.mean())
    pool = np.concatenate([np.where(w["A"]["unlabelled"], 0.0, GAIN[w["A"]["grade"]]),
                           np.where(w["B"]["unlabelled"], 0.0, GAIN[w["B"]["grade"]]),
                           GAIN[w["ideal"]].astype(float)], axis=1)
    pool = -np.sort(-pool, axis=1)[:, : w["k"]]
    idcg = S._dcg(pool)
    return _score(w, _observed_gain(w, "A", m), _observed_gain(w, "B", m), idcg)


def wrong_drop_incomplete_queries(w):
    """Evaluate only queries whose lists are fully labelled."""
    keep = ~(w["A"]["unlabelled"].any(1) | w["B"]["unlabelled"].any(1))
    idcg = S._idcg(w)[keep]
    a = float(np.mean(S._dcg(GAIN[w["A"]["grade"]][keep]) / idcg))
    b = float(np.mean(S._dcg(GAIN[w["B"]["grade"]][keep]) / idcg))
    return {"A": a, "B": b, "delta": b - a,
            "decision": "pass" if b - a >= w["spec"]["threshold"] else "block"}


# The release-gate document specifies the metric completely, including the ideal ordering: imputed slots contribute
# their expected gain in DCG and enter the ideal pool with that same expected gain. `accepted_expected_idcg` is that
# convention; `plugin_idcg` (ideal pool from determined grades only) is therefore NOT an accepted variant and is
# listed among the wrong analyses.
ACCEPTED = {"global_mean": accepted_expected_idcg, "rank_bucket": accepted_rank_bucket_ei,
            "bootstrap": accepted_bootstrap_ei}
WRONG = {"unjudged_zero": wrong_unjudged_zero, "condensed": wrong_condensed, "frame_mean": wrong_frame_mean,
         "labelled_mean": wrong_labelled_mean, "idcg_excludes_imputed": wrong_idcg_excludes_imputed,
         "plugin_idcg": wrong_plugin_idcg, "drop_incomplete_queries": wrong_drop_incomplete_queries}
