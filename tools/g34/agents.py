"""G34 wrong-agent panel: each is a deterministic, self-contained analysis over the same extract."""
from __future__ import annotations
import numpy as np, pandas as pd

H = 36.0
OUT = ("UNPL_FAIL", "PM_OVHL", "ASSET_RET")


def _shares(t, kind, horizon=H, treat_as_removal=OUT):
    order = np.argsort(t); t, kind = t[order], kind[order]
    n = len(t); still = 1.0; acc = {o: 0.0 for o in OUT}; i = 0
    while i < n and t[i] <= horizon:
        q = t[i]; j = i
        while j < n and t[j] == q: j += 1
        at_risk = n - i; removed = 0
        for o in treat_as_removal:
            d = int((kind[i:j] == o).sum())
            if d:
                acc[o] = acc.get(o, 0.0) + still * d / at_risk; removed += d
        still *= 1.0 - removed / at_risk; i = j
    acc["still_original"] = still
    return acc


def _km(t, ev, horizon=H):
    order = np.argsort(t); t, ev = t[order], ev[order]
    n = len(t); S = 1.0; i = 0
    while i < n and t[i] <= horizon:
        q = t[i]; j = i
        while j < n and t[j] == q: j += 1
        d = int(ev[i:j].sum()); S *= 1.0 - d / (n - i); i = j
    return 1.0 - S


def oracle(df):
    t = df["exit_age"].to_numpy(float); k = df["wo_type"].to_numpy(object)
    s = _shares(t, k)
    return dict(q1=s["UNPL_FAIL"], ovhl=s["PM_OVHL"], ret=s["ASSET_RET"], surv=s["still_original"],
                q2=_km(t, k == "UNPL_FAIL"))


def A_polished_1km(df):
    """A. the incumbent: 1-KM per outcome, each censoring the others."""
    t = df["exit_age"].to_numpy(float); k = df["wo_type"].to_numpy(object)
    f = _km(t, k == "UNPL_FAIL")
    return dict(q1=f, ovhl=_km(t, k == "PM_OVHL"), ret=_km(t, k == "ASSET_RET"), surv=1 - f, q2=f)


def B_one_line_aj(df):
    """B. recognises competing risks, treats ONLY overhaul as competing; retirement censored."""
    t = df["exit_age"].to_numpy(float); k = df["wo_type"].to_numpy(object)
    k2 = np.where(k == "ASSET_RET", "", k)
    s = _shares(t, k2)
    return dict(q1=s["UNPL_FAIL"], ovhl=s["PM_OVHL"], ret=s.get("ASSET_RET", 0.0),
                surv=s["still_original"], q2=_km(t, k == "UNPL_FAIL"))


def C_raw_rate(df):
    """C. raw event fractions of the installed base."""
    k = df["wo_type"].to_numpy(object); t = df["exit_age"].to_numpy(float); n = len(k)
    f = float(((k == "UNPL_FAIL") & (t <= H)).sum()) / n
    return dict(q1=f, ovhl=float(((k == "PM_OVHL") & (t <= H)).sum()) / n,
                ret=float(((k == "ASSET_RET") & (t <= H)).sum()) / n, surv=1 - f, q2=f)


def D_mature_only(df):
    """D. only units with a completed record (a work order)."""
    d = df[df["wo_type"] != ""]
    t = d["exit_age"].to_numpy(float); k = d["wo_type"].to_numpy(object)
    s = _shares(t, k)
    return dict(q1=s["UNPL_FAIL"], ovhl=s["PM_OVHL"], ret=s["ASSET_RET"], surv=s["still_original"],
                q2=_km(t, k == "UNPL_FAIL"))


def E_gap_censoring(df):
    """E. a telemetry outage is treated as loss of the unit: censor at gap start."""
    t = df["exit_age"].to_numpy(float).copy(); k = df["wo_type"].to_numpy(object).copy()
    g = df["first_gap_age"].to_numpy(float)
    hit = np.isfinite(g) & (g < t)
    t[hit] = g[hit]; k[hit] = ""
    s = _shares(t, k)
    return dict(q1=s["UNPL_FAIL"], ovhl=s["PM_OVHL"], ret=s["ASSET_RET"], surv=s["still_original"],
                q2=_km(t, k == "UNPL_FAIL"))


def F_all_exits_competing(df):
    """F. every record end treated as a competing outcome, administrative cut-off included."""
    t = df["exit_age"].to_numpy(float); k = df["wo_type"].to_numpy(object)
    k2 = np.where(k == "", "ASSET_RET", k)
    s = _shares(t, k2)
    return dict(q1=s["UNPL_FAIL"], ovhl=s["PM_OVHL"], ret=s["ASSET_RET"], surv=s["still_original"],
                q2=_km(t, k == "UNPL_FAIL"))


def G_cumulative_hazard(df):
    """G. cumulative cause-specific hazard read as a probability."""
    t = df["exit_age"].to_numpy(float); k = df["wo_type"].to_numpy(object)
    tot = 0.0
    for a in np.arange(0, H, 1.0):
        at = int((t > a).sum())
        if at == 0: break
        tot += int(((t > a) & (t <= a + 1) & (k == "UNPL_FAIL")).sum()) / at
    o = oracle(df)
    return dict(q1=tot, ovhl=o["ovhl"], ret=o["ret"], surv=1 - tot, q2=tot)


def H_swap_q1_q2(df):
    """H. correct machinery, the two business objects swapped."""
    o = oracle(df)
    return dict(q1=o["q2"], ovhl=o["ovhl"], ret=o["ret"], surv=o["surv"], q2=o["q1"])


AGENTS = {"A_polished_1km": A_polished_1km, "B_one_line_aj": B_one_line_aj, "C_raw_rate": C_raw_rate,
          "D_mature_only": D_mature_only, "E_gap_censoring": E_gap_censoring,
          "F_all_exits_competing": F_all_exits_competing, "G_cumulative_hazard": G_cumulative_hazard,
          "H_swap_q1_q2": H_swap_q1_q2}


def V_oldest_cohort(df):
    """VALID variation (not a wrong analysis): correct estimators restricted to units observed
    for the full horizon.  Sidesteps administrative censoring by discarding most of the fleet."""
    full = df["age_at_cut_off"].to_numpy(float) >= H
    t = df["exit_age"].to_numpy(float)[full]; k = df["wo_type"].to_numpy(object)[full]
    s = _shares(t, k)
    return dict(q1=s["UNPL_FAIL"], ovhl=s["PM_OVHL"], ret=s["ASSET_RET"], surv=s["still_original"],
                q2=_km(t, k == "UNPL_FAIL"))


VALID_VARIATIONS = {"V_oldest_cohort": V_oldest_cohort}
