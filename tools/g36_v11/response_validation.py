"""G36-v1.1 response validation: IGQA truth derivations, response K9, wrong-response panel.
Deterministic; no model; reads the v1.1 candidate read-only."""
from __future__ import annotations
import copy, itertools, json, math, os, sys, tempfile
from pathlib import Path
import numpy as np
C = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate-v1.1")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(C / s))
import world, scenarios                                         # noqa: E402
from capacity_forecast import estimators, load                  # noqa: E402
REF = 10.0

# ---------------- truth derivation A: the verifier's form, generator helpers, loads then ratio
def truth_A(sp, t):
    c, p = t["target_cdd_mean"], t["estate_shares"]
    l0 = sum(p[i] * world._load_expected(sp, i, c, False) for i in range(4))
    l1 = sum(p[i] * world._load_expected(sp, i, c, True) for i in range(4))
    return (l0 - l1) / l0

# ---------------- truth derivation B: contract-only, NO generator helper; absolute reductions / flat load
def truth_B(sp, t):
    c, p = t["target_cdd_mean"], t["estate_shares"]
    num = den = 0.0
    for i in range(4):
        flat = sp["base"][i] + sp["beta"][i] * c                       # expectation factor cancels in the ratio
        fade = max(1.0 - sp["heat_damping"] * (c - sp["cdd_ref"]) / sp["cdd_ref"], 0.05)
        frac = min(max(sp["resp0"][i] * fade, 0.0), 0.95)
        num += p[i] * flat * frac                                       # absolute kW reduction, segment i
        den += p[i] * flat
    return num / den

# ---------------- estimator-side route B: absolute-reduction aggregation, independent of the oracle helper
def est_route_B(fr, det):
    sh = fr["customers"]["segment_code"].value_counts(normalize=True)
    c = float(fr["forecast"]["cooling_degree_days_forecast"].mean())
    red = tot = 0.0
    for s, d in det.items():
        flat = d["base"] + d["beta"] * c
        red += sh[s] * flat * min(max(d["r0"] + d["r_slope"] * (c - REF), 0.0), 0.95)
        tot += sh[s] * flat
    return red / tot

def wrong_panel(fr, det):
    sh = estimators.estate_shares(fr); tc = estimators.target_cdd(fr); c = float(tc.mean())
    df = fr["loads"]; pil = df[df["year"] == 2026]
    enr = pil.groupby("segment_code")["household_id"].nunique(); enr = enr / enr.sum()
    pc = float(pil["cooling_degree_days"].mean())
    r = lambda s, x: float(np.clip(det[s]["r0"] + det[s]["r_slope"] * (x - REF), 0, .95))
    L = lambda s, x: det[s]["base"] + det[s]["beta"] * x
    lw = lambda w, x: sum(w[s]*L(s, c)*r(s, x) for s in det) / sum(w[s]*L(s, c) for s in det)
    L0 = sum(float(sh[s]) * float(np.mean([L(s, x) for x in tc])) for s in det)
    L1 = sum(float(sh[s]) * float(np.mean([L(s, x)*(1-r(s, x)) for x in tc])) for s in det)
    return {
        "household_weighted": sum(float(sh[s]) * r(s, c) for s in det),
        "segment_unweighted_mean": float(np.mean([r(s, c) for s in det])),
        "zero": 0.0,
        "sign_flipped": -lw({s: float(sh[s]) for s in det}, c),
        "at_pilot_mean_cdd": lw({s: float(sh[s]) for s in det}, pc),
        "enrolled_mix_weights": lw({s: float(enr.get(s, 0)) for s in det}, c),
        "VARIANT_season_average": 1 - L1 / L0,
    }

def build(sp):
    w = world.build(sp); t = world.truth(w)
    d = tempfile.mkdtemp(); os.makedirs(d + "/data")
    return t, load.frames(Path(world.write_sqlite(w, d + "/data")))

def main(reps=4):
    out = {"igqa": {}, "k9": [], "panel": {}}
    print("IGQA - response truth by two derivations sharing no helper")
    for n in scenarios.ALL_NAMES:
        sp = scenarios.by_name(n); t = world.truth(world.build(sp))
        a, b = truth_A(sp, t), truth_B(sp, t)
        out["igqa"][n] = {"A": a, "B": b}
        print("   %-9s A=%.10f  B=%.10f  |A-B|=%.2e" % (n, a, b, abs(a - b)))
    for n in scenarios.ALL_NAMES:
        base = scenarios.by_name(n)
        for k in range(reps):
            sp = copy.deepcopy(base)
            if k: sp["seed"] = base["seed"] + 6577 * k
            t, fr = build(sp); tv = truth_A(sp, t)
            row = {"fixture": n, "draw": k, "truth": tv}
            for fam, f in estimators.FAMILIES.items():
                pt, det = f(fr)
                row[fam + "_A"] = estimators.estate_response_at_target_cdd(fr, det)
                row[fam + "_B"] = est_route_B(fr, det)
            if k == 0:
                _, d1 = estimators.f1_stratified(fr)
                out["panel"][n] = {"truth": tv, **wrong_panel(fr, d1)}
            out["k9"].append(row)
            print("   k9 %-9s r%d truth %.5f  F1 %.5f/%.5f  F2 %.5f/%.5f  F3 %.5f/%.5f" % (
                n, k, tv, row["F1_stratified_A"], row["F1_stratified_B"], row["F2_joint_nonlinear_A"],
                row["F2_joint_nonlinear_B"], row["F3_hierarchical_A"], row["F3_hierarchical_B"]), flush=True)
    Path("/Users/yashshah2311/forensicds/research/g36/v1_1/response_validation.json").write_text(json.dumps(out, indent=1))

if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 4)
