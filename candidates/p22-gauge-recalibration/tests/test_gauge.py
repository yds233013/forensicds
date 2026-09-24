"""P22 verifier: the MAN-4471 yield step.

Grades the scientific quantities beneath the supplier decision, not the implementation. Nothing here reads the
agent's source; every check is on the numbers it produced and on their internal consistency.

Criteria are accumulated and written to /logs/verifier/criteria.json, which tests/test.sh folds into
reward.json alongside the binary headline reward. A criterion is 1 only if it holds on every graded extract.
"""
from __future__ import annotations

import atexit
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
import tolerances as TOL  # noqa: E402
import world  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", sys.executable)
RUN_LIMIT_S = 1200

CRITERIA = [
    "evidence_reconstruction",
    "scientific_object",
    "identification",
    "estimator_implementation",
    "quantitative_results",
    "independent_validation",
    "decision",
]
_state = {c: 1 for c in CRITERIA}
_notes: list[str] = []


def _fail(criterion: str, msg: str):
    _state[criterion] = 0
    _notes.append(f"{criterion}: {msg}")


@atexit.register
def _dump():
    out = Path("/logs/verifier")
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / "criteria.json").write_text(json.dumps(_state, sort_keys=True) + "\n")
        (out / "criteria_notes.txt").write_text("\n".join(_notes) + "\n")
    except OSError:
        pass


# ------------------------------------------------------------------ running the agent's pipeline
def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "quality", "report", "--db", "data/inspection.sqlite", "--out", "out"],
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


def _build_fixture(name: str, dest: Path):
    spec = scenarios.by_name(name)
    w = world.build(spec)
    world.write_sqlite(w, str(dest))
    return w, world.truth(w)


def _read_outputs(out_dir: Path):
    rp = out_dir / "readout.json"
    assert rp.exists(), "out/readout.json was not written"
    readout = json.loads(rp.read_text())
    cp = out_dir / "part_dispositions.csv"
    rows = None
    if cp.exists():
        with open(cp) as fh:
            rows = list(csv.DictReader(fh))
    return readout, rows


# ------------------------------------------------------------------ the graded comparison
def _num(readout, key):
    v = readout.get(key)
    return float(v) if isinstance(v, (int, float)) else None


def _check_extract(name: str, root: Path):
    shutil.copytree(WORKSPACE, root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("out", "data", "__pycache__", ".git"))
    w, t = _build_fixture(name, root)
    _open_up(root)
    r = _run_pipeline(root)
    if r.returncode != 0:
        for c in CRITERIA:
            _fail(c, f"{name}: pipeline failed: {r.stderr[-400:]}")
        pytest.fail(f"{name}: pipeline failed: {r.stderr[-1500:]}")
    readout, csv_rows = _read_outputs(root / "out")
    bad: list[str] = []

    def close(key, got, want, tol, crit, unit=""):
        if got is None:
            _fail(crit, f"{name}: {key} missing or not a number")
            bad.append(f"{key}: missing or not a number")
            return False
        if abs(got - want) > tol:
            _fail(crit, f"{name}: {key} {got} vs {want:.3f} (tol {tol})")
            bad.append(f"{key} = {got}{unit}, expected {want:.3f}{unit} +/- {tol}")
            return False
        return True

    # 1. evidence reconstruction: the population and its strata, as currently dispositioned
    close("baseline_nonconforming_rate_pct", _num(readout, "baseline_nonconforming_rate_pct"),
          t["baseline_nonconforming_rate_pct"], TOL.RATE_DIRECT_PP, "evidence_reconstruction", " pp")
    close("reported_nonconforming_rate_pct", _num(readout, "reported_nonconforming_rate_pct"),
          t["reported_nonconforming_rate_pct"], TOL.RATE_DIRECT_PP, "evidence_reconstruction", " pp")
    strata = readout.get("strata_nonconforming_rate_pct")
    if not isinstance(strata, dict):
        _fail("evidence_reconstruction", f"{name}: strata_nonconforming_rate_pct missing")
        bad.append("strata_nonconforming_rate_pct missing or not an object")
    else:
        post = [p for p in w["parts"] if p["week"] >= w["spec"]["recal_week"]]
        for key, want in t["strata_nonconforming_rate_pct"].items():
            got = strata.get(key)
            if not isinstance(got, dict):
                _fail("evidence_reconstruction", f"{name}: strata {key} missing")
                bad.append(f"strata_nonconforming_rate_pct.{key} missing")
                continue
            ns = _stratum_counts(w, post, key)
            for lvl, wv in want.items():
                if ns.get(lvl, 0) < TOL.STRATUM_MIN_N:
                    continue
                gv = got.get(str(lvl))
                if gv is None or abs(float(gv) - wv) > TOL.STRATUM_PP:
                    _fail("evidence_reconstruction", f"{name}: strata {key}[{lvl}] {gv} vs {wv:.2f}")
                    bad.append(f"strata {key}[{lvl}] = {gv}, expected {wv:.2f} +/- {TOL.STRATUM_PP}")

    # 2. the scientific object: what the drawing tolerance is stated against
    off = readout.get("conformance_reference_offset_um")
    if not isinstance(off, dict):
        _fail("scientific_object", f"{name}: conformance_reference_offset_um missing")
        bad.append("conformance_reference_offset_um missing or not an object")
    else:
        for machine, want in t["conformance_reference_offset_um"].items():
            got = off.get(machine)
            got = float(got) if isinstance(got, (int, float)) else None
            close(f"conformance_reference_offset_um[{machine}]", got, want, TOL.OFFSET_UM,
                  "scientific_object", " um")

    # 3. identification: the rate against that reference
    close("corrected_nonconforming_rate_pct", _num(readout, "corrected_nonconforming_rate_pct"),
          t["corrected_nonconforming_rate_pct"], TOL.RATE_CORRECTED_PP, "identification", " pp")

    # 4. the estimator, as an artefact: per-part dispositions consistent with the stated rate
    if csv_rows is None:
        _fail("estimator_implementation", f"{name}: out/part_dispositions.csv was not written")
        bad.append("out/part_dispositions.csv was not written")
    else:
        n_post = t["n_post"]
        if len(csv_rows) != n_post:
            _fail("estimator_implementation", f"{name}: csv has {len(csv_rows)} rows, expected {n_post}")
            bad.append(f"part_dispositions.csv has {len(csv_rows)} rows, expected {n_post}")
        vals = [str(r.get("disposition_reference", "")).strip().upper() for r in csv_rows]
        if any(v not in ("PASS", "FAIL") for v in vals):
            _fail("estimator_implementation", f"{name}: csv disposition_reference must be PASS or FAIL")
            bad.append("part_dispositions.csv disposition_reference must be PASS or FAIL")
        elif vals:
            share = 100.0 * sum(1 for v in vals if v == "FAIL") / len(vals)
            stated = _num(readout, "corrected_nonconforming_rate_pct")
            if stated is not None and abs(share - stated) > TOL.CSV_CONSISTENCY_PP:
                _fail("estimator_implementation",
                      f"{name}: csv FAIL share {share:.2f} vs stated {stated}")
                bad.append(f"part_dispositions.csv FAIL share {share:.2f} pp disagrees with "
                           f"corrected_nonconforming_rate_pct {stated}")

    # 5. quantitative results: the attribution
    att = readout.get("attribution_pp")
    if not isinstance(att, dict) or set(att) != set(t["attribution_pp"]):
        _fail("quantitative_results", f"{name}: attribution_pp must have exactly the five named keys")
        bad.append(f"attribution_pp must have exactly {sorted(t['attribution_pp'])}")
    else:
        for k, want in t["attribution_pp"].items():
            got = att.get(k)
            got = float(got) if isinstance(got, (int, float)) else None
            close(f"attribution_pp[{k}]", got, want, TOL.ATTRIBUTION_PP, "quantitative_results", " pp")
        try:
            total = sum(float(v) for v in att.values())
            obs = _num(readout, "reported_nonconforming_rate_pct")
            base = _num(readout, "baseline_nonconforming_rate_pct")
            if obs is not None and base is not None and abs(total - (obs - base)) > TOL.ATTRIBUTION_SUM_PP:
                _fail("quantitative_results", f"{name}: attribution sums to {total:.2f}, change {obs - base:.2f}")
                bad.append(f"attribution_pp sums to {total:.2f} pp but the change is {obs - base:.2f} pp")
        except (TypeError, ValueError):
            _fail("quantitative_results", f"{name}: attribution_pp values must be numbers")
            bad.append("attribution_pp values must be numbers")

    # 6. independent validation: the answer must survive the check that uses no bridge at all - the machine
    #    that was never adjusted measures the same population, so its own rate estimates the corrected rate.
    stated = _num(readout, "corrected_nonconforming_rate_pct")
    if stated is None:
        _fail("independent_validation", f"{name}: no corrected rate to validate")
    else:
        indep = t["cmm2_nonconforming_rate_pct"]
        if abs(stated - indep) > TOL.RATE_CORRECTED_PP + TOL.RATE_DIRECT_PP:
            _fail("independent_validation",
                  f"{name}: corrected rate {stated} is inconsistent with the un-adjusted machine's "
                  f"own rate {indep:.2f}")
            bad.append(f"corrected_nonconforming_rate_pct {stated} is inconsistent with the rate on the "
                       f"machine that was never adjusted ({indep:.2f} pp)")

    # 7. the decision
    got_dec = readout.get("supplier_decision")
    if got_dec != t["supplier_decision"]:
        _fail("decision", f"{name}: supplier_decision {got_dec!r} vs {t['supplier_decision']!r}")
        bad.append(f"supplier_decision = {got_dec!r}, expected {t['supplier_decision']!r}")

    return bad


def _stratum_counts(w, post, key):
    col = {"by_machine": "machine_id", "by_shift": "shift", "by_operator": "operator_id"}.get(key)
    fam = {h["heat_id"]: h["family"] for h in w["heats"]}
    out = {}
    for p in post:
        v = fam[p["heat_id"]] if col is None else p[col]
        out[v] = out.get(v, 0) + 1
    return out


# ------------------------------------------------------------------ integrity and contract
def test_database_unmodified():
    ref = tempfile.mkdtemp()
    _build_fixture("visible", Path(ref))
    assert world.db_digest(str(WORKSPACE / "data" / "inspection.sqlite")) == \
        world.db_digest(str(Path(ref) / "data" / "inspection.sqlite")), \
        "data/inspection.sqlite differs from the issued extract"


def test_pipeline_runs():
    r = _run_pipeline(WORKSPACE)
    if r.returncode != 0:
        for c in CRITERIA:
            _fail(c, "pipeline failed on the issued extract")
    assert r.returncode == 0, f"pipeline failed: {r.stderr[-2000:]}"


def test_rerun_is_deterministic():
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    a = _read_outputs(WORKSPACE / "out")
    r = _run_pipeline(WORKSPACE)
    assert r.returncode == 0
    b = _read_outputs(WORKSPACE / "out")
    if a != b:
        _fail("estimator_implementation", "a second run on the same database produced different outputs")
    assert a == b, "a second run on the same database produced different outputs"


def test_output_schema():
    readout, rows = _read_outputs(WORKSPACE / "out")
    required = ("part_number", "window_pre", "window_post", "baseline_nonconforming_rate_pct",
                "reported_nonconforming_rate_pct", "corrected_nonconforming_rate_pct",
                "conformance_reference_offset_um", "strata_nonconforming_rate_pct", "attribution_pp",
                "supplier_decision")
    missing = [k for k in required if k not in readout]
    if missing:
        _fail("evidence_reconstruction", f"readout.json is missing {missing}")
    assert not missing, f"readout.json is missing {missing}"
    assert readout["supplier_decision"] in ("raise_supplier_nonconformance", "no_supplier_action"), \
        "supplier_decision must be raise_supplier_nonconformance or no_supplier_action"
    assert rows is not None, "out/part_dispositions.csv was not written"
    assert set(rows[0].keys()) >= {"part_id", "machine_id", "measured_um", "disposition_reference"}, \
        "part_dispositions.csv must have part_id, machine_id, measured_um, disposition_reference"


# ------------------------------------------------------------------ the graded extracts
def test_visible_extract():
    root = Path(tempfile.mkdtemp())
    bad = _check_extract("visible", root)
    shutil.rmtree(root, ignore_errors=True)
    assert not bad, "visible extract:\n  " + "\n  ".join(bad)


@pytest.mark.parametrize("fixture", [s["name"] for s in scenarios.HIDDEN_SPECS])
def test_hidden_extract(fixture):
    root = Path(tempfile.mkdtemp())
    bad = _check_extract(fixture, root)
    shutil.rmtree(root, ignore_errors=True)
    assert not bad, f"{fixture}:\n  " + "\n  ".join(bad)
