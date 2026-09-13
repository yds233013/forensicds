"""Verifier for ForensicDS Task 04 (retention metrics semantic layer).

Behavioural checks only - no SQL inspection:

  A. Source integrity   data/warehouse.db equals a pristine regeneration of the extract.
  B. Default as-of      the agent's build is re-run (analytics.db and extracts deleted first) and every documented
                        model is compared with an independent reference (tests/reference.py) at its grain:
                        customer_quarter rows, boundary ARR, cohort, movement, segment; quarterly retention metrics;
                        ARR bridge; segment metrics; board extracts; determinism.
  C. Hidden extracts    the same command on unseen extracts (win-backs, short terms, early signing, boundary gaps,
                        segment crossings, contract-type noise, other calendars; tests/scenarios.py).
"""
from __future__ import annotations

import csv
import math
import os
import shutil
import sqlite3
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
DEFAULT_AS_OF = date(2026, 8, 5)
DB = "data/warehouse.db"
ANALYTICS = "analytics/analytics.db"
BOARD = "reports/board"
QUARTERLY_COLS = ["cohort_customers", "starting_arr", "cohort_ending_arr", "nrr", "grr", "churned_customers",
                  "logo_churn_rate", "new_arr", "reactivated_arr", "expansion_arr", "contraction_arr", "churned_arr",
                  "ending_arr", "new_customers", "reactivated_customers"]
SEGMENT_COLS = ["cohort_customers", "starting_arr", "cohort_ending_arr", "nrr", "grr", "churned_customers", "logo_churn_rate"]


def pipeline_env() -> dict:
    """Environment for the agent's pipeline: no verifier variables."""
    env = {k: v for k, v in os.environ.items() if k not in ("TESTS_DIR", "WORKSPACE", "PIPELINE_PYTHON")}
    env["PYTHONPATH"] = str(WORKSPACE / "src")
    return env


def run_build(as_of: date) -> dict:
    (WORKSPACE / ANALYTICS).unlink(missing_ok=True)
    for f in ("retention_quarterly.csv", "retention_by_segment.csv"):
        (WORKSPACE / BOARD / f).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "metrics_layer", "build", "--config", "config/metrics_layer.toml", "--as-of", as_of.isoformat()]
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=pipeline_env(),
                           capture_output=True, text=True, timeout=300)
        rc, out = p.returncode, p.stdout[-2000:] + p.stderr[-4000:]
    except subprocess.TimeoutExpired:
        rc, out = -1, "timed out"
    res = dict(returncode=rc, output=out)
    if rc != 0:
        return res
    try:
        con = sqlite3.connect(WORKSPACE / ANALYTICS)
        res["cq"] = con.execute("SELECT quarter, account_id, start_arr, end_arr, movement, in_cohort, segment "
                                "FROM customer_quarter").fetchall()
        res["quarters"] = con.execute("SELECT quarter, start_date, end_date FROM dim_quarters ORDER BY quarter").fetchall()
        res["quarterly"] = {r[0]: dict(zip(QUARTERLY_COLS, r[1:])) for r in con.execute(
            f"SELECT quarter, {', '.join(QUARTERLY_COLS)} FROM retention_quarterly")}
        res["segments"] = {(r[0], r[1]): dict(zip(SEGMENT_COLS, r[2:])) for r in con.execute(
            f"SELECT quarter, segment, {', '.join(SEGMENT_COLS)} FROM retention_by_segment")}
        con.close()
        for name in ("retention_quarterly", "retention_by_segment"):
            with open(WORKSPACE / BOARD / f"{name}.csv", newline="") as fh:
                res[f"csv_{name}"] = list(csv.DictReader(fh))
        res["raw"] = b"".join((WORKSPACE / BOARD / f).read_bytes() for f in ("retention_quarterly.csv", "retention_by_segment.csv"))
    except Exception as exc:  # recorded, asserted by tests
        res["read_error"] = repr(exc)
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier04_"))
    pristine = tmp / "pristine"
    world.build(world.VISIBLE_SPEC, pristine)
    backup = tmp / "agent_warehouse.db"
    shutil.copyfile(WORKSPACE / DB, backup)
    c = dict(agent_digest=world.sqlite_logical_digest(WORKSPACE / DB),
             pristine_digest=world.sqlite_logical_digest(pristine / DB), hidden={})
    try:
        shutil.copyfile(pristine / DB, WORKSPACE / DB)
        c["ref"] = ref.compute(pristine, DEFAULT_AS_OF)
        c["run1"] = run_build(DEFAULT_AS_OF)
        c["run2"] = run_build(DEFAULT_AS_OF)
        for spec in HIDDEN_SPECS:
            root = tmp / spec["name"]
            world.build(spec, root)
            shutil.copyfile(root / DB, WORKSPACE / DB)
            as_of = date.fromisoformat(spec["as_of"])
            c["hidden"][spec["name"]] = (ref.compute(root, as_of), run_build(as_of))
        shutil.copyfile(pristine / DB, WORKSPACE / DB)
        run_build(DEFAULT_AS_OF)
    finally:
        shutil.copyfile(backup, WORKSPACE / DB)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"build command failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"models or extracts missing or with a different schema: {run['read_error']}"


def num_close(a, b, rel=1e-9, abs_=0.011) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=rel, abs_tol=abs_)


def ratio_close(a, b) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=1e-6)


# ------------------------------------------------------------------------------------------- shared assertions


def check_calendar(run: dict, reference: dict) -> None:
    want = [(q, s.isoformat(), e.isoformat()) for q, s, e in reference["quarters"]]
    assert [tuple(r) for r in run["quarters"]] == want, f"reporting quarters {run['quarters']} expected {want}"


def cq_index(run: dict) -> dict:
    keys = Counter((r[0], r[1]) for r in run["cq"])
    dup = [k for k, n in keys.items() if n > 1]
    assert not dup, f"{len(dup)} (quarter, account) pairs appear more than once in customer_quarter, e.g. {dup[:4]}"
    return {(r[0], r[1]): r for r in run["cq"]}


def check_cq_rows(run: dict, reference: dict) -> None:
    idx = cq_index(run)
    want = {(r["quarter"], r["account_id"]): r for r in reference["customer_quarter"]}
    missing, extra = sorted(set(want) - set(idx)), sorted(set(idx) - set(want))
    assert not missing and not extra, (f"customer_quarter rows differ: {len(missing)} missing (e.g. {missing[:3]}), "
                                       f"{len(extra)} extra (e.g. {extra[:3]})")
    bad = [(k, idx[k][2:4], (w["start_arr"], w["end_arr"])) for k, w in want.items()
           if not (num_close(idx[k][2], w["start_arr"]) and num_close(idx[k][3], w["end_arr"]))]
    assert not bad, f"{len(bad)} rows with wrong start/end ARR, e.g. {bad[:3]}"


def check_cq_semantics(run: dict, reference: dict, fields=("in_cohort", "movement", "segment")) -> None:
    idx = cq_index(run)
    problems = {}
    for w in reference["customer_quarter"]:
        k = (w["quarter"], w["account_id"])
        if k not in idx:
            continue
        got = dict(movement=idx[k][4], in_cohort=idx[k][5], segment=idx[k][6])
        want = dict(movement=w["movement"], in_cohort=int(w["start_arr"] > 0), segment=w["segment"])
        for f in fields:
            g = got[f]
            if f == "in_cohort":
                try:
                    g = int(float(g))
                except (TypeError, ValueError):
                    pass
            if g != want[f] and not (f == "segment" and want[f] is None and g in ("", None)):
                problems.setdefault(f, []).append((k, g, want[f]))
    summary = {f: len(v) for f, v in problems.items()}
    assert not problems, f"customer_quarter classification differs: {summary}; e.g. " + \
        "; ".join(f"{f}: {v[:2]}" for f, v in problems.items())


def check_quarterly(run: dict, reference: dict, cols) -> None:
    want = {q["quarter"]: q for q in reference["quarterly"]}
    assert set(run["quarterly"]) == set(want), f"retention_quarterly quarters {sorted(run['quarterly'])} expected {sorted(want)}"
    bad = []
    for q, w in want.items():
        g = run["quarterly"][q]
        for c in cols:
            ok = ratio_close(g[c], w[c]) if c in ("nrr", "grr", "logo_churn_rate") else num_close(g[c], w[c])
            if not ok:
                bad.append((q, c, g[c], w[c]))
    assert not bad, f"retention_quarterly differs in {len(bad)} values, e.g. {bad[:6]}"


def check_segments(run: dict, reference: dict) -> None:
    want = {(s["quarter"], s["segment"]): s for s in reference["by_segment"] if s["cohort_customers"] > 0}
    got = run["segments"]
    assert set(got) == set(want), f"retention_by_segment keys differ: missing {sorted(set(want) - set(got))[:4]}, extra {sorted(set(got) - set(want))[:4]}"
    bad = []
    for k, w in want.items():
        for c in SEGMENT_COLS:
            ok = ratio_close(got[k][c], w[c]) if c in ("nrr", "grr", "logo_churn_rate") else num_close(got[k][c], w[c])
            if not ok:
                bad.append((k, c, got[k][c], w[c]))
    assert not bad, f"retention_by_segment differs in {len(bad)} values, e.g. {bad[:6]}"


# ------------------------------------------------------------------------------------------- A. integrity


def test_warehouse_extract_unmodified(ctx):
    """data/warehouse.db is the authoritative extract and must not be edited."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/warehouse.db content differs from the extract"


# ------------------------------------------------------------------------------------------- B. default as-of


def test_build_succeeds(ctx):
    """`python -m metrics_layer build --config config/metrics_layer.toml --as-of 2026-08-05` succeeds."""
    require_run(ctx["run1"])


def test_reporting_calendar(ctx):
    """dim_quarters holds the last eight complete calendar quarters."""
    require_run(ctx["run1"])
    check_calendar(ctx["run1"], ctx["ref"])


def test_customer_quarter_rows_and_boundary_arr(ctx):
    """customer_quarter has one row per (quarter, account) with ARR at a boundary, with correct start/end ARR."""
    require_run(ctx["run1"])
    check_cq_rows(ctx["run1"], ctx["ref"])


def test_retention_cohort_membership(ctx):
    """in_cohort identifies exactly the customers at the start of each quarter."""
    require_run(ctx["run1"])
    check_cq_semantics(ctx["run1"], ctx["ref"], ("in_cohort",))


def test_lifecycle_movements(ctx):
    """movement classifies every account-quarter per the handbook (new vs reactivated vs cohort movements)."""
    require_run(ctx["run1"])
    check_cq_semantics(ctx["run1"], ctx["ref"], ("movement",))


def test_segments(ctx):
    """segment is assigned from starting ARR for cohort customers only."""
    require_run(ctx["run1"])
    check_cq_semantics(ctx["run1"], ctx["ref"], ("segment",))


def test_retention_metrics(ctx):
    """NRR, GRR, logo churn and cohort counts per quarter match the handbook."""
    require_run(ctx["run1"])
    check_quarterly(ctx["run1"], ctx["ref"], ["cohort_customers", "starting_arr", "cohort_ending_arr", "nrr", "grr",
                                              "churned_customers", "logo_churn_rate"])


def test_arr_bridge(ctx):
    """ARR bridge categories per quarter match the handbook and reconcile starting to ending ARR."""
    require_run(ctx["run1"])
    check_quarterly(ctx["run1"], ctx["ref"], ["new_arr", "reactivated_arr", "expansion_arr", "contraction_arr",
                                              "churned_arr", "ending_arr", "new_customers", "reactivated_customers"])
    for q, g in ctx["run1"]["quarterly"].items():
        lhs = float(g["starting_arr"]) + float(g["new_arr"]) + float(g["reactivated_arr"]) + float(g["expansion_arr"]) \
            - float(g["contraction_arr"]) - float(g["churned_arr"])
        assert abs(lhs - float(g["ending_arr"])) < 1.0, f"{q}: bridge does not reconcile ({lhs} vs {g['ending_arr']})"


def test_retention_by_segment(ctx):
    """Segment retention metrics match the handbook."""
    require_run(ctx["run1"])
    check_segments(ctx["run1"], ctx["ref"])


def test_board_extracts_match_models(ctx):
    """Board CSV extracts are the built models (no hand-edited extracts)."""
    require_run(ctx["run1"])
    rows = ctx["run1"]["csv_retention_quarterly"]
    assert {r["quarter"] for r in rows} == set(ctx["run1"]["quarterly"]), "retention_quarterly.csv quarters differ from model"
    for r in rows:
        m = ctx["run1"]["quarterly"][r["quarter"]]
        for c in QUARTERLY_COLS:
            assert num_close(r[c], m[c], rel=1e-9, abs_=1e-6), f"retention_quarterly.csv {r['quarter']} {c}={r[c]} model={m[c]}"
    segs = ctx["run1"]["csv_retention_by_segment"]
    assert {(r["quarter"], r["segment"]) for r in segs} == set(ctx["run1"]["segments"]), "retention_by_segment.csv keys differ"
    for r in segs:
        m = ctx["run1"]["segments"][(r["quarter"], r["segment"])]
        for c in SEGMENT_COLS:
            assert num_close(r[c], m[c], rel=1e-9, abs_=1e-6), f"retention_by_segment.csv {r['quarter']} {r['segment']} {c}"


def test_rebuild_is_deterministic(ctx):
    """Rebuilding on the same extract reproduces the board extracts byte for byte."""
    require_run(ctx["run2"])
    assert ctx["run1"]["raw"] == ctx["run2"]["raw"], "board extracts differ between identical builds"


# ------------------------------------------------------------------------------------------- C. hidden extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_customer_quarter(ctx, name):
    """Other extracts: customer_quarter rows, boundary ARR, cohort, movements and segments."""
    reference, run = ctx["hidden"][name]
    require_run(run)
    check_calendar(run, reference)
    check_cq_rows(run, reference)
    check_cq_semantics(run, reference)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_retention_metrics_and_bridge(ctx, name):
    """Other extracts: quarterly retention metrics, ARR bridge and segment metrics."""
    reference, run = ctx["hidden"][name]
    require_run(run)
    check_quarterly(run, reference, QUARTERLY_COLS)
    check_segments(run, reference)
