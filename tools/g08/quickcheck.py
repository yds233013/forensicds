#!/usr/bin/env python3
"""Dev: run a mart implementation (module with build(db, as_of, out) or the workspace package) against extracts and
compare with the reference using the verifier's own comparison functions. usage: quickcheck.py IMPL.py|oracle DIR..."""
import importlib.util
import json
import csv
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "candidates/g08-forecast-accuracy-vintages"
sys.path.insert(0, str(TASK / "tests"))
import reference  # noqa: E402
import test_accuracy_mart as T  # noqa: E402

impl = sys.argv[1]
for d in sys.argv[2:]:
    d = Path(d)
    as_of = json.loads((d / "as_of.json").read_text())["as_of"] if (d / "as_of.json").exists() else "2026-09-22T06:00:00Z"
    out = Path(tempfile.mkdtemp())
    if impl == "oracle":
        ws = Path(tempfile.mkdtemp())
        import shutil
        shutil.copytree(TASK / "environment/workspace", ws, dirs_exist_ok=True)
        for f in ("mart.py", "kpi.py"):
            subprocess.run(["cp", str(TASK / "solution/fcaccuracy" / f), str(ws / "fcaccuracy" / f)], check=True)
        subprocess.run([sys.executable, "-m", "fcaccuracy", "build", "--as-of", as_of, "--db", str(d / "data/warehouse.sqlite"),
                        "--out", str(out)], cwd=ws, check=True)
    else:
        spec = importlib.util.spec_from_file_location("impl", impl)
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        m.main(["build", "--as-of", as_of, "--db", str(d / "data/warehouse.sqlite"), "--out", str(out)])
    run = {"returncode": 0}
    with open(out / "evaluation_examples.csv", newline="") as fh:
        run["examples"] = list(csv.DictReader(fh))
    with open(out / "monthly_kpi.csv", newline="") as fh:
        run["monthly"] = list(csv.DictReader(fh))
    run["summary"] = json.loads((out / "summary.json").read_text())
    want = reference.expected(d / "data/warehouse.sqlite", as_of)
    fails = []
    for name, fn in [("set", lambda: T.check_example_set(run, want)),
                     ("fields", lambda: T.compare_examples(run, want, T.ALL_FIELDS)),
                     ("monthly", lambda: T.check_monthly(run, want)),
                     ("summary", lambda: T.check_summary(run, want, as_of))]:
        try:
            fn()
        except AssertionError as e:
            fails.append(f"{name}: {str(e)[:300]}")
    print(f"{Path(impl).name} on {d.name}: {'PASS' if not fails else 'FAIL'}", *fails, sep="\n  ")
