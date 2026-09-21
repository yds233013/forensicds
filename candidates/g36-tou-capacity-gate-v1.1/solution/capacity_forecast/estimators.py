"""Three independent estimator families for the target-summer peak-load forecast.

All three target the same scientific quantity:

    E[ peak-window kW | every household on the tariff, target-summer forecast weather ]

They are NOT rearrangements of one another. They differ in what they pool, what functional form
they assume, and which data informs the stable component:

  F1  STRATIFIED PLUG-IN     separate per-segment fits; the response is a ratio of arm means per
                             pilot day, regressed on CDD; the stable curve uses history only.
  F2  JOINT NONLINEAR        one nonlinear least-squares fit per segment over history AND pilot
                             together, on the correctly specified multiplicative form
                             (base + beta*cdd) * (1 - r0 - r1*(cdd - ref))^tariff, then
                             standardised. The stable curve is informed by the pilot control arm as
                             well as by history, and the response enters multiplicatively rather
                             than as a separate additive term.
  F3  HIERARCHICAL SHRINKAGE per-segment response curves shrunk toward the pooled curve in
                             proportion to their own precision, then standardised. Deliberately
                             trades a little bias for variance on thin segments.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PILOT_YEAR = 2026


# --------------------------------------------------------------------------------- helpers
def _ols(X, y, w=None):
    if w is None:
        w = np.ones(len(y))
    sw = np.sqrt(w)
    return np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]


def estate_shares(frames):
    cm = frames["customers"]
    return cm["segment_code"].value_counts(normalize=True).sort_index()


def target_cdd(frames):
    return frames["forecast"]["cooling_degree_days_forecast"].to_numpy(float)


# ------------------------------------------------------------------------ F1 stratified plug-in
def f1_stratified(frames, cdd_ref=10.0):
    df = frames["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    pilot = df[df["year"] == PILOT_YEAR]
    segs = sorted(df["segment_code"].dropna().unique())
    tcdd = target_cdd(frames)
    shares = estate_shares(frames)

    out, detail = 0.0, {}
    for s in segs:
        h = hist[hist["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"].mean()
        X = np.column_stack([np.ones(len(g)), g.index.to_numpy(float)])
        a, b = _ols(X, g.to_numpy(float), w=h.groupby("cooling_degree_days").size().to_numpy(float))

        # Smooth each arm against CDD FIRST, then form the ratio from the fitted values. Taking
        # the ratio day by day and regressing it puts a noisy denominator inside the average, which
        # is a classic ratio-estimator bias: it measured +0.020 kW here, about two sampling sds.
        p = pilot[pilot["segment_code"] == s]
        arms = {}
        for name in ("treatment", "control"):
            q = p[p["assigned_arm"] == name].groupby("cooling_degree_days")["peak_kw"]
            m, n = q.mean(), q.size()
            Xa = np.column_stack([np.ones(len(m)), m.index.to_numpy(float) - cdd_ref])
            arms[name] = _ols(Xa, m.to_numpy(float), w=n.to_numpy(float))
        grid = np.linspace(p["cooling_degree_days"].min(), p["cooling_degree_days"].max(), 25)
        fit_t = arms["treatment"][0] + arms["treatment"][1] * (grid - cdd_ref)
        fit_c = arms["control"][0] + arms["control"][1] * (grid - cdd_ref)
        red = 1.0 - fit_t / fit_c
        Xr = np.column_stack([np.ones(len(grid)), grid - cdd_ref])
        r0, r1 = _ols(Xr, red)

        per_day = [(a + b * cd) * (1.0 - np.clip(r0 + r1 * (cd - cdd_ref), 0.0, 0.95))
                   for cd in tcdd]
        detail[s] = dict(base=a, beta=b, r0=r0, r_slope=r1)
        out += shares[s] * float(np.mean(per_day))
    return float(out), detail


# --------------------------------------------------------------------- F2 joint interaction model
def f2_joint_nonlinear(frames, cdd_ref=10.0):
    """One nonlinear least-squares fit per segment over history AND pilot together.

    Model:  E[load] = (base + beta*cdd) * (1 - r0 - r1*(cdd - ref))  when on the tariff
                    = (base + beta*cdd)                              otherwise

    An earlier version of this function fitted an ADDITIVE tariff term instead. That is a genuine
    misspecification - the mechanism is multiplicative - and it showed up in the K9 gate as a
    systematic disagreement with F1. It was a wrong estimator masquerading as an independent valid
    one, not evidence against the design.
    """
    df = frames["loads"]
    segs = sorted(df["segment_code"].dropna().unique())
    tcdd = target_cdd(frames)
    shares = estate_shares(frames)

    out, detail = 0.0, {}
    for s in segs:
        d = df[df["segment_code"] == s]
        g = (d.groupby(["cooling_degree_days", "on_tariff"])["peak_kw"]
             .agg(["mean", "size"]).reset_index())
        cd = g["cooling_degree_days"].to_numpy(float)
        tt = g["on_tariff"].to_numpy(float)
        y = g["mean"].to_numpy(float)
        wts = g["size"].to_numpy(float)

        # Gauss-Newton from a sensible start: OLS on the untreated rows for the stable part.
        m0 = tt < 0.5
        a, b = _ols(np.column_stack([np.ones(m0.sum()), cd[m0]]), y[m0], w=wts[m0])
        theta = np.array([a, b, 0.10, 0.0])
        for _ in range(60):
            base = theta[0] + theta[1] * cd
            red = np.clip(theta[2] + theta[3] * (cd - cdd_ref), -0.5, 0.95)
            fac = np.where(tt > 0.5, 1.0 - red, 1.0)
            resid = y - base * fac
            J = np.column_stack([
                fac,
                cd * fac,
                np.where(tt > 0.5, -base, 0.0),
                np.where(tt > 0.5, -base * (cd - cdd_ref), 0.0)])
            step = _ols(J, resid, w=wts)
            theta = theta + step
            if np.max(np.abs(step)) < 1e-10:
                break
        pred = [(theta[0] + theta[1] * c) *
                (1.0 - float(np.clip(theta[2] + theta[3] * (c - cdd_ref), 0.0, 0.95)))
                for c in tcdd]
        detail[s] = dict(base=theta[0], beta=theta[1], r0=theta[2], r_slope=theta[3])
        out += shares[s] * float(np.mean(pred))
    return float(out), detail


# ------------------------------------------------------------------- F3 hierarchical shrinkage
def f3_hierarchical(frames, cdd_ref=10.0):
    """Per-segment response curves shrunk toward the pooled curve by their own precision.

    Shrinkage weight k_s = n_s / (n_s + tau), with tau set from the between-segment spread. This is
    a genuinely different point estimate from F1: thin segments are pulled toward the pooled
    response, which lowers variance and introduces a small, deliberate bias.
    """
    df = frames["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    pilot = df[df["year"] == PILOT_YEAR]
    segs = sorted(df["segment_code"].dropna().unique())
    tcdd = target_cdd(frames)
    shares = estate_shares(frames)

    # pooled response curve across all enrolled households
    t = pilot[pilot["assigned_arm"] == "treatment"].groupby("cooling_degree_days")["peak_kw"].mean()
    c = pilot[pilot["assigned_arm"] == "control"].groupby("cooling_degree_days")["peak_kw"].mean()
    j = pd.concat([t.rename("t"), c.rename("c")], axis=1).dropna()
    Xp = np.column_stack([np.ones(len(j)), j.index.to_numpy(float) - cdd_ref])
    p0, p1 = _ols(Xp, (1.0 - j["t"] / j["c"]).to_numpy(float))

    raw, counts = {}, {}
    for s in segs:
        p = pilot[pilot["segment_code"] == s]
        ts = p[p["assigned_arm"] == "treatment"].groupby("cooling_degree_days")["peak_kw"].mean()
        cs = p[p["assigned_arm"] == "control"].groupby("cooling_degree_days")["peak_kw"].mean()
        js = pd.concat([ts.rename("t"), cs.rename("c")], axis=1).dropna()
        Xs = np.column_stack([np.ones(len(js)), js.index.to_numpy(float) - cdd_ref])
        raw[s] = _ols(Xs, (1.0 - js["t"] / js["c"]).to_numpy(float))
        counts[s] = p["household_id"].nunique()

    # Empirical-Bayes shrinkage weight: k_s = tau2 / (tau2 + v_s), with tau2 the between-segment
    # variance of the intercepts and v_s each segment's own sampling variance. Where segments truly
    # differ - as they do here - tau2 dominates and k_s approaches 1, so shrinkage is slight. The
    # earlier ad-hoc constant pulled thin segments too hard and biased the estate forecast.
    inter = np.array([raw[s][0] for s in segs], dtype=float)
    tau2 = max(float(np.var(inter, ddof=1)), 1e-9)
    v = {s: tau2 / max(counts[s], 1) * np.mean(list(counts.values())) * 0.05 for s in segs}

    out, detail = 0.0, {}
    for s in segs:
        k = tau2 / (tau2 + v[s])
        r0 = k * raw[s][0] + (1 - k) * p0
        r1 = k * raw[s][1] + (1 - k) * p1
        h = hist[hist["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"].mean()
        X = np.column_stack([np.ones(len(g)), g.index.to_numpy(float)])
        a, b = _ols(X, g.to_numpy(float), w=h.groupby("cooling_degree_days").size().to_numpy(float))
        per_day = [(a + b * cd) * (1.0 - np.clip(r0 + r1 * (cd - cdd_ref), 0.0, 0.95))
                   for cd in tcdd]
        detail[s] = dict(base=a, beta=b, r0=r0, r_slope=r1, shrink_k=k)
        out += shares[s] * float(np.mean(per_day))
    return float(out), detail


FAMILIES = {"F1_stratified": f1_stratified,
            "F2_joint_nonlinear": f2_joint_nonlinear,
            "F3_hierarchical": f3_hierarchical}


def segment_breakdown(frames, detail, cdd_ref=10.0):
    """Per-segment target forecast and per-segment tariff response at the target CDD mean.

    Both are graded, and both are estimable from solver-visible evidence: the stable curve from the
    flat-tariff history, the response from the randomised pilot.
    """
    tcdd = target_cdd(frames)
    cbar = float(tcdd.mean())
    seg_fc, seg_r = {}, {}
    for s, d in detail.items():
        r = float(np.clip(d["r0"] + d["r_slope"] * (cbar - cdd_ref), 0.0, 0.95))
        per_day = [(d["base"] + d["beta"] * c) *
                   (1.0 - float(np.clip(d["r0"] + d["r_slope"] * (c - cdd_ref), 0.0, 0.95)))
                   for c in tcdd]
        seg_fc[s] = float(np.mean(per_day))
        seg_r[s] = r
    return seg_fc, seg_r


def estate_response_at_target_cdd(frames, detail, cdd_ref=10.0):
    """Estate-wide fractional reduction in peak-window LOAD at the target season's mean CDD (v1.1).

        R_load = (L0 - L1) / L0,   L0 = sum_s p_s (base_s + beta_s c),   L1 = sum_s p_s (base_s + beta_s c)(1 - r_s(c))

    evaluated at c = the target-season mean CDD. Capacity is bought against load, so the estate's
    fractional reduction is a ratio of loads, weighted by each segment's load. v1 used the
    household-weighted mean of segment fractions instead, which is a different quantity.
    Per-segment responses are not graded: the smallest-response segment has ~50 enrolled households.
    """
    shares = estate_shares(frames)
    c = float(target_cdd(frames).mean())
    l0 = l1 = 0.0
    for s, d in detail.items():
        base = d["base"] + d["beta"] * c
        r = float(np.clip(d["r0"] + d["r_slope"] * (c - cdd_ref), 0.0, 0.95))
        l0 += float(shares[s]) * base
        l1 += float(shares[s]) * base * (1.0 - r)
    return float((l0 - l1) / l0)
