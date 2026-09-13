#!/usr/bin/env python3
"""Re-run a Task 02 trial's submitted `src/` on pristine visible and hidden extracts and report per-feature
mismatches against the point-in-time reference (independent of the Harbor verifier run).

usage: task02_rerun_agent_code.py <trial_dir> [--only visible hidden_a ...]
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "candidates/02-renewal-risk-regression"
sys.path.insert(0, str(TASK / "tests"))
import reference as ref  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial", type=Path)
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    src = next(p for p in (a.trial / "artifacts").rglob("workspace") if (p / "src/renewal_risk").is_dir()) / "src"
    specs = [("visible", world.VISIBLE_SPEC)] + [(s["name"], s) for s in HIDDEN_SPECS]
    for name, spec in specs:
        if a.only and name not in a.only:
            continue
        root = Path(tempfile.mkdtemp())
        world.build(spec, root)
        as_of = date.fromisoformat(spec["extract_date"])
        data = ref.load(root)
        ex = ref.build_examples(data, as_of)
        good = ref.build_features(data, ex)
        ws = Path(tempfile.mkdtemp())
        shutil.copytree(src, ws / "src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(TASK / "environment/workspace/config", ws / "config")
        (ws / "data").mkdir()
        shutil.copyfile(root / "data/warehouse.db", ws / "data/warehouse.db")
        p = subprocess.run([sys.executable, "-m", "renewal_risk", "features", "--config", "config/pipeline.toml",
                            "--as-of", spec["extract_date"]], cwd=ws, env=dict(os.environ, PYTHONPATH=str(ws / "src")),
                           capture_output=True, text=True)
        if p.returncode:
            print(f"{name}: agent code FAILED\n{p.stderr[-800:]}")
            continue
        got = pd.read_csv(ws / "artifacts/features.csv").set_index("contract_id")
        mism = {}
        for c in ref.FEATURE_COLUMNS:
            n = sum(1 for e in ex if not np.isclose(float(got.loc[e["contract_id"], c]), float(good[e["contract_id"]][c]),
                                                     rtol=1e-6, atol=1e-6))
            if n:
                mism[c] = n
        print(f"{name}: examples={len(ex)} mismatches={mism or 'none'}")


if __name__ == "__main__":
    main()
