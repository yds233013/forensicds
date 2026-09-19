"""G31 Phase-0: accepted estimator families and pre-registered wrong analyses (research only)."""
from __future__ import annotations

import numpy as np

import g31_sim as S

SEGMENTS = S.SEGMENTS


# --------------------------------------------------------------- shared helpers
def maturity_days(ob) -> dict:
    """Per-segment maturity horizon, estimated from fully mature cohorts (99th pct of observed lag)."""
    spec = ob["spec"]
    safe = ob["day"] <= spec["extract_day"] - spec["delay_cap"]
    out = {}
    for g in SEGMENTS:
        sel = safe & (ob["_mask"][g]) & ob["chargeback"]
        lags = (ob["cb_day"] - ob["day"])[sel]
        out[g] = int(np.ceil(np.quantile(lags, 0.99))) if lags.size > 30 else spec["delay_cap"]
    return out


def thresholds(ob) -> dict:
    """Blocking threshold per (model, segment) at the fixed evaluation block rate.

    Scores exist for every row, so this needs no labels and is exact."""
    spec = ob["spec"]
    out = {}
    for g in SEGMENTS:
        sel = ob["_mask"][g]
        for m in ("s6", "s7"):
            out[(m, g)] = np.quantile(ob[m][sel], 1 - spec["eval_block_rate"][g])
    return out


def _recall_from_weighted(yv, w, score, thr):
    """Value-weighted recall from a weighted labelled sample."""
    num = float((w * yv * (score >= thr)).sum())
    den = float((w * yv).sum())
    return num / den if den > 0 else float("nan")


def _pack(rec: dict, spec) -> dict:
    out = dict(rec)
    for g in SEGMENTS:
        d = out[f"recall_v7.{g}"] - out[f"recall_v6.{g}"]
        out[f"delta.{g}"] = d
        out[f"adopt.{g}"] = "v7" if d >= spec["adopt_bar"] else "v6"
    out["decision"] = "|".join(f"{g}:{out[f'adopt.{g}']}" for g in SEGMENTS)
    return out


def _unbiased_sample(ob, T):
    """Rows whose label is observed through a mechanism that is random w.r.t. Y*, with HT weights.

    band 0 : every row settles; resolved iff old enough            -> weight 1
    band>0 : settles only via the logged bypass holdout            -> weight 1/q
    reviewed-and-released rows are excluded: their selection is deterministic in s6.
    """
    spec = ob["spec"]
    age = spec["extract_day"] - ob["day"]
    Tg = np.array([T[g] for g in SEGMENTS])
    seg_i = ob["seg_i"]
    resolved = age >= Tg[seg_i]
    qb = np.array([spec["q_block"][g] for g in SEGMENTS])[seg_i]
    qr = np.array([spec["q_review"][g] for g in SEGMENTS])[seg_i]
    q = np.where(ob["band"] == 2, qb, qr)

    use_allow = (ob["band"] == 0) & resolved
    use_hold = (ob["band"] > 0) & ob["holdout"] & resolved
    use = use_allow | use_hold
    w = np.where(use_hold, 1.0 / q, 1.0)
    y = ob["chargeback"].astype(float)
    return use, w, y


# --------------------------------------------------------------- accepted
def accepted_ht_holdout(ob) -> dict:
    """A1. Horvitz-Thompson: mature allow-band rows + inverse-probability-weighted bypass holdout."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    use, w, y = _unbiased_sample(ob, T)
    rec = {}
    for g in SEGMENTS:
        sel = use & (ob["_mask"][g])
        yv = y[sel] * ob["v"][sel]
        for m, tag in (("s6", "v6"), ("s7", "v7")):
            rec[f"recall_{tag}.{g}"] = _recall_from_weighted(yv, w[sel], ob[m][sel], thr[(m, g)])
    return _pack(rec, spec)


def accepted_poststrat(ob) -> dict:
    """A2. Direct standardisation: fraud-value totals estimated inside segment x v6-decile cells."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    use, w, y = _unbiased_sample(ob, T)
    rec = {}
    for g in SEGMENTS:
        gsel = ob["_mask"][g]
        edges = np.quantile(ob["s6"][gsel], np.linspace(0, 1, 11))
        edges[0], edges[-1] = -np.inf, np.inf
        cell = np.digitize(ob["s6"], edges) - 1
        for m, tag in (("s6", "v6"), ("s7", "v7")):
            num = den = 0.0
            for c in range(10):
                pop = gsel & (cell == c)
                lab = pop & use
                n_pop = float(pop.sum())
                if n_pop == 0 or lab.sum() == 0:
                    continue
                yv = y[lab] * ob["v"][lab]
                ww = w[lab]
                mean_fv = float((ww * yv).sum() / ww.sum())
                mean_fv_hit = float((ww * yv * (ob[m][lab] >= thr[(m, g)])).sum() / ww.sum())
                den += n_pop * mean_fv
                num += n_pop * mean_fv_hit
            rec[f"recall_{tag}.{g}"] = num / den if den > 0 else float("nan")
    return _pack(rec, spec)


def _irls(X, y, w, iters=25):
    beta = np.zeros(X.shape[1])
    for _ in range(iters):
        eta = np.clip(X @ beta, -30, 30)
        mu = 1.0 / (1.0 + np.exp(-eta))
        s = np.clip(mu * (1 - mu), 1e-6, None) * w
        zed = eta + (y - mu) / np.clip(mu * (1 - mu), 1e-6, None)
        XtS = X.T * s
        try:
            beta_new = np.linalg.solve(XtS @ X + 1e-6 * np.eye(X.shape[1]), XtS @ zed)
        except np.linalg.LinAlgError:
            break
        if np.max(np.abs(beta_new - beta)) < 1e-7:
            beta = beta_new
            break
        beta = beta_new
    return beta


def _design(ob, sel):
    """Flexible basis: piecewise-linear splines in both score ranks, their interaction, and log value."""
    a, b = ob["s6"][sel], ob["s7"][sel]
    knots = (0.5, 0.8, 0.95, 0.99)
    cols = [np.ones(sel.sum()), a, b, a * b, np.log(ob["v"][sel])]
    for k in knots:
        cols.append(np.maximum(a - k, 0.0))
        cols.append(np.maximum(b - k, 0.0))
    return np.column_stack(cols)


def accepted_impute(ob) -> dict:
    """A3. Outcome regression: fit P(Y*=1|scores,value) where labels are unbiased, impute everywhere."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    use, w, y = _unbiased_sample(ob, T)
    rec = {}
    for g in SEGMENTS:
        gsel = ob["_mask"][g]
        fit = use & gsel
        beta = _irls(_design(ob, fit), y[fit], w[fit])
        phat = 1.0 / (1.0 + np.exp(-np.clip(_design(ob, gsel) @ beta, -30, 30)))
        fv = phat * ob["v"][gsel]
        for m, tag in (("s6", "v6"), ("s7", "v7")):
            num = float((fv * (ob[m][gsel] >= thr[(m, g)])).sum())
            den = float(fv.sum())
            rec[f"recall_{tag}.{g}"] = num / den if den > 0 else float("nan")
    return _pack(rec, spec)


def accepted_mature_cohort(ob) -> dict:
    """A4. Restrict to cohorts old enough that nothing is censored, then HT. Valid, less efficient."""
    spec = ob["spec"]
    thr = thresholds(ob)
    age = spec["extract_day"] - ob["day"]
    seg_i = ob["seg_i"]
    q = np.where(ob["band"] == 2,
                 np.array([spec["q_block"][g] for g in SEGMENTS])[seg_i],
                 np.array([spec["q_review"][g] for g in SEGMENTS])[seg_i])
    resolved = age >= spec["delay_cap"]
    use = resolved & ((ob["band"] == 0) | (ob["holdout"] & (ob["band"] > 0)))
    w = np.where((ob["band"] > 0) & ob["holdout"], 1.0 / q, 1.0)
    y = ob["chargeback"].astype(float)
    rec = {}
    for g in SEGMENTS:
        sel = use & (ob["_mask"][g])
        yv = y[sel] * ob["v"][sel]
        for m, tag in (("s6", "v6"), ("s7", "v7")):
            rec[f"recall_{tag}.{g}"] = _recall_from_weighted(yv, w[sel], ob[m][sel], thr[(m, g)])
    return _pack(rec, spec)


# --------------------------------------------------------------- wrong
def _naive(ob, labelled, yhat, thr, weights=None):
    rec = {}
    for g in SEGMENTS:
        sel = labelled & (ob["_mask"][g])
        if sel.sum() == 0:
            for tag in ("v6", "v7"):
                rec[f"recall_{tag}.{g}"] = float("nan")
            continue
        w = np.ones(sel.sum()) if weights is None else weights[sel]
        yv = yhat[sel] * ob["v"][sel]
        for m, tag in (("s6", "v6"), ("s7", "v7")):
            rec[f"recall_{tag}.{g}"] = _recall_from_weighted(yv, w, ob[m][sel], thr[(m, g)])
    return rec


def wrong_complete_case(ob) -> dict:
    """W1. Every row with any observed label (chargeback or review determination), as if representative."""
    thr = thresholds(ob)
    lab = ob["chargeback"] | (ob["reviewed"] & (ob["review_fraud"] >= 0)) | (ob["settled"] & ~ob["chargeback"])
    y = np.where(ob["reviewed"], np.maximum(ob["review_fraud"], 0), ob["chargeback"].astype(int)).astype(float)
    return _pack(_naive(ob, lab, y, thr), ob["spec"])


def wrong_age_cutoff_30(ob) -> dict:
    """W2. The legacy readout: settled rows older than 30 days, chargeback within 30 days = fraud."""
    spec = ob["spec"]
    thr = thresholds(ob)
    age = spec["extract_day"] - ob["day"]
    lab = ob["settled"] & (age >= 30)
    y = (ob["chargeback"] & ((ob["cb_day"] - ob["day"]) <= 30)).astype(float)
    return _pack(_naive(ob, lab, y, thr), spec)


def wrong_mature_settled_only(ob) -> dict:
    """W3. Maturity handled correctly, selective non-settlement ignored: allowed rows only."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    age = spec["extract_day"] - ob["day"]
    seg_i = ob["seg_i"]
    Tg = np.array([T[g] for g in SEGMENTS])[seg_i]
    lab = ob["settled"] & (age >= Tg)
    return _pack(_naive(ob, lab, ob["chargeback"].astype(float), thr), spec)


def wrong_reviewed_only(ob) -> dict:
    """W4. Evaluate on manually reviewed cases, which carry the most trustworthy labels."""
    thr = thresholds(ob)
    lab = ob["reviewed"]
    return _pack(_naive(ob, lab, np.maximum(ob["review_fraud"], 0).astype(float), thr), ob["spec"])


def wrong_blocked_is_fraud(ob) -> dict:
    """W5. Treat every blocked authorisation as fraud (the policy blocked it for a reason)."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    age = spec["extract_day"] - ob["day"]
    seg_i = ob["seg_i"]
    Tg = np.array([T[g] for g in SEGMENTS])[seg_i]
    lab = (ob["settled"] & (age >= Tg)) | (ob["band"] == 2)
    y = np.where(ob["band"] == 2, 1.0, ob["chargeback"].astype(float))
    return _pack(_naive(ob, lab, y, thr), spec)


def wrong_unlabelled_is_legit(ob) -> dict:
    """W6. Every row without a positive label counts as legitimate."""
    thr = thresholds(ob)
    lab = np.ones(len(ob["day"]), bool)
    y = np.where(ob["reviewed"], np.maximum(ob["review_fraud"], 0), ob["chargeback"].astype(int)).astype(float)
    return _pack(_naive(ob, lab, y, thr), ob["spec"])


def wrong_ipw_on_v6_score(ob) -> dict:
    """W7. Reweight by the incumbent score band's share rather than the bypass probability."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    age = spec["extract_day"] - ob["day"]
    seg_i = ob["seg_i"]
    Tg = np.array([T[g] for g in SEGMENTS])[seg_i]
    lab = ob["settled"] & (age >= Tg)
    w = np.ones(len(ob["day"]))
    for g in SEGMENTS:
        gsel = ob["_mask"][g]
        for b in (0, 1, 2):
            pop = gsel & (ob["band"] == b)
            labb = pop & lab
            if labb.sum() > 0:
                w[labb] = pop.sum() / labb.sum()
    return _pack(_naive(ob, lab, ob["chargeback"].astype(float), thr, w), spec)


def wrong_pooled_segments(ob) -> dict:
    """W8. Correct correction, but estimated once on the pooled book and applied to every segment."""
    spec = ob["spec"]
    T = maturity_days(ob)
    use, w, y = _unbiased_sample(ob, T)
    pooled = {}
    for m, tag in (("s6", "v6"), ("s7", "v7")):
        thr_pool = np.quantile(ob[m], 1 - np.mean([spec["eval_block_rate"][g] for g in SEGMENTS]))
        yv = y[use] * ob["v"][use]
        pooled[tag] = _recall_from_weighted(yv, w[use], ob[m][use], thr_pool)
    rec = {}
    for g in SEGMENTS:
        rec[f"recall_v6.{g}"] = pooled["v6"]
        rec[f"recall_v7.{g}"] = pooled["v7"]
    return _pack(rec, spec)


def wrong_holdout_only(ob) -> dict:
    """W9. Use only the randomised bypass holdout: unbiased weights, wrong target population."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    age = spec["extract_day"] - ob["day"]
    seg_i = ob["seg_i"]
    Tg = np.array([T[g] for g in SEGMENTS])[seg_i]
    lab = ob["holdout"] & (age >= Tg)
    return _pack(_naive(ob, lab, ob["chargeback"].astype(float), thr), spec)


ACCEPTED = {
    "A1_ht_holdout": accepted_ht_holdout,
    "A2_poststrat": accepted_poststrat,
    "A3_impute": accepted_impute,
    "A4_mature_cohort": accepted_mature_cohort,
}
WRONG = {
    "W1_complete_case": wrong_complete_case,
    "W2_age_cutoff_30": wrong_age_cutoff_30,
    "W3_mature_settled_only": wrong_mature_settled_only,
    "W4_reviewed_only": wrong_reviewed_only,
    "W5_blocked_is_fraud": wrong_blocked_is_fraud,
    "W6_unlabelled_is_legit": wrong_unlabelled_is_legit,
    "W7_ipw_on_v6_band": wrong_ipw_on_v6_score,
    "W8_pooled_segments": wrong_pooled_segments,
    "W9_holdout_only": wrong_holdout_only,
}


def wrong_count_recall(ob) -> dict:
    """W10. Observation process handled correctly, but recall counted per transaction, not per dollar."""
    spec = ob["spec"]
    T = maturity_days(ob)
    thr = thresholds(ob)
    use, w, y = _unbiased_sample(ob, T)
    rec = {}
    for g in SEGMENTS:
        sel = use & (ob["_mask"][g])
        yv = y[sel]                       # unit weight instead of transaction value
        for m, tag in (("s6", "v6"), ("s7", "v7")):
            rec[f"recall_{tag}.{g}"] = _recall_from_weighted(yv, w[sel], ob[m][sel], thr[(m, g)])
    return _pack(rec, spec)


WRONG["W10_count_recall"] = wrong_count_recall
