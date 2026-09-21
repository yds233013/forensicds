"""SE_REF for each candidate response definition, measured with the reference F1 estimator.
Deterministic Monte Carlo on the frozen generator. No model, no candidate modification.
Reads candidate code read-only; writes only into research/g36/adjudication/."""
from __future__ import annotations
import copy, json, math, os, sys, tempfile
from pathlib import Path
import numpy as np
C = Path("/Users/yashshah2311/forensicds/candidates/g36-tou-capacity-gate")
for s in ("environment/build", "tests", "solution"):
    sys.path.insert(0, str(C / s))
import world, scenarios                                   # noqa: E402
from capacity_forecast import estimators, load            # noqa: E402


def truths(sp, t):
    c = t["target_cdd_mean"]; p = t["estate_shares"]
    r = [world.response_at(sp, i, c) for i in range(4)]
    L = [world._load_expected(sp, i, c, False) for i in range(4)]
    return dict(hh=sum(p[i]*r[i] for i in range(4)),
                load=sum(p[i]*L[i]*r[i] for i in range(4)) / sum(p[i]*L[i] for i in range(4)),
                season=1 - t["target_peak_mean"]/t["target_peak_mean_no_tariff"])


def estimates(fr):
    pt, det = estimators.f1_stratified(fr)
    sh = estimators.estate_shares(fr); tc = estimators.target_cdd(fr); c = float(tc.mean())
    rr = lambda s, x: float(np.clip(det[s]["r0"] + det[s]["r_slope"]*(x-10.0), 0, .95))
    Lb = lambda s, x: det[s]["base"] + det[s]["beta"]*x
    hh = sum(float(sh[s])*rr(s, c) for s in det)
    ld = sum(float(sh[s])*Lb(s, c)*rr(s, c) for s in det) / sum(float(sh[s])*Lb(s, c) for s in det)
    L0 = sum(float(sh[s])*float(np.mean([Lb(s, x) for x in tc])) for s in det)
    return dict(hh=hh, load=ld, season=1 - pt/L0)


def main(R=12):
    out = {}
    for name in scenarios.ALL_NAMES:
        base = scenarios.by_name(name); errs = {k: [] for k in ("hh", "load", "season")}
        for k in range(R):
            sp = copy.deepcopy(base); sp["seed"] = base["seed"] + 10007*(k+1)
            w = world.build(sp); t = world.truth(w)
            d = tempfile.mkdtemp(); os.makedirs(d+"/data")
            fr = load.frames(Path(world.write_sqlite(w, d+"/data")))
            tv, ev = truths(sp, t), estimates(fr)
            for q in errs: errs[q].append(ev[q]-tv[q])
        w = world.build(base); t = world.truth(w)
        out[name] = {q: math.sqrt(np.mean(np.square(e))) for q, e in errs.items()}
        out[name]["_truth"] = truths(base, t)
        print(name, {q: round(v, 5) for q, v in out[name].items() if q != "_truth"}, flush=True)
    Path(__file__).with_name("definition_se.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
