"""G41 verifier: the weekly spare-parts rebalance.

Grades the operational state the plan is built on, not the implementation. Nothing here reads the
agent's source; every check is on the numbers and on whether the submitted plan is executable.

The graded quantities are deterministic functions of the extract, so they are graded exactly:
  * total_shortfall_units and shortfall_by_depot: exact integers;
  * transfer_cost: to the cent (the contract says the plan must be the cheapest one achieving that
    shortfall, and costs in the extract carry two decimals);
  * the plan itself must be executable under the availability policy.
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, os.environ.get("TESTS_DIR", "/tests"))
import scenarios  # noqa: E402
import world  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", sys.executable)
RUN_LIMIT_S = 1200
COST_TOL = 0.01


def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "service_parts", "plan", "--warehouse", "data/warehouse.sqlite", "--out", "out"],
        cwd=str(cwd), capture_output=True, text=True, timeout=RUN_LIMIT_S,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONPATH": str(cwd), "PYTHONDONTWRITEBYTECODE": "1"})


def _open_up(root: Path) -> None:
    """pytest's mkdtemp is root-owned mode 700; the planner runs unprivileged and must traverse."""
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


def _read_outputs(out_dir: Path):
    rp = out_dir / "readout.json"
    pp = out_dir / "plan.csv"
    assert rp.exists(), "out/readout.json was not written"
    assert pp.exists(), "out/plan.csv was not written"
    readout = json.loads(rp.read_text())
    with open(pp) as fh:
        plan = [r for r in csv.DictReader(fh)]
    return readout, plan


def _build_fixture(name: str, dest: Path):
    spec = scenarios.by_name(name)
    w = world.build(spec)
    world.write_sqlite(w, str(dest))
    return w, world.truth(w)


def _check_plan_executable(w, plan, bad):
    """Conservative feasibility check on the submitted plan: every shipped unit must leave on a real
    lane, arrive in time for some job it could serve at the destination, and stay within what the
    origin can actually release (shippable on-hand plus inbound that lands inside the horizon).

    Deliberately permissive where a tighter check would need the plan's own unit-to-job assignment:
    it flags plans that are impossible, never plans that are merely hard to verify.
    """
    st = world.state(w)
    t0 = w["t0"]
    horizon_end = t0 + timedelta(days=w["spec"]["horizon_days"])
    releasable = dict(st["shippable"])
    for r in st["inbound"]:
        if r["usable_from"] <= horizon_end:
            k = (r["depot"], r["part"])
            releasable[k] = releasable.get(k, 0) + r["qty"]
    shipped = {}
    for row in plan:
        try:
            q = int(row["qty"])
        except (KeyError, ValueError, TypeError):
            bad.append(f"plan row with a non-integer qty: {row}")
            continue
        if q <= 0:
            bad.append(f"plan row with non-positive qty: {row}")
            continue
        src, dst, part = row.get("from_depot"), row.get("to_depot"), row.get("part_id")
        if src == dst:
            bad.append(f"plan row transfers to the same depot: {row}")
            continue
        lane = w["lanes"].get((src, dst))
        if lane is None:
            bad.append(f"plan uses a lane that does not exist: {src} -> {dst}")
            continue
        shipped[(src, part)] = shipped.get((src, part), 0) + q
        arrive = t0 + timedelta(days=lane["transit_days"])
        if not any(j["depot"] == dst and j["part"] == part and arrive <= j["need_by"] for j in st["jobs"]):
            bad.append(f"transfer {src}->{dst} {part} cannot arrive in time for any scheduled job there")
    for (src, part), q in shipped.items():
        cap = releasable.get((src, part), 0)
        if q > cap:
            bad.append(f"plan ships {q} of {part} from {src}, which can release at most {cap} units "
                       f"(available to promise above safety stock, plus inbound usable this horizon)")


def _check_extract(name: str, root: Path, bad: list):
    # The whole workspace travels, minus the extract and the outputs: an agent may reorganise the
    # planner or add modules of its own, and the run against another extract must still work.
    shutil.copytree(WORKSPACE, root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("out", "data", "__pycache__", ".git"))
    w, truth = _build_fixture(name, root)
    _open_up(root)
    r = _run_pipeline(root)
    if r.returncode != 0:
        bad.append(f"{name}: pipeline failed: {r.stderr[-1500:]}")
        return
    readout, plan = _read_outputs(root / "out")
    if int(readout.get("demand_units", -1)) != truth["demand_units"]:
        bad.append(f"{name}: demand_units {readout.get('demand_units')}, extract has {truth['demand_units']}")
    got = readout.get("total_shortfall_units")
    if got != truth["shortfall"]:
        bad.append(f"{name}: total_shortfall_units {got}, the minimum achievable is {truth['shortfall']}")
    by = {k: int(v) for k, v in (readout.get("shortfall_by_depot") or {}).items() if int(v) != 0}
    if by != {k: v for k, v in truth["shortfall_by_depot"].items()}:
        bad.append(f"{name}: shortfall_by_depot {by}, expected {truth['shortfall_by_depot']}")
    if sum(by.values()) != (got if isinstance(got, int) else -1):
        bad.append(f"{name}: shortfall_by_depot sums to {sum(by.values())}, not total_shortfall_units {got}")
    cost = readout.get("transfer_cost")
    if not isinstance(cost, (int, float)) or abs(float(cost) - truth["transfer_cost"]) > COST_TOL:
        bad.append(f"{name}: transfer_cost {cost}, the cheapest plan achieving that shortfall costs "
                   f"{truth['transfer_cost']}")
    plan_units = sum(int(row["qty"]) for row in plan if str(row.get("qty", "")).lstrip("-").isdigit())
    if int(readout.get("transfer_units", -1)) != plan_units:
        bad.append(f"{name}: transfer_units {readout.get('transfer_units')} does not match plan.csv ({plan_units})")
    if readout.get("expedite_recommendation") != truth["decision"]:
        bad.append(f"{name}: expedite_recommendation {readout.get('expedite_recommendation')!r}, "
                   f"expected {truth['decision']!r}")
    _check_plan_executable(w, plan, bad)


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
    a = _read_outputs(WORKSPACE / "out")
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    b = _read_outputs(WORKSPACE / "out")
    assert a == b, "a second run on the same extract produced different outputs"


def test_output_schema():
    readout, plan = _read_outputs(WORKSPACE / "out")
    for k in ("extract_date", "demand_units", "total_shortfall_units", "shortfall_by_depot",
              "transfer_units", "transfer_cost", "expedite_recommendation"):
        assert k in readout, f"readout.json is missing {k!r}"
    assert isinstance(readout["total_shortfall_units"], int), "total_shortfall_units must be a whole number"
    assert readout["expedite_recommendation"] in ("expedite", "no_expedite")
    if plan:
        assert set(plan[0].keys()) >= {"from_depot", "to_depot", "part_id", "qty"}, \
            "plan.csv must have from_depot, to_depot, part_id, qty"


# ------------------------------------------------------------------------- the planning quantities
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
