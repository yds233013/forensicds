"""G36 gates measured on the PACKAGED extract: recognition-vs-execution, same-history,
coherent-wrong, cheap solves, falsification/negative control, leakage.

Research/dev only; no model, no container.
    python tools/g36/packaged_gates.py
"""
from __future__ import annotations

import copy, os, sys, tempfile
from pathlib import Path

import numpy as np

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(R / s))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import world, scenarios                                             # noqa: E402
from capacity_forecast import estimators, load                      # noqa: E402
from analysis_panel import build_fixture, methods, GATE, _ols       # noqa: E402

PILOT_YEAR = 2026
CDD_REF = 10.0

HINTS = {
    "H0 nothing":                                  ["M03_historical_model",
                                                    "M04_latest_window_retrain",
                                                    "M23_seasonal_naive"],
    "H1 pilot response does not transport":        ["M08_selection_fixed_only"],
    "H2 response depends on cooling demand":       ["M09_temperature_fixed_only"],
    "H1+H2 both insights":                         ["V_F1_stratified"],
}


def backtest(fr):
    """Fit the incumbent on the first flat-tariff season, score on the withheld second one."""
    df = fr["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    years = sorted(hist["year"].unique())
    tr, te = hist[hist["year"] == years[0]], hist[hist["year"] == years[-1]]
    errs, ys = [], []
    for s in sorted(df["segment_code"].dropna().unique()):
        h = tr[tr["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"]
        m, n = g.mean(), g.size()
        a, b = _ols(np.column_stack([np.ones(len(m)), m.index.to_numpy(float)]),
                    m.to_numpy(float), w=n.to_numpy(float))
        t = te[te["segment_code"] == s]
        pred = a + b * t["cooling_degree_days"].to_numpy(float)
        errs.append(t["peak_kw"].to_numpy(float) - pred)
        ys.append(t["peak_kw"].to_numpy(float))
    e, y = np.concatenate(errs), np.concatenate(ys)
    return dict(rmse=float(np.sqrt(np.mean(e ** 2))),
                r2=float(1 - np.mean(e ** 2) / np.var(y)), bias=float(e.mean()))


def negative_control(fr):
    """Run the response-estimation pipeline on a PRE-PILOT season, where no tariff existed.

    Enrolled households are split by their eventual pilot arm and compared during a flat-tariff
    season. A correct pipeline must find approximately zero response.
    """
    df = fr["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    pre = hist[hist["assigned_arm"].isin(["treatment", "control"])]
    if pre.empty:
        return None
    # Stratify by segment. Random assignment of ~550 households leaves segment imbalance between
    # the arms, and segment base loads span 1.05 to 3.30 kW, so an unstratified comparison reports
    # a spurious "response" of a few per cent. That is a property of the diagnostic, not of the
    # data: the same stratification the main analysis uses removes it.
    import pandas as pd
    num = den = 0.0
    for s in sorted(pre["segment_code"].dropna().unique()):
        q = pre[pre["segment_code"] == s]
        tt = q[q["assigned_arm"] == "treatment"].groupby("cooling_degree_days")["peak_kw"].mean()
        cc = q[q["assigned_arm"] == "control"].groupby("cooling_degree_days")["peak_kw"].mean()
        j = pd.concat([tt.rename("t"), cc.rename("c")], axis=1).dropna()
        if j.empty:
            continue
        w = q["household_id"].nunique()
        num += w * float(np.mean(1.0 - j["t"] / j["c"]))
        den += w
    return float(num / den) if den else 0.0


def main():
    rows = []
    for name in scenarios.ALL_NAMES:
        w, t, fr = build_fixture(scenarios.by_name(name))
        rows.append((name, w, t, fr, methods(fr)))
    names = [r[0] for r in rows]
    valid_sd = 0.0148

    print("=" * 108)
    print("RECOGNITION-VS-EXECUTION on the packaged extract (the gate G35 failed)")
    print("=" * 108)
    print("Errors in units of the accepted estimator's sampling sd (%.4f).\n" % valid_sd)
    print("%-44s %s  %8s %s" % ("insight given away", "".join("%10s" % n for n in names),
                                "worst", "wrong decisions"))
    for hint, keys in HINTS.items():
        best, bad = [], 0
        for name, w, t, fr, m in rows:
            errs = [(abs(m[k] - t["target_peak_mean"]), k) for k in keys if k in m]
            e, k = min(errs)
            best.append(e)
            d = "procure" if m[k] >= GATE else "defer"
            bad += (d != t["decision"])
        print("%-44s %s  %7.1f sd  %d/5" % (
            hint, "".join("%10.1f" % (v / valid_sd) for v in best), max(best) / valid_sd, bad))

    print()
    print("=" * 108)
    print("SAME-HISTORY / DIFFERENT-FUTURE")
    print("=" * 108)
    print("%-12s %12s %12s %12s %12s %10s" % (
        "fixture", "holdout_RMSE", "holdout_R2", "hist_mean", "TRUTH", "decision"))
    for name, w, t, fr, m in rows:
        b = backtest(fr)
        hm = float(fr["loads"][fr["loads"]["year"] != PILOT_YEAR]["peak_kw"].mean())
        print("%-12s %12.4f %12.4f %12.4f %12.4f %10s" % (
            name, b["rmse"], b["r2"], hm, t["target_peak_mean"], t["decision"]))
    b_, c_ = rows[2], rows[3]
    bb, bc = backtest(b_[3]), backtest(c_[3])
    print("\nthe discriminating pair (identical response magnitude and history generation):")
    print("   holdout RMSE  %.4f vs %.4f  (difference %.4f)" % (
        bb["rmse"], bc["rmse"], abs(bb["rmse"] - bc["rmse"])))
    print("   TRUTH         %.4f vs %.4f  -> %s vs %s" % (
        b_[2]["target_peak_mean"], c_[2]["target_peak_mean"],
        b_[2]["decision"], c_[2]["decision"]))

    print()
    print("=" * 108)
    print("COHERENT-BUT-WRONG: the incumbent production model")
    print("=" * 108)
    print("%-12s %12s %12s %12s %12s %12s" % (
        "fixture", "holdout_R2", "holdout_bias", "forecast", "truth", "error"))
    for name, w, t, fr, m in rows:
        b = backtest(fr)
        print("%-12s %12.4f %12.4f %12.4f %12.4f %12.4f" % (
            name, b["r2"], b["bias"], m["M03_historical_model"], t["target_peak_mean"],
            m["M03_historical_model"] - t["target_peak_mean"]))

    print()
    print("=" * 108)
    print("NEGATIVE CONTROL: response pipeline run on a PRE-PILOT (flat-tariff) season")
    print("=" * 108)
    for name, w, t, fr, m in rows:
        nc = negative_control(fr)
        print("   %-12s estimated tariff response before any tariff existed: %+.5f  %s" % (
            name, nc, "OK (approximately zero)" if abs(nc) < 0.02 else "*** NOT ZERO ***"))

    print()
    print("=" * 108)
    print("REPRESENTATION-LEAKAGE PROBES on the packaged extract")
    print("=" * 108)
    for name, w, t, fr, m in rows:
        cm = fr["customers"].merge(fr["enrolment"], on="household_id", how="left")
        cm["enrolled"] = cm["assigned_arm"].notna()
        # A linear correlation on an alphabetically-coded NOMINAL variable is the wrong statistic
        # and reported a near-zero association even though enrolment differs sevenfold by segment.
        # The selection is reported as an over-representation ratio instead.
        est = cm["segment_code"].value_counts(normalize=True)
        enr = cm[cm["enrolled"]]["segment_code"].value_counts(normalize=True)
        ratios = {s: float(enr.get(s, 0.0) / est[s]) for s in est.index}
        codes = {s: i for i, s in enumerate(sorted(cm["segment_code"].unique()))}
        segnum = cm["segment_code"].map(codes).to_numpy(float)
        r_order = float(np.corrcoef(np.arange(len(cm)), segnum)[0, 1])
        print("   %-12s enrolment over-representation %.2fx to %.2fx | corr(row order, segment)=%+.3f"
              " | n_enrolled=%d" % (name, min(ratios.values()), max(ratios.values()),
                                    r_order, int(cm["enrolled"].sum())))
    print("\n   corr(segment, enrolled) is SUPPOSED to be non-zero: it IS the selection the task is")
    print("   about and the analyst must measure it. Knowing who enrolled does not give the answer.")


if __name__ == "__main__":
    main()
