"""P20 verifier: the no-show model monitoring readout.

Grades the scientific quantities beneath the model-risk decision. Nothing here reads the agent's source; every
check is on the numbers it produced, on the population it says it evaluated, and on their consistency with the
artefacts it wrote.

Criteria accumulate into /logs/verifier/criteria.json, which tests/test.sh folds into reward.json beside the
binary headline reward. A criterion is 1 only if it holds on every graded extract.
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
RUN_LIMIT_S = 1800

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
        [PIPELINE_PYTHON, "-m", "mlops", "monitor", "--db", "data/appointments.sqlite", "--out", "out"],
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
    cp = out_dir / "evaluation_population.csv"
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
    readout, pop_rows = _read_outputs(root / "out")
    bad: list[str] = []

    def close(key, got, want, tol, crit):
        if got is None:
            _fail(crit, f"{name}: {key} missing or not a number")
            bad.append(f"{key}: missing or not a number")
            return False
        if abs(got - want) > tol:
            _fail(crit, f"{name}: {key} {got} vs {want:.4f} (tol {tol})")
            bad.append(f"{key} = {got}, expected {want:.4f} +/- {tol}")
            return False
        return True

    # 1. evidence reconstruction: the dashboard figure, the registry figure and the floor it implies
    close("monitored_auc", _num(readout, "monitored_auc"), t["deployed_auc_v31"], TOL.AUC,
          "evidence_reconstruction")
    close("validation_auc", _num(readout, "validation_auc"), t["validation_auc"], TOL.AUC,
          "evidence_reconstruction")
    close("retention_floor_auc", _num(readout, "retention_floor_auc"), t["retention_floor_auc"], TOL.AUC,
          "evidence_reconstruction")

    # 2. the scientific object: which population the standard's test is computed on
    pop = readout.get("evaluation_population")
    want_pop = sorted(t["monitoring_population"])
    if not isinstance(pop, dict) or not isinstance(pop.get("clinic_ids"), list):
        _fail("scientific_object", f"{name}: evaluation_population.clinic_ids missing")
        bad.append("evaluation_population.clinic_ids missing or not a list")
    else:
        got_pop = sorted(str(x) for x in pop["clinic_ids"])
        if got_pop != want_pop:
            _fail("scientific_object", f"{name}: evaluation population {got_pop} vs {want_pop}")
            bad.append(f"evaluation_population.clinic_ids = {got_pop}, expected {want_pop}")
        n_want = t["n_recent_control"]
        n_got = _num(pop, "n_appointments")
        if n_got is None or abs(n_got - n_want) > TOL.POPULATION_N_REL * n_want:
            _fail("scientific_object", f"{name}: n_appointments {n_got} vs about {n_want}")
            bad.append(f"evaluation_population.n_appointments = {n_got}, expected about {n_want}")

    # 3. identification: the four scoring bases on that population
    sc = readout.get("auc_by_scoring")
    wants = {"as_served": t["holdback_auc_v31_asof_features"],
             "record_features_asof_window": t["holdback_auc_v31_repaired_feed"],
             "feature_store_current": t["holdback_auc_v31_current_features"],
             "candidate_v4": t["holdback_auc_v40"]}
    if not isinstance(sc, dict) or set(sc) != set(wants):
        _fail("identification", f"{name}: auc_by_scoring must have exactly the four named keys")
        bad.append(f"auc_by_scoring must have exactly {sorted(wants)}")
    else:
        for k, want in wants.items():
            close(f"auc_by_scoring[{k}]", _num(sc, k), want, TOL.AUC, "identification")

    # 4. the estimator as an artefact: the per-clinic population file must agree with what was claimed
    if pop_rows is None:
        _fail("estimator_implementation", f"{name}: out/evaluation_population.csv was not written")
        bad.append("out/evaluation_population.csv was not written")
    else:
        ids = sorted(str(r.get("clinic_id", "")).strip() for r in pop_rows)
        if ids != want_pop:
            _fail("estimator_implementation", f"{name}: csv clinics {ids} vs {want_pop}")
            bad.append(f"evaluation_population.csv lists {ids}, expected {want_pop}")
        try:
            total = sum(int(r["n_appointments"]) for r in pop_rows)
        except (KeyError, ValueError, TypeError):
            total = None
            _fail("estimator_implementation", f"{name}: csv n_appointments not integers")
            bad.append("evaluation_population.csv n_appointments must be integers")
        if total is not None and isinstance(pop, dict):
            claimed = _num(pop, "n_appointments")
            if claimed is not None and abs(total - claimed) > 1:
                _fail("estimator_implementation", f"{name}: csv sums to {total}, readout claims {claimed}")
                bad.append(f"evaluation_population.csv sums to {total} but the readout claims {claimed}")

    # 5. quantitative results: the feed audit, the programme effect, and the decomposition
    close("feed_defect_share_pct", _num(readout, "feed_defect_share_pct"), t["feed_defect_share"],
          TOL.DEFECT_SHARE_PP, "quantitative_results")
    close("programme_effect_pp", _num(readout, "programme_effect_pp"), t["reminder_effect_pp"],
          TOL.EFFECT_PP, "quantitative_results")
    att = readout.get("attribution_auc")
    if not isinstance(att, dict) or set(att) != set(t["attribution_auc"]):
        _fail("quantitative_results", f"{name}: attribution_auc must have exactly the five named keys")
        bad.append(f"attribution_auc must have exactly {sorted(t['attribution_auc'])}")
    else:
        for k, want in t["attribution_auc"].items():
            close(f"attribution_auc[{k}]", _num(att, k), want, TOL.ATTRIBUTION, "quantitative_results")

    # 6. independent validation. Two checks that do not depend on the population being the right one:
    #    (a) the reported as-served figure must be the figure the shipped scores actually give on the clinic set
    #        the readout itself declares - so a number that was not computed on the declared population fails;
    #    (b) the decomposition must close on the figures the readout itself states.
    if isinstance(pop, dict) and isinstance(pop.get("clinic_ids"), list) and isinstance(sc, dict):
        declared = {str(x) for x in pop["clinic_ids"]}
        rows_decl = [a for a in w["appointments"]
                     if a["clinic_id"] in declared and a["week"] >= w["spec"]["n_weeks"]
                     - w["spec"]["recent_weeks"] + 1]
        if len(rows_decl) >= 200:
            own = world.auc([a["_score"] for a in rows_decl], [a["no_show"] for a in rows_decl])
            got_served = _num(sc, "as_served")
            if got_served is None or abs(got_served - own) > TOL.AUC:
                _fail("independent_validation",
                      f"{name}: as_served {got_served} is not what the shipped scores give on the declared "
                      f"population ({own:.4f})")
                bad.append(f"auc_by_scoring.as_served = {got_served} but the shipped scores give "
                           f"{own:.4f} on the clinics the readout declares")
        else:
            _fail("independent_validation", f"{name}: declared population too small to validate")
    else:
        _fail("independent_validation", f"{name}: no declared population to validate against")
    if isinstance(att, dict):
        try:
            total = sum(float(v) for v in att.values())
            v, m = _num(readout, "validation_auc"), _num(readout, "monitored_auc")
            if v is None or m is None:
                _fail("independent_validation", f"{name}: cannot close the decomposition")
            elif abs(total - (v - m)) > TOL.ATTRIBUTION_SUM:
                _fail("independent_validation",
                      f"{name}: attribution sums to {total:.4f}, gap is {v - m:.4f}")
                bad.append(f"attribution_auc sums to {total:.4f} but validation - monitored is {v - m:.4f}")
        except (TypeError, ValueError):
            _fail("independent_validation", f"{name}: attribution_auc values must be numbers")
            bad.append("attribution_auc values must be numbers")
    else:
        _fail("independent_validation", f"{name}: no decomposition to close")

    # 7. the decision
    got = readout.get("decision")
    if got != t["decision"]:
        _fail("decision", f"{name}: decision {got!r} vs {t['decision']!r}")
        bad.append(f"decision = {got!r}, expected {t['decision']!r}")
    return bad


def test_database_unmodified():
    ref = tempfile.mkdtemp()
    _build_fixture("visible", Path(ref))
    assert world.db_digest(str(WORKSPACE / "data" / "appointments.sqlite")) == \
        world.db_digest(str(Path(ref) / "data" / "appointments.sqlite")), \
        "data/appointments.sqlite differs from the issued extract"


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
    required = ("model_version", "window_weeks", "monitored_auc", "validation_auc", "retention_floor_auc",
                "evaluation_population", "auc_by_scoring", "feed_defect_share_pct", "programme_effect_pp",
                "attribution_auc", "decision")
    missing = [k for k in required if k not in readout]
    if missing:
        _fail("evidence_reconstruction", f"readout.json is missing {missing}")
    assert not missing, f"readout.json is missing {missing}"
    assert readout["decision"] in ("retain_model", "retrain_on_recent_data", "replace_with_v4",
                                  "remediate_feature_pipeline"), "decision is not one of the four allowed values"
    assert rows is not None, "out/evaluation_population.csv was not written"
    assert set(rows[0].keys()) >= {"clinic_id", "n_appointments", "no_show_rate", "auc_as_served"}, \
        "evaluation_population.csv must have clinic_id, n_appointments, no_show_rate, auc_as_served"


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
