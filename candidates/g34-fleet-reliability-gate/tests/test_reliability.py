"""G34 verifier: the FY27 installed-base reliability run.

Grades the statistical OBJECTS, not the implementation. Nothing here inspects the agent's source
for an estimator name; every check is on the numbers the run produced and on their mutual coherence.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sqlite3
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
HORIZON = 36.0
TRIGGER = 0.28
RUN_LIMIT_S = 900

QUANT = ("unplanned_failure_rate_36m", "overhaul_rate_36m", "retirement_rate_36m",
         "still_original_assembly_36m", "assembly_failure_rate_36m")
TRUTH_KEY = {"unplanned_failure_rate_36m": "cif_failure_36", "overhaul_rate_36m": "cif_overhaul_36",
             "retirement_rate_36m": "cif_retirement_36",
             "still_original_assembly_36m": "survival_36",
             "assembly_failure_rate_36m": "q2_net_failure_36"}


# Tolerance multiplier. Set only from the accepted estimator's own finite-sample behaviour, never
# from any wrong method: SE_REF is itself estimated from a finite number of redraws, several graded
# quantities depend on a thinning risk set and so have heavier-than-normal tails, and twenty numeric
# checks across four extracts must hold simultaneously.
TOL_MULTIPLIER = scenarios.TOL_MULTIPLIER


def _tol(fixture: str, quant: str) -> float:
    return TOL_MULTIPLIER * scenarios.SE_REF[fixture][quant]


def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "fleet_reliability", "analyse",
         "--warehouse", "data/warehouse.sqlite", "--out", "out"],
        cwd=str(cwd), capture_output=True, text=True, timeout=RUN_LIMIT_S,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONPATH": str(cwd),
             "PYTHONDONTWRITEBYTECODE": "1"})


def _read_results(out_dir: Path) -> dict:
    p = out_dir / "analysis_results.json"
    assert p.exists(), "out/analysis_results.json was not written"
    return json.loads(p.read_text())


def _flat(res: dict) -> dict:
    a = res.get("aftermarket") or {}
    e = res.get("engineering") or {}
    return {"unplanned_failure_rate_36m": a.get("unplanned_failure_rate_36m"),
            "overhaul_rate_36m": a.get("overhaul_rate_36m"),
            "retirement_rate_36m": a.get("retirement_rate_36m"),
            "still_original_assembly_36m": a.get("still_original_assembly_36m"),
            "assembly_failure_rate_36m": e.get("assembly_failure_rate_36m")}


def _open_up(root: Path) -> None:
    """The pipeline runs as an unprivileged user; it must be able to traverse the work tree."""
    os.chmod(root, 0o755)
    for parent in root.parents:
        if str(parent) in ("/", "/tmp"):
            break
        try:
            os.chmod(parent, 0o755)
        except OSError:
            pass
    for dirpath, dirnames, filenames in os.walk(root):
        os.chmod(dirpath, 0o755)
        try:
            os.chown(dirpath, 65534, 65534)
        except OSError:
            pass
        for f in filenames:
            try:
                os.chmod(os.path.join(dirpath, f), 0o644)
                os.chown(os.path.join(dirpath, f), 65534, 65534)
            except OSError:
                pass


def _build_fixture(name: str, dest: Path) -> dict:
    spec = scenarios.by_name(name)
    w = world.build(spec)
    world.write_sqlite(w, str(dest))
    return world.truth(w)


@pytest.fixture(scope="session")
def visible_run():
    res = _read_results(WORKSPACE / "out")
    return res


@pytest.fixture(scope="session")
def visible_truth():
    return world.truth(world.build(scenarios.by_name("visible")))


# ----------------------------------------------------------------- integrity
def test_warehouse_unmodified():
    """The extract is the system of record."""
    ref = tempfile.mkdtemp()
    _build_fixture("visible", Path(ref))
    assert world.db_digest(str(WORKSPACE / "data" / "warehouse.sqlite")) == \
        world.db_digest(str(Path(ref) / "data" / "warehouse.sqlite")), \
        "data/warehouse.sqlite differs from the issued extract"


def test_pipeline_runs():
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0, f"pipeline failed: {r.stderr[-2000:]}"


def test_rerun_is_deterministic():
    a = _read_results(WORKSPACE / "out")
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    b = _read_results(WORKSPACE / "out")
    assert a == b, "a second run on the same extract produced different output"


# ----------------------------------------------------------------- schema and bookkeeping
def test_output_schema(visible_run):
    res = visible_run
    assert res.get("horizon_months") == 36
    for k in ("installed_base_units", "event_counts", "units_at_risk", "aftermarket",
              "engineering", "recommendation"):
        assert k in res, f"missing key {k}"
    f = _flat(res)
    for k, v in f.items():
        assert isinstance(v, (int, float)) and v == v, f"{k} is not a number"
        assert -1e-9 <= v <= 1 + 1e-9, f"{k}={v} is not a proportion"
    assert res["recommendation"] in ("expanded", "baseline")


def test_event_counts_and_population(visible_run):
    con = sqlite3.connect(str(WORKSPACE / "data" / "warehouse.sqlite"))
    n = con.execute("SELECT COUNT(*) FROM asset_register").fetchone()[0]
    counts = dict(con.execute("SELECT wo_type, COUNT(*) FROM work_orders GROUP BY wo_type").fetchall())
    con.close()
    res = visible_run
    assert res["installed_base_units"] == n, "installed base is not the units in the extract"
    ec = res["event_counts"]
    for code in ("UNPL_FAIL", "PM_OVHL", "ASSET_RET"):
        assert ec.get(code) == counts.get(code, 0), f"{code} count is wrong"
    assert ec.get("no_work_order") == n - sum(counts.values()), "no_work_order count is wrong"


def test_units_at_risk(visible_run):
    """Units still in service with the original assembly, and still inside the window, by age."""
    ref = tempfile.mkdtemp()
    _build_fixture("visible", Path(ref))
    con = sqlite3.connect(str(Path(ref) / "data" / "warehouse.sqlite"))
    rows = con.execute(
        "SELECT a.commissioned_on, w.wo_date, (SELECT value FROM extract_meta WHERE key='extract_cut_off')"
        " FROM asset_register a LEFT JOIN work_orders w ON a.unit_id = w.unit_id").fetchall()
    con.close()
    from datetime import date
    want = {}
    for age in (12, 24, 36):
        k = 0
        for comm, wo, cut in rows:
            c = date.fromisoformat(comm)
            end = date.fromisoformat(wo) if wo else date.fromisoformat(cut)
            if (end - c).days / 30.4375 > age:
                k += 1
        want[str(age)] = k
    got = visible_run["units_at_risk"]
    for a in ("12", "24", "36"):
        assert abs(int(got.get(a, -1)) - want[a]) <= max(2, int(0.005 * want[a])), \
            f"units_at_risk[{a}]={got.get(a)}, expected about {want[a]}"


# ----------------------------------------------------------------- the statistical objects
def _check_quantities(res, truth, fixture):
    bad = []
    f = _flat(res)
    for q in QUANT:
        tol = _tol(fixture, q)
        err = abs(f[q] - truth[TRUTH_KEY[q]])
        if err > tol:
            bad.append((q, round(err, 5), round(tol, 5)))
    return bad


def test_aftermarket_quantities(visible_run, visible_truth):
    bad = [b for b in _check_quantities(visible_run, visible_truth, "visible")
           if b[0] != "assembly_failure_rate_36m"]
    assert not bad, f"aftermarket outcomes outside tolerance (quantity, error, tolerance): {bad}"


def test_engineering_quantity(visible_run, visible_truth):
    q = "assembly_failure_rate_36m"
    tol = _tol("visible", q)
    err = abs(_flat(visible_run)[q] - visible_truth[TRUTH_KEY[q]])
    assert err <= tol, f"assembly life figure outside tolerance: error {err:.5f} > {tol:.5f}"


def test_two_objects_are_different(visible_run, visible_truth):
    """The two questions have different answers; reporting one number for both is wrong."""
    f = _flat(visible_run)
    gap = f["assembly_failure_rate_36m"] - f["unplanned_failure_rate_36m"]
    true_gap = visible_truth["q2_net_failure_36"] - visible_truth["cif_failure_36"]
    assert gap > 0.5 * true_gap, (
        "the aftermarket and engineering figures are too close together: the same number appears to "
        f"have been used for both questions (gap {gap:.4f}, expected about {true_gap:.4f})")


def test_probability_conservation(visible_run):
    """The four aftermarket outcomes are what happens to the same units: they must sum to one."""
    a = visible_run["aftermarket"]
    s = (a["unplanned_failure_rate_36m"] + a["overhaul_rate_36m"]
         + a["retirement_rate_36m"] + a["still_original_assembly_36m"])
    assert abs(s - 1.0) <= 0.01, f"the four aftermarket outcomes sum to {s:.4f}, not 1"


def test_recommendation(visible_run, visible_truth):
    assert visible_run["recommendation"] == visible_truth["decision"], \
        f"recommendation {visible_run['recommendation']!r}, expected {visible_truth['decision']!r}"


# ----------------------------------------------------------------- hidden extracts
@pytest.mark.parametrize("fixture", [s["name"] for s in scenarios.HIDDEN_SPECS])
def test_hidden_extract(fixture):
    """The same run on other quarterly extracts."""
    work = Path(tempfile.mkdtemp()) / "ws"
    shutil.copytree(WORKSPACE, work, ignore=shutil.ignore_patterns("out", "data", "__pycache__"))
    truth = _build_fixture(fixture, work)
    _open_up(work)
    r = _run_pipeline(work)
    assert r.returncode == 0, f"pipeline failed on {fixture}: {r.stderr[-2000:]}"
    res = _read_results(work / "out")

    bad = _check_quantities(res, truth, fixture)
    a = res["aftermarket"]
    s = (a["unplanned_failure_rate_36m"] + a["overhaul_rate_36m"]
         + a["retirement_rate_36m"] + a["still_original_assembly_36m"])
    problems = []
    if bad:
        problems.append(f"quantities outside tolerance {bad}")
    if abs(s - 1.0) > 0.01:
        problems.append(f"aftermarket outcomes sum to {s:.4f}")
    if res["recommendation"] != truth["decision"]:
        problems.append(f"recommendation {res['recommendation']!r} expected {truth['decision']!r}")
    assert not problems, f"{fixture}: " + "; ".join(problems)
