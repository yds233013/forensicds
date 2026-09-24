"""Run a task's mutation suite against its real verifier, exactly as Harbor would.

For each mutant: build the task's environment image, overlay the reference solution plus the mutant's changed
modules into /workspace, copy /tests in, run tests/test.sh as root, and read the reward back out of
/logs/verifier/. Reports the binary reward and, where the verifier emits one, the criterion breakdown.

    python tools/bench/mutation_harness.py --task candidates/p22-gauge-recalibration \
        --package quality --mutations tools/p22/mutations --out tools/p22/mutation_results.txt

Shared by P22, P20 and P31. Nothing here is task-specific.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]


def sh(cmd, **kw):
    return subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--package", required=True, help="the workspace package the solution replaces")
    ap.add_argument("--mutations", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="run a single mutation id")
    a = ap.parse_args()

    task = ROOT / a.task
    muts = ROOT / a.mutations
    out_path = ROOT / a.out
    base_tag = f"forensicds-{task.name}-base"

    r = sh(["docker", "build", "-q", "-t", base_tag, str(task / "environment")])
    if r.returncode != 0:
        print("base image build failed:\n" + r.stderr[-3000:])
        return 1

    expected = {}
    for line in (muts / "expected.txt").read_text().splitlines():
        if line.strip():
            mid, want = line.split()
            expected[mid] = int(want)

    lines, n_ok, n_bad = [], 0, 0
    for mid, want in sorted(expected.items()):
        if a.only and mid != a.only:
            continue
        work = pathlib.Path(tempfile.mkdtemp())
        ctx = work / "ctx"
        ctx.mkdir()
        shutil.copytree(task / "solution" / a.package, ctx / a.package)
        shutil.copytree(task / "tests", ctx / "tests")
        for p in ctx.rglob("__pycache__"):
            shutil.rmtree(p, ignore_errors=True)
        for f in sorted((muts / mid).glob("*.py")):
            shutil.copy(f, ctx / a.package / f.name)
        (ctx / "Dockerfile").write_text(
            f"FROM {base_tag}\nCOPY {a.package}/ /workspace/{a.package}/\nCOPY tests/ /tests/\n")
        tag = f"{task.name}-mut:{mid.lower().replace('_', '-')}"
        r = sh(["docker", "build", "-q", "-t", tag, str(ctx)])
        if r.returncode != 0:
            lines.append(f"{mid:<40} want={want} BUILD_FAILED")
            n_bad += 1
            shutil.rmtree(work, ignore_errors=True)
            continue
        r = sh(["docker", "run", "--rm", tag, "bash", "-c",
                "bash /tests/test.sh >/tmp/out.txt 2>&1; cat /logs/verifier/reward.txt; echo; "
                "cat /logs/verifier/reward.json 2>/dev/null || true"])
        parts = [x for x in r.stdout.strip().splitlines() if x.strip()]
        got = parts[0].strip() if parts else "NO_REWARD"
        crit = ""
        if len(parts) > 1:
            try:
                d = json.loads(parts[-1])
                failed = sorted(k.replace("criterion_", "") for k, v in d.items()
                                if k.startswith("criterion_") and not v)
                crit = ("  failed: " + ",".join(failed)) if failed else "  all criteria pass"
            except ValueError:
                crit = ""
        ok = got == str(want)
        n_ok += ok
        n_bad += (not ok)
        lines.append(f"{mid:<40} want={want} got={got} {'OK' if ok else 'UNEXPECTED'}{crit}")
        print(lines[-1], flush=True)
        sh(["docker", "rmi", "-f", tag])
        shutil.rmtree(work, ignore_errors=True)

    lines.append(f"--- mutation suite: {n_ok} as expected, {n_bad} unexpected ---")
    print(lines[-1])
    out_path.write_text("\n".join(lines) + "\n")
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
