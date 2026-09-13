"""Verifier for ForensicDS Task 03 (lead-score evaluation population).

Behavioural checks only - no source inspection:

  A. Source integrity   data/revops.db equals a pristine regeneration of the extract.
  B. Default as-of      the agent's evaluation is re-run (outputs deleted first) for 2026-09-01 and compared with an
                        independent reference (tests/reference.py): cohort grain and membership, labels, scores,
                        report metrics recomputed from the cohort file, report vs reference, determinism.
  C. Hidden extracts    the same command on unseen extracts where the routed, worked and labelled populations are
                        produced differently (tests/scenarios.py).
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
DEFAULT_AS_OF = date(2026, 9, 1)
DB = "data/revops.db"
TOL = 1e-9


def run_eval(as_of: date) -> dict:
    rel_report = f"reports/model_monitoring/lead_score_eval_{as_of.isoformat()}.json"
    for rel in ("artifacts/eval_cohort.csv", rel_report, "reports/model_monitoring/latest.json"):
        (WORKSPACE / rel).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "lead_eval", "run", "--config", "config/evaluation.toml", "--as-of", as_of.isoformat()]
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=dict(os.environ, PYTHONPATH=str(WORKSPACE / "src")),
                           capture_output=True, text=True, timeout=300)
        rc, out = p.returncode, p.stdout[-2000:] + p.stderr[-4000:]
    except subprocess.TimeoutExpired:
        rc, out = -1, "timed out"
    res = dict(returncode=rc, output=out)
    if rc == 0:
        try:
            with open(WORKSPACE / "artifacts/eval_cohort.csv", newline="") as fh:
                res["cohort"] = list(csv.DictReader(fh))
            res["report"] = json.loads((WORKSPACE / rel_report).read_text())
            res["raw"] = (WORKSPACE / "artifacts/eval_cohort.csv").read_bytes() + (WORKSPACE / rel_report).read_bytes()
        except Exception as exc:  # recorded, asserted by tests
            res["read_error"] = repr(exc)
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier03_"))
    pristine = tmp / "pristine"
    world.build(world.VISIBLE_SPEC, pristine)
    backup = tmp / "agent_revops.db"
    shutil.copyfile(WORKSPACE / DB, backup)
    c = dict(agent_digest=world.sqlite_logical_digest(WORKSPACE / DB),
             pristine_digest=world.sqlite_logical_digest(pristine / DB), hidden={})
    try:
        shutil.copyfile(pristine / DB, WORKSPACE / DB)
        rows = ref.cohort(pristine, DEFAULT_AS_OF)
        c["ref"] = (rows, ref.metrics(rows))
        c["run1"] = run_eval(DEFAULT_AS_OF)
        c["run2"] = run_eval(DEFAULT_AS_OF)
        for spec in HIDDEN_SPECS:
            root = tmp / spec["name"]
            world.build(spec, root)
            shutil.copyfile(root / DB, WORKSPACE / DB)
            as_of = date.fromisoformat(spec["as_of"])
            hrows = ref.cohort(root, as_of)
            c["hidden"][spec["name"]] = ((hrows, ref.metrics(hrows)), run_eval(as_of))
        shutil.copyfile(pristine / DB, WORKSPACE / DB)
        run_eval(DEFAULT_AS_OF)
    finally:
        shutil.copyfile(backup, WORKSPACE / DB)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"evaluation command failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"evaluation outputs missing or unreadable: {run['read_error']}"


# ------------------------------------------------------------------------------------------- shared assertions


def check_grain(run: dict) -> None:
    ids = Counter(r["lead_id"] for r in run["cohort"])
    dup = [k for k, n in ids.items() if n > 1]
    assert not dup, f"{len(dup)} leads appear more than once in eval_cohort.csv, e.g. {dup[:5]}"
    header = set(run["cohort"][0].keys()) if run["cohort"] else set()
    missing = {"lead_id", "created_at", "source", "score", "label"} - header
    assert not missing, f"eval_cohort.csv is missing columns {sorted(missing)}"


def check_membership(run: dict, reference) -> None:
    rows, _m = reference
    want = {r["lead_id"] for r in rows}
    got = {r["lead_id"] for r in run["cohort"]}
    missing, extra = sorted(want - got), sorted(got - want)
    assert not missing and not extra, (
        f"evaluation population differs: {len(missing)} leads missing (e.g. {missing[:4]}), "
        f"{len(extra)} leads that should not be evaluated (e.g. {extra[:4]}); expected {len(want)}, got {len(got)}")


def as_int(v) -> int:
    """Parse a 0/1 label written as 0/1, 0.0/1.0 or True/False."""
    t = str(v).strip().lower()
    if t in ("true", "false"):
        return int(t == "true")
    return int(float(t))


def check_labels_scores(run: dict, reference) -> None:
    rows, _m = reference
    want = {r["lead_id"]: r for r in rows}
    bad_label, bad_score = [], []
    for r in run["cohort"]:
        w = want.get(r["lead_id"])
        if w is None:
            continue
        if as_int(r["label"]) != w["label"]:
            bad_label.append((r["lead_id"], r["label"], w["label"]))
        if abs(float(r["score"]) - w["score"]) > 1e-6:
            bad_score.append((r["lead_id"], r["score"], w["score"]))
    assert not bad_label, f"{len(bad_label)} labels differ from the 60-day closed-won outcome, e.g. {bad_label[:4]}"
    assert not bad_score, f"{len(bad_score)} scores differ from the champion intake score, e.g. {bad_score[:4]}"


def recomputed(run: dict) -> dict:
    rows = [dict(lead_id=r["lead_id"], source=r["source"], score=float(r["score"]), label=as_int(r["label"]))
            for r in run["cohort"]]
    return ref.metrics(rows)


def close(a, b, tol=TOL) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def compare_report(report: dict, want: dict, label: str) -> None:
    bad = [k for k in ("n_leads", "n_converted", "conversion_rate", "roc_auc", "top_decile_conversion_rate",
                       "top_decile_lift", "recommended_threshold") if not close(report.get(k), want[k], 1e-6)]
    assert not bad, f"{label}: report fields differ: " + ", ".join(f"{k}={report.get(k)} expected {want[k]}" for k in bad)
    cal = report.get("calibration") or []
    assert len(cal) == len(want["calibration"]), f"{label}: calibration has {len(cal)} bins"
    for g, w in zip(cal, want["calibration"]):
        for k in ("n", "min_score", "max_score", "mean_score", "conversion_rate"):
            assert close(g.get(k), w[k], 1e-6), f"{label}: calibration bin {w['bin']} {k}={g.get(k)} expected {w[k]}"
    bs = report.get("by_source") or {}
    assert set(bs) == set(want["by_source"]), f"{label}: by_source keys {sorted(bs)} expected {sorted(want['by_source'])}"
    for s, w in want["by_source"].items():
        assert bs[s]["n"] == w["n"] and close(bs[s]["conversion_rate"], w["conversion_rate"], 1e-6), f"{label}: by_source {s}"


# ------------------------------------------------------------------------------------------- A. integrity


def test_revops_extract_unmodified(ctx):
    """data/revops.db is the authoritative extract and must not be edited."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/revops.db content differs from the extract"


# ------------------------------------------------------------------------------------------- B. default as-of


def test_evaluation_run_succeeds(ctx):
    """`python -m lead_eval run --config config/evaluation.toml --as-of 2026-09-01` succeeds and writes its outputs."""
    require_run(ctx["run1"])


def test_cohort_one_row_per_lead(ctx):
    """eval_cohort.csv has one row per lead and the documented columns."""
    require_run(ctx["run1"])
    check_grain(ctx["run1"])


def test_cohort_membership(ctx):
    """The evaluated leads are exactly the population the evaluation is meant to measure."""
    require_run(ctx["run1"])
    check_membership(ctx["run1"], ctx["ref"])


def test_cohort_labels_and_scores(ctx):
    """Each evaluated lead carries its 60-day closed-won outcome and its champion intake score."""
    require_run(ctx["run1"])
    check_labels_scores(ctx["run1"], ctx["ref"])


def test_report_computed_from_cohort(ctx):
    """Report metrics equal the documented metric definitions applied to eval_cohort.csv (no patched numbers)."""
    require_run(ctx["run1"])
    compare_report(ctx["run1"]["report"], recomputed(ctx["run1"]), "report vs its own cohort")


def test_report_matches_reference(ctx):
    """Report metrics (AUC, conversion, top decile, calibration, recommended threshold, by source) match the reference."""
    require_run(ctx["run1"])
    compare_report(ctx["run1"]["report"], ctx["ref"][1], "report vs reference")


def test_rerun_is_deterministic(ctx):
    """Re-running the evaluation on the same extract reproduces the cohort and report byte for byte."""
    require_run(ctx["run2"])
    assert ctx["run1"]["raw"] == ctx["run2"]["raw"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. hidden extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_cohort_membership(ctx, name):
    """Other extracts: the evaluation population is reconstructed correctly."""
    reference, run = ctx["hidden"][name]
    require_run(run)
    check_grain(run)
    check_membership(run, reference)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_labels_scores_and_report(ctx, name):
    """Other extracts: labels, scores and report metrics match the reference."""
    reference, run = ctx["hidden"][name]
    require_run(run)
    check_labels_scores(run, reference)
    compare_report(run["report"], recomputed(run), "report vs its own cohort")
    compare_report(run["report"], reference[1], "report vs reference")
