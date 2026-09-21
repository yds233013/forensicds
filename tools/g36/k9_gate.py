"""K9 BLOCKING GATE: do genuinely independent valid estimator families agree?

Run BEFORE any tolerance is chosen. Research/dev only; no model, no container.
    python tools/g36/k9_gate.py [n_replications]
"""
from __future__ import annotations

import copy, os, sys, tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2] / "candidates" / "g36-tou-capacity-gate"
sys.path.insert(0, str(ROOT / "environment" / "build"))
sys.path.insert(0, str(ROOT / "solution"))
import world                                                        # noqa: E402
from capacity_forecast import estimators, load                      # noqa: E402


def build_and_eval(spec):
    w = world.build(spec)
    t = world.truth(w)
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "data"), exist_ok=True)
    db = world.write_sqlite(w, os.path.join(d, "data"))
    fr = load.frames(Path(db))
    vals = {k: f(fr)[0] for k, f in estimators.FAMILIES.items()}
    return t, vals


def main(reps=6):
    base = world.VISIBLE_SPEC
    print("=" * 92)
    print("K9 GATE - independent valid estimator families")
    print("=" * 92)
    print("%-12s %10s %11s %11s %11s %10s" % (
        "draw", "truth", "F1_strat", "F2_joint", "F3_hier", "spread"))
    spreads = []
    errs = {k: [] for k in estimators.FAMILIES}
    for r in range(reps):
        sp = copy.deepcopy(base)
        sp["seed"] = base["seed"] + 7919 * r
        t, v = build_and_eval(sp)
        spreads.append(max(v.values()) - min(v.values()))
        for k in v:
            errs[k].append(v[k] - t["target_peak_mean"])
        print("%-12s %10.4f %11.4f %11.4f %11.4f %10.4f" % (
            "draw_%d" % r, t["target_peak_mean"], v["F1_stratified"],
            v["F2_joint_nonlinear"], v["F3_hierarchical"], spreads[-1]))

    print("\n%-26s %10s %10s" % ("family", "bias", "sd"))
    for k, e in errs.items():
        print("%-26s %10.4f %10.4f" % (k, float(np.mean(e)), float(np.std(e))))
    sd = float(np.mean([np.std(e) for e in errs.values()]))
    print("\nmax absolute disagreement across families: %.4f" % max(spreads))
    print("mean sampling sd of a family:               %.4f" % sd)
    print("disagreement / sd:                          %.2f" % (max(spreads) / max(sd, 1e-9)))
    print("\nK9 verdict: %s" % ("PASS - disagreement within sampling noise"
                                if max(spreads) <= 2.0 * sd else "FAIL - families disagree"))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 6)
