"""Verifier for ForensicDS Task 02 (renewal-risk temporal provenance).

Behavioural checks only - no source-code inspection:

  A. Source integrity   data/warehouse.db equals a pristine regeneration of the extract.
  B. Current extract    the agent's pipeline is re-run from source (outputs deleted first) at the
                        default as-of date. Examples, every feature value, predictions, the report,
                        model behaviour, idempotence and the production scoring command are compared
                        with an independent reference (tests/reference.py, tests/reference_model.py)
                        in which every feature uses only information loaded into the warehouse before
                        00:00 UTC on the example's prediction date.
  C. Hidden extracts    the same command on unseen warehouse extracts with other run dates, ids,
                        leak channels and replication schedules (tests/scenarios.py).
"""
from __future__ import annotations

import csv
import json
import math
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import reference as ref  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
DEFAULT_AS_OF = date(2026, 8, 15)
DB = "data/warehouse.db"
OUTPUTS = ["artifacts/examples.csv", "artifacts/features.csv", "artifacts/eval_predictions.csv",
           "artifacts/model/renewal_risk.joblib"]
RUN_TIMEOUT_S = 300  # instruction: a training run must finish within 5 minutes
FEATURE_TOL = 1e-6
AUC_BAND = 0.02
MIN_SCORE_RANK_CORR = 0.98


# --------------------------------------------------------------------------- harness


def read_csv(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def spearman(a: list[float], b: list[float]) -> float:
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2.0
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / len(ra), sum(rb) / len(rb)
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    return cov / math.sqrt(sum((x - ma) ** 2 for x in ra) * sum((y - mb) ** 2 for y in rb))


def run_pipeline(as_of: date) -> dict:
    for rel in OUTPUTS + [f"reports/model_evaluation/eval_{as_of.isoformat()}.json", "reports/model_evaluation/latest.json"]:
        (WORKSPACE / rel).unlink(missing_ok=True)
    env = dict(os.environ, PYTHONPATH=str(WORKSPACE / "src"))
    cmd = [PIPELINE_PYTHON, "-m", "renewal_risk", "run", "--config", "config/pipeline.toml", "--as-of", as_of.isoformat()]
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=env, capture_output=True, text=True, timeout=RUN_TIMEOUT_S)
        rc, out = p.returncode, p.stdout[-2500:] + p.stderr[-5000:]
    except subprocess.TimeoutExpired:
        rc, out = -1, "timed out"
    res = dict(returncode=rc, output=out)
    if rc == 0:
        try:
            res["examples"] = read_csv(WORKSPACE / "artifacts/examples.csv")
            res["features"] = read_csv(WORKSPACE / "artifacts/features.csv")
            res["predictions"] = read_csv(WORKSPACE / "artifacts/eval_predictions.csv")
            res["report"] = json.loads((WORKSPACE / f"reports/model_evaluation/eval_{as_of.isoformat()}.json").read_text())
            res["raw"] = {rel: (WORKSPACE / rel).read_bytes() for rel in OUTPUTS[:3]}
        except Exception as exc:  # recorded and asserted by tests
            res["read_error"] = repr(exc)
    return res


def reference_bundle(root: Path, as_of: date, tmp: Path) -> dict:
    examples, feats, data = ref.compute(root, as_of)
    tmp.mkdir(parents=True, exist_ok=True)
    with open(tmp / "examples.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["contract_id", "account_id", "renewal_date", "prediction_date", "label", "split"],
                           extrasaction="ignore")
        w.writeheader()
        w.writerows(examples)
    with open(tmp / "features.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["contract_id"] + ref.FEATURE_COLUMNS)
        for e in examples:
            w.writerow([e["contract_id"]] + [repr(feats[e["contract_id"]][c]) for c in ref.FEATURE_COLUMNS])
    subprocess.run([PIPELINE_PYTHON, str(TESTS_DIR / "reference_model.py"), str(tmp / "examples.csv"),
                    str(tmp / "features.csv"), str(tmp / "model.json")], cwd=TESTS_DIR, check=True,
                   env={k: v for k, v in os.environ.items() if k != "PYTHONPATH"}, capture_output=True, text=True, timeout=600)
    scores = json.loads((tmp / "model.json").read_text())["scores"]
    labels = {e["contract_id"]: e["label"] for e in examples}
    ev = sorted(scores)
    return dict(examples=examples, features=feats, scores=scores,
                auc=ref.auc([labels[c] for c in ev], [scores[c] for c in ev]), data=data)


def install_db(src_root: Path) -> None:
    shutil.copyfile(src_root / DB, WORKSPACE / DB)


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier02_"))
    pristine = tmp / "pristine"
    world.build(world.VISIBLE_SPEC, pristine)
    backup = tmp / "agent_warehouse.db"
    shutil.copyfile(WORKSPACE / DB, backup)
    c = dict(tmp=tmp, pristine=pristine, hidden={},
             agent_digest=world.sqlite_logical_digest(WORKSPACE / DB),
             pristine_digest=world.sqlite_logical_digest(pristine / DB))
    try:
        install_db(pristine)
        c["ref"] = reference_bundle(pristine, DEFAULT_AS_OF, tmp / "ref_visible")
        c["run1"] = run_pipeline(DEFAULT_AS_OF)
        c["run2"] = run_pipeline(DEFAULT_AS_OF)
        score_date = DEFAULT_AS_OF - timedelta(days=30)
        (WORKSPACE / f"artifacts/scores/scores_{score_date.isoformat()}.csv").unlink(missing_ok=True)
        p = subprocess.run([PIPELINE_PYTHON, "-m", "renewal_risk", "score", "--config", "config/pipeline.toml",
                            "--score-date", score_date.isoformat()], cwd=WORKSPACE, capture_output=True, text=True,
                           env=dict(os.environ, PYTHONPATH=str(WORKSPACE / "src")), timeout=600)
        c["score"] = dict(returncode=p.returncode, output=p.stdout[-1500:] + p.stderr[-3000:], date=score_date)
        for spec in HIDDEN_SPECS:
            root = tmp / spec["name"]
            world.build(spec, root)
            install_db(root)
            as_of = date.fromisoformat(spec["extract_date"])
            c["hidden"][spec["name"]] = (reference_bundle(root, as_of, tmp / f"ref_{spec['name']}"), run_pipeline(as_of))
        # re-run the default training so the workspace is left with current-extract outputs
        install_db(pristine)
        run_pipeline(DEFAULT_AS_OF)
    finally:
        shutil.copyfile(backup, WORKSPACE / DB)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"training command failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"training outputs missing or unreadable: {run['read_error']}"


# --------------------------------------------------------------------------- shared assertions


def check_examples(run: dict, rb: dict) -> None:
    got = run["examples"]
    keys = Counter(r["contract_id"] for r in got)
    dup = [k for k, n in keys.items() if n > 1]
    assert not dup, f"{len(dup)} renewals appear more than once in examples.csv, e.g. {dup[:5]}"
    want = {e["contract_id"]: e for e in rb["examples"]}
    missing = sorted(set(want) - set(keys))
    extra = sorted(set(keys) - set(want))
    assert not missing, f"{len(missing)} eligible renewals missing from examples.csv, e.g. {missing[:5]}"
    assert not extra, f"{len(extra)} ineligible rows in examples.csv, e.g. {extra[:5]}"
    bad = [(r["contract_id"], k) for r in got for k in ("prediction_date", "label", "split")
           if str(r[k]) != str(want[r["contract_id"]][k])]
    assert not bad, f"{len(bad)} example fields differ from the documented definition, e.g. {bad[:5]}"


def feature_mismatches(run: dict, rb: dict, columns: list[str]) -> dict[str, list]:
    rows = {r["contract_id"]: r for r in run["features"]}
    out = {}
    for c in columns:
        bad = []
        for cid, want in rb["features"].items():
            r = rows.get(cid)
            try:
                raw = r[c]
                g = {"True": 1.0, "False": 0.0, "true": 1.0, "false": 0.0}.get(raw, None)
                g = float(raw) if g is None else g
            except (TypeError, KeyError, ValueError):
                bad.append((cid, None, want[c]))
                continue
            if not math.isclose(g, float(want[c]), rel_tol=FEATURE_TOL, abs_tol=FEATURE_TOL):
                bad.append((cid, g, want[c]))
        if bad:
            out[c] = bad
    return out


def check_features(run: dict, rb: dict, columns: list[str]) -> None:
    header = list(run["features"][0].keys()) if run["features"] else []
    absent = [c for c in ref.FEATURE_COLUMNS if c not in header]
    assert not absent, f"feature columns missing from features.csv: {absent}"
    assert len(run["features"]) == len(rb["examples"]), (
        f"features.csv has {len(run['features'])} rows, expected one per example ({len(rb['examples'])})")
    mism = feature_mismatches(run, rb, columns)
    summary = {c: len(v) for c, v in mism.items()}
    examples = {c: v[:2] for c, v in mism.items()}
    assert not mism, f"feature values differ from their definition at prediction time: {summary}; e.g. {examples}"


def check_predictions_and_report(run: dict, rb: dict) -> None:
    preds = run["predictions"]
    want_eval = {e["contract_id"]: e for e in rb["examples"] if e["split"] == "eval"}
    ids = Counter(p["contract_id"] for p in preds)
    assert set(ids) == set(want_eval) and all(n == 1 for n in ids.values()), (
        f"eval_predictions.csv must have exactly one row per eval example ({len(want_eval)}); got {len(preds)} rows")
    scores = [float(p["score"]) for p in preds]
    assert all(0.0 <= s <= 1.0 for s in scores), "scores outside [0, 1]"
    labels = [int(p["label"]) for p in preds]
    assert all(int(p["label"]) == want_eval[p["contract_id"]]["label"] for p in preds), "prediction labels differ from examples"
    rep = run["report"]
    auc = ref.auc(labels, scores)
    assert abs(float(rep["roc_auc"]) - auc) <= 1e-6, f"report roc_auc {rep['roc_auc']} != AUC of eval_predictions.csv {auc}"
    brier = sum((s - y) ** 2 for s, y in zip(scores, labels)) / len(scores)
    assert abs(float(rep["brier"]) - brier) <= 1e-6, f"report brier {rep['brier']} != Brier of eval_predictions.csv {brier}"
    n_train = sum(1 for e in rb["examples"] if e["split"] == "train")
    assert int(rep["n_train"]) == n_train and int(rep["n_eval"]) == len(want_eval), (
        f"report counts n_train={rep['n_train']} n_eval={rep['n_eval']}, expected {n_train}/{len(want_eval)}")


def check_model_behaviour(run: dict, rb: dict) -> None:
    got = {p["contract_id"]: float(p["score"]) for p in run["predictions"]}
    ids = sorted(rb["scores"])
    rho = spearman([got[c] for c in ids], [rb["scores"][c] for c in ids])
    auc = float(run["report"]["roc_auc"])
    assert abs(auc - rb["auc"]) <= AUC_BAND, (
        f"eval ROC AUC {auc:.4f} differs from the specified model on correct features ({rb['auc']:.4f}) by more than {AUC_BAND}")
    assert rho >= MIN_SCORE_RANK_CORR, (
        f"eval scores rank-correlate {rho:.4f} with the specified model on correct features (need >= {MIN_SCORE_RANK_CORR})")


# --------------------------------------------------------------------------- A. source integrity


def test_warehouse_extract_unmodified(ctx):
    """data/warehouse.db is the authoritative extract and must not be edited."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/warehouse.db content differs from the extract"


# --------------------------------------------------------------------------- B. current extract


def test_training_run_succeeds(ctx):
    """`python -m renewal_risk run --config config/pipeline.toml --as-of 2026-08-15` succeeds and writes all outputs."""
    require_run(ctx["run1"])


def test_examples_one_per_eligible_renewal(ctx):
    """examples.csv: exactly one row per eligible renewal with the documented prediction date, label and split."""
    require_run(ctx["run1"])
    check_examples(ctx["run1"], ctx["ref"])


def test_contract_usage_support_features(ctx):
    """Features that already respected the prediction point keep their values."""
    require_run(ctx["run1"])
    check_features(ctx["run1"], ctx["ref"], ref.CONTRACT + ref.USAGE + ref.SUPPORT)


def test_crm_pipeline_features_point_in_time(ctx):
    """CRM pipeline features equal their definitions using only CRM information loaded before the prediction time."""
    require_run(ctx["run1"])
    check_features(ctx["run1"], ctx["ref"], ref.PIPELINE)


def test_customer_success_features_point_in_time(ctx):
    """Customer Success health features equal their definitions using only information loaded before the prediction time."""
    require_run(ctx["run1"])
    check_features(ctx["run1"], ctx["ref"], ref.HEALTH)


def test_predictions_and_report_consistent(ctx):
    """One prediction per eval example; report metrics are computed from those predictions."""
    require_run(ctx["run1"])
    check_predictions_and_report(ctx["run1"], ctx["ref"])


def test_model_specification_preserved(ctx):
    """The documented model trained on the training split: AUC and score ranking match the specified model on correct features."""
    require_run(ctx["run1"])
    check_model_behaviour(ctx["run1"], ctx["ref"])


def test_rerun_is_deterministic(ctx):
    """Re-running the training command on the same extract reproduces examples, features and predictions."""
    require_run(ctx["run2"])
    for rel in ctx["run1"]["raw"]:
        assert ctx["run1"]["raw"][rel] == ctx["run2"]["raw"][rel], f"{rel} differs between identical runs"


def test_production_scoring_command(ctx):
    """`python -m renewal_risk score` still scores every undecided renewal due horizon days after the score date."""
    require_run(ctx["run1"])
    s = ctx["score"]
    assert s["returncode"] == 0, f"scoring command failed:\n{s['output']}"
    due = (s["date"] + timedelta(days=ref.HORIZON_DAYS)).isoformat()
    decided = {c for c, _a, _o, _s in ctx["ref"]["data"]["outcomes"]}
    want = {c for c, _a, _st, r, *_ in ctx["ref"]["data"]["contracts"] if r == due and c not in decided}
    rows = read_csv(WORKSPACE / f"artifacts/scores/scores_{s['date'].isoformat()}.csv")
    assert {r["contract_id"] for r in rows} == want and len(rows) == len(want), "scores file does not cover the due renewals"
    assert all(0.0 <= float(r["score"]) <= 1.0 for r in rows), "scores outside [0, 1]"


# --------------------------------------------------------------------------- C. hidden extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_extract_examples(ctx, name):
    """Other extracts and run dates: training succeeds with one example per eligible renewal."""
    rb, run = ctx["hidden"][name]
    require_run(run)
    check_examples(run, rb)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_extract_features_point_in_time(ctx, name):
    """Other extracts: every feature uses only information loaded before each example's prediction time."""
    rb, run = ctx["hidden"][name]
    require_run(run)
    check_features(run, rb, ref.FEATURE_COLUMNS)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_extract_evaluation(ctx, name):
    """Other extracts: predictions, report and model behaviour are consistent with the specification."""
    rb, run = ctx["hidden"][name]
    require_run(run)
    check_predictions_and_report(run, rb)
    check_model_behaviour(run, rb)
