"""Verifier for ForensicDS G05 (SCO 2.0 tranche-2 continuation gate).

Behavioural checks only; no source inspection. Causal quantities are graded against the generator's exact potential-
outcome effects with tolerances of 3.5 x a reference standard error (research/g05/G05_phase0_gate.md).

  A. Source     data/warehouse.sqlite equals a pristine regeneration of the extract.
  B. Extract    `python -m sco_readout gate` is re-run (outputs deleted first) and graded: the analysis panel
                (actual go-live, event weeks, comparable trading weeks, log net sales), each live wave's run-rate
                uplift, the tranche-2 gate figure, intervals, and the decision.
  C. Other      the same command on three unseen warehouses with other chains, calendars and true answers.
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
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import world  # noqa: E402
from scenarios import HIDDEN_SPECS, SE_REF  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
DB_REL = "data/warehouse.sqlite"
OUT_REL = "out"
OUTPUTS = ("analysis_panel.csv", "readout.json")
RUN_LIMIT_SEC = 1200
TOL_SIGMA = 3.5
WAVES = ("1", "2", "3", "4")


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
    except (TypeError, ValueError):
        raise AssertionError(f"not a number: {v!r}")
    if not math.isfinite(x):
        raise AssertionError(f"not a finite number: {v!r}")
    return x


def expected(w) -> dict:
    t = world.truth(w)
    return {"panel": world.expected_panel(w), "waves": t["effect_by_wave"], "gate": t["gate_effect"],
            "decision": t["decision"], "name": w["spec"]["name"]}


def run_pipeline() -> dict:
    out = WORKSPACE / OUT_REL
    for n in OUTPUTS:
        (out / n).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "sco_readout", "gate", "--warehouse", DB_REL, "--out", OUT_REL]
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
        with open(out / "analysis_panel.csv", newline="") as fh:
            res["panel"] = list(csv.DictReader(fh))
        res["readout"] = json.loads((out / "readout.json").read_text())
        res["raw"] = b"".join((out / n).read_bytes() for n in OUTPUTS)
    except Exception as exc:
        res["read_error"] = repr(exc)
    return res


# ------------------------------------------------------------------------------------------- checks


def check_panel(run: dict, t: dict) -> None:
    rows = run["panel"]
    need = {"store_id", "week_start", "wave", "go_live_week", "event_week", "comparable", "log_net_sales"}
    missing = need - set(rows[0].keys() if rows else [])
    assert not missing, f"analysis_panel.csv is missing columns {sorted(missing)}"
    want = t["panel"]
    got = {}
    for r in rows:
        k = (r["store_id"], r["week_start"])
        assert k not in got, f"duplicate panel row {k}"
        got[k] = r
    miss, extra = set(want) - set(got), set(got) - set(want)
    assert not miss and not extra, (f"panel rows differ: {len(miss)} missing (e.g. {sorted(miss)[:2]}), "
                                    f"{len(extra)} unexpected (e.g. {sorted(extra)[:2]})")
    bad = {"wave": [], "go_live_week": [], "event_week": [], "comparable": [], "log_net_sales": []}
    for k, (wave, glw, ev, comp, lns) in want.items():
        r = got[k]
        try:
            if int(num(r["wave"])) != wave:
                bad["wave"].append(k)
        except AssertionError:
            bad["wave"].append(k)
        if (r["go_live_week"] or "").strip() != glw:
            bad["go_live_week"].append((k, r["go_live_week"], glw))
        e = (r["event_week"] or "").strip()
        if ev is None:
            if e != "":
                bad["event_week"].append((k, e, ""))
        else:
            try:
                if int(num(e)) != ev or num(e) != int(num(e)):
                    bad["event_week"].append((k, e, ev))
            except AssertionError:
                bad["event_week"].append((k, e, ev))
        try:
            if int(num(r["comparable"])) != comp:
                bad["comparable"].append((k, r["comparable"], comp))
        except AssertionError:
            bad["comparable"].append((k, r["comparable"], comp))
        try:
            if abs(num(r["log_net_sales"]) - lns) > 1e-6:
                bad["log_net_sales"].append(k)
        except AssertionError:
            bad["log_net_sales"].append(k)
    msgs = [f"{col}: {len(v)} wrong (e.g. {v[:2]})" for col, v in bad.items() if v]
    assert not msgs, "analysis_panel.csv: " + "; ".join(msgs)


def _entry(ro, key):
    e = ro.get(key) if isinstance(ro, dict) else None
    assert isinstance(e, dict), f"readout.json: {key!r} missing or not an object"
    return num(e.get("estimate")), num(e.get("ci_low")), num(e.get("ci_high"))


def _quantities(run):
    ro = run["readout"]
    assert isinstance(ro, dict), "readout.json is not an object"
    waves = ro.get("effect_by_wave")
    assert isinstance(waves, dict), "readout.json: effect_by_wave missing"
    assert set(waves) == set(WAVES), f"effect_by_wave must hold waves {list(WAVES)}, got {sorted(waves)}"
    q = {f"wave.{w}": _entry(waves, w) for w in WAVES}
    q["gate"] = _entry(ro, "gate_effect")
    return q


def _truth_q(t):
    return {**{f"wave.{w}": t["waves"][w] for w in WAVES}, "gate": t["gate"]}


def check_effects(run: dict, t: dict) -> None:
    q, tq, se = _quantities(run), _truth_q(t), SE_REF[t["name"]]
    bad = []
    for k in q:
        tol = TOL_SIGMA * se[k]
        err = q[k][0] - tq[k]
        if abs(err) > tol:
            bad.append((k, round(err, 5), round(tol, 5)))
    assert not bad, f"effects outside tolerance (quantity, error, tolerance): {bad}"


def check_intervals(run: dict, t: dict) -> None:
    q, tq, se = _quantities(run), _truth_q(t), SE_REF[t["name"]]
    bad = []
    for k, (est, lo, hi) in q.items():
        ref = 2 * 1.96 * se[k]
        w = hi - lo
        if not (lo <= est <= hi):
            bad.append(("interval does not contain the estimate", k, lo, est, hi))
        elif not (0.10 * ref <= w <= 3.0 * ref):
            bad.append(("interval width", k, round(w, 5), round(ref, 5)))
        elif not (est - w <= tq[k] <= est + w):
            bad.append(("interval does not cover truth when doubled", k, round(est, 5), round(tq[k], 5)))
    assert not bad, f"intervals unusable: {bad}"


def check_decision(run: dict, t: dict) -> None:
    got = run["readout"].get("decision") if isinstance(run["readout"], dict) else None
    assert got == t["decision"], f"decision {got!r}, expected {t['decision']!r}"


CHECKS = (("panel", check_panel), ("effects", check_effects), ("intervals", check_intervals),
          ("decision", check_decision))


def graded_run(t: dict) -> dict:
    run = run_pipeline()
    res = {k: run[k] for k in ("returncode", "output", "seconds") if k in run}
    if "read_error" in run:
        res["read_error"] = run["read_error"]
    if run["returncode"] == 0 and "read_error" not in run:
        res["raw_hash"] = hashlib.sha256(run["raw"]).hexdigest()
        res["time"] = None if run["seconds"] <= RUN_LIMIT_SEC else f"took {run['seconds']:.0f} s (limit {RUN_LIMIT_SEC})"
        for name, fn in CHECKS:
            try:
                fn(run, t)
                res[name] = None
            except AssertionError as exc:
                res[name] = str(exc)[:3000]
            except Exception as exc:
                res[name] = f"{type(exc).__name__}: {exc}"[:3000]
    del run
    gc.collect()
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier_g05_"))
    agent_db = WORKSPACE / DB_REL
    backup = tmp / "agent_warehouse.sqlite"
    w = world.build_world(copy.deepcopy(world.VISIBLE_SPEC))
    pristine = tmp / "pristine.sqlite"
    world.write_warehouse(w, str(pristine))
    c = dict(pristine_digest=world.db_digest(str(pristine)), hidden={})
    c["agent_digest"] = world.db_digest(str(agent_db)) if agent_db.exists() else "<missing>"
    if agent_db.exists():
        shutil.copyfile(agent_db, backup)
    try:
        install_db(pristine)
        t = expected(w)
        del w
        gc.collect()
        c["run1"] = graded_run(t)
        c["run2"] = graded_run(t)
        del t
        for hs in HIDDEN_SPECS:
            hw = world.build_world(copy.deepcopy(hs))
            hdb = tmp / f"{hs['name']}.sqlite"
            world.write_warehouse(hw, str(hdb))
            ht = expected(hw)
            del hw
            gc.collect()
            install_db(hdb)
            c["hidden"][hs["name"]] = graded_run(ht)
            del ht
            gc.collect()
            hdb.unlink(missing_ok=True)
    finally:
        if backup.exists():
            install_db(backup)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"`sco_readout gate` failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"outputs missing or unreadable: {run['read_error']}"


def _verdict(run: dict, name: str) -> None:
    require_run(run)
    assert run.get(name) is None, run.get(name)


# ------------------------------------------------------------------------------------------- A. source


def test_warehouse_unmodified(ctx):
    """data/warehouse.sqlite is the system of record and is unchanged."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/warehouse.sqlite differs from the extract"


# ------------------------------------------------------------------------------------------- B. this extract


def test_gate_succeeds(ctx):
    """`python -m sco_readout gate` succeeds and writes both outputs."""
    require_run(ctx["run1"])


def test_run_time(ctx):
    """A readout finishes within 20 minutes."""
    require_run(ctx["run1"])
    assert ctx["run1"]["seconds"] <= RUN_LIMIT_SEC, f"took {ctx['run1']['seconds']:.0f} s (limit {RUN_LIMIT_SEC})"


def test_analysis_panel(ctx):
    """Every store-week with its wave, actual go-live week, event week, comparability and log net sales."""
    _verdict(ctx["run1"], "panel")


def test_effects(ctx):
    """Each live wave's run-rate uplift and the gate figure, within tolerance of the true causal effects."""
    _verdict(ctx["run1"], "effects")


def test_intervals(ctx):
    """Intervals contain their estimate, have a sane width and cover the truth when widened."""
    _verdict(ctx["run1"], "intervals")


def test_decision(ctx):
    """The tranche-2 decision under the business case's gate."""
    _verdict(ctx["run1"], "decision")


def test_rerun_is_deterministic(ctx):
    """Re-running on the same extract reproduces the outputs byte for byte."""
    require_run(ctx["run1"])
    require_run(ctx["run2"])
    assert ctx["run1"]["raw_hash"] == ctx["run2"]["raw_hash"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. other warehouses

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_panel(ctx, name):
    """Other warehouses: the analysis panel."""
    _verdict(ctx["hidden"][name], "panel")


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_effects_and_decision(ctx, name):
    """Other warehouses: effects, intervals, decision and run time."""
    run = ctx["hidden"][name]
    for k in ("effects", "intervals", "decision", "time"):
        _verdict(run, k)
