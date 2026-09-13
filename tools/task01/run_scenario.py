#!/usr/bin/env python3
"""Dev helper: build a scenario world, run a given revrec src tree on it, reconcile.

usage: run_scenario.py <scenario-name|visible> <src_dir> [out_dir]
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / "candidates/01-revenue-reconciliation"
sys.path.insert(0, str(TASK / "tests"))
import world  # noqa: E402  (tests copy)
from scenarios import HIDDEN_SPECS  # noqa: E402

name, src = sys.argv[1], Path(sys.argv[2]).resolve()
out = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(tempfile.mkdtemp())
spec = world.VISIBLE_SPEC if name == "visible" else next(s for s in HIDDEN_SPECS if s["name"] == name)
shutil.copytree(src, out / "src", dirs_exist_ok=True)
shutil.copytree(TASK / "environment/workspace/config", out / "config", dirs_exist_ok=True)
world.build(spec, out)
r = subprocess.run([sys.executable, "-m", "revrec", "run", "--config", "config/pipeline.toml"], cwd=out,
                   env=dict(os.environ, PYTHONPATH=str(out / "src"), REVREC_RUN_TS="dev"), capture_output=True, text=True)
if r.returncode:
    print(r.stdout[-2000:], r.stderr[-3000:])
    sys.exit(1)
subprocess.run([sys.executable, str(Path(__file__).parent / "reconcile.py"), str(out)])
print(out)
