"""Verifier for ForensicDS G08 (forecast accuracy under settlement vintages).

Behavioural checks only - no source inspection:

  A. Source     data/warehouse.sqlite equals a pristine regeneration of the extract.
  B. Extract    the agent's `python -m fcaccuracy build` is re-run (outputs deleted first) at the extract's as-of time
                and compared with an independent reference (tests/reference.py): evaluation examples (set, forecast in
                force, KPI month, status, settlement runs, actual and error), monthly KPI, head-to-head, determinism.
  C. Other      the same command on unseen warehouse extracts and as-of times (tests/scenarios.py).
"""
from __future__ import annotations

import copy
import csv
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import reference as ref  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
DB_REL = "data/warehouse.sqlite"
OUT_REL = "out/accuracy"
VISIBLE_AS_OF = "2026-09-22T06:00:00Z"
MWH_TOL = 1e-6
WAPE_TOL = 1e-7
REL_TOL = 1e-6
BUILD_LIMIT_SEC = 600
EXAMPLE_COLS = {"model", "run_date", "issue_id", "region", "portfolio", "target_date", "horizon", "kpi_month",
                "forecast_mwh", "status", "actual_run_ids", "actual_mwh", "abs_error_mwh"}
MONTHLY_COLS = {"model", "kpi_month", "portfolio", "horizon", "n_examples", "n_scored", "abs_error_mwh", "actual_mwh", "wape"}


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
    if s == "" or s.lower() == "nan":
        return None
    try:
        return float(s)
    except ValueError:
        raise AssertionError(f"not a number: {v!r}")


def run_build(as_of: str) -> dict:
    out = WORKSPACE / OUT_REL
    for name in ("evaluation_examples.csv", "monthly_kpi.csv", "summary.json"):
        (out / name).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "fcaccuracy", "build", "--as-of", as_of]
    started = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=pipeline_env(), capture_output=True, text=True,
                           timeout=BUILD_LIMIT_SEC + 60)
        rc, text = p.returncode, p.stdout[-2000:] + p.stderr[-4000:]
    except subprocess.TimeoutExpired:
        rc, text = -1, f"timed out after {BUILD_LIMIT_SEC + 60} s"
    res = dict(returncode=rc, output=text, seconds=time.monotonic() - started)
    if rc != 0:
        return res
    try:
        with open(out / "evaluation_examples.csv", newline="") as fh:
            res["examples"] = list(csv.DictReader(fh))
        with open(out / "monthly_kpi.csv", newline="") as fh:
            res["monthly"] = list(csv.DictReader(fh))
        res["summary"] = json.loads((out / "summary.json").read_text())
        res["raw"] = b"".join((out / n).read_bytes() for n in ("evaluation_examples.csv", "monthly_kpi.csv", "summary.json"))
    except Exception as exc:  # recorded, asserted by tests
        res["read_error"] = repr(exc)
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier_g08_"))
    spec = copy.deepcopy(world.VISIBLE_SPEC)
    spec["artifacts"] = False
    pristine = tmp / "pristine"
    world.build(spec, pristine)
    pristine_db = pristine / DB_REL
    agent_db = WORKSPACE / DB_REL
    backup = tmp / "agent_warehouse.sqlite"
    c = dict(pristine_digest=world.db_digest(pristine_db), hidden={})
    c["agent_digest"] = world.db_digest(agent_db) if agent_db.exists() else "<missing>"
    if agent_db.exists():
        shutil.copyfile(agent_db, backup)
    try:
        install_db(pristine_db)
        c["ref"] = ref.expected(pristine_db, VISIBLE_AS_OF)
        c["run1"] = run_build(VISIBLE_AS_OF)
        c["run2"] = run_build(VISIBLE_AS_OF)
        for hs in HIDDEN_SPECS:
            root = tmp / hs["name"]
            world.build(hs, root)
            install_db(root / DB_REL)
            c["hidden"][hs["name"]] = (ref.expected(root / DB_REL, hs["as_of"]), run_build(hs["as_of"]))
    finally:
        if backup.exists():
            install_db(backup)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"build failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"mart outputs missing or unreadable: {run['read_error']}"


# ------------------------------------------------------------------------------------------- parsing


def example_map(run: dict) -> dict:
    rows = run["examples"]
    missing = EXAMPLE_COLS - set(rows[0].keys() if rows else [])
    assert not missing, f"evaluation_examples.csv is missing columns {sorted(missing)}"
    keys = Counter((r["model"], r["region"], r["portfolio"], r["target_date"], int(float(r["horizon"]))) for r in rows)
    dup = [k for k, n in keys.items() if n > 1]
    assert not dup, f"{len(dup)} duplicate examples (model, region, portfolio, target_date, horizon), e.g. {dup[:3]}"
    return {(r["model"], r["region"], r["portfolio"], r["target_date"], int(float(r["horizon"]))): r for r in rows}


def sample(items, n=5):
    return sorted(items)[:n]


def check_example_set(run, want):
    got = example_map(run)
    missing, extra = set(want["examples"]) - set(got), set(got) - set(want["examples"])
    assert not missing and not extra, (f"example set differs: {len(missing)} missing (e.g. {sample(missing, 4)}), "
                                       f"{len(extra)} unexpected (e.g. {sample(extra, 4)})")


def compare_examples(run, want, fields):
    got = example_map(run)
    bad = []
    for k, w in want["examples"].items():
        g = got.get(k)
        if g is None:
            continue
        for f in fields:
            if f in ("forecast_mwh", "actual_mwh", "abs_error_mwh"):
                gv, wv = num(g[f]), w[f]
                ok = (gv is None and wv is None) or (gv is not None and wv is not None and abs(gv - wv) <= MWH_TOL)
            elif f == "actual_run_ids":
                gv = ";".join(sorted(x for x in (g[f] or "").split(";") if x))
                wv = w[f]
                ok = gv == wv
            else:
                gv, wv = (g[f] or "").strip(), w[f]
                ok = gv == wv
            if not ok:
                bad.append((k, f, gv, wv))
                break
    assert not bad, f"{len(bad)} examples differ (key, field, got, expected), e.g. {bad[:4]}"


def check_monthly(run, want):
    rows = run["monthly"]
    missing = MONTHLY_COLS - set(rows[0].keys() if rows else [])
    assert not missing, f"monthly_kpi.csv is missing columns {sorted(missing)}"
    got = {}
    for r in rows:
        k = (r["model"], r["kpi_month"], r["portfolio"], int(float(r["horizon"])))
        assert k not in got, f"duplicate monthly KPI row {k}"
        got[k] = r
    missing_k, extra_k = set(want["monthly"]) - set(got), set(got) - set(want["monthly"])
    assert not missing_k and not extra_k, (f"monthly KPI rows differ: {len(missing_k)} missing (e.g. {sample(missing_k, 3)}), "
                                           f"{len(extra_k)} unexpected (e.g. {sample(extra_k, 3)})")
    bad = []
    for k, w in want["monthly"].items():
        g = got[k]
        if int(float(g["n_examples"])) != w["n_examples"] or int(float(g["n_scored"])) != w["n_scored"]:
            bad.append((k, "counts", (g["n_examples"], g["n_scored"]), (w["n_examples"], w["n_scored"])))
            continue
        for f, tol in (("abs_error_mwh", 1e-6 * max(1, w["n_scored"])), ("actual_mwh", 1e-6 * max(1, w["n_scored"]))):
            gv = num(g[f]) or 0.0
            if abs(gv - w[f]) > tol:
                bad.append((k, f, gv, w[f]))
                break
        else:
            gw = num(g["wape"])
            if w["wape"] is None:
                if gw is not None:
                    bad.append((k, "wape", gw, None))
            elif gw is None or abs(gw - w["wape"]) > WAPE_TOL:
                bad.append((k, "wape", gw, w["wape"]))
    assert not bad, f"{len(bad)} monthly KPI rows differ (key, field, got, expected), e.g. {bad[:4]}"


def check_summary(run, want, as_of):
    s = run["summary"]
    assert s.get("closed_months") == want["closed_months"], f"closed_months {s.get('closed_months')} expected {want['closed_months']}"
    got = {}
    for e in s.get("head_to_head", []):
        k = (e.get("model_a"), e.get("model_b"))
        assert k not in got, f"duplicate head-to-head entry {k}"
        got[k] = e
    assert set(got) == set(want["head_to_head"]), f"head-to-head pairs {sorted(got)} expected {sorted(want['head_to_head'])}"
    bad = []
    for k, w in want["head_to_head"].items():
        g = got[k]
        if int(g.get("n_pairs", -1)) != w["n_pairs"] or g.get("first_month") != w["first_month"] or g.get("last_month") != w["last_month"]:
            bad.append((k, "pairs/months", (g.get("n_pairs"), g.get("first_month"), g.get("last_month")),
                        (w["n_pairs"], w["first_month"], w["last_month"])))
            continue
        for f, tol in (("wape_a", WAPE_TOL), ("wape_b", WAPE_TOL), ("relative_change", REL_TOL)):
            gv = num(g.get(f))
            if gv is None or not math.isfinite(gv) or abs(gv - w[f]) > tol:
                bad.append((k, f, gv, w[f]))
                break
    assert not bad, f"head-to-head differs: {bad}"


# ------------------------------------------------------------------------------------------- A. source


def test_warehouse_unmodified(ctx):
    """data/warehouse.sqlite is the system of record and is unchanged."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/warehouse.sqlite differs from the extract"


# ------------------------------------------------------------------------------------------- B. this extract


def test_build_succeeds(ctx):
    """`python -m fcaccuracy build --as-of 2026-09-22T06:00:00Z` succeeds and writes the three mart outputs."""
    require_run(ctx["run1"])


def test_example_set(ctx):
    """One example per model, region, portfolio, delivery day and horizon for every forecast in closed KPI months."""
    require_run(ctx["run1"])
    check_example_set(ctx["run1"], ctx["ref"])


def test_forecast_in_force(ctx):
    """Each example carries the forecast run day, issue and value the KPI evaluates."""
    require_run(ctx["run1"])
    compare_examples(ctx["run1"], ctx["ref"], ["run_date", "issue_id", "forecast_mwh"])


def test_kpi_month_and_status(ctx):
    """KPI month and scored/unsettled status per example."""
    require_run(ctx["run1"])
    compare_examples(ctx["run1"], ctx["ref"], ["kpi_month", "status"])


def test_settlement_runs(ctx):
    """The settlement runs each scored example is evaluated against."""
    require_run(ctx["run1"])
    compare_examples(ctx["run1"], ctx["ref"], ["actual_run_ids"])


def test_actuals_and_errors(ctx):
    """Actual volume and absolute error per example."""
    require_run(ctx["run1"])
    compare_examples(ctx["run1"], ctx["ref"], ["actual_mwh", "abs_error_mwh"])


def test_monthly_kpi(ctx):
    """Monthly KPI rows, counts, sums and WAPE."""
    require_run(ctx["run1"])
    check_monthly(ctx["run1"], ctx["ref"])


def test_summary_head_to_head(ctx):
    """Closed months and the model head-to-head."""
    require_run(ctx["run1"])
    check_summary(ctx["run1"], ctx["ref"], VISIBLE_AS_OF)


def test_build_time(ctx):
    """A build on this extract finishes within 10 minutes."""
    require_run(ctx["run1"])
    assert ctx["run1"]["seconds"] <= BUILD_LIMIT_SEC, f"build took {ctx['run1']['seconds']:.0f} s (limit {BUILD_LIMIT_SEC} s)"


def test_rerun_is_deterministic(ctx):
    """Re-running the build on the same extract reproduces the outputs byte for byte."""
    require_run(ctx["run2"])
    assert ctx["run1"]["raw"] == ctx["run2"]["raw"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. other extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]
ALL_FIELDS = ["run_date", "issue_id", "forecast_mwh", "kpi_month", "status", "actual_run_ids", "actual_mwh", "abs_error_mwh"]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_examples(ctx, name):
    """Other extracts: evaluation examples (set and every field)."""
    want, run = ctx["hidden"][name]
    require_run(run)
    check_example_set(run, want)
    compare_examples(run, want, ALL_FIELDS)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_monthly_kpi(ctx, name):
    """Other extracts: monthly KPI."""
    want, run = ctx["hidden"][name]
    require_run(run)
    check_monthly(run, want)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_head_to_head(ctx, name):
    """Other extracts: closed months and head-to-head."""
    want, run = ctx["hidden"][name]
    require_run(run)
    check_summary(run, want, None)
