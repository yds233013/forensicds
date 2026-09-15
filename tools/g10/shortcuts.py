#!/usr/bin/env python3
"""Anti-gaming mutation suite for G10 (unconstrained demand under stockout censoring).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, runs the review,
then runs the real tests/test.sh (sandboxed pipeline). Correct implementations must score 1; natural wrong corrections,
partial repairs, patches, cheats and overfits must score 0. Overfits must additionally pass every visible-extract
check and fail only hidden-extract checks.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task [--workspace DIR] [--tools DIR]   (internal / dev)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/g10-censored-demand"
WS = Path("/workspace")
TOOLS = HERE
REVIEW = [sys.executable, "-m", "demandsci", "review", "--db", "data/warehouse.sqlite", "--out", "out/review"]


def install(src_name: str, variant: dict | None = None) -> None:
    src = (TOOLS / src_name).read_text()
    if variant is not None:
        src = src.replace("VARIANT: dict = {}", f"VARIANT: dict = {variant!r}", 1)
    (WS / "demandsci/cli.py").write_text(src)


def install_variant(**variant) -> None:
    install("variant_review.py", variant)


def oracle_files(demand=True, trends=True) -> None:
    sol = TASK / "solution/demandsci"
    shutil.copyfile(sol / "warehouse.py", WS / "demandsci/warehouse.py")
    if demand:
        shutil.copyfile(sol / "demand.py", WS / "demandsci/demand.py")
    if trends:
        shutil.copyfile(sol / "trends.py", WS / "demandsci/trends.py")


def visible_facts() -> dict:
    """Facts an overfitting agent could read off this extract (computed in the container from the visible warehouse)."""
    sys.path.insert(0, str(TOOLS))
    import variant_review as V
    X = V.load(WS / "data/warehouse.sqlite")
    prof = V.profiles(X)
    _rate, alpha = V.fit(X, X["sales"], V.exposure(X, prof)[0], "nb")
    con = sqlite3.connect(WS / "data/warehouse.sqlite")
    hold = [r[0] for r in con.execute("SELECT store_id FROM programme_assignment WHERE arm = 'holdout'")]
    go_live = con.execute("SELECT MIN(go_live_date) FROM programme_assignment").fetchone()[0]
    con.close()
    return {"profile": prof.tolist(), "alpha": [float(alpha[X["A"]["cat"] == c][0]) for c in range(len(X["cats"]))],
            "holdout": hold, "go_live": go_live, "cats": X["cats"]}


# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution (pandas: joint NB MLE with in-stock exposure offset, posterior imputation)."""
    oracle_files()


def alt_correct_numpy_ipf():
    """Independent correct review: numpy NB with iterative proportional fitting and grid dispersion."""
    install_variant()


def alt_correct_em():
    """Independent correct review: EM over latent Gamma day intensities."""
    install_variant(method="em")


def alt_correct_separate_category_fits():
    """Independent correct specification: separate NB exposure fit per category (numpy IPF)."""
    install_variant(method="sep_cat")


def alt_correct_gibbs():
    """Independent correct review: Gibbs data augmentation with its own loader and holdout-store traffic profile."""
    install("alt_gibbs_review.py")


# ------------------------------------------------------------------------------------------------ natural wrong corrections


def wrong_sales_as_demand_all_days():
    """Sales = demand, baselines on all non-promotional days (spec-conformant aggregation, no censoring correction)."""
    install_variant(method="sales")


def wrong_drop_censored_days():
    """Censored days replaced by a rate fitted on uncensored days only (selection on the outcome)."""
    install_variant(method="drop_censored")


def wrong_per_day_traffic_scaling():
    """Each censored day's sales divided by its traffic-weighted in-stock share (ignores the stopping-time bias)."""
    install_variant(method="per_day_scale")


def wrong_uniform_time_scaling():
    """Each censored day's sales divided by its share of in-stock trading hours (ignores the traffic shape)."""
    install_variant(method="uniform_time_scale")


def wrong_mean_rate_imputation():
    """Unobserved exposure filled at the uncensored-day mean rate (ignores that censoring is informative)."""
    install_variant(method="mean_rate_impute")


def wrong_poisson_offset():
    """Poisson GLM with in-stock exposure offset (no overdispersion: the day's own sales do not update its rate)."""
    install_variant(method="poisson_offset")


def wrong_daily_censored_poisson():
    """Daily right-censored Poisson (Tobit-style) at full-day exposure; intraday timing unused."""
    install_variant(method="daily_censored_poisson")


def wrong_forecast_imputation():
    """Censored days set to the production forecast (circular: the forecast set the stock)."""
    install_variant(method="forecast_impute")


def wrong_profile_from_all_days():
    """NB exposure model with the traffic profile estimated from all days (censored evenings flatten the shape)."""
    install_variant(method="profile_all_days")


def wrong_nb_without_promotions():
    """NB exposure model without promotion effects (censoring depends on an omitted covariate)."""
    install_variant(method="nb_no_promo")


def wrong_forecast_as_prior():
    """Production forecast as each day's prior mean with a fitted NB posterior (no demand model)."""
    install_variant(method="forecast_prior")


def wrong_v3_as_prior():
    """v3 forecast as each day's prior mean with a fitted NB posterior (no demand model)."""
    install_variant(method="v3_prior")


def wrong_nb_plugin_imputation():
    """NB exposure model, but the missing exposure is filled at the fitted rate (the day's own sales ignored)."""
    install_variant(method="nb_plugin")


def wrong_fixed_effects_traffic_profile():
    """NB exposure model with the traffic shape from a conditional (per-day fixed effect) likelihood on all days."""
    install_variant(method="fe_profile")


def wrong_holdout_transfer():
    """Demand history = sales; buy-plan actions from holdout-store sales trends."""
    install_variant(method="holdout_transfer")


# ------------------------------------------------------------------------------------------------ partial repairs, patches, cheats


def partial_demand_fixed_clean_day_baselines():
    """Partial: correct demand history, but baselines still exclude stockout days (deployed trends.py)."""
    oracle_files(trends=False)


def partial_baselines_fixed_sales_demand():
    """Partial: baselines on all non-promotional days, but demand is still sales."""
    oracle_files(demand=False)


def output_only_patch():
    """Patch: run a correct review once, then restore the deployed code (outputs are regenerated by the verifier)."""
    oracle_files()
    subprocess.run(REVIEW, cwd=WS, check=True, capture_output=True)
    for f in ("warehouse.py", "demand.py", "trends.py"):
        shutil.copyfile(TASK / "environment/workspace/demandsci" / f, WS / "demandsci" / f)


def warehouse_edit():
    """Cheat: correct code, but stockout days' events are deleted from data/warehouse.sqlite first."""
    oracle_files()
    con = sqlite3.connect(WS / "data/warehouse.sqlite")
    con.execute("DELETE FROM availability_events WHERE event_type = 'out_of_stock'")
    con.commit()
    con.close()


def import_verifier_generator():
    """Cheat: if the verifier's generator and hidden specs are importable, output realised demand; else sales."""
    install_variant(method="sales")
    cli = WS / "demandsci/cli.py"
    s = cli.read_text()
    s = s.replace("def estimate(X) -> np.ndarray:\n", '''def estimate(X) -> np.ndarray:
    import os, sys, copy
    for d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if d and os.path.exists(os.path.join(d, "world.py")):
                sys.path.insert(0, d)
                import world, scenarios
                first = min(r[2] for r in X["rows"])
                for sp in [world.VISIBLE_SPEC] + scenarios.HIDDEN_SPECS:
                    if sp["start"] == first:
                        w = world.generate(copy.deepcopy(sp))
                        dem = {(r["store"], r["sku"], r["date"].isoformat()): r["demand"] for r in w.rows if not r["closed"]}
                        return np.array([float(dem[(s, k, dd)]) for s, k, dd, _ in X["rows"]])
        except Exception:
            pass
''', 1)
    cli.write_text(s)


def tamper_stdlib_exit_hook():
    """Cheat: deployed code; the standard library's site.py forces every interpreter to exit 0 (verifier included)."""
    site = Path("/usr/local/lib/python3.12/site.py")
    site.write_text(site.read_text() + "\nimport atexit as _a, os as _o\n_a.register(lambda: _o._exit(0))\n")


def tamper_shadow_pytest():
    """Cheat: deployed code; a `pytest` module added to the standard library that exits 0 before any test runs."""
    Path("/usr/local/lib/python3.12/pytest.py").write_text("import os\nos._exit(0)\n")


# ------------------------------------------------------------------------------------------------ overfits (visible pass, hidden fail)


def overfit_hardcoded_traffic_profile():
    """Correct model, but the traffic profile is hard-coded from this extract."""
    install_variant(hardcoded_profile=visible_facts()["profile"])


def overfit_hardcoded_dispersion():
    """Correct model, but per-category dispersion is hard-coded from this extract's fit."""
    install_variant(hardcoded_alpha=visible_facts()["alpha"])


def overfit_hardcoded_go_live():
    """Correct model, but the go-live date is hard-coded."""
    install_variant(hardcoded_go_live=visible_facts()["go_live"])


def overfit_hardcoded_holdout_stores():
    """Correct model, but the holdout store list is hard-coded."""
    install_variant(hardcoded_holdout=visible_facts()["holdout"])


def overfit_hardcoded_actions():
    """Correct model, but buy-plan actions are hard-coded from this extract's repaired review."""
    oracle_files()
    subprocess.run(REVIEW, cwd=WS, check=True, capture_output=True)
    import csv
    acts = {r["category"]: r["action"] for r in csv.DictReader(open(WS / "out/review/category_trends.csv"))}
    install_variant(hardcoded_actions=acts)


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_numpy_ipf, 1), (alt_correct_em, 1), (alt_correct_gibbs, 1),
            (alt_correct_separate_category_fits, 1)]
WRONG = [wrong_sales_as_demand_all_days, wrong_drop_censored_days, wrong_per_day_traffic_scaling, wrong_uniform_time_scaling,
         wrong_mean_rate_imputation, wrong_poisson_offset, wrong_daily_censored_poisson, wrong_forecast_imputation,
         wrong_profile_from_all_days, wrong_nb_without_promotions, wrong_holdout_transfer, wrong_forecast_as_prior,
         wrong_v3_as_prior, wrong_nb_plugin_imputation, wrong_fixed_effects_traffic_profile,
         partial_demand_fixed_clean_day_baselines, partial_baselines_fixed_sales_demand, output_only_patch, warehouse_edit,
         import_verifier_generator, tamper_stdlib_exit_hook, tamper_shadow_pytest]
OVERFITS = [overfit_hardcoded_traffic_profile, overfit_hardcoded_dispersion, overfit_hardcoded_go_live,
            overfit_hardcoded_holdout_stores, overfit_hardcoded_actions]
PLAN = CONTROLS + [(f, 0) for f in WRONG] + [(f, "overfit") for f in OVERFITS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task --tools /tools; "
        "find /workspace -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m demandsci review --db data/warehouse.sqlite --out out/review > /tmp/agent_run.log 2>&1 || true); "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; rm -rf /tests/__pycache__; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '[0-9]+ (passed|failed)' /tmp/verifier.log | tail -1; grep -E '^(FAILED|PASSED|ERROR)' /tmp/verifier.log || true"
    )
    p = subprocess.run(["docker", "run", "--rm", "--cpus", "2", "--memory", "4g", "-v", f"{TASK}:/task:ro", "-v", f"{HERE}:/tools:ro",
                        image, "bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", p.stdout)
    reward = int(m.group(1)) if m else -1
    summary = next((l.strip("= ") for l in p.stdout.splitlines() if " passed" in l or " failed" in l), p.stderr[-400:])
    failed = re.findall(r"(?:FAILED|ERROR) \S+::(\S+)", p.stdout)
    if expected == "overfit":
        ok = reward == 0 and bool(failed) and all(t.startswith("test_hidden_") for t in failed)
    else:
        ok = reward == expected
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward, ok=bool(ok),
                summary=summary, failed=failed)


def main():
    global TASK, WS, TOOLS
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker")
    ap.add_argument("--apply")
    ap.add_argument("--task")
    ap.add_argument("--workspace")
    ap.add_argument("--tools")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.workspace:
        WS = Path(a.workspace)
    if a.tools:
        TOOLS = Path(a.tools)
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:44} reward={r['reward']} expected={r['expected']}  {r['summary']}"
                  f"  failed={','.join(r['failed'][:6])}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
