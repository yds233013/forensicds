#!/usr/bin/env python3
"""Dev: build a world with spec overrides, run the incident-time pipeline, probe AUCs.

usage: tune.py '<json overrides merged into VISIBLE_SPEC (nested dicts merged one level)>' [spec_name]
"""
import copy
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parents[2] / "candidates/02-renewal-risk-regression"
sys.path.insert(0, str(TASK / "environment/build"))
import world  # noqa: E402

over = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
spec = copy.deepcopy(world.VISIBLE_SPEC)
if len(sys.argv) > 2:
    sys.path.insert(0, str(TASK / "tests"))
    from scenarios import HIDDEN_SPECS
    spec = copy.deepcopy(next(s for s in HIDDEN_SPECS if s["name"] == sys.argv[2]))
for k, v in over.items():
    if isinstance(v, dict):
        spec[k].update(v)
    else:
        spec[k] = v
root = Path(tempfile.mkdtemp())
world.build(spec, root)
shutil.copytree(TASK / "environment/workspace/src", root / "src")
shutil.copytree(TASK / "environment/workspace/config", root / "config")
cmd = [sys.executable, "-m", "renewal_risk", "run", "--config", "config/pipeline.toml", "--as-of", spec["extract_date"]]
subprocess.run(cmd, cwd=root, env={"PYTHONPATH": str(root / "src"), "PATH": "/usr/bin:/bin"}, check=True, capture_output=True)
print(json.dumps(over))
subprocess.run([sys.executable, str(Path(__file__).parent / "probe.py"), str(root), spec["extract_date"]])
print(root)
