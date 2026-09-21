"""K9 acceptance test, done properly: paired differences between estimator families.

The earlier crude rule ("max spread over all draws <= 2 sd") is not a valid test. The maximum of a
spread over many draws has an expectation well above 2 sd even when every family is unbiased for the
same estimand. The correct question is whether the PAIRED difference between two families has a mean
indistinguishable from zero relative to its own standard error, and whether decisions agree.
"""
from __future__ import annotations
import copy, itertools, os, sys, tempfile
from pathlib import Path
import numpy as np

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(R / s))
import world, scenarios                                             # noqa: E402
from capacity_forecast import estimators, load                      # noqa: E402
GATE = 3.057


def main(reps=4):
    vals = {k: [] for k in estimators.FAMILIES}
    resp = {k: [] for k in estimators.FAMILIES}
    truths, tresp, decs = [], [], []
    for name in scenarios.ALL_NAMES:
        base = scenarios.by_name(name)
        for r in range(reps):
            sp = copy.deepcopy(base)
            if r:
                sp["seed"] = base["seed"] + 6577 * r
            w = world.build(sp); t = world.truth(w)
            d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"), exist_ok=True)
            fr = load.frames(Path(world.write_sqlite(w, os.path.join(d, "data"))))
            truths.append(t["target_peak_mean"])
            tresp.append(sum(a * b for a, b in zip(t["estate_shares"],
                                                   t["response_at_target_cdd"])))
            decs.append(t["decision"])
            for k, f in estimators.FAMILIES.items():
                pt, det = f(fr)
                vals[k].append(pt)
                resp[k].append(estimators.estate_response_at_target_cdd(fr, det))

    n = len(truths)
    print("=" * 96)
    print("K9 ACCEPTANCE - paired differences, %d draws across %d fixtures" % (n, len(scenarios.ALL_NAMES)))
    print("=" * 96)
    print("\n1. Is each family unbiased for the target quantity?")
    print("%-26s %10s %10s %10s %8s" % ("family", "mean err", "sd", "se(mean)", "t"))
    for k in vals:
        e = np.array(vals[k]) - np.array(truths)
        se = e.std(ddof=1) / np.sqrt(n)
        print("%-26s %10.4f %10.4f %10.4f %8.2f" % (k, e.mean(), e.std(ddof=1), se, e.mean() / se))

    print("\n2. Do families differ from each other beyond sampling noise?")
    print("%-46s %10s %10s %8s %s" % ("pair", "mean diff", "se(diff)", "t", "verdict"))
    ok = True
    for a, b in itertools.combinations(vals, 2):
        d = np.array(vals[a]) - np.array(vals[b])
        se = d.std(ddof=1) / np.sqrt(n)
        tstat = d.mean() / se if se > 0 else 0.0
        v = "compatible" if abs(tstat) < 3.0 else "DIFFERENT"
        ok &= abs(tstat) < 3.0
        print("%-46s %10.4f %10.4f %8.2f %s" % ("%s vs %s" % (a[:18], b[:18]), d.mean(), se, tstat, v))

    print("\n3. Do families agree on the procurement decision?")
    agree = 0
    for i in range(n):
        ds = {("procure" if vals[k][i] >= GATE else "defer") for k in vals}
        if len(ds) == 1 and ds.pop() == decs[i]:
            agree += 1
    print("   unanimous AND correct on %d / %d draws" % (agree, n))

    print("\n4. Does the estate-weighted response add discrimination beyond the forecast?")
    f = "F1_stratified"
    rho = np.corrcoef(np.array(vals[f]) - np.array(truths),
                      np.array(resp[f]) - np.array(tresp))[0, 1]
    e_r = np.array(resp[f]) - np.array(tresp)
    print("   response bias %.4f, sd %.4f" % (e_r.mean(), e_r.std(ddof=1)))
    print("   corr(forecast error, response error) = %+.3f" % rho)
    print("   -> %s" % ("largely redundant with the forecast" if abs(rho) > 0.8
                        else "carries partly independent information"))

    print("\nK9 VERDICT: %s" % ("PASS" if (ok and agree == n) else "FAIL"))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
