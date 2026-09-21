"""Reference standard errors per graded extract and quantity (research/dev tool; no model).

    python tools/g36/fixture_audit.py [redraws]
"""
from __future__ import annotations
import copy, json, math, os, sys, tempfile
from pathlib import Path

R = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(R / s))
import world, scenarios                                             # noqa: E402
from capacity_forecast import estimators, load                      # noqa: E402


def accepted_values(db):
    fr = load.frames(Path(db))
    pt, det = estimators.f1_stratified(fr)
    return {"target_peak_kw": pt,
            "estate_tou_response_at_target_cdd":
                estimators.estate_response_at_target_cdd(fr, det)}


def truth_values(t):
    return {"target_peak_kw": t["target_peak_mean"],
            "estate_tou_response_at_target_cdd":
                sum(a * b for a, b in zip(t["estate_shares"], t["response_at_target_cdd"]))}


def main(redraws=30):
    out = {}
    for name in scenarios.ALL_NAMES:
        base = scenarios.by_name(name)
        errs = {q: [] for q in scenarios.QUANT}
        for k in range(redraws):
            sp = copy.deepcopy(base)
            sp["seed"] = base["seed"] + 10007 * (k + 1)
            w = world.build(sp); t = world.truth(w)
            d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "data"), exist_ok=True)
            db = world.write_sqlite(w, os.path.join(d, "data"))
            a, tv = accepted_values(db), truth_values(t)
            for q in scenarios.QUANT:
                errs[q].append(a[q] - tv[q])
        out[name] = {q: math.sqrt(sum(e * e for e in errs[q]) / len(errs[q]))
                     for q in scenarios.QUANT}
        w = world.build(base); t = world.truth(w)
        out[name]["_truth"] = {k: (round(v, 6) if isinstance(v, float) else v)
                               for k, v in truth_values(t).items()}
        out[name]["_decision"] = t["decision"]
        print(name, json.dumps({q: round(out[name][q], 6) for q in scenarios.QUANT}),
              t["decision"], flush=True)
    Path(__file__).with_name("fixture_audit.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\nSE_REF = {")
    for name in scenarios.ALL_NAMES:
        print("    %r: {" % name)
        for q in scenarios.QUANT:
            print("        %r: %.8f," % (q, out[name][q]))
        print("    },")
    print("}")
    print("SE_REF_REDRAWS = %d" % redraws)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 30)
