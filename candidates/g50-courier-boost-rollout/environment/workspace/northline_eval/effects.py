"""Programme effect and the checks the programme readout reports."""
import math

import pandas as pd

from northline_eval import panel, warehouse


def phase2_frame(con):
    """Metric-population phase-2 orders in enrolled markets, with their arm."""
    o = warehouse.orders(con)
    run, hold, weeks = panel.phase2_markets(con)
    f = o[o["market_id"].isin(run) & o["week_start"].isin(weeks)]
    return f[f["arm"].isin(["boost", "control"])].copy()


def arm_contrast(con):
    """Late-rate difference between the phase-2 arms, with a two-proportion interval."""
    f = phase2_frame(con)
    b = f[f["arm"] == "boost"]["is_late"]
    c = f[f["arm"] == "control"]["is_late"]
    diff = (b.mean() - c.mean()) * 100.0
    se = math.sqrt(b.var(ddof=1) / len(b) + c.var(ddof=1) / len(c)) * 100.0
    return dict(effect_pp=diff, ci_low_pp=diff - 1.96 * se, ci_high_pp=diff + 1.96 * se,
                n_boost=int(len(b)), n_control=int(len(c)), n=int(len(f)))


def sample_ratio_check(con):
    """Realised boost share against the configured target, per market-week."""
    f = phase2_frame(con)
    cfg = warehouse.config(con)
    cfg = cfg[cfg["phase"] == "phase2_order_randomised"][["market_id", "week_start",
                                                          "boost_share_target"]]
    got = (f.assign(b=(f["arm"] == "boost").astype(int))
             .groupby(["market_id", "week_start"], as_index=False)
             .agg(n=("b", "size"), realised=("b", "mean")))
    m = got.merge(cfg, on=["market_id", "week_start"], how="left")
    m["z"] = (m["realised"] - m["boost_share_target"]) / (
        (m["boost_share_target"] * (1 - m["boost_share_target"]) / m["n"]) ** 0.5)
    return dict(max_abs_z=float(m["z"].abs().max()), market_weeks=int(len(m)))


def pre_period_balance(con):
    """Pre-programme late rate of the enrolled markets against the never-enrolled markets."""
    b = warehouse.baseline(con)
    run, hold, _ = panel.phase2_markets(con)
    b["late_rate_pct"] = b["late_orders"] / b["orders"] * 100.0
    e = b[b["market_id"].isin(run)]
    h = b[b["market_id"].isin(hold)]
    return dict(enrolled_pre_late_pct=float((e["late_orders"].sum() / e["orders"].sum()) * 100),
                holdout_pre_late_pct=float((h["late_orders"].sum() / h["orders"].sum()) * 100))


def courier_hours_by_arm(con):
    """Courier hours available to each arm's orders, as a capacity balance check."""
    f = phase2_frame(con)
    ch = warehouse.courier_hours(con)
    key = ["market_id", "order_date", "hour"]
    h = ch.rename(columns={"shift_date": "order_date", "hour_start": "hour"})
    j = f.merge(h[key + ["courier_hours"]], on=key, how="left")
    per = j.groupby("arm")["courier_hours"].mean()
    boost, control = float(per.get("boost", float("nan"))), float(per.get("control", float("nan")))
    return dict(boost=boost, control=control,
                pct_gap=(boost / control - 1.0) * 100.0 if control else float("nan"))


def control_vs_holdout(con):
    """Phase-2 control-arm late rate against the never-enrolled markets over the same weeks."""
    o = warehouse.orders(con)
    run, hold, weeks = panel.phase2_markets(con)
    ctl = o[(o["market_id"].isin(run)) & (o["week_start"].isin(weeks)) & (o["arm"] == "control")]
    ho = o[(o["market_id"].isin(hold)) & (o["week_start"].isin(weeks))]
    return dict(control_late_pct=float(ctl["is_late"].mean() * 100),
                holdout_late_pct=float(ho["is_late"].mean() * 100),
                difference_pp=float((ctl["is_late"].mean() - ho["is_late"].mean()) * 100))


def by_market(con):
    f = phase2_frame(con)
    g = (f.groupby(["market_id", "arm"])["is_late"].mean().unstack() * 100.0)
    g["effect_pp"] = g["boost"] - g["control"]
    return g.reset_index()
