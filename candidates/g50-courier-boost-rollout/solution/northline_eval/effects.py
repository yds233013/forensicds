"""The programme effect at the unit Boost was assigned at, on the estate-wide basis the memo names."""
import math

import numpy as np
import pandas as pd

from northline_eval import panel, warehouse

T_CRIT_14 = 2.145          # two-sided 95 %, 16 markets less two fitted parameters


def phase2_frame(con):
    o = warehouse.orders(con)
    run, hold, weeks = panel.phase2_markets(con)
    f = o[o["market_id"].isin(run) & o["week_start"].isin(weeks)]
    return f[f["arm"].isin(["boost", "control"])].copy()


def arm_contrast(con):
    f = phase2_frame(con)
    b = f[f["arm"] == "boost"]["is_late"]; c = f[f["arm"] == "control"]["is_late"]
    diff = (b.mean() - c.mean()) * 100.0
    se = math.sqrt(b.var(ddof=1) / len(b) + c.var(ddof=1) / len(c)) * 100.0
    return dict(effect_pp=diff, ci_low_pp=diff - 1.96 * se, ci_high_pp=diff + 1.96 * se, n=int(len(f)))


def phases(con):
    """Phase-1 on/off market groups and the pre-programme and phase-1 week labels."""
    c = warehouse.config(con)
    p1 = c[c["phase"] == "phase1_soak"]
    on = sorted(p1[(p1["status"] == "running") & (p1["boost_share_target"] > 0.5)]["market_id"].unique())
    off = sorted(p1[(p1["status"] == "running") & (p1["boost_share_target"] <= 0.5)]["market_id"].unique())
    soak_weeks = sorted(p1["week_start"].unique())
    pre_weeks = sorted(c[c["phase"] == "pre"]["week_start"].unique())
    return on, off, soak_weeks, pre_weeks


def programme_effect(con):
    """Boost on for every eligible order versus off for all of them.

    Phase 1 set Boost at the market level, so the phase-1 on and off groups differ in exactly the
    quantity the memo names. Markets differ persistently in delivery performance, and with eight
    markets an arm those differences do not balance out, so each market is compared with its own
    pre-programme weeks and the two arms' changes are compared. Markets are weighted by their share of
    pre-programme estate orders, which is the estate-wide basis the memo specifies and which cannot be
    moved by the programme. Inference is at the market, because the market is what was assigned.
    """
    mw = panel.market_week(con)
    on, off, soak_weeks, pre_weeks = phases(con)
    enrolled = list(on) + list(off)
    pre = mw[mw["week_start"].isin(pre_weeks) & mw["market_id"].isin(enrolled)]
    soak = mw[mw["week_start"].isin(soak_weeks) & mw["market_id"].isin(enrolled)]

    def rate(df, m):
        d = df[df["market_id"] == m]
        return d["late_orders"].sum() / d["orders"].sum() * 100.0

    ids = enrolled
    delta = np.array([rate(soak, m) - rate(pre, m) for m in ids])
    weight = np.array([float(pre[pre["market_id"] == m]["orders"].sum()) for m in ids])
    treat = np.array([1.0 if m in on else 0.0 for m in ids])

    X = np.column_stack([np.ones_like(delta), treat])
    Wd = np.diag(weight)
    XtW = X.T @ Wd
    beta = np.linalg.solve(XtW @ X, XtW @ delta)
    resid = delta - X @ beta
    bread = np.linalg.inv(XtW @ X)
    V = bread @ (X.T @ np.diag(weight ** 2 * resid ** 2) @ X) @ bread * len(delta) / (len(delta) - 2)
    se = float(np.sqrt(V[1, 1]))
    eff = float(beta[1])
    return dict(effect_pp=eff, ci_low_pp=eff - T_CRIT_14 * se, ci_high_pp=eff + T_CRIT_14 * se,
                se=se, n_units=int(len(ids)))


def courier_hours_response(con):
    """Courier hours per order with Boost on for every order against off, from phase 1."""
    mw = panel.market_week(con)
    on, off, soak_weeks, _ = phases(con)
    s = mw[mw["week_start"].isin(soak_weeks)]
    a = s[s["market_id"].isin(on)]; b = s[s["market_id"].isin(off)]
    ra = a["courier_hours"].sum() / a["orders"].sum()
    rb = b["courier_hours"].sum() / b["orders"].sum()
    return dict(response_pct=float((ra / rb - 1.0) * 100.0))
