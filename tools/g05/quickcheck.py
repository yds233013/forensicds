#!/usr/bin/env python3
"""Dev: grade an implementation on the verifier's four warehouses with the verifier's own check functions.

usage: quickcheck.py build CACHE_DIR                       build warehouses + expected pickles once
       quickcheck.py run CACHE_DIR workspace:DIR           run a workspace package and grade it
       quickcheck.py run CACHE_DIR variant:METHOD          run tools/g05/variant_cli.py with {"method": METHOD}
       quickcheck.py run CACHE_DIR variantjson:JSON        run the variant with an explicit VARIANT dict
"""
from __future__ import annotations

import copy
import json
import os
import pickle
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "candidates/g05-sco-rollout-gate"
sys.path.insert(0, str(TASK / "tests"))
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

NAMES = ["visible"] + [s["name"] for s in HIDDEN_SPECS]


def build(cache: Path):
    import test_readout as TR
    for sp in [world.VISIBLE_SPEC] + HIDDEN_SPECS:
        root = cache / sp["name"]
        root.mkdir(parents=True, exist_ok=True)
        t0 = time.time()
        w = world.build_world(copy.deepcopy(sp))
        world.write_warehouse(w, str(root / "warehouse.sqlite"))
        pickle.dump(TR.expected(w), open(root / "expected.pkl", "wb"))
        print("built", sp["name"], round(time.time() - t0, 1), flush=True)


def make_variant_ws(variant: dict) -> Path:
    ws = Path(tempfile.mkdtemp(prefix="g05var_"))
    shutil.copytree(TASK / "environment/workspace", ws, dirs_exist_ok=True)
    install_variant(ws, variant)
    return ws


def install_variant(ws: Path, variant: dict) -> None:
    pkg = ws / "sco_readout"
    src = (HERE / "variant_cli.py").read_text().replace('VARIANT = {"method": "imp_format_week"}',
                                                          f"VARIANT = {json.dumps(variant)}")
    (pkg / "cli.py").write_text(src)
    pilot = ROOT / "research/g05/pilot"
    (pkg / "_g05_sim.py").write_text((pilot / "g05_sim.py").read_text())
    (pkg / "_g05_estimators.py").write_text(
        (pilot / "g05_estimators.py").read_text().replace("import g05_sim as S", "from sco_readout import _g05_sim as S"))


def run(cache: Path, impl: str) -> int:
    import test_readout as TR
    if impl.startswith("workspace:"):
        ws = Path(impl.split(":", 1)[1])
    else:
        kind, arg = impl.split(":", 1)
        ws = make_variant_ws({"method": arg} if kind == "variant" else json.loads(arg))
    TR.WORKSPACE = ws
    TR.PIPELINE_PYTHON = sys.executable
    all_ok = True
    for name in NAMES:
        (ws / "data").mkdir(exist_ok=True)
        shutil.copyfile(cache / name / "warehouse.sqlite", ws / "data/warehouse.sqlite")
        t = pickle.load(open(cache / name / "expected.pkl", "rb"))
        t0 = time.time()
        res = TR.graded_run(t)
        ok = res.get("returncode") == 0 and all(res.get(k) is None for k, _ in TR.CHECKS)
        all_ok &= ok
        ratios = ""
        try:
            ro = json.loads((ws / "out/readout.json").read_text())
            se = TR.SE_REF[name]
            q = {f"wave.{w}": ro["effect_by_wave"][w]["estimate"] for w in TR.WAVES}
            q["gate"] = ro["gate_effect"]["estimate"]
            tq = {f"wave.{w}": t["waves"][w] for w in TR.WAVES}
            tq["gate"] = t["gate"]
            ratios = json.dumps({k: round(abs(q[k] - tq[k]) / (TR.TOL_SIGMA * se[k]), 2) for k in q})
        except Exception:
            pass
        verdicts = "  ".join(f"{k}={'ok' if res.get(k) is None else 'FAIL[' + str(res.get(k))[:140] + ']'}"
                             for k, _ in TR.CHECKS)
        print(f"{name:9s} {'PASS' if ok else 'fail'} {time.time() - t0:5.0f}s ratios={ratios} {verdicts}"
              + ("" if res.get("returncode") == 0 else f" rc={res.get('returncode')} {res.get('output', '')[-300:]}"),
              flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    if sys.argv[1] == "build":
        build(Path(sys.argv[2]))
    else:
        sys.exit(run(Path(sys.argv[2]), sys.argv[3]))
