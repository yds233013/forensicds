"""Verifier for ForensicDS G50 (Boost national-rollout decision).

The agent submits an executable procedure. The verifier regenerates four worlds it has never seen,
runs the agent's own command against each, and grades only the newly produced outputs.

What is graded is what the final state can actually evidence: whether the metric population and the
market-week evidence were rebuilt, whether the reported decision quantity is a different object from
the phase-2 arm contrast, whether it lands near the world-specific rollout effect, whether the
interval is a market-level interval, whether the courier-supply response was measured, and whether
the memo's decision rule was applied. It does not grade reasoning, warrant, or estimator identity.
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
import time
from pathlib import Path

sys.path.insert(0, os.environ.get("TESTS_DIR", "/tests"))

import numpy as np                                      # noqa: E402  (image analytics stack)
import scenarios                                        # noqa: E402
import world                                            # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
TESTS_DIR = Path(os.environ.get("TESTS_DIR", "/tests"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", sys.executable)
LOGS = Path("/logs/verifier")

# The command the task instruction freezes as the executable entry point.
RUN_ARGS = ["-m", "northline_eval", "readout", "--db", "data/northline.sqlite", "--out", "out"]
RUN_TIMEOUT_S = 1800

READOUT_KEYS = {
    "orders_analysed": int,
    "order_arm_contrast_pp": float,
    "programme_effect_pp": float,
    "programme_effect_ci_low_pp": float,
    "programme_effect_ci_high_pp": float,
    "inference_unit_n": int,
    "courier_hours_response_pct": float,
    "decision": str,
}
PANEL_COLUMNS = ["market_id", "week_start", "orders", "late_orders", "late_rate_pct",
                 "boost_share", "courier_hours"]

# --- tolerances -------------------------------------------------------------------------------
# Measured over the four graded worlds against the frozen world.truth() anchor:
#   reference (pre-adjusted, estate-weighted market-level) max deviation 0.815 pp; the other
#   legitimate routes (weighted two-way FE 0.804, arm-level pooled 0.846, market-unweighted 1.072,
#   post-treatment weights 0.817, one-week pre-window 0.870, boost-share panel 0.717) all sit below
#   1.30.  The routes that get the scientific object wrong sit far above it: unadjusted estate-
#   weighted 3.519, unadjusted market-unweighted 7.344, arms swapped 20.030, raw arm contrast 9.391
#   (minimum separation over the four worlds 3.325 -> 2.55x this tolerance).
EFFECT_TOL_PP = 1.303
# The arm contrast is a reconstruction of a number in the data, not an estimate: tight.
CONTRAST_TOL_PP = 0.25
# The decision quantity must not be the arm contrast. The two differ by >= 6.9 pp on every graded
# world; 1.5 pp is well inside that and well outside any rounding.
MIN_OBJECT_GAP_PP = 1.5
# Courier-hours response: four defensible definitional variants spread 1.022 pp and deviate up to
# 1.718 from the anchor, against an incumbent (zero-power identity check) minimum error of 1.957.
# A flat band cannot separate those, so the band is mixed. Admits all four variants with >= 2.2x
# headroom; rejects the incumbent on all four worlds, tightest margin 1.63x.
def courier_tol(anchor: float) -> float:
    return max(1.20, 0.12 * abs(anchor))
# A market-level interval on 16 enrolled markets is 4.6-7.1x wider than an order-level interval on
# ~200k orders (reference widths 3.97-6.29 pp; order-level arm widths 0.867-0.931 pp). The band is
# set on absolute width, not relative to the reference, so it does not encode the reference's SE.
CI_MIN_WIDTH_PP = 2.0
CI_MAX_WIDTH_PP = 25.0
CI_CONTAIN_SLACK_PP = 0.5
MAX_INFERENCE_UNITS = 40          # 20 markets; an order- or market-week-level count fails this

CRITERIA = ["evidence_reconstruction", "scientific_object", "quantitative_result",
            "uncertainty", "courier_supply_response", "decision"]

SKIP_TREE = {"data", "out", "__pycache__", ".git", ".ipynb_checkpoints", ".venv", "venv"}


# --- helpers ----------------------------------------------------------------------------------
def _no_nan(s):
    raise AssertionError(f"readout.json contains the non-JSON constant {s!r}")


def _num(v):
    """A JSON number, not a bool and not a numeric string."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    if not math.isfinite(float(v)):
        return None
    return float(v)


def _int(v):
    if isinstance(v, bool) or not isinstance(v, int):
        return None
    return int(v)


def _escapes(path: Path, root: Path) -> bool:
    try:
        return not str(path.resolve()).startswith(str(root.resolve()))
    except OSError:
        return True


def copy_submission(dest: Path) -> list[str]:
    """Copy the agent's code into a private scratch tree. data/ and out/ are never copied, so a
    pre-baked warehouse or a pre-baked output directory cannot travel with the submission."""
    notes = []
    for src in sorted(WORKSPACE.rglob("*")):
        rel = src.relative_to(WORKSPACE)
        if set(rel.parts) & SKIP_TREE:
            continue
        if src.is_symlink():
            if _escapes(src, WORKSPACE):
                notes.append(f"symlink outside the workspace not copied: {rel}")
                continue
            notes.append(f"symlink flattened: {rel}")
            if src.is_dir():
                continue
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copyfile(src, dest / rel)
            except OSError as exc:
                notes.append(f"{rel}: {exc}")
            continue
        if src.is_dir():
            (dest / rel).mkdir(parents=True, exist_ok=True)
        elif src.is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest / rel)
    return notes


def authoritative(w) -> dict:
    """Everything the verifier needs about one world, from the generator."""
    t = world.truth(w)
    o = w["o"]
    m_of, w_of = w["m_ix"][o], w["w_ix"][o]
    pop = world.metric_population(w)
    # Lateness as the warehouse records it. The generator's latent flag is computed on unrounded
    # delivery times; `orders.delivered_after_min` is stored to two decimals, so 1.5-2.1 orders per
    # 10,000 sit exactly on the promise boundary and flip. The analyst can only see the recorded
    # value, so that is what the panel and the arm contrast are graded against. (The rollout effect
    # has no recorded counterpart - it is a contrast of potential outcomes - so world.truth() stays
    # the anchor there; the same discretisation moves it by under 0.01 pp.)
    late = (np.round(w["total"], 2) > w["spec"]["promise_min"])
    mids = [f"MKT-{i + 1:03d}" for i in range(w["M"])]
    weeks = [(world.EPOCH + world.timedelta(days=wk * 7)).isoformat() for wk in range(w["W"])]

    panel = {}
    for mi in range(w["M"]):
        for wk in range(w["W"]):
            sel = (m_of == mi) & (w_of == wk) & pop
            n = int(sel.sum())
            if n == 0:
                continue
            hrs = ((w["m_ix"] == mi) & (w["w_ix"] == wk))
            row = dict(orders=n, late_orders=int(late[sel].sum()),
                       courier_hours=float(np.round(w["Kact"][hrs]).sum()))
            row["late_rate_pct"] = row["late_orders"] / n * 100.0
            # boost_share is NOT graded against a single value. Two sources are defensible and the
            # output contract does not disambiguate them: the realised per-order arm in
            # experiment_assignment (0 in phase 1, where Boost was set at market level and no
            # assignment row exists) and the configured experiment_config.boost_share_target (1.0
            # for a phase-1 on market). Grading either convention exactly would fail a legitimate
            # route, so only the facts both conventions agree on are graded: the share is a
            # proportion, nothing was boosted before the programme opened, and something was
            # boosted in phase 2. See the limitations section of the handoff.
            in_p2 = bool(wk >= w["PW"] + w["SW"]) and mi in set(int(x) for x in w["enrolled"])
            row["share_band"] = ((0.05, 1.0) if in_p2
                                 else ((0.0, 0.02) if wk < w["PW"] else (0.0, 1.0)))
            panel[(mids[mi], weeks[wk])] = row

    g = w["exp_mh"][o] & w["enr_mh"][o] & pop
    b = w["boosted"]
    arm_contrast = float((late[g & b].mean() - late[g & ~b].mean()) * 100.0)

    ci_excludes_zero = True       # verified for every legitimate route on every graded world
    decision = ("roll_out" if (t["rollout_effect_pp"] <= -t["break_even_pp"] and ci_excludes_zero)
                else "do_not_roll_out")
    return dict(
        panel=panel,
        n_markets=w["M"], n_weeks=w["W"],
        orders_analysed=t["graded_orders"],
        arm_contrast_pp=round(arm_contrast, 4),
        effect_pp=t["rollout_effect_pp"],
        courier_pct=t["courier_supply_response_pct"],
        decision=decision,
        break_even_pp=t["break_even_pp"],
    )


def run_submission(scratch: Path) -> dict:
    """Run the frozen command in the scratch tree as the unprivileged pipeline user."""
    out = scratch / "out"
    shutil.rmtree(out, ignore_errors=True)          # no stale outputs survive into grading
    assert not out.exists(), "could not clear the output directory"
    t0 = time.time()
    proc = subprocess.run(
        [PIPELINE_PYTHON] + RUN_ARGS, cwd=str(scratch), timeout=RUN_TIMEOUT_S,
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "HOME": "/tmp", "PYTHONPATH": str(scratch),
             "PYTHONDONTWRITEBYTECODE": "1", "MPLBACKEND": "Agg",
             "OPENBLAS_NUM_THREADS": "2", "OMP_NUM_THREADS": "2"},
    )
    return dict(rc=proc.returncode, stdout=proc.stdout[-4000:], stderr=proc.stderr[-4000:],
                t0=t0, elapsed=time.time() - t0)


def grade(scratch: Path, auth: dict, run: dict) -> tuple[dict, list[str]]:
    res = {c: False for c in CRITERIA}
    why: list[str] = []
    out = scratch / "out"
    rj, pc = out / "readout.json", out / "market_week_panel.csv"

    if run["rc"] != 0:
        why.append(f"the frozen command exited {run['rc']}: {run['stderr'][-600:]}")
        return res, why
    for p in (rj, pc):
        if not p.is_file() or p.is_symlink():
            why.append(f"{p.name} was not produced as a regular file by the frozen command")
            return res, why
        if p.stat().st_mtime < run["t0"] - 1.0:
            why.append(f"{p.name} predates the run: stale output")
            return res, why

    try:
        r = json.loads(rj.read_text(), parse_constant=_no_nan)
    except Exception as exc:
        why.append(f"readout.json is not parseable JSON: {exc}")
        return res, why
    if not isinstance(r, dict):
        why.append("readout.json is not a JSON object")
        return res, why
    if set(r) != set(READOUT_KEYS):
        why.append(f"readout.json keys are {sorted(set(r))}, contract requires "
                   f"{sorted(READOUT_KEYS)}")
        return res, why

    v = {}
    for k, kind in READOUT_KEYS.items():
        if kind is str:
            v[k] = r[k] if isinstance(r[k], str) else None
        elif kind is int:
            v[k] = _int(r[k])
        else:
            v[k] = _num(r[k])
        if v[k] is None:
            why.append(f"{k} is not a finite {kind.__name__}: {r[k]!r}")
    if any(x is None for x in v.values()):
        return res, why

    # --- evidence_reconstruction ---------------------------------------------------------------
    ev, bad = [], 0
    try:
        with pc.open(newline="") as fh:
            rows = list(csv.reader(fh))
    except Exception as exc:
        rows = []
        ev.append(f"panel unreadable: {exc}")
    if rows and [c.strip() for c in rows[0]] != PANEL_COLUMNS:
        ev.append(f"panel header is {rows[0]}, contract requires {PANEL_COLUMNS}")
    elif rows:
        seen, dup = {}, 0
        for ln in rows[1:]:
            if len(ln) != len(PANEL_COLUMNS):
                bad += 1
                continue
            key = (ln[0].strip(), ln[1].strip()[:10])
            if key in seen:
                dup += 1
            seen[key] = ln
        if dup:
            ev.append(f"{dup} duplicate market-week rows in the panel")
        if bad:
            ev.append(f"{bad} panel rows have the wrong number of fields")
        missing = sorted(set(auth["panel"]) - set(seen))
        extra = sorted(set(seen) - set(auth["panel"]))
        if missing:
            ev.append(f"{len(missing)} market-weeks missing from the panel, e.g. {missing[:3]}")
        if extra:
            ev.append(f"{len(extra)} market-weeks in the panel are not in the warehouse window, "
                      f"e.g. {extra[:3]}")
        nerr = {}
        for key, want in auth["panel"].items():
            ln = seen.get(key)
            if ln is None:
                continue
            try:
                got_n, got_l = int(float(ln[2])), int(float(ln[3]))
                got_r, got_b, got_h = float(ln[4]), float(ln[5]), float(ln[6])
            except ValueError:
                nerr.setdefault("unparseable numbers", []).append(key)
                continue
            if got_n != want["orders"]:
                nerr.setdefault("orders", []).append(key)
            if got_l != want["late_orders"]:
                nerr.setdefault("late_orders", []).append(key)
            if abs(got_r - want["late_rate_pct"]) > 1e-4:
                nerr.setdefault("late_rate_pct", []).append(key)
            if abs(got_h - want["courier_hours"]) > 1e-4:
                nerr.setdefault("courier_hours", []).append(key)
            blo, bhi = want["share_band"]
            if not (blo - 1e-9 <= got_b <= bhi + 1e-9):
                nerr.setdefault(f"boost_share outside [{blo}, {bhi}]", []).append(key)
        for col, keys in sorted(nerr.items()):
            ev.append(f"panel {col} wrong in {len(keys)} market-weeks, e.g. {keys[:3]}")
    if v["orders_analysed"] != auth["orders_analysed"]:
        ev.append(f"orders_analysed {v['orders_analysed']} != {auth['orders_analysed']} "
                  "(metric population, phase 2, enrolled markets)")
    res["evidence_reconstruction"] = not ev
    why += ev

    # --- scientific_object ---------------------------------------------------------------------
    so = []
    d = abs(v["order_arm_contrast_pp"] - auth["arm_contrast_pp"])
    if d > CONTRAST_TOL_PP:
        so.append(f"order_arm_contrast_pp off by {d:.3f} pp (> {CONTRAST_TOL_PP})")
    gap = abs(v["programme_effect_pp"] - v["order_arm_contrast_pp"])
    if gap < MIN_OBJECT_GAP_PP:
        so.append(f"programme_effect_pp is within {gap:.3f} pp of the arm contrast: the decision "
                  "quantity has not been distinguished from the arm contrast")
    res["scientific_object"] = not so
    why += so

    # --- quantitative_result -------------------------------------------------------------------
    d = abs(v["programme_effect_pp"] - auth["effect_pp"])
    res["quantitative_result"] = d <= EFFECT_TOL_PP
    if not res["quantitative_result"]:
        why.append(f"programme_effect_pp {v['programme_effect_pp']:+.3f} is {d:.3f} pp from the "
                   f"rollout effect {auth['effect_pp']:+.3f} (tolerance {EFFECT_TOL_PP})")

    # --- uncertainty ---------------------------------------------------------------------------
    un = []
    lo, hi, pt = v["programme_effect_ci_low_pp"], v["programme_effect_ci_high_pp"], v["programme_effect_pp"]
    wid = hi - lo
    if not lo < hi:
        un.append(f"interval is not an interval: [{lo}, {hi}]")
    else:
        if not lo - 1e-9 <= pt <= hi + 1e-9:
            un.append(f"interval [{lo:+.3f}, {hi:+.3f}] does not contain the estimate {pt:+.3f}")
        if wid < CI_MIN_WIDTH_PP:
            un.append(f"interval width {wid:.3f} pp is below {CI_MIN_WIDTH_PP}: this is order-level "
                      "precision for a market-randomised quantity")
        if wid > CI_MAX_WIDTH_PP:
            un.append(f"interval width {wid:.3f} pp exceeds {CI_MAX_WIDTH_PP}: uninformative")
        if not (lo - CI_CONTAIN_SLACK_PP <= auth["effect_pp"] <= hi + CI_CONTAIN_SLACK_PP):
            un.append(f"interval [{lo:+.3f}, {hi:+.3f}] excludes the rollout effect "
                      f"{auth['effect_pp']:+.3f}")
    n = v["inference_unit_n"]
    if not 2 <= n <= MAX_INFERENCE_UNITS:
        un.append(f"inference_unit_n {n} is not a count of independent randomisation units "
                  f"(2..{MAX_INFERENCE_UNITS})")
    res["uncertainty"] = not un
    why += un

    # --- courier_supply_response ---------------------------------------------------------------
    tol = courier_tol(auth["courier_pct"])
    d = abs(v["courier_hours_response_pct"] - auth["courier_pct"])
    res["courier_supply_response"] = d <= tol
    if not res["courier_supply_response"]:
        why.append(f"courier_hours_response_pct {v['courier_hours_response_pct']:+.3f} is {d:.3f} "
                   f"from {auth['courier_pct']:+.3f} (tolerance {tol:.3f})")

    # --- decision ------------------------------------------------------------------------------
    res["decision"] = v["decision"] == auth["decision"]
    if not res["decision"]:
        why.append(f"decision {v['decision']!r} != {auth['decision']!r}")
    return res, why


# --- the test ---------------------------------------------------------------------------------
def test_boost_rollout_readout():
    LOGS.mkdir(parents=True, exist_ok=True)
    assert (WORKSPACE / "northline_eval").is_dir(), "no northline_eval package in /workspace"

    # An opaque scratch root, and scratch directories named by index rather than by world, so the
    # submitted code cannot read which world it is being run against from its own surroundings.
    root = Path(tempfile.mkdtemp(prefix="g50-", dir="/tmp"))
    os.chmod(root, 0o711)
    per_world, notes = {}, []
    for i, name in enumerate(scenarios.ALL_NAMES):
        w = world.build(scenarios.by_name(name))
        auth = authoritative(w)
        scratch = root / f"r{i}"
        scratch.mkdir()
        notes += [f"{name}: {m}" for m in copy_submission(scratch)]
        world.write_sqlite(w, str(scratch))
        del w
        for p in scratch.rglob("*"):
            try:
                os.chmod(p, 0o777 if p.is_dir() else 0o666)
            except OSError:
                pass
        os.chmod(scratch, 0o777)
        os.chmod(scratch / "data", 0o755)
        for p in (scratch / "data").iterdir():
            os.chmod(p, 0o444)                      # read-only warehouse
        run = run_submission(scratch)
        res, why = grade(scratch, auth, run)
        per_world[name] = dict(criteria=res, reasons=why, rc=run["rc"],
                               elapsed=round(run["elapsed"], 1))
        print(f"\n=== {name} (rc={run['rc']}, {run['elapsed']:.1f}s) ===")
        print("  anchors: effect %+.4f  contrast %+.4f  courier %+.4f  decision %s  orders %d"
              % (auth["effect_pp"], auth["arm_contrast_pp"], auth["courier_pct"],
                 auth["decision"], auth["orders_analysed"]))
        for c in CRITERIA:
            print(f"  {'PASS' if res[c] else 'FAIL'}  {c}")
        for m in why:
            print(f"    - {m}")
        if run["rc"] != 0:
            print("  stderr tail:\n" + "\n".join("    " + l for l in run["stderr"].splitlines()[-25:]))

    merged = {c: all(per_world[n]["criteria"][c] for n in per_world) for c in CRITERIA}
    (LOGS / "criteria.json").write_text(json.dumps({k: int(v) for k, v in merged.items()},
                                                   sort_keys=True))
    (LOGS / "g50_detail.json").write_text(json.dumps(
        dict(per_world=per_world, merged=merged, notes=notes), indent=1, sort_keys=True))
    shutil.rmtree(root, ignore_errors=True)

    failed = [c for c in CRITERIA if not merged[c]]
    assert not failed, "criteria failed across the graded worlds: " + ", ".join(failed)
