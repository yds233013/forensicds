"""G44 verifier: the quarterly performance certificate.

Grades the quantities the service agreement is written on, not the implementation. Nothing here reads
the agent's source; every check is on the numbers the run produces, against the same quantities
recomputed from the extract by the shipped generator.

All graded quantities are deterministic functions of the extract: counts exactly, rates and precisions
to the six decimals the output contract states (compared with a 5e-5 tolerance, which is looser than
the contract's precision and far tighter than any wrong construction in the pre-build panel).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.environ.get("TESTS_DIR", "/tests"))
import scenarios  # noqa: E402
import world  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", sys.executable)
RUN_LIMIT_S = 1800
TOL = 5e-5


def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "screen_perf", "report", "--warehouse", "data/warehouse.sqlite", "--out", "out"],
        cwd=str(cwd), capture_output=True, text=True, timeout=RUN_LIMIT_S,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONPATH": str(cwd), "PYTHONDONTWRITEBYTECODE": "1"})


def _open_up(root: Path) -> None:
    """pytest's mkdtemp is root-owned mode 700; the pipeline runs unprivileged and must traverse."""
    os.chmod(root, 0o755)
    for parent in root.parents:
        if str(parent) in ("/", "/tmp"):
            break
        try:
            os.chmod(parent, 0o755)
        except OSError:
            pass
    for dirpath, _dirnames, filenames in os.walk(root):
        os.chmod(dirpath, 0o755)
        try:
            os.chown(dirpath, 65534, 65534)
        except OSError:
            pass
        for f in filenames:
            p = os.path.join(dirpath, f)
            try:
                os.chmod(p, 0o644)
                os.chown(p, 65534, 65534)
            except OSError:
                pass


def _read_output(out_dir: Path) -> dict:
    p = out_dir / "performance.json"
    assert p.exists(), "out/performance.json was not written"
    return json.loads(p.read_text())


def _build_fixture(name: str, dest: Path):
    spec = scenarios.by_name(name)
    w = world.build(spec)
    world.write_sqlite(w, str(dest))
    return w, world.truth(w)


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


LABELS = {
    "sensitivity": "the share of fraud in the quarter's traffic that the screen flagged",
    "specificity": "the share of legitimate traffic that the screen passed",
    "observed_precision": "the share of Kestrel's own flagged transactions that were fraud",
    "contract_precision": "precision under clause 3.2 of the service agreement",
}


def _check_extract(name: str, root: Path, bad: list):
    shutil.copytree(WORKSPACE, root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("out", "data", "__pycache__", ".git"))
    w, truth = _build_fixture(name, root)
    _open_up(root)
    r = _run_pipeline(root)
    if r.returncode != 0:
        bad.append(f"{name}: pipeline failed: {r.stderr[-1500:]}")
        return
    got = _read_output(root / "out")

    for k in ("window_start", "window_end"):
        if got.get(k) != truth[k]:
            bad.append(f"{name}: {k} {got.get(k)!r}, the extract's window is {truth[k]!r}")
    for k in ("flagged_transactions", "adjudicated_sample_reviews"):
        if got.get(k) != truth[k]:
            bad.append(f"{name}: {k} {got.get(k)}, the extract has {truth[k]}")
    for k, what in LABELS.items():
        v = _num(got.get(k))
        if v is None or abs(v - truth[k]) > TOL:
            bad.append(f"{name}: {k} {got.get(k)}, {what} is {truth[k]}")
    if got.get("decision") != truth["decision"]:
        bad.append(f"{name}: decision {got.get('decision')!r}, expected {truth['decision']!r}")


# ------------------------------------------------------------------------------------ integrity
def test_warehouse_unmodified():
    ref = tempfile.mkdtemp()
    _build_fixture("visible", Path(ref))
    assert world.db_digest(str(WORKSPACE / "data" / "warehouse.sqlite")) == \
        world.db_digest(str(Path(ref) / "data" / "warehouse.sqlite")), \
        "data/warehouse.sqlite differs from the issued extract"


def test_pipeline_runs():
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0, f"pipeline failed: {r.stderr[-2000:]}"


def test_rerun_is_deterministic():
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    a = _read_output(WORKSPACE / "out")
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    assert a == _read_output(WORKSPACE / "out"), "a second run on the same extract produced different outputs"


def test_output_schema():
    got = _read_output(WORKSPACE / "out")
    for k in ("window_start", "window_end", "flagged_transactions", "adjudicated_sample_reviews",
              "sensitivity", "specificity", "observed_precision", "contract_precision", "decision"):
        assert k in got, f"performance.json is missing {k!r}"
    assert isinstance(got["flagged_transactions"], int), "flagged_transactions must be a whole number"
    assert got["decision"] in ("accept", "remediate")
    for k in ("sensitivity", "specificity", "observed_precision", "contract_precision"):
        v = _num(got[k])
        assert v is not None and 0.0 <= v <= 1.0, f"{k} must be a proportion"


# --------------------------------------------------------------------------- the contract quantities
def test_visible_extract():
    bad = []
    root = Path(tempfile.mkdtemp())
    _check_extract("visible", root, bad)
    assert not bad, "visible extract:\n  " + "\n  ".join(bad)
    shutil.rmtree(root, ignore_errors=True)


@pytest.mark.parametrize("fixture", [s["name"] for s in scenarios.HIDDEN_SPECS])
def test_hidden_extract(fixture):
    bad = []
    root = Path(tempfile.mkdtemp())
    _check_extract(fixture, root, bad)
    assert not bad, f"{fixture}:\n  " + "\n  ".join(bad)
    shutil.rmtree(root, ignore_errors=True)
