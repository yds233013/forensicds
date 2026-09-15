"""Verifier for ForensicDS G10 (unconstrained demand under stockout censoring).

Behavioural checks only; no source inspection. Every statistical quantity is graded against the generator's realised
demand with tolerances fixed by the tolerance pilot (research/g10/G10_tolerance_pilot.md).

  A. Source     data/warehouse.sqlite equals a pristine regeneration of the extract.
  B. Extract    `python -m demandsci review` is re-run (outputs deleted first) and graded: demand history structure and
                identities, demand and lost-units strata, category baseline trends and buy-plan actions, programme
                impact (lost units, lost share, forecast bias), determinism, build time.
  C. Other      the same command on three unseen extracts with other regimes and calendars.
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
from collections import Counter, defaultdict
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import truth as T  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
DB_REL = "data/warehouse.sqlite"
OUT_REL = "out/review"
BUILD_LIMIT_SEC = 900
TOL = json.loads((TESTS_DIR / "tolerances.json").read_text())
ACTION_MARGIN_PP = 2.0
HISTORY_COLS = {"store_id", "sku_id", "date", "units_sold", "expected_demand", "lost_units"}
TREND_COLS = {"category", "baseline_pre", "baseline_post", "baseline_change_pct", "action"}
ARMS = ("lean26", "holdout")
PERIODS = ("pre", "post")


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
        return None
    try:
        x = float(s)
    except ValueError:
        raise AssertionError(f"not a number: {v!r}")
    if not math.isfinite(x):
        raise AssertionError(f"not a finite number: {v!r}")
    return x


def run_review() -> dict:
    out = WORKSPACE / OUT_REL
    for name in ("demand_history.csv", "category_trends.csv", "programme_impact.json"):
        (out / name).unlink(missing_ok=True)
    cmd = [PIPELINE_PYTHON, "-m", "demandsci", "review", "--db", DB_REL, "--out", OUT_REL]
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
        with open(out / "demand_history.csv", newline="") as fh:
            res["history"] = list(csv.DictReader(fh))
        with open(out / "category_trends.csv", newline="") as fh:
            res["trends"] = list(csv.DictReader(fh))
        res["impact"] = json.loads((out / "programme_impact.json").read_text())
        res["raw"] = b"".join((out / n).read_bytes() for n in ("demand_history.csv", "category_trends.csv", "programme_impact.json"))
    except Exception as exc:  # recorded, asserted by tests
        res["read_error"] = repr(exc)
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier_g10_"))
    pristine = tmp / "pristine"
    w = world.build(copy.deepcopy(world.VISIBLE_SPEC), pristine)
    pristine_db = pristine / DB_REL
    agent_db = WORKSPACE / DB_REL
    backup = tmp / "agent_warehouse.sqlite"
    c = dict(pristine_digest=world.db_digest(pristine_db), hidden={})
    c["agent_digest"] = world.db_digest(agent_db) if agent_db.exists() else "<missing>"
    if agent_db.exists():
        shutil.copyfile(agent_db, backup)
    try:
        install_db(pristine_db)
        c["truth"] = T.expected(w)
        del w
        c["run1"] = run_review()
        c["run2"] = run_review()
        for hs in HIDDEN_SPECS:
            root = tmp / hs["name"]
            hw = world.build(copy.deepcopy(hs), root)
            ht = T.expected(hw)
            del hw
            install_db(root / DB_REL)
            c["hidden"][hs["name"]] = (ht, run_review())
            shutil.rmtree(root, ignore_errors=True)
    finally:
        if backup.exists():
            install_db(backup)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"review failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"review outputs missing or unreadable: {run['read_error']}"


# ------------------------------------------------------------------------------------------- parsing / derived


def history_map(run: dict) -> dict:
    rows = run["history"]
    missing = HISTORY_COLS - set(rows[0].keys() if rows else [])
    assert not missing, f"demand_history.csv is missing columns {sorted(missing)}"
    keys = Counter((r["store_id"], r["sku_id"], r["date"]) for r in rows)
    dup = [k for k, n in keys.items() if n > 1]
    assert not dup, f"{len(dup)} duplicate store/sku/date rows, e.g. {dup[:3]}"
    return {(r["store_id"], r["sku_id"], r["date"]): r for r in rows}


def rel_err(got: float, want: float) -> float:
    return 100.0 * (got / want - 1.0) if want else (0.0 if abs(got) < 1e-9 else float("inf"))


def strata_from_history(run: dict, t: dict) -> dict:
    """Aggregate the agent's history into the graded strata (period, arm, promo from the warehouse definitions)."""
    return run.setdefault("_strata", _strata(run, t))


def _strata(run, t):
    meta = t["meta"]
    totals, lost, dem = defaultdict(float), defaultdict(float), defaultdict(float)
    for k, r in history_map(run).items():
        if k not in meta:
            continue
        post, arm, promo = meta[k]
        e = num(r["expected_demand"])
        s = num(r["units_sold"])
        totals[(post, arm, promo)] += e
        lost[(post, arm)] += e - s
        lost[(post, promo)] += e - s
        dem[(post, arm)] += e
    return {"totals": totals, "lost": lost, "dem": dem}


def check_history_structure(run: dict, t: dict) -> None:
    got = history_map(run)
    missing, extra = set(t["keys"]) - set(got), set(got) - set(t["keys"])
    assert not missing and not extra, (f"demand history rows differ from the trading store-SKU-days: {len(missing)} "
                                       f"missing (e.g. {sorted(missing)[:3]}), {len(extra)} unexpected (e.g. {sorted(extra)[:3]})")
    bad_sold, bad_neg, bad_cons, bad_ident = [], [], [], []
    for k, r in got.items():
        sold, exp_d, lost = num(r["units_sold"]), num(r["expected_demand"]), num(r["lost_units"])
        if sold is None or exp_d is None or lost is None:
            bad_cons.append((k, "empty value"))
            continue
        if abs(sold - t["keys"][k]) > 1e-9:
            bad_sold.append((k, sold, t["keys"][k]))
        if exp_d < sold - 1e-6 or lost < -1e-6:
            bad_neg.append((k, sold, exp_d, lost))
        if abs(lost - (exp_d - sold)) > 1e-6 * max(1.0, exp_d):
            bad_cons.append((k, exp_d, sold, lost))
        if k in t["full_in_stock"] and abs(exp_d - sold) > 1e-6:
            bad_ident.append((k, sold, exp_d))
    assert not bad_sold, f"{len(bad_sold)} rows with units_sold different from the warehouse, e.g. {bad_sold[:3]}"
    assert not bad_neg, f"{len(bad_neg)} rows with expected demand below sales or negative lost units, e.g. {bad_neg[:3]}"
    assert not bad_cons, f"{len(bad_cons)} rows where lost_units != expected_demand - units_sold, e.g. {bad_cons[:3]}"
    assert not bad_ident, (f"{len(bad_ident)} rows that were on shelf for all trading hours have expected demand "
                           f"different from units sold, e.g. {bad_ident[:3]}")


def check_demand_strata(run: dict, t: dict) -> None:
    st = strata_from_history(run, t)
    bad = []
    for (post, arm, promo), want in t["totals"].items():
        key = f"total::post{int(post == 'post')}_lean{int(arm == 'lean26')}_promo{int(promo == 'promo')}"
        e = rel_err(st["totals"][(post, arm, promo)], want)
        if abs(e) > TOL[key]:
            bad.append((post, arm, promo, round(e, 2), TOL[key]))
    assert not bad, f"expected-demand totals outside tolerance (period, arm, promo, error %, tolerance %): {bad}"


def check_lost_strata(run: dict, t: dict) -> None:
    """Lost units before go-live (all stores; by promotion) and from go-live (by arm; by promotion)."""
    st = strata_from_history(run, t)
    got, want = dict(st["lost"]), dict(t["lost"])
    got[("pre", "all")] = got.get(("pre", "lean26"), 0.0) + got.get(("pre", "holdout"), 0.0)
    want[("pre", "all")] = want[("pre", "lean26")] + want[("pre", "holdout")]
    graded = [(("pre", "all"), "lost::pre_all")]
    graded += [((p, pr), f"lost::post{int(p == 'post')}_promo{int(pr == 'promo')}") for p in PERIODS for pr in ("nonpromo", "promo")]
    graded += [(("post", a), f"lost::post1_lean{int(a == 'lean26')}") for a in ARMS]
    bad = []
    for key, tk in graded:
        e = rel_err(got.get(key, 0.0), want[key])
        if abs(e) > TOL[tk]:
            bad.append((*key, round(e, 2), TOL[tk]))
    assert not bad, f"lost units outside tolerance (period, group, error %, tolerance %): {bad}"


def trends_map(run: dict) -> dict:
    rows = run["trends"]
    missing = TREND_COLS - set(rows[0].keys() if rows else [])
    assert not missing, f"category_trends.csv is missing columns {sorted(missing)}"
    return {r["category"]: r for r in rows}


def check_trends(run: dict, t: dict) -> None:
    got = trends_map(run)
    assert set(got) == set(t["category_change"]), f"categories {sorted(got)} expected {sorted(t['category_change'])}"
    # baselines must be the ones implied by the submitted demand history
    meta = t["meta"]
    series = defaultdict(lambda: [0.0, 0])
    for k, r in history_map(run).items():
        if k in meta and meta[k][2] == "nonpromo":
            acc = series[(t["cat_of"][k[1]], meta[k][0], k[0], k[1])]
            acc[0] += num(r["expected_demand"])
            acc[1] += 1
    base = defaultdict(float)
    for (cat, post, _s, _k), (sm, n) in series.items():
        base[(cat, post)] += sm / n
    bad_cons, bad_tol, bad_act, bad_rule = [], [], [], []
    for cat, want in t["category_change"].items():
        r = got[cat]
        pre, post, ch = num(r["baseline_pre"]), num(r["baseline_post"]), num(r["baseline_change_pct"])
        if abs(pre - base[(cat, "pre")]) > 1e-6 * max(1, pre) or abs(post - base[(cat, "post")]) > 1e-6 * max(1, post) \
                or abs(ch - 100 * (post / pre - 1)) > 1e-6:
            bad_cons.append((cat, pre, post, ch))
        if abs(ch - want) > TOL[f"cat_change::{cat}"]:
            bad_tol.append((cat, round(ch, 2), round(want, 2), TOL[f"cat_change::{cat}"]))
        rule_act = "reduce" if ch <= -5 else "increase" if ch >= 5 else "maintain"
        if (r["action"] or "").strip() != rule_act:
            bad_rule.append((cat, r["action"], round(ch, 3)))
        if min(abs(want - 5), abs(want + 5)) >= ACTION_MARGIN_PP:
            want_act = "reduce" if want <= -5 else "increase" if want >= 5 else "maintain"
            if (r["action"] or "").strip() != want_act:
                bad_act.append((cat, r["action"], want_act))
    assert not bad_cons, f"category baselines are not the ones implied by demand_history.csv: {bad_cons[:4]}"
    assert not bad_tol, f"baseline change outside tolerance (category, got pp, truth pp, tolerance): {bad_tol}"
    assert not bad_act, f"buy-plan actions differ (category, got, expected): {bad_act}"
    assert not bad_rule, f"actions do not follow the buy-plan rule for the reported baseline change: {bad_rule}"


def check_impact(run: dict, t: dict) -> None:
    imp = run["impact"]
    st = strata_from_history(run, t)
    assert imp.get("go_live_date") == t["go_live_date"], f"go_live_date {imp.get('go_live_date')} expected {t['go_live_date']}"
    bad = []
    for p in PERIODS:
        for a in ARMS:
            lu = num((imp.get("lost_units") or {}).get(p, {}).get(a))
            ls = num((imp.get("lost_share") or {}).get(p, {}).get(a))
            if lu is None or ls is None:
                bad.append((p, a, "missing"))
                continue
            if abs(lu - st["lost"][(p, a)]) > 1e-6 * max(1, lu) or abs(ls - st["lost"][(p, a)] / st["dem"][(p, a)]) > 1e-9:
                bad.append((p, a, "not consistent with demand_history.csv", lu, ls))
                continue
            if p == "post":                                    # before go-live the arms are consistency-checked only
                key = f"lost::post1_lean{int(a == 'lean26')}"
                e = rel_err(ls, t["lost_share"][(p, a)])
                if abs(e) > TOL[key]:
                    bad.append((p, a, "lost_share", round(ls, 5), round(t["lost_share"][(p, a)], 5)))
    fb = imp.get("forecast_bias_pct") or {}
    for k, tk in (("v3_pre_all_stores", "bias::v3_pre"), ("v4_post_lean26", "bias::v4_post_lean")):
        v = num(fb.get(k))
        if v is None or abs(v - t["bias"][k]) > TOL[tk]:
            bad.append((k, v, round(t["bias"][k], 3), TOL[tk]))
    assert not bad, f"programme impact differs: {bad}"


# ------------------------------------------------------------------------------------------- A. source


def test_warehouse_unmodified(ctx):
    """data/warehouse.sqlite is the system of record and is unchanged."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], "data/warehouse.sqlite differs from the extract"


# ------------------------------------------------------------------------------------------- B. this extract


def test_review_succeeds(ctx):
    """`python -m demandsci review` succeeds and writes the three review outputs."""
    require_run(ctx["run1"])


def test_build_time(ctx):
    """A review on this extract finishes within 15 minutes."""
    require_run(ctx["run1"])
    assert ctx["run1"]["seconds"] <= BUILD_LIMIT_SEC, f"review took {ctx['run1']['seconds']:.0f} s (limit {BUILD_LIMIT_SEC} s)"


def test_demand_history_structure(ctx):
    """One row per trading store-SKU-day; units sold as recorded; lost = expected - sold >= 0; expected demand equals
    sales on days the item was on shelf for all trading hours."""
    require_run(ctx["run1"])
    check_history_structure(ctx["run1"], ctx["truth"])


def test_expected_demand_strata(ctx):
    """Expected demand by period x programme arm x promotion within tolerance of realised demand."""
    require_run(ctx["run1"])
    check_demand_strata(ctx["run1"], ctx["truth"])


def test_lost_units_strata(ctx):
    """Lost units within tolerance of realised lost demand: before go-live overall and by promotion; from go-live by
    programme arm and by promotion."""
    require_run(ctx["run1"])
    check_lost_strata(ctx["run1"], ctx["truth"])


def test_category_trends(ctx):
    """Category baselines implied by the history; baseline change within tolerance; buy-plan actions."""
    require_run(ctx["run1"])
    check_trends(ctx["run1"], ctx["truth"])


def test_programme_impact(ctx):
    """Lost units and lost share by period x arm, and production forecast bias against demand."""
    require_run(ctx["run1"])
    check_impact(ctx["run1"], ctx["truth"])


def test_rerun_is_deterministic(ctx):
    """Re-running the review on the same extract reproduces the outputs byte for byte."""
    require_run(ctx["run2"])
    assert ctx["run1"]["raw"] == ctx["run2"]["raw"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. other extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_demand_history(ctx, name):
    """Other extracts: demand history structure, demand and lost-units strata."""
    t, run = ctx["hidden"][name]
    require_run(run)
    check_history_structure(run, t)
    check_demand_strata(run, t)
    check_lost_strata(run, t)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_trends_and_impact(ctx, name):
    """Other extracts: category trends, actions and programme impact."""
    t, run = ctx["hidden"][name]
    require_run(run)
    check_trends(run, t)
    check_impact(run, t)
