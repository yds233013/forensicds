"""G38 auxiliary audits (research only).

1. G05-overlap ablation: identical DGP, but enrolment is EXOGENOUS (random suppliers, random month 24..29, same count).
   If the hard part is selection on an extreme realisation, naive pre/post and DiD must become ~unbiased here.
2. Trigger-window audit: EVALUATES (never selects) rolling windows L in {1, 3, 6, 12} for the visible regime:
   enrolment count, RTM bias of naive pre/post, and the valid state-space estimator's bias/SD.

    python research/g38/sim/aux_audits.py [draws]
"""
from __future__ import annotations

import json, sys
from pathlib import Path

import numpy as np

import g38_sim as G

DRAWS = int(sys.argv[1]) if len(sys.argv) > 1 else 60


def summarize(p, methods, draws, exogenous):
    rng = np.random.default_rng(p["seed"] + (7 if exogenous else 0))
    err = {m: [] for m in methods}; n = []; tq = []
    for _ in range(draws):
        X, Tr = G.draw(p, rng, exogenous=exogenous)
        if Tr["n_enr"] < 5:
            continue
        n.append(Tr["n_enr"]); tq.append(Tr["q1"])
        for m, fn in methods.items():
            err[m].append(fn(X)["q1"] - Tr["q1"])
    se = float(np.sqrt(np.mean(np.square(err["V2_state_space"]))))
    return {"n_enr": float(np.mean(n)), "truth_q1": float(np.mean(tq)), "se_ref_q1": se,
            "bias_defects": {m: float(np.mean(e)) for m, e in err.items()},
            "bias_se": {m: float(np.mean(e) / se) for m, e in err.items()},
            "sd_se": {m: float(np.std(e) / se) for m, e in err.items()}}


def main():
    out = {"ablation": {}, "trigger_window": {}}
    meth = {"V2_state_space": G.V2_state_space, "W01_pre_post_trigger_window": G.W01_pre_post_trigger_window,
            "W05_did_never_enrolled": G.W05_did_never_enrolled, "W07_did_excluding_trigger_window": G.W07_did_excluding_trigger_window}
    for fx in G.FIX:
        p = G.params(fx)
        endo = summarize(p, meth, DRAWS, False)
        p2 = dict(p); p2["_n_enr"] = int(round(endo["n_enr"]))
        exo = summarize(p2, meth, DRAWS, True)
        out["ablation"][fx] = {"threshold_triggered": endo, "exogenous_timing": exo}
        print("%-9s  bias (SE_REF units)  triggered: %s   |  exogenous: %s" % (fx,
              " ".join("%s %+.1f" % (m[:3], endo["bias_se"][m]) for m in meth), " ".join("%s %+.1f" % (m[:3], exo["bias_se"][m]) for m in meth)))
    wm = {"V2_state_space": G.V2_state_space, "W01_pre_post_trigger_window": G.W01_pre_post_trigger_window,
          "W21_v2_iid_transient": G.W21_v2_iid_transient, "W04_pre_mean_excluding_trigger": G.W04_pre_mean_excluding_trigger}
    for L in (1, 3, 6, 12):
        p = G.params("visible"); p["L"] = L
        r = summarize(p, wm, DRAWS, False)
        out["trigger_window"][L] = r
        print("L=%2d  enrollees %.0f  truthQ1 %.0f  SE_REF %.1f  bias_se %s" % (L, r["n_enr"], r["truth_q1"], r["se_ref_q1"],
              {m[:24]: round(v, 2) for m, v in r["bias_se"].items()}))
    Path(__file__).with_name("aux_audits.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
