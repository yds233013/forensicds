#!/usr/bin/env python3
"""G10 tolerance calibration and validation on the task generator (pilot protocol, research/g10/G10_tolerance_pilot.md).

phase cal: seeds 7000+13i, i<n, per regime; correct estimators only; tolerance = max(floor, 1.5 x max |error|).
phase val: seeds 9000+13i; correct and wrong estimators graded with the fixed tolerances (verifier definitions).

usage: recalibrate.py run PHASE REGIME N OUT.json      (one regime; run regimes in parallel)
       recalibrate.py tolerances CAL_JSON... > tolerances.json
       recalibrate.py summarize TOL.json VAL_JSON...
"""
from __future__ import annotations

import copy, json, math, sys, tempfile, time, shutil
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "candidates/g10-censored-demand"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))
import world, truth  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402
import variant_review as V  # noqa: E402

CORRECT = ["nb", "em", "nb_4week", "store_week", "sep_cat", "alpha_sku", "promo_common", "cat_period_only", "store_only"]
WRONG = ["sales", "drop_censored", "per_day_scale", "uniform_time_scale", "mean_rate_impute", "poisson_offset",
         "daily_censored_poisson", "forecast_impute", "profile_all_days", "nb_no_promo", "forecast_prior", "v3_prior", "nb_plugin"]
PROBES = ["nb_common_alpha", "nb_lognormal", "fe_profile"]           # research/g10/recal/PREREGISTRATION_2.md
FLOORS = {"cat_change": 1.5, "bias": 1.0, "total": 1.5, "lost": 6.0}      # research/g10/recal/PREREGISTRATION.md
CAPS = {"cat_change": 2.0}


def aggregates(X, ED, t) -> dict:
    """Agent and truth aggregates for every candidate graded quantity (so strata can be re-keyed without re-running)."""
    N = X["sales"]
    keys = [(s, k, d) for s, k, d, _ in X["rows"]]
    meta = [t["meta"][kk] for kk in keys]
    got = defaultdict(float)
    series = defaultdict(lambda: [0.0, 0])
    for i, (post, arm, promo) in enumerate(meta):
        e = ED[i]
        got[f"total|{post}|{arm}|{promo}"] += e
        for g in (f"{post}|{arm}", f"{post}|{promo}", f"{post}|all"):
            got[f"lost|{g}"] += e - N[i]
            got[f"dem|{g}"] += e
        if promo == "nonpromo":
            acc = series[(t["cat_of"][keys[i][1]], post, keys[i][0], keys[i][1])]
            acc[0] += e
            acc[1] += 1
    base = defaultdict(float)
    for (c, p, _s, _k), (sm, n) in series.items():
        base[(c, p)] += sm / n
    for c in t["category_change"]:
        got[f"cat|{c}"] = 100 * (base[(c, "post")] / base[(c, "pre")] - 1)
    pre = np.array([m[0] == "pre" for m in meta])
    pl = np.array([m[0] == "post" and m[1] == "lean26" for m in meta])
    got["bias|v3_pre_all_stores"] = 100 * (np.nansum(X["v3"][pre]) - ED[pre].sum()) / ED[pre].sum()
    got["bias|v4_post_lean26"] = 100 * (np.nansum(X["v4"][pl]) - ED[pl].sum()) / ED[pl].sum()
    want = {}
    for (p, a, pr), v in t["totals"].items():
        want[f"total|{p}|{a}|{pr}"] = v
    for (p, g), v in t["lost"].items():
        want[f"lost|{p}|{g}"] = v
    for p in ("pre", "post"):
        want[f"lost|{p}|all"] = t["lost"][(p, "lean26")] + t["lost"][(p, "holdout")]
        for a in ("lean26", "holdout"):
            want[f"share|{p}|{a}"] = t["lost_share"][(p, a)]
            got[f"share|{p}|{a}"] = got[f"lost|{p}|{a}"] / got[f"dem|{p}|{a}"]
    for c, v in t["category_change"].items():
        want[f"cat|{c}"] = v
    want["bias|v3_pre_all_stores"] = t["bias"]["v3_pre_all_stores"]
    want["bias|v4_post_lean26"] = t["bias"]["v4_post_lean26"]
    return {"got": {k: float(v) for k, v in got.items()}, "want": want}


def graded_errors(agg) -> dict:
    """Signed errors keyed like tests/tolerances.json under the round-2 graded strata."""
    g, w = agg["got"], agg["want"]
    rel = lambda a, b: 100 * (a / b - 1) if b else (0.0 if abs(a) < 1e-9 else float("inf"))
    out = {}
    for k in w:
        if k.startswith("total|"):
            _, p, a, pr = k.split("|")
            out[f"total::post{int(p == 'post')}_lean{int(a == 'lean26')}_promo{int(pr == 'promo')}"] = rel(g[k], w[k])
    out["lost::pre_all"] = rel(g["lost|pre|all"], w["lost|pre|all"])
    for pr in ("promo", "nonpromo"):
        for p in ("pre", "post"):
            out[f"lost::post{int(p == 'post')}_promo{int(pr == 'promo')}"] = rel(g[f"lost|{p}|{pr}"], w[f"lost|{p}|{pr}"])
    for a in ("lean26", "holdout"):
        out[f"lost::post1_lean{int(a == 'lean26')}"] = rel(g[f"lost|post|{a}"], w[f"lost|post|{a}"])
        out[f"share::lost::post1_lean{int(a == 'lean26')}"] = rel(g[f"share|post|{a}"], w[f"share|post|{a}"])
    for k in w:
        if k.startswith("cat|"):
            out[f"cat_change::{k[4:]}"] = g[k] - w[k]
    out["bias::v3_pre"] = g["bias|v3_pre_all_stores"] - w["bias|v3_pre_all_stores"]
    out["bias::v4_post_lean"] = g["bias|v4_post_lean26"] - w["bias|v4_post_lean26"]
    acts_ok = acts_n = 0
    for k in w:
        if k.startswith("cat|") and min(abs(w[k] - 5), abs(w[k] + 5)) >= 2.0:
            act = lambda x: "reduce" if x <= -5 else "increase" if x >= 5 else "maintain"
            acts_n += 1
            acts_ok += act(g[k]) == act(w[k])
    out["_actions"] = [acts_ok, acts_n]
    return out


def run(phase: str, regime: str, n: int, out_path: str):
    base = 7000 if phase == "cal" else 9000
    methods = CORRECT if phase == "cal" else CORRECT + WRONG + PROBES
    spec0 = next(s for s in [world.VISIBLE_SPEC] + HIDDEN_SPECS if s["name"] == regime)
    res = []
    for i in range(n):
        sp = copy.deepcopy(spec0)
        sp["seed"] = base + 13 * i
        tmp = Path(tempfile.mkdtemp(prefix="g10cal_"))
        t0 = time.time()
        w = world.build(sp, tmp)
        t = truth.expected(w)
        del w
        for m in methods:
            V.CFG.clear()
            V.CFG.update({"method": m, "hardcoded_actions": None, "hardcoded_go_live": None, "hardcoded_holdout": None,
                          "hardcoded_alpha": None, "hardcoded_profile": None})
            X = V.load(tmp / "data/warehouse.sqlite")
            ED = V.estimate(X)
            agg = aggregates(X, ED, t)
            res.append({"regime": regime, "seed": sp["seed"], "method": m, "agg": agg, "err": graded_errors(agg)})
        print(regime, sp["seed"], f"{time.time() - t0:.0f}s", flush=True)
        shutil.rmtree(tmp, ignore_errors=True)
        Path(out_path).write_text(json.dumps(res))


def family(k):
    return "lost" if k.startswith("share::") else k.split("::")[0]


def tol_key(k):
    return k[len("share::"):] if k.startswith("share::") else k


def tolerances(paths):
    worst = defaultdict(float)
    for p in paths:
        for r in json.load(open(p)):
            if r["method"] not in CORRECT:
                continue
            for k, v in (graded_errors(r["agg"]) if "agg" in r else r["err"]).items():
                if k.startswith("_") or k.startswith("share::"):
                    continue
                worst[k] = max(worst[k], abs(v))
    tol = {k: round(max(FLOORS[family(k)], 1.5 * v), 2) for k, v in sorted(worst.items())}
    over = {k: v for k, v in tol.items() if family(k) in CAPS and v > CAPS[family(k)]}
    if over:
        sys.stderr.write(f"CALIBRATION FAILS CAP: {over}\n")
    print(json.dumps(tol, indent=1))
    sys.stderr.write(json.dumps({k: round(v, 3) for k, v in sorted(worst.items())}, indent=1) + "\n")


def summarize(tol_path, paths):
    tol = json.load(open(tol_path))
    rows = [r for p in paths for r in json.load(open(p))]
    by = defaultdict(list)
    for r in rows:
        if "agg" in r:
            r["err"] = graded_errors(r["agg"])
        ratio = max(abs(v) / tol[tol_key(k)] for k, v in r["err"].items() if not k.startswith("_"))
        fams = defaultdict(float)
        for k, v in r["err"].items():
            if not k.startswith("_"):
                fams[family(k)] = max(fams[family(k)], abs(v) / tol[tol_key(k)])
        ok_act = r["err"]["_actions"][0] == r["err"]["_actions"][1]
        by[r["method"]].append((r["regime"], r["seed"], ratio, ok_act, dict(fams)))
    print(f"{'method':24} {'worlds pass':>11} {'min ratio':>9} {'max ratio':>9}  per-regime min ratio (visible/a/b/c)   trends-only pass  actions ok")
    for m, lst in by.items():
        npass = sum(1 for _r, _s, ratio, ok, _f in lst if ratio <= 1 and ok)
        per = {}
        for reg in ("visible", "hidden_a", "hidden_b", "hidden_c"):
            v = [ratio for r, _s, ratio, _o, _f in lst if r == reg]
            per[reg] = round(min(v), 2) if v else None
        trends_only = sum(1 for *_x, f in lst if f.get("cat_change", 0) <= 1)
        acts = sum(1 for _r, _s, _ra, ok, _f in lst if ok)
        print(f"{m:24} {npass:>5}/{len(lst):<5} {min(x[2] for x in lst):9.2f} {max(x[2] for x in lst):9.2f}  "
              f"{per}  {trends_only}/{len(lst)}  {acts}/{len(lst)}")


if __name__ == "__main__":
    if sys.argv[1] == "run":
        run(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5])
    elif sys.argv[1] == "tolerances":
        tolerances(sys.argv[2:])
    else:
        summarize(sys.argv[2], sys.argv[3:])
