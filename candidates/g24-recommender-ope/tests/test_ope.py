"""Verifier for ForensicDS G24 (off-policy evaluation of home-row rankers).

Behavioural checks only; no source inspection. Statistical quantities are graded against the generator's exact policy
values with tolerances derived from the generator itself (3.5 x the standard error of the least efficient accepted
estimator, research/g24/G24_phase0_gate.md).

  A. Source     data/logs.sqlite equals a pristine regeneration of the extract.
  B. Extract    `python -m recs_eval ope` is re-run (outputs deleted first) and graded: the decision table, the
                counterfactual target slates, the policy values and intervals, and the launch decision.
  C. Other      the same command on three unseen extracts with other traffic regimes and other true answers.
"""
from __future__ import annotations

import copy
import csv
import gc
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import truth as T  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
DB_REL = "data/logs.sqlite"
OUT_REL = "out/ope"
RUN_LIMIT_SEC = 1200
TOL_SIGMA = 3.5
POLICIES = ("v6", "v7", "v7_pd")
OUTPUTS = ("decisions.csv", "target_slates.csv", "policy_values.csv", "launch.json")


def pipeline_env() -> dict:
    env = {k: v for k, v in os.environ.items()
           if k not in ("TESTS_DIR", "WORKSPACE", "PIPELINE_PYTHON") and not k.startswith("PYTEST")}
    env["PYTHONPATH"] = str(WORKSPACE)
    return env


def install_db(src: Path) -> None:
    dst = WORKSPACE / DB_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    shutil.copyfile(src, dst)
    try:
        os.chmod(dst, 0o644)
    except OSError:
        pass


def num(v):
    s = "" if v is None else str(v).strip()
    if s == "":
        raise AssertionError("empty numeric field")
    try:
        x = float(s)
    except ValueError:
        raise AssertionError(f"not a number: {v!r}")
    if not math.isfinite(x):
        raise AssertionError(f"not a finite number: {v!r}")
    return x


def run_pipeline() -> dict:
    out = WORKSPACE / OUT_REL
    for name in OUTPUTS:
        (out / name).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "recs_eval", "ope", "--logs", DB_REL, "--out", OUT_REL]
    started = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=pipeline_env(), capture_output=True, text=True,
                           timeout=RUN_LIMIT_SEC + 120)
        rc, text = p.returncode, p.stdout[-2000:] + p.stderr[-4000:]
    except subprocess.TimeoutExpired:
        rc, text = -1, f"timed out after {RUN_LIMIT_SEC + 120} s"
    res = dict(returncode=rc, output=text, seconds=time.monotonic() - started)
    if rc != 0:
        return res
    try:
        with open(out / "decisions.csv", newline="") as fh:
            res["decisions"] = list(csv.DictReader(fh))
        with open(out / "target_slates.csv", newline="") as fh:
            res["slates"] = list(csv.DictReader(fh))
        with open(out / "policy_values.csv", newline="") as fh:
            res["values"] = list(csv.DictReader(fh))
        res["launch"] = json.loads((out / "launch.json").read_text())
        res["raw"] = b"".join((out / n).read_bytes() for n in OUTPUTS)
    except Exception as exc:  # recorded, asserted by the tests
        res["read_error"] = repr(exc)
    return res


CHECKS = ("decisions", "slates", "values", "intervals", "launch")


def graded_run(t: dict) -> dict:
    """Run the pipeline, grade it at once, and keep only the verdicts (outputs are large)."""
    run = run_pipeline()
    res = {k: run[k] for k in ("returncode", "output", "seconds") if k in run}
    if "read_error" in run:
        res["read_error"] = run["read_error"]
    if run["returncode"] == 0 and "read_error" not in run:
        res["raw_hash"] = hashlib.sha256(run["raw"]).hexdigest()
        res["time"] = None if run["seconds"] <= RUN_LIMIT_SEC else f"took {run['seconds']:.0f} s (limit {RUN_LIMIT_SEC})"
        for name, fn in (("decisions", check_decisions), ("slates", check_target_slates), ("values", check_values),
                         ("intervals", check_intervals), ("launch", check_launch)):
            try:
                fn(run, t)
                res[name] = None
            except AssertionError as exc:
                res[name] = str(exc)
            except Exception as exc:  # malformed outputs count as failures
                res[name] = f"{type(exc).__name__}: {exc}"
    del run
    gc.collect()
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier_g24_"))
    pristine = tmp / "pristine"
    w = world.build(copy.deepcopy(world.VISIBLE_SPEC), pristine)
    pristine_db = pristine / DB_REL
    agent_db = WORKSPACE / DB_REL
    backup = tmp / "agent_logs.sqlite"
    c = dict(pristine_digest=world.db_digest(pristine_db), hidden={})
    c["agent_digest"] = world.db_digest(agent_db) if agent_db.exists() else "<missing>"
    if agent_db.exists():
        shutil.copyfile(agent_db, backup)
    try:
        install_db(pristine_db)
        t = T.expected(w)
        del w
        gc.collect()
        c["run1"] = graded_run(t)
        c["run2"] = graded_run(t)
        del t
        for hs in HIDDEN_SPECS:
            root = tmp / hs["name"]
            hw = world.build(copy.deepcopy(hs), root)
            ht = T.expected(hw)
            del hw
            gc.collect()
            install_db(root / DB_REL)
            c["hidden"][hs["name"]] = graded_run(ht)
            del ht
            gc.collect()
            shutil.rmtree(root, ignore_errors=True)
    finally:
        if backup.exists():
            install_db(backup)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"`recs_eval ope` failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"outputs missing or unreadable: {run['read_error']}"


# ------------------------------------------------------------------------------------------- checks


def check_decisions(run: dict, t: dict) -> None:
    """One row per decision and slot: the decision's own slate and the click outcome merged over its serves."""
    rows = run["decisions"]
    need = {"decision_id", "stream", "device", "decided_at", "position", "item_id", "clicked"}
    missing = need - set(rows[0].keys() if rows else [])
    assert not missing, f"decisions.csv is missing columns {sorted(missing)}"
    got = {}
    for r in rows:
        key = (r["decision_id"], int(r["position"]))
        assert key not in got, f"duplicate row for {key}"
        got[key] = r
    want = t["rows"]
    missing = set(want) - set(got)
    extra = set(got) - set(want)
    assert not missing and not extra, (
        f"decision rows differ: {len(missing)} missing (e.g. {sorted(missing)[:3]}), "
        f"{len(extra)} unexpected (e.g. {sorted(extra)[:3]}); decision_id must be the serve_id of the response "
        f"that created the decision")
    bad = []
    for key, r in got.items():
        w = want[key]
        if (r["stream"] != w["stream"] or r["device"] != w["device"] or r["decided_at"] != w["decided_at"]
                or r["item_id"] != w["item_id"] or int(num(r["clicked"])) != w["clicked"]):
            bad.append((key, r["item_id"], w["item_id"], r["clicked"], w["clicked"]))
    assert not bad, f"{len(bad)} decision rows with wrong slate/outcome fields, e.g. {bad[:3]}"


def check_target_slates(run: dict, t: dict) -> None:
    """The slate each ranker would have served, for every decision whose candidate list was logged."""
    rows = run["slates"]
    need = {"decision_id", "policy", "position", "item_id"}
    missing = need - set(rows[0].keys() if rows else [])
    assert not missing, f"target_slates.csv is missing columns {sorted(missing)}"
    got = {(r["decision_id"], r["policy"], int(r["position"])): r["item_id"] for r in rows}
    want = t["slates"]
    miss = set(want) - set(got)
    extra = set(got) - set(want)
    assert not miss and not extra, (f"target slate rows differ: {len(miss)} missing (e.g. {sorted(miss)[:3]}), "
                                    f"{len(extra)} unexpected (e.g. {sorted(extra)[:3]})")
    bad = [(k, got[k], want[k]) for k in want if got[k] != want[k]]
    assert not bad, f"{len(bad)} target slate positions hold the wrong title, e.g. {bad[:3]}"


def _values(run):
    out = {}
    for r in run["values"]:
        assert r["policy"] not in out, f"duplicate row for policy {r['policy']!r} in policy_values.csv"
        out[r["policy"]] = r
    return out


def check_values(run: dict, t: dict) -> None:
    """Policy values and lifts against the generator's exact values."""
    v = _values(run)
    assert set(v) == set(POLICIES), f"policy_values.csv must hold exactly {sorted(POLICIES)}, got {sorted(v)}"
    bad = []
    for p in POLICIES:
        tol = TOL_SIGMA * t["se"][p]
        err = num(v[p]["value"]) - t["values"][p]
        if abs(err) > tol:
            bad.append(("value", p, round(err, 5), round(tol, 5)))
    for p in ("v7", "v7_pd"):
        tol = TOL_SIGMA * t["se_lift"][p]
        err = num(v[p]["lift_vs_v6"]) - t["lifts"][p]
        if abs(err) > tol:
            bad.append(("lift", p, round(err, 5), round(tol, 5)))
    assert not bad, f"policy values outside tolerance (quantity, policy, error, tolerance): {bad}"


def check_intervals(run: dict, t: dict) -> None:
    """Intervals must contain their own estimate, be of a sane width, and cover the truth when widened."""
    v = _values(run)
    bad = []
    for p in POLICIES:
        val, lo, hi = num(v[p]["value"]), num(v[p]["ci_low"]), num(v[p]["ci_high"])
        ref = 2 * 1.96 * t["se"][p]
        w = hi - lo
        if not (lo <= val <= hi):
            bad.append(("value interval does not contain the estimate", p, lo, val, hi))
        elif not (0.10 * ref <= w <= 3.0 * ref):
            bad.append(("value interval width", p, round(w, 5), round(ref, 5)))
        elif not (val - w <= t["values"][p] <= val + w):
            bad.append(("value interval does not cover truth when doubled", p, round(val, 5),
                        round(t["values"][p], 5)))
    for p in ("v7", "v7_pd"):
        lift, lo, hi = num(v[p]["lift_vs_v6"]), num(v[p]["lift_ci_low"]), num(v[p]["lift_ci_high"])
        ref = 2 * 1.96 * t["se_lift"][p]
        w = hi - lo
        if not (lo <= lift <= hi):
            bad.append(("lift interval does not contain the estimate", p, lo, lift, hi))
        elif not (0.10 * ref <= w <= 3.0 * ref):
            bad.append(("lift interval width", p, round(w, 5), round(ref, 5)))
        elif not (lift - w <= t["lifts"][p] <= lift + w):
            bad.append(("lift interval does not cover truth when doubled", p, round(lift, 5),
                        round(t["lifts"][p], 5)))
    assert not bad, f"intervals unusable: {bad}"


def check_launch(run: dict, t: dict) -> None:
    got = (run["launch"] or {}).get("launch")
    assert got == t["launch"], f"launch decision {got!r}, expected {t['launch']!r}"


# ------------------------------------------------------------------------------------------- A. source


def test_logs_unmodified(ctx):
    """data/logs.sqlite is the system of record and is unchanged."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/logs.sqlite differs from the extract"


# ------------------------------------------------------------------------------------------- B. this extract


def test_ope_succeeds(ctx):
    """`python -m recs_eval ope` succeeds and writes the four outputs."""
    require_run(ctx["run1"])


def test_run_time(ctx):
    """An evaluation finishes within 20 minutes."""
    require_run(ctx["run1"])
    assert ctx["run1"]["seconds"] <= RUN_LIMIT_SEC, f"took {ctx['run1']['seconds']:.0f} s (limit {RUN_LIMIT_SEC})"


def _verdict(run: dict, name: str) -> None:
    require_run(run)
    assert run.get(name) is None, run.get(name)


def test_decision_table(ctx):
    """One row per decision and slot, with the decision's slate and the click outcome merged over its serves."""
    _verdict(ctx["run1"], "decisions")


def test_target_slates(ctx):
    """The row each ranker would have served, for every decision with a logged candidate list."""
    _verdict(ctx["run1"], "slates")


def test_policy_values(ctx):
    """Policy values and lifts within tolerance of the generator's exact values."""
    _verdict(ctx["run1"], "values")


def test_intervals(ctx):
    """Intervals contain their estimate, have a sane width and cover truth when widened."""
    _verdict(ctx["run1"], "intervals")


def test_launch_decision(ctx):
    """The launch decision under the workspace's launch policy."""
    _verdict(ctx["run1"], "launch")


def test_rerun_is_deterministic(ctx):
    """Re-running on the same extract reproduces the outputs byte for byte."""
    require_run(ctx["run1"])
    require_run(ctx["run2"])
    assert ctx["run1"]["raw_hash"] == ctx["run2"]["raw_hash"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. other extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_tables(ctx, name):
    """Other extracts: decision table and target slates."""
    run = ctx["hidden"][name]
    _verdict(run, "decisions")
    _verdict(run, "slates")


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_values_and_launch(ctx, name):
    """Other extracts: values, intervals and launch decision."""
    run = ctx["hidden"][name]
    for k in ("values", "intervals", "launch", "time"):
        _verdict(run, k)
