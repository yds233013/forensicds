"""G35 verifier: the priority-dispatch rollout readout.

Grades the statistical OBJECTS, not the implementation. Nothing here inspects the agent's source for
an estimator name; every check is on the numbers the run produced.

The central design decision, carried over from the G34 baseline: internal coherence is not
validation. A run whose counts reconcile perfectly, whose dashboard number reproduces exactly, and
whose recommendation is right can still be scientifically wrong, and must fail. Separation therefore
comes from numeric comparison of all three effects against latent truth - never from reconciliation
alone.
"""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, os.environ.get("TESTS_DIR", "/tests"))
import scenarios  # noqa: E402
import world  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
TESTS_DIR = Path(os.environ.get("TESTS_DIR", "/tests"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", sys.executable)
GATE = 0.015
RUN_LIMIT_S = 1800

QUANT = scenarios.QUANT
TOL_MULTIPLIER = scenarios.TOL_MULTIPLIER


def _tol(fixture: str, quant: str) -> float:
    return TOL_MULTIPLIER * scenarios.SE_REF[fixture][quant]


def _open_up(root: Path) -> None:
    """pytest's mkdtemp is root-owned mode 700; the pipeline runs unprivileged and must traverse."""
    os.chmod(root, 0o755)
    for dirpath, dirnames, filenames in os.walk(root):
        os.chmod(dirpath, 0o755)
        try:
            os.chown(dirpath, 65534, 65534)
        except (PermissionError, OSError):
            pass
        for f in filenames:
            p = os.path.join(dirpath, f)
            os.chmod(p, 0o644)
            try:
                os.chown(p, 65534, 65534)
            except (PermissionError, OSError):
                pass


def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "dispatch_experiment", "analyse",
         "--warehouse", "data/warehouse.sqlite", "--out", "out"],
        cwd=str(cwd), capture_output=True, text=True, timeout=RUN_LIMIT_S,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONPATH": str(cwd),
             "PYTHONDONTWRITEBYTECODE": "1"})


def _read_results(out_dir: Path) -> dict:
    p = out_dir / "analysis_results.json"
    assert p.exists(), "out/analysis_results.json was not written"
    return json.loads(p.read_text())


@pytest.fixture(scope="session")
def visible_run():
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0, "pipeline failed:\n%s\n%s" % (r.stdout[-3000:], r.stderr[-3000:])
    return _read_results(WORKSPACE / "out")


@pytest.fixture(scope="session")
def visible_truth():
    return world.truth(world.build(scenarios.by_name("visible")))


# ----------------------------------------------------------------------------------- integrity
def test_warehouse_unmodified():
    db = WORKSPACE / "data" / "warehouse.sqlite"
    assert db.exists(), "the warehouse extract is missing"
    assert world.db_digest(str(db)) == world.db_digest(str(db)), "unstable digest"
    con = sqlite3.connect(str(db))
    try:
        n = con.execute("SELECT COUNT(*) FROM merchant_day_orders").fetchone()[0]
        sat = con.execute("SELECT COUNT(DISTINCT assigned_saturation) FROM block_assignment"
                          ).fetchone()[0]
    finally:
        con.close()
    assert n > 0, "the orders table is empty"
    assert sat == 5, "the saturation arms of the design are not intact"


def test_pipeline_runs(visible_run):
    assert isinstance(visible_run, dict)


def test_rerun_is_deterministic(visible_run):
    tmp = Path(tempfile.mkdtemp())
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    again = _read_results(WORKSPACE / "out")
    assert again == visible_run, "re-running on the same extract changed the output"
    shutil.rmtree(tmp, ignore_errors=True)


# --------------------------------------------------------------------- schema and bookkeeping
def test_output_schema(visible_run):
    for key in ("n_dispatch_blocks", "n_merchant_days", "orders_requested_total",
                "blocks_by_saturation", "effects", "recommendation"):
        assert key in visible_run, "missing key %r" % key
    for q in QUANT:
        assert q in visible_run["effects"], "missing effect %r" % q
        assert isinstance(visible_run["effects"][q], (int, float)), "%s is not numeric" % q
    assert visible_run["recommendation"] in ("launch", "hold")


def test_counts_reconcile(visible_run):
    db = WORKSPACE / "data" / "warehouse.sqlite"
    con = sqlite3.connect(str(db))
    try:
        n_blocks = con.execute("SELECT COUNT(*) FROM block_assignment").fetchone()[0]
        n_rows = con.execute("SELECT COUNT(*) FROM merchant_day_orders").fetchone()[0]
        req = con.execute("SELECT SUM(orders_requested) FROM merchant_day_orders").fetchone()[0]
    finally:
        con.close()
    assert visible_run["n_dispatch_blocks"] == n_blocks
    assert visible_run["n_merchant_days"] == n_rows
    assert visible_run["orders_requested_total"] == req


def test_saturation_arms(visible_run):
    db = WORKSPACE / "data" / "warehouse.sqlite"
    con = sqlite3.connect(str(db))
    try:
        rows = con.execute("SELECT assigned_saturation, COUNT(*) FROM block_assignment "
                           "GROUP BY assigned_saturation").fetchall()
    finally:
        con.close()
    expected = {"%.2f" % s: n for s, n in rows}
    got = {str(k): int(v) for k, v in visible_run["blocks_by_saturation"].items()}
    assert got == expected, "blocks_by_saturation does not match the assignment log"


# -------------------------------------------------------------------- the statistical objects
def _check(fixture, got, truth):
    bad = []
    for q in QUANT:
        tol = _tol(fixture, q)
        err = abs(got["effects"][q] - truth[q])
        if err > tol:
            bad.append("%s: reported %+.5f, expected %+.5f, error %.5f > tolerance %.5f (%.1f x)"
                       % (q, got["effects"][q], truth[q], err, tol, err / tol))
    return bad


def test_direct_effect(visible_run, visible_truth):
    q = "direct_effect_50"
    err = abs(visible_run["effects"][q] - visible_truth[q])
    assert err <= _tol("visible", q), (
        "%s is wrong: reported %+.5f, expected %+.5f (error %.5f, tolerance %.5f)"
        % (q, visible_run["effects"][q], visible_truth[q], err, _tol("visible", q)))


def test_spillover_effect(visible_run, visible_truth):
    q = "spillover_50"
    err = abs(visible_run["effects"][q] - visible_truth[q])
    assert err <= _tol("visible", q), (
        "%s is wrong: reported %+.5f, expected %+.5f (error %.5f, tolerance %.5f)"
        % (q, visible_run["effects"][q], visible_truth[q], err, _tol("visible", q)))


def test_policy_effect(visible_run, visible_truth):
    """The rollout object. This is the quantity the commitment gate is written on."""
    q = "policy_effect_full"
    err = abs(visible_run["effects"][q] - visible_truth[q])
    assert err <= _tol("visible", q), (
        "%s is wrong: reported %+.5f, expected %+.5f (error %.5f, tolerance %.5f). "
        "The pooled treated-minus-control comparison is a different quantity."
        % (q, visible_run["effects"][q], visible_truth[q], err, _tol("visible", q)))


def test_three_objects_are_distinct(visible_run, visible_truth):
    """Reporting one number for several different questions is itself the failure under test."""
    e = visible_run["effects"]
    assert abs(e["direct_effect_50"] - e["policy_effect_full"]) > 1e-6, (
        "the direct effect and the full-rollout effect were reported as the same number; they are "
        "different objects")
    assert abs(e["spillover_50"] - e["policy_effect_full"]) > 1e-6, (
        "the spillover and the full-rollout effect were reported as the same number")


def test_recommendation(visible_run, visible_truth):
    assert visible_run["recommendation"] == visible_truth["decision"], (
        "recommendation %r does not follow from the rollout effect"
        % visible_run["recommendation"])


# --------------------------------------------------------------------------- hidden extracts
@pytest.mark.parametrize("fixture", [s["name"] for s in scenarios.HIDDEN_SPECS])
def test_hidden_extract(fixture):
    spec = scenarios.by_name(fixture)
    w = world.build(spec)
    truth = world.truth(w)

    root = Path(tempfile.mkdtemp())
    (root / "data").mkdir(parents=True, exist_ok=True)
    world.write_sqlite(w, str(root / "data"))
    src = WORKSPACE / "dispatch_experiment"
    shutil.copytree(src, root / "dispatch_experiment")
    _open_up(root)

    r = _run_pipeline(root)
    assert r.returncode == 0, "%s: pipeline failed:\n%s\n%s" % (
        fixture, r.stdout[-2000:], r.stderr[-2000:])
    got = _read_results(root / "out")

    # Bookkeeping is re-checked on every extract, not only the visible one. Checking it only on the
    # visible extract lets a run hard-code that extract's counts and still pass; the hidden extracts
    # are deliberately different sizes, so the same constants cannot survive here.
    con = sqlite3.connect(str(root / "data" / "warehouse.sqlite"))
    try:
        n_blocks = con.execute("SELECT COUNT(*) FROM block_assignment").fetchone()[0]
        n_rows = con.execute("SELECT COUNT(*) FROM merchant_day_orders").fetchone()[0]
        req = con.execute("SELECT SUM(orders_requested) FROM merchant_day_orders").fetchone()[0]
        arms = {"%.2f" % s: n for s, n in con.execute(
            "SELECT assigned_saturation, COUNT(*) FROM block_assignment "
            "GROUP BY assigned_saturation")}
    finally:
        con.close()

    bad = _check(fixture, got, truth)
    for label, expected, actual in (("n_dispatch_blocks", n_blocks, got.get("n_dispatch_blocks")),
                                    ("n_merchant_days", n_rows, got.get("n_merchant_days")),
                                    ("orders_requested_total", req,
                                     got.get("orders_requested_total"))):
        if actual != expected:
            bad.append("%s: reported %r, extract contains %r" % (label, actual, expected))
    if {str(k): int(v) for k, v in got.get("blocks_by_saturation", {}).items()} != arms:
        bad.append("blocks_by_saturation does not match this extract's assignment log")
    if got["recommendation"] != truth["decision"]:
        bad.append("recommendation %r, expected %r" % (got["recommendation"], truth["decision"]))
    assert not bad, "%s:\n  %s" % (fixture, "\n  ".join(bad))
    shutil.rmtree(root, ignore_errors=True)
