"""G36 verifier: the FY27 residential capacity readout.

Grades the scientific quantities, not the implementation. Nothing here inspects the agent's source
for an estimator name, a package, or a code string; every check is on the numbers the run produced.

Two design decisions carried from earlier tasks:

  * The procurement decision alone can never earn reward. The cheap-solve panel measured a shortcut
    that reproduces four of five decisions while missing the forecast by up to 0.24 kW, so the
    numeric forecast carries the essential weight.

  * Historical fit quality earns nothing. The incumbent model holds out at R2 0.75 on a genuine
    unseen season and is wrong about the target season, because the mechanism it omits did not
    exist during the period it was validated on.
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
CAPACITY_GATE_KW = 3.057
RUN_LIMIT_S = 2400

QUANT = scenarios.QUANT
TOL_MULTIPLIER = scenarios.TOL_MULTIPLIER


def _tol(fixture: str, quant: str) -> float:
    return TOL_MULTIPLIER * scenarios.SE_REF[fixture][quant]


def _truth_values(t):
    return {"target_peak_kw": t["target_peak_mean"],
            "estate_tou_response_at_target_cdd":
                sum(a * b for a, b in zip(t["estate_shares"], t["response_at_target_cdd"]))}


def _open_up(root: Path) -> None:
    """pytest's mkdtemp is root-owned mode 700; the pipeline runs unprivileged and must traverse."""
    os.chmod(root, 0o755)
    for dirpath, _dirnames, filenames in os.walk(root):
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
        [PIPELINE_PYTHON, "-m", "capacity_forecast", "analyse",
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
    assert db.exists(), "the planning extract is missing"
    con = sqlite3.connect(str(db))
    try:
        n = con.execute("SELECT COUNT(*) FROM peak_window_load").fetchone()[0]
        arms = con.execute("SELECT COUNT(DISTINCT assigned_arm) FROM tou_pilot_enrolment"
                           ).fetchone()[0]
        fc = con.execute("SELECT COUNT(*) FROM weather_forecast_2027").fetchone()[0]
    finally:
        con.close()
    assert n > 0, "the load table is empty"
    assert arms == 2, "the pilot's treatment and control arms are not both present"
    assert fc > 0, "the target-season weather outlook is missing"


def test_pipeline_runs(visible_run):
    assert isinstance(visible_run, dict)


def test_rerun_is_deterministic(visible_run):
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    assert _read_results(WORKSPACE / "out") == visible_run, \
        "re-running on the same extract changed the output"


# --------------------------------------------------------------------- schema and bookkeeping
def test_output_schema(visible_run):
    for key in ("n_households", "estate_segment_shares", "target_cdd_mean",
                "segment_target_peak_kw", "estate_tou_response_at_target_cdd",
                "target_peak_kw", "procurement_decision"):
        assert key in visible_run, "missing key %r" % key
    assert isinstance(visible_run["target_peak_kw"], (int, float))
    assert visible_run["procurement_decision"] in ("procure", "defer")


def _bookkeeping(run, db_path, bad):
    con = sqlite3.connect(str(db_path))
    try:
        n = con.execute("SELECT COUNT(*) FROM customer_master").fetchone()[0]
        shares = {s: c / n for s, c in con.execute(
            "SELECT segment_code, COUNT(*) FROM customer_master GROUP BY segment_code")}
        cdd = con.execute(
            "SELECT AVG(cooling_degree_days_forecast) FROM weather_forecast_2027").fetchone()[0]
    finally:
        con.close()
    if run.get("n_households") != n:
        bad.append("n_households: reported %r, extract contains %r" % (run.get("n_households"), n))
    got = run.get("estate_segment_shares") or {}
    if set(got) != set(shares):
        bad.append("estate_segment_shares covers %r, extract has %r"
                   % (sorted(got), sorted(shares)))
    else:
        for s, v in shares.items():
            if abs(float(got[s]) - v) > 1e-6:
                bad.append("estate_segment_shares[%s]: reported %.6f, extract gives %.6f"
                           % (s, float(got[s]), v))
    if abs(float(run.get("target_cdd_mean", -1)) - cdd) > 1e-3:
        bad.append("target_cdd_mean: reported %r, outlook gives %.4f"
                   % (run.get("target_cdd_mean"), cdd))
    return bad


def test_bookkeeping(visible_run):
    bad = _bookkeeping(visible_run, WORKSPACE / "data" / "warehouse.sqlite", [])
    assert not bad, "\n  " + "\n  ".join(bad)


# -------------------------------------------------------------------- the scientific quantities
def test_target_peak_forecast(visible_run, visible_truth):
    """The headline quantity: expected peak-window load with the whole estate on the tariff."""
    tv = _truth_values(visible_truth)["target_peak_kw"]
    got = float(visible_run["target_peak_kw"])
    tol = _tol("visible", "target_peak_kw")
    assert abs(got - tv) <= tol, (
        "target_peak_kw is wrong: reported %.5f, expected %.5f (error %.5f, tolerance %.5f). "
        "The flat-tariff historical relationship does not by itself answer this."
        % (got, tv, abs(got - tv), tol))


def test_estate_tou_response(visible_run, visible_truth):
    """The estate-wide tariff response at the target season's weather.

    Graded because it isolates the transport work: it requires both reweighting the pilot's response
    to the estate and evaluating it at the target season's cooling demand. Per-segment responses are
    deliberately NOT graded - the smallest-response segment has roughly fifty enrolled households
    and its own response is not estimable to any useful tolerance.
    """
    tv = _truth_values(visible_truth)["estate_tou_response_at_target_cdd"]
    got = float(visible_run["estate_tou_response_at_target_cdd"])
    tol = _tol("visible", "estate_tou_response_at_target_cdd")
    assert abs(got - tv) <= tol, (
        "estate_tou_response_at_target_cdd is wrong: reported %.5f, expected %.5f "
        "(error %.5f, tolerance %.5f)" % (got, tv, abs(got - tv), tol))


def test_segment_forecasts_reconcile(visible_run):
    """Segment forecasts must weight to the headline figure.

    This is a coherence check and it is deliberately NOT load-bearing: the incumbent model passes it
    while being wrong by 45 sampling deviations. It is here to catch arithmetic slips, not to
    establish validity.
    """
    seg = visible_run.get("segment_target_peak_kw") or {}
    shares = visible_run.get("estate_segment_shares") or {}
    if not seg or set(seg) != set(shares):
        pytest.skip("segment breakdown not comparable")
    recomposed = sum(float(shares[s]) * float(seg[s]) for s in seg)
    assert abs(recomposed - float(visible_run["target_peak_kw"])) <= 0.02, (
        "segment forecasts weight to %.5f but the headline figure is %.5f"
        % (recomposed, float(visible_run["target_peak_kw"])))


def test_procurement_decision(visible_run, visible_truth):
    assert visible_run["procurement_decision"] == visible_truth["decision"], (
        "procurement_decision %r does not follow from the target-season forecast"
        % visible_run["procurement_decision"])


# --------------------------------------------------------------------------- hidden extracts
@pytest.mark.parametrize("fixture", [s["name"] for s in scenarios.HIDDEN_SPECS])
def test_hidden_extract(fixture):
    spec = scenarios.by_name(fixture)
    w = world.build(spec)
    truth = world.truth(w)
    tv = _truth_values(truth)

    root = Path(tempfile.mkdtemp())
    (root / "data").mkdir(parents=True, exist_ok=True)
    world.write_sqlite(w, str(root / "data"))
    shutil.copytree(WORKSPACE / "capacity_forecast", root / "capacity_forecast")
    _open_up(root)

    r = _run_pipeline(root)
    assert r.returncode == 0, "%s: pipeline failed:\n%s\n%s" % (
        fixture, r.stdout[-2000:], r.stderr[-2000:])
    got = _read_results(root / "out")

    bad = []
    for q in QUANT:
        tol = _tol(fixture, q)
        err = abs(float(got.get(q, 1e9)) - tv[q])
        if err > tol:
            bad.append("%s: reported %s, expected %.5f, error %.5f > tolerance %.5f (%.1f x)"
                       % (q, got.get(q), tv[q], err, tol, err / tol))
    # bookkeeping is re-checked on every extract, so constants from the visible one cannot survive
    _bookkeeping(got, root / "data" / "warehouse.sqlite", bad)
    if got.get("procurement_decision") != truth["decision"]:
        bad.append("procurement_decision %r, expected %r"
                   % (got.get("procurement_decision"), truth["decision"]))
    assert not bad, "%s:\n  %s" % (fixture, "\n  ".join(bad))
    shutil.rmtree(root, ignore_errors=True)
