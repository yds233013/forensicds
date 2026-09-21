"""K9 re-run against the FINAL fixture construction and FINAL business threshold.

Also measures whether the estate-weighted response adds discrimination beyond the forecast.
Research/dev only; no model, no container.
"""
from __future__ import annotations
import copy, os, sys, tempfile
from pathlib import Path
import numpy as np

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
sys.path.insert(0, str(R / "environment" / "build"))
sys.path.insert(0, str(R / "tests"))
sys.path.insert(0, str(R / "solution"))
import world, scenarios                                             # noqa: E402
from capacity_forecast import estimators, load                      # noqa: E402

GATE = 3.057


def evaluate(spec):
    w = world.build(spec)
    t = world.truth(w)
    d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"), exist_ok=True)
    db = world.write_sqlite(w, os.path.join(d, "data"))
    fr = load.frames(Path(db))
    vals, resp = {}, {}
    for k, f in estimators.FAMILIES.items():
        pt, det = f(fr)
        vals[k] = pt
        resp[k] = estimators.estate_response_at_target_cdd(fr, det)
    true_r = sum(s * r for s, r in zip(t["estate_shares"], t["response_at_target_cdd"]))
    return t, vals, resp, true_r


def main(reps=4):
    print("=" * 104)
    print("K9 FINAL - independent estimator families on the FINAL fixtures and threshold %.3f kW" % GATE)
    print("=" * 104)
    errs = {k: [] for k in estimators.FAMILIES}
    rerrs = {k: [] for k in estimators.FAMILIES}
    spreads, rspreads = [], []
    print("%-10s %-6s %9s %10s %10s %10s %9s %s" % (
        "fixture", "draw", "truth", "F1", "F2", "F3", "spread", "decisions"))
    for name in scenarios.ALL_NAMES:
        base = scenarios.by_name(name)
        for r in range(reps):
            sp = copy.deepcopy(base)
            if r:
                sp["seed"] = base["seed"] + 6577 * r
            t, v, rr, tr = evaluate(sp)
            spreads.append(max(v.values()) - min(v.values()))
            rspreads.append(max(rr.values()) - min(rr.values()))
            for k in v:
                errs[k].append(v[k] - t["target_peak_mean"])
                rerrs[k].append(rr[k] - tr)
            dec = "".join(("P" if v[k] >= GATE else "d") for k in
                          ("F1_stratified", "F2_joint_nonlinear", "F3_hierarchical"))
            truth_d = "P" if t["target_peak_mean"] >= GATE else "d"
            print("%-10s %-6s %9.4f %10.4f %10.4f %10.4f %9.4f  %s truth=%s%s" % (
                name, "r%d" % r, t["target_peak_mean"], v["F1_stratified"],
                v["F2_joint_nonlinear"], v["F3_hierarchical"], spreads[-1], dec, truth_d,
                "" if set(dec) == {truth_d} else "   <-- DISAGREE"))

    print("\n%-26s %10s %10s | %10s %10s" % ("family", "bias", "sd", "resp_bias", "resp_sd"))
    for k in errs:
        print("%-26s %10.4f %10.4f | %10.4f %10.4f" % (
            k, float(np.mean(errs[k])), float(np.std(errs[k])),
            float(np.mean(rerrs[k])), float(np.std(rerrs[k]))))
    sd = float(np.mean([np.std(e) for e in errs.values()]))
    rsd = float(np.mean([np.std(e) for e in rerrs.values()]))
    print("\nforecast : max disagreement %.4f, mean sd %.4f, ratio %.2f" % (
        max(spreads), sd, max(spreads) / sd))
    print("response : max disagreement %.4f, mean sd %.4f, ratio %.2f" % (
        max(rspreads), rsd, max(rspreads) / rsd))
    print("\nK9 FINAL verdict: %s" % ("PASS" if max(spreads) <= 2.0 * sd else "FAIL"))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
