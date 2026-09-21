"""G34 semantic audit F/G/H: deterministic counterexample search against the FROZEN verifier's numeric
checks. Research-only; imports G34's world/scenarios read-only; writes nothing inside the task.

The verifier is replicated in-process (tests/test_reliability.py): five quantities within
TOL_MULTIPLIER x SE_REF on each of the four extracts, aftermarket outcomes sum to 1 (0.01), the
recommendation equals the latent decision, and on the visible extract only, the engineering-minus-
aftermarket gap exceeds half the true gap. Bookkeeping fields are always filled correctly here so that
each method is judged on its interpretation alone.

    python tools/g34_audit/counterexamples.py
"""
from __future__ import annotations

import json, math, os, sqlite3, sys, tempfile
from pathlib import Path

import numpy as np
import pandas as pd

T = Path("/Users/yashshah2311/forensicds/candidates/g34-fleet-reliability-gate")
sys.path.insert(0, str(T / "tests"))
import world, scenarios                                             # noqa: E402

H, GATE, MONTH = 36.0, 0.28, 30.4375
QK = ("unplanned_failure_rate_36m", "overhaul_rate_36m", "retirement_rate_36m",
      "still_original_assembly_36m", "assembly_failure_rate_36m")
TK = {"unplanned_failure_rate_36m": "cif_failure_36", "overhaul_rate_36m": "cif_overhaul_36",
      "retirement_rate_36m": "cif_retirement_36", "still_original_assembly_36m": "survival_36",
      "assembly_failure_rate_36m": "q2_net_failure_36"}
CAUSES = ("UNPL_FAIL", "PM_OVHL", "ASSET_RET")


# ------------------------------------------------------------------------------ data
def frame(db):
    con = sqlite3.connect(db)
    a = pd.read_sql_query("SELECT unit_id, model_code, site_id, commissioned_on FROM asset_register", con)
    w = pd.read_sql_query("SELECT unit_id, wo_date, wo_type FROM work_orders", con)
    g = pd.read_sql_query("SELECT unit_id, MIN(gap_start) AS gap0 FROM telemetry_status GROUP BY unit_id", con)
    cut = pd.Timestamp(con.execute("SELECT value FROM extract_meta WHERE key='extract_cut_off'").fetchone()[0])
    con.close()
    df = a.merge(w, on="unit_id", how="left").merge(g, on="unit_id", how="left")
    c = pd.to_datetime(df["commissioned_on"])
    df["age_cut"] = (cut - c).dt.days / MONTH
    df["exit"] = ((pd.to_datetime(df["wo_date"]) - c).dt.days / MONTH).fillna(df["age_cut"])
    df["code"] = df["wo_type"].fillna("")
    df["gap_age"] = (pd.to_datetime(df["gap0"]) - c).dt.days / MONTH
    return df


# ------------------------------------------------------------------------------ estimators
def aj(t, code, h=H):
    """Aalen-Johansen CIFs and all-cause KM survival at h."""
    o = np.argsort(t, kind="mergesort"); t, code = t[o], code[o]
    n, S, cif, i = len(t), 1.0, {k: 0.0 for k in CAUSES}, 0
    while i < n and t[i] <= h:
        j = i
        while j < n and t[j] == t[i]:
            j += 1
        r = n - i
        for k in CAUSES:
            cif[k] += S * np.sum(code[i:j] == k) / r
        S *= 1 - np.sum(code[i:j] != "") / r
        i = j
    return cif, S


def km_event(t, ev, h=H):
    o = np.argsort(t, kind="mergesort"); t, ev = t[o], ev[o]
    n, S, i = len(t), 1.0, 0
    while i < n and t[i] <= h:
        j = i
        while j < n and t[j] == t[i]:
            j += 1
        S *= 1 - ev[i:j].sum() / (n - i)
        i = j
    return 1 - S


def na_event(t, ev, h=H):
    o = np.argsort(t, kind="mergesort"); t, ev = t[o], ev[o]
    n, Hc, i = len(t), 0.0, 0
    while i < n and t[i] <= h:
        j = i
        while j < n and t[j] == t[i]:
            j += 1
        Hc += ev[i:j].sum() / (n - i)
        i = j
    return 1 - math.exp(-Hc)


def weibull_mle(t, ev, h=H):
    from scipy.optimize import minimize
    t = np.maximum(t, 1e-6)
    def nll(p):
        k, lam = math.exp(p[0]), math.exp(p[1])
        z = (t / lam) ** k
        return -(np.sum(ev * (math.log(k) - math.log(lam) + (k - 1) * np.log(t / lam))) - np.sum(z))
    r = minimize(nll, [math.log(2.0), math.log(40.0)], method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-9, "maxiter": 5000})
    k, lam = math.exp(r.x[0]), math.exp(r.x[1])
    return 1 - math.exp(-(h / lam) ** k)


def correct(df):
    t, c = df["exit"].to_numpy(float), df["code"].to_numpy(object)
    cif, S = aj(t, c)
    return {"unplanned_failure_rate_36m": cif["UNPL_FAIL"], "overhaul_rate_36m": cif["PM_OVHL"],
            "retirement_rate_36m": cif["ASSET_RET"], "still_original_assembly_36m": S,
            "assembly_failure_rate_36m": km_event(t, c == "UNPL_FAIL")}


def aftermarket_from(q1, qo, qr, s):
    return {"unplanned_failure_rate_36m": q1, "overhaul_rate_36m": qo,
            "retirement_rate_36m": qr, "still_original_assembly_36m": s}


# ------------------------------------------------------------------------------ interpretations
# (label, legitimacy fixed BEFORE scoring, function df -> full output of the five quantities)
def m_crude_any_age(df):
    n = len(df); p = {k: float((df["code"] == k).sum()) / n for k in CAUSES}
    out = correct(df)
    out.update(aftermarket_from(p["UNPL_FAIL"], p["PM_OVHL"], p["ASSET_RET"], float((df["code"] == "").sum()) / n))
    return out


def m_admin_as_surviving(df):
    n = len(df); p = {k: float(((df["code"] == k) & (df["exit"] <= H)).sum()) / n for k in CAUSES}
    out = correct(df)
    out.update(aftermarket_from(p["UNPL_FAIL"], p["PM_OVHL"], p["ASSET_RET"], 1 - sum(p.values())))
    return out


def m_incumbent_km_all(df):
    t, c = df["exit"].to_numpy(float), df["code"].to_numpy(object)
    f, o, r = (km_event(t, c == k) for k in CAUSES)
    return {"unplanned_failure_rate_36m": f, "overhaul_rate_36m": o, "retirement_rate_36m": r,
            "still_original_assembly_36m": 1 - f, "assembly_failure_rate_36m": f}


def m_incumbent_km_forced_sum(df):
    """competing events treated as censoring for Q1, but 'fixed up' so the four sum to one."""
    t, c = df["exit"].to_numpy(float), df["code"].to_numpy(object)
    out = correct(df)
    f = km_event(t, c == "UNPL_FAIL")
    rest = out["overhaul_rate_36m"] + out["retirement_rate_36m"]
    out.update(aftermarket_from(f, rest and out["overhaul_rate_36m"] * (1 - f - out["still_original_assembly_36m"]) / rest,
                                rest and out["retirement_rate_36m"] * (1 - f - out["still_original_assembly_36m"]) / rest,
                                out["still_original_assembly_36m"]))
    return out


def m_complete_cohort(df):
    d = df[df["age_cut"] >= H]; n = len(d)
    p = {k: float(((d["code"] == k) & (d["exit"] <= H)).sum()) / n for k in CAUSES}
    out = correct(df)
    out.update(aftermarket_from(p["UNPL_FAIL"], p["PM_OVHL"], p["ASSET_RET"], 1 - sum(p.values())))
    return out


def m_actuarial_monthly(df):
    """Life table with monthly intervals, censored units at risk for half the interval."""
    S, cif = 1.0, {k: 0.0 for k in CAUSES}
    t, c = df["exit"].to_numpy(float), df["code"].to_numpy(object)
    for m in range(36):
        at = t > m
        inside = at & (t <= m + 1)
        cens = inside & (c == "")
        r = at.sum() - 0.5 * cens.sum()
        dk = {k: (inside & (c == k)).sum() for k in CAUSES}
        for k in CAUSES:
            cif[k] += S * dk[k] / r
        S *= 1 - sum(dk.values()) / r
    tf = km_event(t, c == "UNPL_FAIL")
    return {"unplanned_failure_rate_36m": cif["UNPL_FAIL"], "overhaul_rate_36m": cif["PM_OVHL"],
            "retirement_rate_36m": cif["ASSET_RET"], "still_original_assembly_36m": S,
            "assembly_failure_rate_36m": tf}


def _strat(df, col, equal):
    groups = sorted(df[col].unique()); outs, w = [], []
    for g in groups:
        outs.append(correct(df[df[col] == g])); w.append(1.0 if equal else float((df[col] == g).mean()))
    w = np.array(w) / np.sum(w)
    return {q: float(sum(wi * o[q] for wi, o in zip(w, outs))) for q in QK}


def m_strat_model_share(df): return _strat(df, "model_code", False)
def m_strat_model_equal(df): return _strat(df, "model_code", True)
def m_strat_site_equal(df): return _strat(df, "site_id", True)


def m_today_running_forward(df):
    """'today's installed base' read as units still running: mean forward probability of an unplanned
    failure before age 36 given survival to the current age (AJ-based)."""
    t, c = df["exit"].to_numpy(float), df["code"].to_numpy(object)
    o = np.argsort(t, kind="mergesort"); ts, cs = t[o], c[o]
    n = len(ts); S, F = 1.0, 0.0; tt, SS, FF = [0.0], [1.0], [0.0]; i = 0
    while i < n and ts[i] <= H:
        j = i
        while j < n and ts[j] == ts[i]:
            j += 1
        r = n - i
        F += S * np.sum(cs[i:j] == "UNPL_FAIL") / r
        S *= 1 - np.sum(cs[i:j] != "") / r
        tt.append(ts[i]); SS.append(S); FF.append(F); i = j
    tt, SS, FF = np.array(tt), np.array(SS), np.array(FF)
    F36 = FF[-1]
    vals = []
    for a in df[df["code"] == ""]["age_cut"].to_numpy(float):
        if a >= H:
            vals.append(0.0); continue
        k = np.searchsorted(tt, a, side="right") - 1
        vals.append((F36 - FF[k]) / SS[k] if SS[k] > 0 else 0.0)
    out = correct(df)
    q1 = float(np.mean(vals))
    out["unplanned_failure_rate_36m"] = q1
    return out


def m_gap_as_failure(df):
    d = df.copy()
    m = d["gap_age"].notna() & (d["gap_age"] < d["exit"])
    d.loc[m, "exit"] = d.loc[m, "gap_age"]; d.loc[m, "code"] = "UNPL_FAIL"
    return correct(d)


def m_gap_as_censoring(df):
    d = df.copy()
    m = d["gap_age"].notna() & (d["gap_age"] < d["exit"])
    d.loc[m, "exit"] = d.loc[m, "gap_age"]; d.loc[m, "code"] = ""
    return correct(d)


# ---- engineering-quantity (Q2) alternatives; aftermarket kept correct
def q2(fn):
    def f(df):
        out = correct(df); out["assembly_failure_rate_36m"] = float(fn(df)); return out
    return f


E = lambda df: (df["exit"].to_numpy(float), df["code"].to_numpy(object))
Q2_ALT = {
    "E02_q2_equals_cif": ("wrong", q2(lambda df: correct(df)["unplanned_failure_rate_36m"])),
    "E03_retired_as_never_failing": ("wrong", q2(lambda df: km_event(
        np.where(df["code"] == "ASSET_RET", 1e9, df["exit"].to_numpy(float)), (df["code"] == "UNPL_FAIL").to_numpy()))),
    "E04_overhauled_as_never_failing": ("wrong", q2(lambda df: km_event(
        np.where(df["code"] == "PM_OVHL", 1e9, df["exit"].to_numpy(float)), (df["code"] == "UNPL_FAIL").to_numpy()))),
    "E05_nelson_aalen": ("legitimate", q2(lambda df: na_event(df["exit"].to_numpy(float), (df["code"] == "UNPL_FAIL").to_numpy()))),
    "E06_weibull_mle": ("legitimate", q2(lambda df: weibull_mle(df["exit"].to_numpy(float), (df["code"] == "UNPL_FAIL").to_numpy(float)))),
    "E07_fail_given_not_removed": ("wrong", q2(lambda df: (lambda o: o["unplanned_failure_rate_36m"] /
        (o["unplanned_failure_rate_36m"] + o["still_original_assembly_36m"]))(correct(df)))),
    "E08_horizon_24": ("wrong", q2(lambda df: km_event(df["exit"].to_numpy(float), (df["code"] == "UNPL_FAIL").to_numpy(), 24.0))),
    "E09_complete_case_denominator": ("wrong", q2(lambda df: float(((df["code"] == "UNPL_FAIL") & (df["exit"] <= H)).sum()) /
        float((((df["code"] == "UNPL_FAIL") & (df["exit"] <= H)) | (df["exit"] > H)).sum()))),
    "E10_km_complete_cohort": ("legitimate", q2(lambda df: km_event(df[df["age_cut"] >= H]["exit"].to_numpy(float),
        (df[df["age_cut"] >= H]["code"] == "UNPL_FAIL").to_numpy()))),
    "E11_one_minus_allcause_survival": ("wrong", q2(lambda df: 1 - correct(df)["still_original_assembly_36m"])),
    "E12_crude_fail_over_N": ("wrong", q2(lambda df: float(((df["code"] == "UNPL_FAIL") & (df["exit"] <= H)).sum()) / len(df))),
}

METHODS = {
    "V00_correct_aj_km": ("legitimate", correct),
    "C01_crude_any_age": ("wrong", m_crude_any_age),
    "C02_admin_censored_as_surviving": ("wrong", m_admin_as_surviving),
    "C03_incumbent_competing_as_censoring": ("wrong", m_incumbent_km_all),
    "C04_competing_as_censoring_forced_sum": ("wrong", m_incumbent_km_forced_sum),
    "C05_complete_followup_cohort": ("legitimate", m_complete_cohort),
    "C06_actuarial_monthly": ("legitimate", m_actuarial_monthly),
    "C07_stratified_model_share_weights": ("legitimate", m_strat_model_share),
    "C08_stratified_model_equal_weights": ("ambiguous", m_strat_model_equal),
    "C09_stratified_site_equal_weights": ("ambiguous", m_strat_site_equal),
    "C10_today_running_forward_q1": ("ambiguous", m_today_running_forward),
    "C11_telemetry_gap_as_failure": ("wrong", m_gap_as_failure),
    "C12_telemetry_gap_as_censoring": ("wrong", m_gap_as_censoring),
}
METHODS.update(Q2_ALT)


# ------------------------------------------------------------------------------ verifier replica
def verdict(out, truth, fx):
    fails, et = [], {}
    for q in QK:
        tol = scenarios.TOL_MULTIPLIER * scenarios.SE_REF[fx][q]
        e = abs(out[q] - truth[TK[q]]); et[q] = e / tol
        if e > tol:
            fails.append(q)
    s = sum(out[q] for q in QK[:4])
    if abs(s - 1) > 0.01:
        fails.append("sum_to_one")
    dec = "expanded" if out["unplanned_failure_rate_36m"] > GATE else "baseline"
    if dec != truth["decision"]:
        fails.append("recommendation")
    if fx == "visible":
        gap = out["assembly_failure_rate_36m"] - out["unplanned_failure_rate_36m"]
        if not gap > 0.5 * (truth["q2_net_failure_36"] - truth["cif_failure_36"]):
            fails.append("two_objects_gap")
    return fails, et, dec


def main():
    fxs = {}
    for name in scenarios.ALL_NAMES:
        w = world.build(scenarios.by_name(name)); t = world.truth(w)
        d = tempfile.mkdtemp(); db = world.write_sqlite(w, d)
        fxs[name] = (frame(db), t)

    res = {"fixtures": {}, "methods": {}}
    print("DECISION / TOLERANCE COMPATIBILITY (Q1 vs 28% gate)")
    for name, (df, t) in fxs.items():
        tol = scenarios.TOL_MULTIPLIER * scenarios.SE_REF[name]["unplanned_failure_rate_36m"]
        dist = abs(t["cif_failure_36"] - GATE)
        res["fixtures"][name] = {k: t[k] for k in TK.values()} | {"decision": t["decision"], "q1_tol": tol, "dist_to_gate": dist,
                                "n": len(df), "complete_cohort_n": int((df["age_cut"] >= H).sum())}
        print("  %-9s q1=%.4f  gate=0.28  |q1-gate|=%.4f  tol=%.4f  ratio dist/tol=%5.2f  %s  q2=%.4f tol_q2=%.4f  %s" % (
            name, t["cif_failure_36"], dist, tol, dist / tol, "OK" if tol < dist else "FLAG",
            t["q2_net_failure_36"], scenarios.TOL_MULTIPLIER * scenarios.SE_REF[name]["assembly_failure_rate_36m"], t["decision"]))

    print("\nCOUNTEREXAMPLES (reward under the frozen G34 verifier's numeric checks)")
    for m, (kind, fn) in METHODS.items():
        rows, reward = {}, 1
        for name, (df, t) in fxs.items():
            out = fn(df)
            fails, et, dec = verdict(out, t, name)
            if fails:
                reward = 0
            rows[name] = {"fails": fails, "err_tol": et, "decision": dec,
                          "values": {q: float(out[q]) for q in QK}}
        rej = [f for f, r in rows.items() if r["fails"]]
        res["methods"][m] = {"kind": kind, "reward": reward, "rejecting_fixtures": rej, "fixtures": rows}
        worst = {f: max(r["err_tol"].values()) for f, r in rows.items()}
        print("  %-40s %-10s reward=%d  rejected by %d/4 %-32s max err/tol per fx %s" % (
            m, kind, reward, len(rej), ",".join(rej),
            " ".join("%s:%.2f" % (f[:8], worst[f]) for f in scenarios.ALL_NAMES)))
    Path("/Users/yashshah2311/forensicds/research/g34/counterexamples.json").write_text(json.dumps(res, indent=1, default=float) + "\n")


if __name__ == "__main__":
    main()
