#!/usr/bin/env python3
"""Dev: grade review implementations on the verifier's four extracts with the verifier's own check functions.

usage: quickcheck.py build CACHE_DIR                 build extracts + truth pickles once
       quickcheck.py run CACHE_DIR IMPL [VARIANT_JSON]   IMPL = path to a module with main(argv) or 'workspace:DIR'
"""
import copy, importlib.util, json, pickle, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "candidates/g10-censored-demand"
sys.path.insert(0, str(TASK / "tests"))
import world, truth  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402


def build(cache: Path):
    for sp in [world.VISIBLE_SPEC] + HIDDEN_SPECS:
        root = cache / sp["name"]
        t0 = time.time()
        w = world.build(copy.deepcopy(sp), root)
        pickle.dump(truth.expected(w), open(root / "truth.pkl", "wb"))
        print("built", sp["name"], round(time.time() - t0, 1), flush=True)


def run(cache: Path, impl: str, variant: str | None):
    import test_demand_review as TD
    for sp in [world.VISIBLE_SPEC] + HIDDEN_SPECS:
        root = cache / sp["name"]
        t = pickle.load(open(root / "truth.pkl", "rb"))
        out = Path(tempfile.mkdtemp())
        t0 = time.time()
        if impl.startswith("workspace:"):
            ws = Path(impl.split(":", 1)[1])
            p = subprocess.run([sys.executable, "-m", "demandsci", "review", "--db", str(root / "data/warehouse.sqlite"),
                                "--out", str(out)], cwd=ws, capture_output=True, text=True, env={"PYTHONPATH": str(ws), "PATH": "/usr/bin:/bin"})
            if p.returncode:
                print(sp["name"], "FAILED", p.stderr[-800:]); continue
        else:
            spec = importlib.util.spec_from_file_location("impl", impl)
            m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            if variant:
                m.VARIANT.update(json.loads(variant))
            m.main(["review", "--db", str(root / "data/warehouse.sqlite"), "--out", str(out)])
        secs = time.time() - t0
        import csv
        run = {"returncode": 0}
        run["history"] = list(csv.DictReader(open(out / "demand_history.csv", newline="")))
        run["trends"] = list(csv.DictReader(open(out / "category_trends.csv", newline="")))
        run["impact"] = json.loads((out / "programme_impact.json").read_text())
        res = []
        for name, fn in [("structure", TD.check_history_structure), ("demand", TD.check_demand_strata),
                         ("lost", TD.check_lost_strata), ("trends", TD.check_trends), ("impact", TD.check_impact)]:
            try:
                fn(run, t); res.append(f"{name}=ok")
            except AssertionError as e:
                res.append(f"{name}=FAIL[{str(e)[:220]}]")
        ok = all(r.endswith("=ok") for r in res)
        try:
            rat = ratios(TD, run, t)
        except Exception as exc:  # noqa: BLE001
            rat = {"error": repr(exc)[:80]}
        print(f"{sp['name']:9} {'PASS' if ok else 'fail'} {secs:5.0f}s  ratios={json.dumps(rat)}  " + "  ".join(res), flush=True)


def ratios(TD, run, t):
    """Worst |error| / tolerance per graded family (>1 fails)."""
    st = TD.strata_from_history(run, t)
    r = {}
    r["demand"] = max(abs(TD.rel_err(st["totals"][k], w)) / TD.TOL[f"total::post{int(k[0] == 'post')}_lean{int(k[1] == 'lean26')}_promo{int(k[2] == 'promo')}"]
                      for k, w in t["totals"].items())
    lost, want = dict(st["lost"]), dict(t["lost"])
    lost[("pre", "all")] = lost[("pre", "lean26")] + lost[("pre", "holdout")]
    want[("pre", "all")] = want[("pre", "lean26")] + want[("pre", "holdout")]
    keys = [(("pre", "all"), "lost::pre_all")] + [((p, pr), f"lost::post{int(p == 'post')}_promo{int(pr == 'promo')}")
                                                  for p in ("pre", "post") for pr in ("nonpromo", "promo")] \
        + [(("post", a), f"lost::post1_lean{int(a == 'lean26')}") for a in ("lean26", "holdout")]
    r["lost"] = max(abs(TD.rel_err(lost[k], want[k])) / TD.TOL[tk] for k, tk in keys)
    tr = {x["category"]: float(x["baseline_change_pct"]) for x in run["trends"]}
    r["cat_change"] = max(abs(tr[c] - w) / TD.TOL[f"cat_change::{c}"] for c, w in t["category_change"].items())
    fb = run["impact"].get("forecast_bias_pct") or {}
    r["bias"] = max(abs(float(fb[k]) - t["bias"][k]) / TD.TOL[tk] for k, tk in (("v3_pre_all_stores", "bias::v3_pre"), ("v4_post_lean26", "bias::v4_post_lean")))
    return {k: round(v, 2) for k, v in r.items()}


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(Path(sys.argv[2]))
    else:
        run(Path(sys.argv[2]), sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
