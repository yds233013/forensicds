"""Verifier for ForensicDS Task 05 (XP-231 onboarding experiment readout).

Behavioural checks only - no source inspection:

  A. Source integrity   data/product.db equals a pristine regeneration of the extract.
  B. Default date       the agent's readout is re-run (outputs deleted first) for 2026-09-01 and compared with an
                        independent reference (tests/reference.py): unit grain and membership, arm and stratum per
                        unit, outcome per unit, readout recomputed from the unit file, readout vs reference,
                        decision, determinism.
  C. Hidden extracts    the same command on unseen extracts where exposures, identities, assignments and the true
                        effect are produced differently (tests/scenarios.py).
"""
from __future__ import annotations

import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import reference as ref  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
DEFAULT_DATE = date(2026, 9, 1)
DB = "data/product.db"
UNITS = "artifacts/XP-231_units.csv"
SCALARS = ("n_units_control", "n_units_treatment", "rate_control", "rate_treatment", "effect", "se", "ci_low", "ci_high",
           "srm_p_value")


def pipeline_env() -> dict:
    """Environment for the agent's pipeline: no verifier variables."""
    env = {k: v for k, v in os.environ.items() if k not in ("TESTS_DIR", "WORKSPACE", "PIPELINE_PYTHON")}
    env["PYTHONPATH"] = str(WORKSPACE / "src")
    return env


def run_readout(analysis_date: date) -> dict:
    rel = f"reports/experiments/XP-231_readout_{analysis_date.isoformat()}.json"
    for p in (UNITS, rel, "reports/experiments/XP-231_latest.json"):
        (WORKSPACE / p).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "xp_analysis", "readout", "--config", "config/xp231.toml",
           "--analysis-date", analysis_date.isoformat()]
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=pipeline_env(),
                           capture_output=True, text=True, timeout=300)
        rc, out = p.returncode, p.stdout[-2000:] + p.stderr[-4000:]
    except subprocess.TimeoutExpired:
        rc, out = -1, "timed out"
    res = dict(returncode=rc, output=out)
    if rc == 0:
        try:
            with open(WORKSPACE / UNITS, newline="") as fh:
                res["units"] = list(csv.DictReader(fh))
            res["readout"] = json.loads((WORKSPACE / rel).read_text())
            res["latest_same"] = (WORKSPACE / "reports/experiments/XP-231_latest.json").read_bytes() == (WORKSPACE / rel).read_bytes()
            res["raw"] = (WORKSPACE / UNITS).read_bytes() + (WORKSPACE / rel).read_bytes()
        except Exception as exc:  # recorded, asserted by tests
            res["read_error"] = repr(exc)
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier05_"))
    pristine = tmp / "pristine"
    world.build(world.VISIBLE_SPEC, pristine)
    backup = tmp / "agent_product.db"
    shutil.copyfile(WORKSPACE / DB, backup)
    c = dict(agent_digest=world.sqlite_logical_digest(WORKSPACE / DB),
             pristine_digest=world.sqlite_logical_digest(pristine / DB), hidden={})
    try:
        shutil.copyfile(pristine / DB, WORKSPACE / DB)
        rows = ref.units(pristine, DEFAULT_DATE)
        c["ref"] = (rows, ref.readout(rows))
        c["run1"] = run_readout(DEFAULT_DATE)
        c["run2"] = run_readout(DEFAULT_DATE)
        for spec in HIDDEN_SPECS:
            root = tmp / spec["name"]
            world.build(spec, root)
            shutil.copyfile(root / DB, WORKSPACE / DB)
            d = date.fromisoformat(spec["analysis_date"])
            hrows = ref.units(root, d)
            c["hidden"][spec["name"]] = ((hrows, ref.readout(hrows)), run_readout(d))
        shutil.copyfile(pristine / DB, WORKSPACE / DB)
        run_readout(DEFAULT_DATE)
    finally:
        shutil.copyfile(backup, WORKSPACE / DB)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"readout command failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"readout outputs missing or unreadable: {run['read_error']}"


def as_int(v) -> int:
    """Parse a 0/1 outcome written as 0/1, 0.0/1.0 or True/False."""
    t = str(v).strip().lower()
    if t in ("true", "false"):
        return int(t == "true")
    return int(float(t))


def close(a, b, tol=1e-9) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


# ------------------------------------------------------------------------------------------- shared assertions


def check_grain(run: dict) -> None:
    header = set(run["units"][0].keys()) if run["units"] else set()
    missing = {"unit_id", "stratum", "arm", "activated"} - header
    assert not missing, f"{UNITS} is missing columns {sorted(missing)}"
    dup = [k for k, n in Counter(r["unit_id"] for r in run["units"]).items() if n > 1]
    assert not dup, f"{len(dup)} units appear more than once in {UNITS}, e.g. {dup[:5]}"


def check_membership(run: dict, reference) -> None:
    rows, _r = reference
    want = {r["unit_id"] for r in rows}
    got = {r["unit_id"] for r in run["units"]}
    missing, extra = sorted(want - got), sorted(got - want)
    assert not missing and not extra, (
        f"analysis units differ: {len(missing)} expected units missing (e.g. {missing[:4]}), {len(extra)} units that "
        f"should not be analyzed (e.g. {extra[:4]}); expected {len(want)}, got {len(got)}")


def check_unit_values(run: dict, reference) -> None:
    rows, _r = reference
    want = {r["unit_id"]: r for r in rows}
    bad = {"arm": [], "stratum": [], "activated": []}
    for r in run["units"]:
        w = want.get(r["unit_id"])
        if w is None:
            continue
        if r["arm"] != w["arm"]:
            bad["arm"].append((r["unit_id"], r["arm"], w["arm"]))
        if r["stratum"] != w["stratum"]:
            bad["stratum"].append((r["unit_id"], r["stratum"], w["stratum"]))
        if as_int(r["activated"]) != w["activated"]:
            bad["activated"].append((r["unit_id"], r["activated"], w["activated"]))
    assert not any(bad.values()), "unit values differ: " + "; ".join(
        f"{k}: {len(v)} (e.g. {v[:3]})" for k, v in bad.items() if v)


def recomputed(run: dict) -> dict:
    rows = [dict(unit_id=r["unit_id"], stratum=r["stratum"], arm=r["arm"], activated=as_int(r["activated"]))
            for r in run["units"]]
    arms = {r["arm"] for r in rows}
    assert arms == {"control", "treatment"}, f"unit table arms {sorted(arms)} (expected control and treatment)"
    try:
        return ref.readout(rows)
    except (ZeroDivisionError, KeyError, ValueError) as exc:
        raise AssertionError(f"the plan's estimator cannot be applied to the unit table: {exc!r}") from exc


def compare_readout(readout: dict, want: dict, label: str) -> None:
    assert readout.get("experiment_id") == "XP-231", f"{label}: experiment_id {readout.get('experiment_id')}"
    bad = [k for k in SCALARS if not close(readout.get(k), want[k], 1e-6)]
    assert not bad, f"{label}: readout fields differ: " + ", ".join(f"{k}={readout.get(k)} expected {want[k]}" for k in bad)
    assert readout.get("decision") == want["decision"], f"{label}: decision {readout.get('decision')} expected {want['decision']}"
    got = {s.get("stratum"): s for s in readout.get("strata") or []}
    assert set(got) == {s["stratum"] for s in want["strata"]}, f"{label}: strata {sorted(got)}"
    for w in want["strata"]:
        g = got[w["stratum"]]
        for k in ("n_control", "n_treatment", "rate_control", "rate_treatment", "effect", "weight"):
            assert close(g.get(k), w[k], 1e-6), f"{label}: stratum {w['stratum']} {k}={g.get(k)} expected {w[k]}"


# ------------------------------------------------------------------------------------------- A. integrity


def test_product_extract_unmodified(ctx):
    """data/product.db is the authoritative extract and must not be edited."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/product.db content differs from the extract"


# ------------------------------------------------------------------------------------------- B. default date


def test_readout_run_succeeds(ctx):
    """`python -m xp_analysis readout --config config/xp231.toml --analysis-date 2026-09-01` succeeds."""
    require_run(ctx["run1"])


def test_units_one_row_per_unit(ctx):
    """The unit table has one row per analysis unit and the documented columns."""
    require_run(ctx["run1"])
    check_grain(ctx["run1"])
    assert ctx["run1"]["latest_same"], "XP-231_latest.json differs from the dated readout"


def test_analysis_units(ctx):
    """The analyzed units are exactly the population the experiment plan analyzes."""
    require_run(ctx["run1"])
    check_membership(ctx["run1"], ctx["ref"])


def test_unit_arm_stratum_and_outcome(ctx):
    """Each unit carries its analysis arm, its stratum and its primary-metric outcome."""
    require_run(ctx["run1"])
    check_unit_values(ctx["run1"], ctx["ref"])


def test_readout_computed_from_units(ctx):
    """Readout fields equal the plan's estimator applied to the unit table (no patched numbers)."""
    require_run(ctx["run1"])
    compare_readout(ctx["run1"]["readout"], recomputed(ctx["run1"]), "readout vs its own units")


def test_readout_matches_reference(ctx):
    """Effect, CI, per-stratum results, SRM and decision match the reference."""
    require_run(ctx["run1"])
    compare_readout(ctx["run1"]["readout"], ctx["ref"][1], "readout vs reference")


def test_rerun_is_deterministic(ctx):
    """Re-running the readout on the same extract reproduces the unit table and readout byte for byte."""
    require_run(ctx["run2"])
    assert ctx["run1"]["raw"] == ctx["run2"]["raw"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. hidden extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_analysis_units(ctx, name):
    """Other extracts: analysis units, arms, strata and outcomes."""
    reference, run = ctx["hidden"][name]
    require_run(run)
    check_grain(run)
    check_membership(run, reference)
    check_unit_values(run, reference)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_readout(ctx, name):
    """Other extracts: readout computed from the units and matching the reference, including the decision."""
    reference, run = ctx["hidden"][name]
    require_run(run)
    compare_readout(run["readout"], recomputed(run), "readout vs its own units")
    compare_readout(run["readout"], reference[1], "readout vs reference")
