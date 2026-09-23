"""G42 verifier: the trailing-twelve-month recordable incident rate.

Grades the quantities the client's access requirement is written on, not the implementation. Nothing
here reads the agent's source; every check is on the numbers the run produces, against the same
quantities recomputed from the extract by the shipped generator.

The graded quantities are deterministic functions of the extract, so they are graded to the precision
the output contract states: hours to the cent, cases exactly, rates to four decimals.
"""
from __future__ import annotations

import csv
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
HOURS_TOL = 0.01
RATE_TOL = 0.0001


def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "safety_rate", "rate", "--warehouse", "data/warehouse.sqlite", "--out", "out"],
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


def _read_outputs(out_dir: Path):
    rp = out_dir / "readout.json"
    sp = out_dir / "site_rates.csv"
    assert rp.exists(), "out/readout.json was not written"
    assert sp.exists(), "out/site_rates.csv was not written"
    readout = json.loads(rp.read_text())
    with open(sp) as fh:
        sites = [r for r in csv.DictReader(fh)]
    return readout, sites


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


def _check_extract(name: str, root: Path, bad: list):
    shutil.copytree(WORKSPACE, root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("out", "data", "__pycache__", ".git"))
    w, truth = _build_fixture(name, root)
    _open_up(root)
    r = _run_pipeline(root)
    if r.returncode != 0:
        bad.append(f"{name}: pipeline failed: {r.stderr[-1500:]}")
        return
    readout, sites = _read_outputs(root / "out")

    if readout.get("window_start") != truth["window_start"] or readout.get("window_end") != truth["window_end"]:
        bad.append(f"{name}: window {readout.get('window_start')}..{readout.get('window_end')}, "
                   f"the contract window is {truth['window_start']}..{truth['window_end']}")
    h = _num(readout.get("hours_worked"))
    if h is None or abs(h - truth["hours_worked"]) > HOURS_TOL:
        bad.append(f"{name}: hours_worked {readout.get('hours_worked')}, hours actually worked in the "
                   f"window total {truth['hours_worked']}")
    if readout.get("recordable_cases") != truth["recordable_cases"]:
        bad.append(f"{name}: recordable_cases {readout.get('recordable_cases')}, "
                   f"the extract has {truth['recordable_cases']}")
    rate = _num(readout.get("rate"))
    if rate is None or abs(rate - truth["rate"]) > RATE_TOL:
        bad.append(f"{name}: rate {readout.get('rate')}, the contract rate is {truth['rate']}")
    if readout.get("access_decision") != truth["decision"]:
        bad.append(f"{name}: access_decision {readout.get('access_decision')!r}, "
                   f"expected {truth['decision']!r}")

    got_sites = readout.get("rate_by_site") or {}
    want = truth["rate_by_site"]
    missing = sorted(set(want) - set(got_sites))
    extra = sorted(set(got_sites) - set(want))
    if missing:
        bad.append(f"{name}: rate_by_site is missing {len(missing)} site(s) with hours worked, e.g. {missing[:4]}")
    if extra:
        bad.append(f"{name}: rate_by_site has {len(extra)} site(s) with no hours worked, e.g. {extra[:4]}")
    off = []
    for s in sorted(set(want) & set(got_sites)):
        v = _num(got_sites[s])
        if v is None or abs(v - want[s]) > RATE_TOL:
            off.append(f"{s}: {got_sites[s]} vs {want[s]}")
    if off:
        bad.append(f"{name}: {len(off)} site rate(s) wrong, e.g. {off[:3]}")

    # site_rates.csv must agree with the readout it is published alongside
    csv_rates = {}
    for row in sites:
        v = _num(row.get("rate"))
        if row.get("site_id"):
            csv_rates[row["site_id"]] = v
    if csv_rates and set(csv_rates) != set(got_sites):
        bad.append(f"{name}: site_rates.csv covers {len(csv_rates)} sites, rate_by_site covers {len(got_sites)}")
    for s, v in csv_rates.items():
        if s in got_sites and (v is None or abs(v - _num(got_sites[s])) > RATE_TOL):
            bad.append(f"{name}: site_rates.csv disagrees with rate_by_site for {s}")
            break


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
    readout, sites = _read_outputs(WORKSPACE / "out")
    for k in ("window_start", "window_end", "hours_worked", "recordable_cases", "rate",
              "rate_by_site", "access_decision"):
        assert k in readout, f"readout.json is missing {k!r}"
    assert isinstance(readout["recordable_cases"], int), "recordable_cases must be a whole number"
    assert isinstance(readout["rate_by_site"], dict), "rate_by_site must be an object keyed by site_id"
    assert readout["access_decision"] in ("suspend", "clear")
    if sites:
        assert set(sites[0].keys()) >= {"site_id", "hours_worked", "recordable_cases", "rate"}, \
            "site_rates.csv must have site_id, hours_worked, recordable_cases, rate"


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
