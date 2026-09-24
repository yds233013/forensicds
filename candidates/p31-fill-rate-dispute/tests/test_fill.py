"""P31 verifier: the ambient-grocery fill-rate dispute.

Grades the quantities and the three adjudications beneath the commercial decisions. Nothing here reads the
agent's source.

This task is the defer-or-overturn control, so the graded verdict differs across extracts: the published figure
is right on two of the four, materially wrong on one, and not determinable on one. A constant verdict cannot
pass.

Criteria accumulate into /logs/verifier/criteria.json, which tests/test.sh folds into reward.json beside the
binary headline reward.
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


def _run_pipeline(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [PIPELINE_PYTHON, "-m", "service", "fill", "--db", "data/service.sqlite", "--out", "out"],
        cwd=str(cwd), capture_output=True, text=True, timeout=RUN_LIMIT_S,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONPATH": str(cwd), "PYTHONDONTWRITEBYTECODE": "1"})


def _open_up(root: Path) -> None:
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
    w = world.build(scenarios.by_name(name))
    world.write_sqlite(w, str(dest))
    return w, world.truth(w)


def _read_outputs(out_dir: Path):
    rp = out_dir / "readout.json"
    assert rp.exists(), "out/readout.json was not written"
    readout = json.loads(rp.read_text())
    cp = out_dir / "account_fill.csv"
    rows = None
    if cp.exists():
        with open(cp) as fh:
            rows = list(csv.DictReader(fh))
    return readout, rows


def _num(d, key):
    v = d.get(key) if isinstance(d, dict) else None
    return float(v) if isinstance(v, (int, float)) else None


def _check_extract(name: str, root: Path):
    shutil.copytree(WORKSPACE, root, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("out", "data", "__pycache__", ".git"))
    w, t = _build_fixture(name, root)
    _open_up(root)
    r = _run_pipeline(root)
    if r.returncode != 0:
        for c in CRITERIA:
            _fail(c, f"{name}: pipeline failed")
        pytest.fail(f"{name}: pipeline failed: {r.stderr[-1500:]}")
    readout, acct_rows = _read_outputs(root / "out")
    bad: list[str] = []

    def close(key, got, want, tol, crit):
        if got is None:
            _fail(crit, f"{name}: {key} missing or not a number")
            bad.append(f"{key}: missing or not a number")
            return False
        if abs(got - want) > tol:
            _fail(crit, f"{name}: {key} {got} vs {want:.3f} (tol {tol})")
            bad.append(f"{key} = {got}, expected {want:.3f} +/- {tol}")
            return False
        return True

    # 1. evidence reconstruction: both published figures reproduced from the order book
    close("published_rate_pct", _num(readout, "published_rate_pct"), t["published_rate_pct"],
          TOL.RATE_PP, "evidence_reconstruction")
    close("fill_rate_supplier_definition_pct", _num(readout, "fill_rate_supplier_definition_pct"),
          t["fill_rate_supplier_definition_pct"], TOL.RATE_PP, "evidence_reconstruction")

    # 2. the scientific object: the figure the agreement defines, and the range it admits
    close("fill_rate_contract_pct", _num(readout, "fill_rate_contract_pct"), t["fill_rate_contract_pct"],
          TOL.RATE_PP, "scientific_object")
    close("fill_rate_contract_low_pct", _num(readout, "fill_rate_contract_low_pct"),
          t["fill_rate_contract_low_pct"], TOL.RATE_PP, "scientific_object")
    close("fill_rate_contract_high_pct", _num(readout, "fill_rate_contract_high_pct"),
          t["fill_rate_contract_high_pct"], TOL.RATE_PP, "scientific_object")
    gd = readout.get("governing_definition")
    if gd != t["governing_definition"]:
        _fail("scientific_object", f"{name}: governing_definition {gd!r} vs {t['governing_definition']!r}")
        bad.append(f"governing_definition = {gd!r}, expected {t['governing_definition']!r}")

    # 3. identification: the bridge between the two definitions
    br = readout.get("bridge_pp")
    if not isinstance(br, dict) or set(br) != set(t["bridge_pp"]):
        _fail("identification", f"{name}: bridge_pp must have exactly the five named keys")
        bad.append(f"bridge_pp must have exactly {sorted(t['bridge_pp'])}")
    else:
        for k, want in t["bridge_pp"].items():
            close(f"bridge_pp[{k}]", _num(br, k), want, TOL.BRIDGE_PP, "identification")

    # 4. the estimator as an artefact: the per-account file must agree with the readout
    if acct_rows is None:
        _fail("estimator_implementation", f"{name}: out/account_fill.csv was not written")
        bad.append("out/account_fill.csv was not written")
    else:
        try:
            csv_below = sum(1 for r in acct_rows if str(r["below_floor"]).strip() in ("1", "True", "true"))
            csv_rates = {r["account_id"]: float(r["fill_rate_pct"]) for r in acct_rows}
        except (KeyError, ValueError, TypeError):
            csv_below, csv_rates = None, {}
            _fail("estimator_implementation", f"{name}: account_fill.csv columns are malformed")
            bad.append("account_fill.csv must have numeric fill_rate_pct and a 0/1 below_floor")
        claimed = readout.get("accounts_below_floor")
        if csv_below is not None and isinstance(claimed, int) and abs(csv_below - claimed) > 0:
            _fail("estimator_implementation",
                  f"{name}: csv marks {csv_below} accounts below the floor, readout claims {claimed}")
            bad.append(f"account_fill.csv marks {csv_below} accounts below the floor but the readout "
                       f"claims {claimed}")
        # the accounts that escalated are materially below the floor, and their rates are robust
        for aid, want in t["account_fill_pct"].items():
            got = csv_rates.get(aid)
            if got is None or abs(got - want) > TOL.ACCOUNT_RATE_PP:
                _fail("estimator_implementation", f"{name}: csv rate for {aid} {got} vs {want:.2f}")
                bad.append(f"account_fill.csv rate for {aid} = {got}, expected {want:.2f}")

    # 5. quantitative results: the tail and the ticket reconciliation
    n_below = readout.get("accounts_below_floor")
    if not isinstance(n_below, int) or abs(n_below - t["accounts_below_floor"]) > TOL.BELOW_FLOOR_COUNT:
        _fail("quantitative_results",
              f"{name}: accounts_below_floor {n_below} vs {t['accounts_below_floor']}")
        bad.append(f"accounts_below_floor = {n_below}, expected {t['accounts_below_floor']} "
                   f"+/- {TOL.BELOW_FLOOR_COUNT}")
    af = readout.get("account_fill_pct")
    if not isinstance(af, dict):
        _fail("quantitative_results", f"{name}: account_fill_pct missing")
        bad.append("account_fill_pct missing or not an object")
    else:
        for aid, want in t["account_fill_pct"].items():
            close(f"account_fill_pct[{aid}]", _num(af, aid), want, TOL.ACCOUNT_RATE_PP,
                  "quantitative_results")
    close("returns_driven_ticket_share_pct", _num(readout, "returns_driven_ticket_share_pct"),
          t["returns_driven_ticket_share_pct"], TOL.TICKET_SHARE_PP, "quantitative_results")

    # 6. independent validation: the bridge must close, and the range must contain the point estimate
    if isinstance(br, dict):
        try:
            total = sum(float(v) for v in br.values())
            c, s = _num(readout, "fill_rate_contract_pct"), _num(readout, "fill_rate_supplier_definition_pct")
            if c is None or s is None:
                _fail("independent_validation", f"{name}: cannot close the bridge")
            elif abs(total - (s - c)) > TOL.BRIDGE_SUM_PP:
                _fail("independent_validation",
                      f"{name}: bridge sums to {total:.3f}, gap is {s - c:.3f}")
                bad.append(f"bridge_pp sums to {total:.3f} pp but the gap between the definitions "
                           f"is {s - c:.3f} pp")
        except (TypeError, ValueError):
            _fail("independent_validation", f"{name}: bridge_pp values must be numbers")
            bad.append("bridge_pp values must be numbers")
    else:
        _fail("independent_validation", f"{name}: no bridge to close")
    lo, pt, hi = (_num(readout, "fill_rate_contract_low_pct"), _num(readout, "fill_rate_contract_pct"),
                  _num(readout, "fill_rate_contract_high_pct"))
    if None not in (lo, pt, hi) and not (lo - 1e-9 <= pt <= hi + 1e-9):
        _fail("independent_validation", f"{name}: {lo} <= {pt} <= {hi} does not hold")
        bad.append(f"fill_rate_contract_pct {pt} is outside the range [{lo}, {hi}] it reports")

    # 7. the adjudications
    for key in ("incumbent_verdict", "bonus_gate_met", "supplier_claim_payable"):
        got, want = readout.get(key), t[key]
        if got != want:
            _fail("decision", f"{name}: {key} {got!r} vs {want!r}")
            bad.append(f"{key} = {got!r}, expected {want!r}")
    return bad


def test_database_unmodified():
    ref = tempfile.mkdtemp()
    _build_fixture("visible", Path(ref))
    assert world.db_digest(str(WORKSPACE / "data" / "service.sqlite")) == \
        world.db_digest(str(Path(ref) / "data" / "service.sqlite")), \
        "data/service.sqlite differs from the issued extract"


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
        _fail("estimator_implementation", "a second run produced different outputs")
    assert a == b, "a second run on the same database produced different outputs"


def test_output_schema():
    readout, rows = _read_outputs(WORKSPACE / "out")
    required = ("period", "fill_rate_contract_pct", "fill_rate_contract_low_pct",
                "fill_rate_contract_high_pct", "fill_rate_supplier_definition_pct", "published_rate_pct",
                "bridge_pp", "account_fill_pct", "accounts_below_floor",
                "returns_driven_ticket_share_pct", "governing_definition", "incumbent_verdict",
                "bonus_gate_met", "supplier_claim_payable")
    missing = [k for k in required if k not in readout]
    if missing:
        _fail("evidence_reconstruction", f"readout.json is missing {missing}")
    assert not missing, f"readout.json is missing {missing}"
    assert readout["incumbent_verdict"] in (
        "incumbent_correct", "incumbent_incorrect", "not_determinable_from_available_evidence"), \
        "incumbent_verdict is not one of the three allowed values"
    for k in ("bonus_gate_met", "supplier_claim_payable"):
        assert readout[k] in ("yes", "no", "not_determinable"), f"{k} is not one of the three allowed values"
    assert readout["governing_definition"] in (
        "contract_line_fill_confirmed", "supplier_order_fill_requested"), \
        "governing_definition is not one of the two allowed values"
    assert rows is not None, "out/account_fill.csv was not written"
    assert set(rows[0].keys()) >= {"account_id", "lines", "lines_filled", "fill_rate_pct", "below_floor"}, \
        "account_fill.csv must have account_id, lines, lines_filled, fill_rate_pct, below_floor"


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
