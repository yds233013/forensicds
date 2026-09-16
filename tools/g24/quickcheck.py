#!/usr/bin/env python3
"""Dev: grade an implementation on the verifier's four extracts with the verifier's own check functions.

usage: quickcheck.py build CACHE_DIR                  build extracts + truth pickles once
       quickcheck.py run CACHE_DIR workspace:DIR      run a workspace package and grade it
       quickcheck.py run CACHE_DIR variant:NAME       run tools/g24/variant_ope.py with {"method": NAME}
       quickcheck.py run CACHE_DIR variantjson:JSON   run the variant with an explicit VARIANT dict
"""
import copy, json, pickle, subprocess, sys, tempfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "candidates/g24-recommender-ope"
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


def run(cache: Path, impl: str):
    import test_ope as TO
    if impl.startswith("file:"):
        ws = Path(tempfile.mkdtemp())
        import shutil
        shutil.copytree(TASK / "environment/workspace", ws, dirs_exist_ok=True)
        shutil.copyfile(impl.split(":", 1)[1], ws / "recs_eval/cli.py")
    elif impl.startswith("variant"):
        kind, arg = impl.split(":", 1)
        variant = {"method": arg} if kind == "variant" else json.loads(arg)
        ws = Path(tempfile.mkdtemp())
        base = TASK / "environment/workspace"
        import shutil
        shutil.copytree(base, ws, dirs_exist_ok=True)
        src = (HERE / "variant_ope.py").read_text().replace("VARIANT: dict = {}", f"VARIANT: dict = {variant!r}", 1)
        (ws / "recs_eval/cli.py").write_text(src)
    else:
        ws = Path(impl.split(":", 1)[1])
    for sp in [world.VISIBLE_SPEC] + HIDDEN_SPECS:
        root = cache / sp["name"]
        t = pickle.load(open(root / "truth.pkl", "rb"))
        out = Path(tempfile.mkdtemp())
        t0 = time.time()
        p = subprocess.run([sys.executable, "-m", "recs_eval", "ope", "--logs", str(root / "data/logs.sqlite"),
                            "--out", str(out)], cwd=ws, capture_output=True, text=True,
                           env={"PYTHONPATH": str(ws), "PATH": "/usr/bin:/bin"})
        if p.returncode:
            print(f"{sp['name']:9} FAILED {p.stderr[-500:]}")
            continue
        secs = time.time() - t0
        import csv as _csv
        run = {"returncode": 0}
        with open(out / "decisions.csv", newline="") as fh:
            run["decisions"] = list(_csv.DictReader(fh))
        with open(out / "target_slates.csv", newline="") as fh:
            run["slates"] = list(_csv.DictReader(fh))
        with open(out / "policy_values.csv", newline="") as fh:
            run["values"] = list(_csv.DictReader(fh))
        run["launch"] = json.loads((out / "launch.json").read_text())
        res = []
        for name, fn in (("decisions", TO.check_decisions), ("slates", TO.check_target_slates),
                         ("values", TO.check_values), ("intervals", TO.check_intervals),
                         ("launch", TO.check_launch)):
            try:
                fn(run, t)
                res.append(f"{name}=ok")
            except AssertionError as e:
                res.append(f"{name}=FAIL[{str(e)[:150]}]")
        ok = all(r.endswith("=ok") for r in res)
        ratios = {}
        try:
            v = {r["policy"]: r for r in run["values"]}
            ratios = {p: round(abs(float(v[p]["value"]) - t["values"][p]) / (3.5 * t["se"][p]), 2) for p in
                      ("v6", "v7", "v7_pd")}
            ratios["lift"] = max(round(abs(float(v[p]["lift_vs_v6"]) - t["lifts"][p]) / (3.5 * t["se_lift"][p]), 2)
                                 for p in ("v7", "v7_pd"))
        except Exception:
            pass
        print(f"{sp['name']:9} {'PASS' if ok else 'fail'} {secs:5.0f}s ratios={json.dumps(ratios)} " + "  ".join(res),
              flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(Path(sys.argv[2]))
    else:
        run(Path(sys.argv[2]), sys.argv[3])
