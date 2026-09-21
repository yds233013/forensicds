"""G36 wrong-method panel, cheap-solve panel, recognition gate and same-history gate,
all measured on the PACKAGED extract (correct-table conditions).

Research/dev only; no model, no container.
    python tools/g36/analysis_panel.py
"""
from __future__ import annotations

import copy, os, sys, tempfile
from pathlib import Path

import numpy as np
import pandas as pd

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(R / s))
import world, scenarios                                             # noqa: E402
from capacity_forecast import estimators, load                      # noqa: E402

GATE = 3.057
PILOT_YEAR = 2026
CDD_REF = 10.0


def _ols(X, y, w=None):
    w = np.ones(len(y)) if w is None else w
    sw = np.sqrt(w)
    return np.linalg.lstsq(X * sw[:, None], y * sw, rcond=None)[0]


def build_fixture(spec):
    w = world.build(spec)
    t = world.truth(w)
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"), exist_ok=True)
    db = world.write_sqlite(w, os.path.join(d, "data"))
    return w, t, load.frames(Path(db))


def methods(fr):
    """Every analysis operates on the SAME perfectly correct table. The only mistake available is
    a scientific one."""
    df = fr["loads"]
    hist = df[df["year"] != PILOT_YEAR]
    pilot = df[df["year"] == PILOT_YEAR]
    segs = sorted(df["segment_code"].dropna().unique())
    tcdd = estimators.target_cdd(fr)
    cbar = float(tcdd.mean())
    shares = estimators.estate_shares(fr)
    out = {}

    stable = {}
    for s in segs:
        h = hist[hist["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"]
        m, n = g.mean(), g.size()
        stable[s] = _ols(np.column_stack([np.ones(len(m)), m.index.to_numpy(float)]),
                         m.to_numpy(float), w=n.to_numpy(float))

    # per-segment response curve from the randomised pilot (arms smoothed before the ratio)
    curve, enrolled_n = {}, {}
    for s in segs:
        p = pilot[pilot["segment_code"] == s]
        enrolled_n[s] = p["household_id"].nunique()
        arm = {}
        for name in ("treatment", "control"):
            q = p[p["assigned_arm"] == name].groupby("cooling_degree_days")["peak_kw"]
            m, n = q.mean(), q.size()
            arm[name] = _ols(np.column_stack([np.ones(len(m)), m.index.to_numpy(float) - CDD_REF]),
                             m.to_numpy(float), w=n.to_numpy(float))
        grid = np.linspace(p["cooling_degree_days"].min(), p["cooling_degree_days"].max(), 25)
        ft = arm["treatment"][0] + arm["treatment"][1] * (grid - CDD_REF)
        fc = arm["control"][0] + arm["control"][1] * (grid - CDD_REF)
        curve[s] = _ols(np.column_stack([np.ones(len(grid)), grid - CDD_REF]), 1.0 - ft / fc)

    def r_at(s, cdd):
        return float(np.clip(curve[s][0] + curve[s][1] * (cdd - CDD_REF), 0.0, 0.95))

    def compose(weights, use_resp, cdd_for_resp=None):
        tot = 0.0
        for s in segs:
            a, b = stable[s]
            if use_resp:
                per = [(a + b * c) * (1 - r_at(s, cdd_for_resp if cdd_for_resp else c))
                       for c in tcdd]
            else:
                per = [(a + b * c) for c in tcdd]
            tot += weights[s] * float(np.mean(per))
        return tot

    pop = {s: float(shares[s]) for s in segs}
    enr_tot = sum(enrolled_n.values())
    enr = {s: enrolled_n[s] / enr_tot for s in segs}

    # ---------------- VALID
    out["V_F1_stratified"] = estimators.f1_stratified(fr)[0]
    out["V_F2_joint_nonlinear"] = estimators.f2_joint_nonlinear(fr)[0]
    out["V_F3_hierarchical"] = estimators.f3_hierarchical(fr)[0]

    # ---------------- WRONG
    out["M03_historical_model"] = compose(pop, False)
    last = hist[hist["year"] == hist["year"].max()]
    tot = 0.0
    for s in segs:
        h = last[last["segment_code"] == s]
        g = h.groupby("cooling_degree_days")["peak_kw"]
        m, n = g.mean(), g.size()
        a, b = _ols(np.column_stack([np.ones(len(m)), m.index.to_numpy(float)]),
                    m.to_numpy(float), w=n.to_numpy(float))
        tot += pop[s] * float(np.mean(a + b * tcdd))
    out["M04_latest_window_retrain"] = tot
    out["M05_historical_only_mean"] = float(hist["peak_kw"].mean())
    out["M06_pilot_mean"] = float(pilot[pilot["assigned_arm"] == "treatment"]["peak_kw"].mean())

    pt = pilot[pilot["assigned_arm"] == "treatment"]["peak_kw"].mean()
    pc = pilot[pilot["assigned_arm"] == "control"]["peak_kw"].mean()
    out["M07_pilot_effect_applied_flat"] = out["M03_historical_model"] * (pt / pc)

    pilot_cbar = float(pilot["cooling_degree_days"].mean())
    out["M08_selection_fixed_only"] = compose(pop, True, cdd_for_resp=pilot_cbar)
    out["M09_temperature_fixed_only"] = compose(enr, True)
    out["M10_pilot_population_forecast"] = compose(enr, True, cdd_for_resp=pilot_cbar)

    lvl = sum(pop[s] * float(pilot[(pilot["segment_code"] == s) &
                                   (pilot["assigned_arm"] == "treatment")]["peak_kw"].mean() or 0)
              for s in segs)
    out["M11_reweight_outcomes_not_response"] = lvl
    out["M12_intercept_recalibration"] = out["M03_historical_model"] + (
        pc - float(hist["peak_kw"].mean()))
    eq = {s: 1.0 / len(segs) for s in segs}
    out["M13_wrong_segment_weights"] = compose(eq, True)
    out["M14_response_averaged_over_cdd"] = compose(
        pop, True, cdd_for_resp=float(np.mean([pilot_cbar, cbar])))
    hist_cbar = float(hist["cooling_degree_days"].mean())
    tot = 0.0
    for s in segs:
        a, b = stable[s]
        tot += pop[s] * (a + b * hist_cbar) * (1 - r_at(s, hist_cbar))
    out["M15_target_weather_ignored"] = tot
    out["M16_historical_weather_for_target"] = tot
    out["M17_mediator_control"] = out["M03_historical_model"]
    agg = 1.0 - pt / pc
    out["M18_aggregate_effect_uniform"] = out["M03_historical_model"] * (1 - agg)
    out["M22_dashboard_copy"] = out["M03_historical_model"]
    out["M23_seasonal_naive"] = float(hist["peak_kw"].mean())
    out["M24_latest_value"] = float(last["peak_kw"].mean())
    out["M26_no_response_at_all"] = compose(pop, False)
    out["M27_double_counted_response"] = compose(pop, True) * (1 - float(
        sum(pop[s] * r_at(s, cbar) for s in segs)))
    return out


def main():
    rows = []
    for name in scenarios.ALL_NAMES:
        w, t, fr = build_fixture(scenarios.by_name(name))
        rows.append((name, t, methods(fr)))
    names = [r[0] for r in rows]
    keys = list(rows[0][2].keys())

    print("=" * 112)
    print("WRONG-METHOD PANEL on the packaged extract (correct-table conditions)")
    print("=" * 112)
    print("%-36s %s   %s" % ("method", "".join("%13s" % n for n in names), "wrong decisions"))
    print("%-36s %s" % ("TRUTH", "".join("%13.4f" % r[1]["target_peak_mean"] for r in rows)))
    print("%-36s %s" % ("TRUTH decision",
                        "".join("%13s" % r[1]["decision"][:7] for r in rows)))
    print("-" * 112)
    summary = {}
    for k in keys:
        line, bad = "", 0
        for name, t, m in rows:
            err = m[k] - t["target_peak_mean"]
            d = "procure" if m[k] >= GATE else "defer"
            if d != t["decision"]:
                bad += 1
            line += "%13s" % ("%+.4f%s" % (err, "*" if d != t["decision"] else " "))
        summary[k] = bad
        print("%-36s %s   %d/5" % (k, line, bad))
    print("\n(values are ERROR against latent truth; * marks a wrong procurement decision)")
    print("\nvalid methods with any wrong decision: %s" %
          ([k for k in keys if k.startswith("V_") and summary[k] > 0] or "none"))
    print("wrong methods with NO wrong decision : %s" %
          ([k for k in keys if not k.startswith("V_") and summary[k] == 0] or "none"))


if __name__ == "__main__":
    main()
