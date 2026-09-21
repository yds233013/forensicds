"""G36-v1.1 forecast-only scientific sufficiency gate + counterexample search (research/dev only).

Scores every mutation and every counterexample MODELLING route against the PROPOSED v1.1 reward,
with the estate response removed from reward. No container, no model, no saved Gemini submission.

Reward-bearing checks reproduced in-process (they mirror tests/test_capacity.py for v1.1):
  per graded extract (visible + 4 hidden): |target_peak_kw - truth| <= 2.5 x SE_REF (frozen v1),
  procurement_decision == truth decision, bookkeeping exact (n, shares, target CDD mean);
  visible only: schema keys and segment reconciliation (0.02 kW).

    python tools/g36_v11/forecast_sufficiency.py
"""
from __future__ import annotations

import json, os, sqlite3, sys, tempfile
from pathlib import Path

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate-v1.1")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(R / s))
sys.path.insert(0, str(Path(__file__).parent))
import world, scenarios                                             # noqa: E402
import make_mutations as mm                                         # noqa: E402

TOL_MULT = 2.5                                                      # frozen v1 forecast multiplier
GATE = 3.057
L0 = "float(np.mean([stable[s][0] + stable[s][1] * c for c in tcdd]))"
L0E = "sum(pop[s] * %s for s in segs)" % L0

# ---------------------------------------------------------------- counterexample MODELLING routes
# Each is a wrong (or deliberately alternative) way to MODEL the tariff response inside the forecast,
# written before any of them was scored. "kind" is fixed here, before scoring.
CE = {
    "CE01_constant_fraction_ratio_of_means": ("wrong", dict(EXTRA=(
        "    _rc = {s: 1 - float(pilot[(pilot.segment_code == s) & (pilot.assigned_arm == 'treatment')].peak_kw.mean())\n"
        "                / float(pilot[(pilot.segment_code == s) & (pilot.assigned_arm == 'control')].peak_kw.mean()) for s in segs}\n"
        "    seg_fc = {s: %s * (1 - _rc[s]) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)") % L0)),
    "CE02_constant_absolute_kw": ("wrong", dict(EXTRA=(
        "    _dk = {s: float(pilot[(pilot.segment_code == s) & (pilot.assigned_arm == 'control')].peak_kw.mean())\n"
        "            - float(pilot[(pilot.segment_code == s) & (pilot.assigned_arm == 'treatment')].peak_kw.mean()) for s in segs}\n"
        "    seg_fc = {s: %s - _dk[s] for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)") % L0)),
    "CE03_plugin_at_target_mean_cdd": ("wrong", dict(EXTRA=(
        "    seg_fc = {s: (stable[s][0] + stable[s][1] * cbar) * (1 - r_at(s, cbar)) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)"))),
    "CE04_pilot_mean_cdd_transported": ("wrong", dict(RC="pilot_cbar")),
    "CE05_household_weighted_response_in_forecast": ("wrong", dict(EXTRA=(
        "    total = %s * (1 - sum(pop[s] * r_at(s, cbar) for s in segs))") % L0E)),
    "CE06_segment_unweighted_response_in_forecast": ("wrong", dict(EXTRA=(
        "    total = %s * (1 - sum(r_at(s, cbar) for s in segs) / len(segs))") % L0E)),
    "CE07_pooled_response_curve": ("wrong", dict(EXTRA=(
        "    _arm = {}\n"
        "    for _nm in ('treatment', 'control'):\n"
        "        _q = pilot[pilot['assigned_arm'] == _nm].groupby('cooling_degree_days')['peak_kw']\n"
        "        _m, _n = _q.mean(), _q.size()\n"
        "        _arm[_nm] = _ols(np.column_stack([np.ones(len(_m)), _m.index.to_numpy(float) - CDD_REF]), _m.to_numpy(float), w=_n.to_numpy(float))\n"
        "    _g = np.linspace(pilot['cooling_degree_days'].min(), pilot['cooling_degree_days'].max(), 25)\n"
        "    _cv = _ols(np.column_stack([np.ones(len(_g)), _g - CDD_REF]), 1.0 - (_arm['treatment'][0] + _arm['treatment'][1] * (_g - CDD_REF)) / (_arm['control'][0] + _arm['control'][1] * (_g - CDD_REF)))\n"
        "    _rp = lambda c: float(np.clip(_cv[0] + _cv[1] * (c - CDD_REF), 0.0, 0.95))\n"
        "    seg_fc = {s: float(np.mean([(stable[s][0] + stable[s][1] * c) * (1 - _rp(c)) for c in tcdd])) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)"))),
    "CE08_ratio_heat_adjustment": ("wrong", dict(EXTRA=(
        "    seg_fc = {s: %s * (1 - r_at(s, pilot_cbar) * pilot_cbar / cbar) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)") % L0)),
    "CE09_loglinear_response_form": ("alternative", dict(EXTRA=(
        "    _lc = {}\n"
        "    for s in segs:\n"
        "        _g = np.linspace(pilot['cooling_degree_days'].min(), pilot['cooling_degree_days'].max(), 25)\n"
        "        _r = np.array([max(r_at(s, c), 1e-4) for c in _g])\n"
        "        _lc[s] = _ols(np.column_stack([np.ones(len(_g)), _g - CDD_REF]), np.log(_r))\n"
        "    _rl = lambda s, c: float(np.clip(np.exp(_lc[s][0] + _lc[s][1] * (c - CDD_REF)), 0.0, 0.95))\n"
        "    seg_fc = {s: float(np.mean([(stable[s][0] + stable[s][1] * c) * (1 - _rl(s, c)) for c in tcdd])) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)"))),
    "CE10_incumbent_latest_window": ("wrong", dict(UR="False", ER="0.0", EXTRA=(
        "    _ly = hist[hist['year'] == hist['year'].max()]\n"
        "    for s in segs:\n"
        "        _g = _ly[_ly['segment_code'] == s].groupby('cooling_degree_days')['peak_kw']\n"
        "        stable[s] = _ols(np.column_stack([np.ones(len(_g.mean())), _g.mean().index.to_numpy(float)]), _g.mean().to_numpy(float), w=_g.size().to_numpy(float))\n"
        "    seg_fc = {s: %s for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)") % L0)),
    "CE11_latest_window_plus_response": ("alternative", dict(EXTRA=(
        "    _ly = hist[hist['year'] == hist['year'].max()]\n"
        "    for s in segs:\n"
        "        _g = _ly[_ly['segment_code'] == s].groupby('cooling_degree_days')['peak_kw']\n"
        "        stable[s] = _ols(np.column_stack([np.ones(len(_g.mean())), _g.mean().index.to_numpy(float)]), _g.mean().to_numpy(float), w=_g.size().to_numpy(float))\n"
        "    seg_fc = {s: float(np.mean([(stable[s][0] + stable[s][1] * c) * (1 - r_at(s, c)) for c in tcdd])) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)"))),
    "CE12_aggregate_pre_post": ("wrong", dict(EXTRA=(
        "    _th = set(pilot[pilot['assigned_arm'] == 'treatment']['household_id'])\n"
        "    _pre = float(hist[hist['household_id'].isin(_th)]['peak_kw'].mean())\n"
        "    _post = float(pilot[pilot['household_id'].isin(_th)]['peak_kw'].mean())\n"
        "    _rpp = 1 - _post / _pre\n"
        "    seg_fc = {s: %s * (1 - _rpp) for s in segs}\n"
        "    total = sum(pop[s] * seg_fc[s] for s in segs)") % L0)),
    "CE13_rload_composed_at_mean": ("alternative", dict(EXTRA=(
        "    _l0c = sum(pop[s] * (stable[s][0] + stable[s][1] * cbar) for s in segs)\n"
        "    _l1c = sum(pop[s] * (stable[s][0] + stable[s][1] * cbar) * (1 - r_at(s, cbar)) for s in segs)\n"
        "    total = %s * (_l1c / _l0c)") % L0E)),
}


def fixtures():
    out = {}
    for name in scenarios.ALL_NAMES:
        sp = scenarios.by_name(name)
        w = world.build(sp)
        t = world.truth(w)
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"), exist_ok=True)
        db = world.write_sqlite(w, os.path.join(d, "data"))
        out[name] = (db, t)
    return out


def bookkeeping(run, db):
    con = sqlite3.connect(db)
    n = con.execute("SELECT COUNT(*) FROM customer_master").fetchone()[0]
    shares = {s: c / n for s, c in con.execute(
        "SELECT segment_code, COUNT(*) FROM customer_master GROUP BY segment_code")}
    cdd = con.execute("SELECT AVG(cooling_degree_days_forecast) FROM weather_forecast_2027").fetchone()[0]
    con.close()
    bad = []
    if run.get("n_households") != n:
        bad.append("n_households")
    got = run.get("estate_segment_shares") or {}
    if set(got) != set(shares) or any(abs(float(got[s]) - v) > 1e-6 for s, v in shares.items()):
        bad.append("shares")
    if abs(float(run.get("target_cdd_mean", -1)) - cdd) > 1e-3:
        bad.append("target_cdd_mean")
    return bad


def score(src, fx):
    ns = {}
    exec(compile(src, "mut", "exec"), ns)
    rows, reward = {}, 1
    for name, (db, t) in fx.items():
        out = Path(tempfile.mkdtemp()) / "out"
        ns["analyse"](Path(db), out)
        run = json.loads((out / "analysis_results.json").read_text())
        tv = t["target_peak_mean"]
        tol = TOL_MULT * scenarios.SE_REF[name]["target_peak_kw"]
        fc = float(run["target_peak_kw"])
        failed = []
        if abs(fc - tv) > tol:
            failed.append("forecast")
        if run.get("procurement_decision") != t["decision"]:
            failed.append("decision")
        failed += bookkeeping(run, db)
        if name == "visible":
            seg, sh = run.get("segment_target_peak_kw") or {}, run.get("estate_segment_shares") or {}
            if seg and set(seg) == set(sh):
                if abs(sum(float(sh[s]) * float(seg[s]) for s in seg) - fc) > 0.02:
                    failed.append("reconcile")
        if failed:
            reward = 0
        rows[name] = {"forecast": fc, "truth": tv, "err": fc - tv, "err_tol": abs(fc - tv) / tol,
                      "decision": run.get("procurement_decision"), "truth_decision": t["decision"],
                      "response": run.get("estate_tou_response_at_target_cdd"), "failed": failed}
    return reward, rows


def main():
    fx = fixtures()
    results = {}
    panel = [(n, k, mm.render(d)) for n, (d, k) in mm.CASES.items()]
    panel += [(n, k, mm.render(dict(mm.BASE, **o))) for n, (k, o) in CE.items()]
    for name, kind, src in panel:
        rw, rows = score(src, fx)
        results[name] = {"kind": kind, "reward": rw, "fixtures": rows,
                         "max_err_tol": max(r["err_tol"] for r in rows.values()),
                         "min_err_tol": min(r["err_tol"] for r in rows.values())}
        fails = sorted({f for r in rows.values() for f in r["failed"]})
        print("%-48s %-11s reward=%d  err/tol max %6.2f  per-fixture %s  fails=%s" % (
            name, kind, rw, results[name]["max_err_tol"],
            " ".join("%.2f" % rows[f]["err_tol"] for f in scenarios.ALL_NAMES), ",".join(fails)))
    Path("research/g36/v1_1/forecast_sufficiency.json").write_text(json.dumps(results, indent=1) + "\n")


if __name__ == "__main__":
    main()
