"""For each mutation, does visible-instance grading catch it, or only the world family?

Runs each mutant's pipeline locally (no Docker, no model) on every extract and compares every graded field
against world.truth() using the task's own frozen tolerances. Reports, per mutant, whether it passes on the
visible extract alone and whether it passes across the whole family.

This is the model-free calibration of the instrument: a mutant that passes visible-only and fails the family is
a procedural defect that single-instance grading cannot see.

    python tools/bench/visible_vs_family.py
"""
from __future__ import annotations

import importlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "bench"))
from check_solution import compare, RUNNERS  # noqa: E402

TASKS = [("p22", "candidates/p22-gauge-recalibration", "quality"),
         ("p20", "candidates/p20-noshow-monitoring", "mlops"),
         ("p31", "candidates/p31-fill-rate-dispute", "service")]


def run_one(task_dir, package, overlay_dir, scenarios, world, tolerances):
    argv, db = RUNNERS[package]
    ws = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(task_dir / "environment/workspace", ws, dirs_exist_ok=True)
    for f in (task_dir / "solution" / package).glob("*.py"):
        shutil.copy(f, ws / package / f.name)
    if overlay_dir:
        for f in sorted(pathlib.Path(overlay_dir).glob("*.py")):
            shutil.copy(f, ws / package / f.name)
    per = {}
    for n in scenarios.ALL_NAMES:
        w = world.build(scenarios.by_name(n))
        world.write_sqlite(w, str(ws))
        r = subprocess.run([sys.executable, *argv, "--db", db, "--out", "out"], cwd=str(ws),
                           env={**os.environ, "PYTHONPATH": str(ws)}, capture_output=True, text=True)
        if r.returncode != 0:
            per[n] = ["pipeline failed"]
            continue
        got = json.loads((ws / "out/readout.json").read_text())
        per[n] = compare(package, got, world.truth(w), tolerances)
    shutil.rmtree(ws, ignore_errors=True)
    return per


def main():
    print("# Visible-instance grading vs world-family grading, over the frozen mutation suites\n")
    print("Model-free. Each mutant is the expert reference procedure with exactly one defect applied.\n")
    grand = {"vis_pass_family_fail": 0, "both_fail": 0, "both_pass": 0, "total": 0}
    rows = []
    for key, rel, package in TASKS:
        task_dir = ROOT / rel
        sys.path.insert(0, str(task_dir / "tests"))
        for m in ("world", "scenarios", "tolerances"):
            sys.modules.pop(m, None)
        world = importlib.import_module("world")
        scenarios = importlib.import_module("scenarios")
        tolerances = importlib.import_module("tolerances")
        expected = {}
        for line in (ROOT / f"tools/{key}/mutations/expected.txt").read_text().splitlines():
            if line.strip():
                mid, want = line.split()
                expected[mid] = int(want)
        for mid, want in sorted(expected.items()):
            per = run_one(task_dir, package, ROOT / f"tools/{key}/mutations/{mid}", scenarios, world, tolerances)
            vis_ok = not per["visible"]
            fam_ok = all(not v for v in per.values())
            rows.append((key, mid, want, vis_ok, fam_ok, {k: len(v) for k, v in per.items()}))
            if want == 0:
                grand["total"] += 1
                if vis_ok and not fam_ok:
                    grand["vis_pass_family_fail"] += 1
                elif not vis_ok:
                    grand["both_fail"] += 1
                else:
                    grand["both_pass"] += 1
            print(f"  {key} {mid:42s} want={want}  visible={'PASS' if vis_ok else 'FAIL'}  "
                  f"family={'PASS' if fam_ok else 'FAIL'}  mismatches/extract={rows[-1][5]}", flush=True)
        sys.path.pop(0)
    print("\n## Summary over the defective mutants (want=0)\n")
    t = grand["total"]
    print(f"  total defective mutants                       : {t}")
    print(f"  caught by visible-instance grading            : {grand['both_fail']}  ({100*grand['both_fail']/t:.0f}%)")
    print(f"  MISSED by visible-only, caught by the family  : {grand['vis_pass_family_fail']}  ({100*grand['vis_pass_family_fail']/t:.0f}%)")
    print(f"  missed by both (instrument blind spot)        : {grand['both_pass']}  ({100*grand['both_pass']/t:.0f}%)")
    json.dump([{"task": r[0], "mutation": r[1], "expected_reward": r[2], "visible_pass": r[3],
                "family_pass": r[4], "mismatches_per_extract": r[5]} for r in rows],
              open(ROOT / "research/mercor_apex/mutation_visible_vs_family.json", "w"), indent=1)


if __name__ == "__main__":
    main()
