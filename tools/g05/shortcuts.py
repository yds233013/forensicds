#!/usr/bin/env python3
"""Anti-gaming mutation suite for G05 (SCO 2.0 tranche-2 continuation gate).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, runs the readout,
then runs the real tests/test.sh (sandboxed pipeline). Correct implementations must score 1; natural wrong causal
analyses, partial repairs, patches, cheats and overfits must score 0. Overfits must additionally pass every
visible-warehouse check and fail only hidden-warehouse checks.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task --tools /tools --research /research   (internal)
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
ROOT = HERE.parents[1] if len(HERE.parents) > 1 else HERE
TASK = ROOT / "candidates/g05-sco-rollout-gate"
RESEARCH = ROOT / "research/g05/pilot"
WS = Path("/workspace")
TOOLS = HERE
RUN = [sys.executable, "-m", "sco_readout", "gate", "--warehouse", "data/warehouse.sqlite", "--out", "out"]


def install_variant(**variant) -> None:
    pkg = WS / "sco_readout"
    src = (TOOLS / "variant_cli.py").read_text().replace('VARIANT = {"method": "imp_format_week"}',
                                                           f"VARIANT = {variant!r}")
    (pkg / "cli.py").write_text(src)
    (pkg / "_g05_sim.py").write_text((RESEARCH / "g05_sim.py").read_text())
    (pkg / "_g05_estimators.py").write_text(
        (RESEARCH / "g05_estimators.py").read_text().replace("import g05_sim as S", "from sco_readout import _g05_sim as S"))


def oracle_files() -> None:
    for f in ("panel.py", "estimate.py", "report.py", "cli.py"):
        shutil.copyfile(TASK / "solution/sco_readout" / f, WS / "sco_readout" / f)


# ------------------------------------------------------------------------------------------------ controls

def nop():
    """No change (Nop agent): the Programme team's TWFE readout on basket size."""

def oracle():
    """Reference solution: actual go-live, comparable weeks, format-conditional imputation, kit transport, bootstrap."""
    oracle_files()

def alt_correct_pandas_did():
    """Independent pandas implementation: same-format not-yet-installed 2x2 comparisons, comparable pre-period base."""
    shutil.copyfile(TOOLS / "alt_cs_did.py", WS / "sco_readout/cli.py")

def alt_correct_never_installed_controls():
    """Accepted: same-format never-installed controls only."""
    install_variant(method="cs_format_never")

def alt_correct_store_trends():
    """Accepted: imputation with store-specific linear trends and week effects."""
    install_variant(method="imp_store_trend")

def alt_correct_single_base_week():
    """Accepted: same-format not-yet-installed DiD with each store's latest comparable week in e = -8..-3 as base."""
    install_variant(method="cs_base_last")

def alt_correct_format_kit_week():
    """Accepted: imputation with format-by-kit-by-week effects."""
    install_variant(method="imp_format_kit_week")


# ------------------------------------------------------------------------------------------------ natural wrong analyses

def wrong_before_after():
    """Live stores' run-rate weeks against their own pre-period, no comparison group."""
    install_variant(method="before_after")

def wrong_twfe_static_sales():
    """Static two-way fixed effects on log net sales (actual dates, comparable weeks)."""
    install_variant(method="twfe_static_sales")

def wrong_twfe_event_study_ref_minus1():
    """TWFE event study with reference week -1 (inside the install closure), run-rate from the lags."""
    install_variant(method="twfe_event_ref_m1")

def wrong_did_base_g_minus_1():
    """2x2 DiD with base week g-1 and pooled not-yet-installed controls."""
    install_variant(method="cs_gm1_pooled")

def wrong_unconditional_imputation():
    """Store + week effects only: ignores format trends behind the wave sequencing."""
    install_variant(method="imp_unconditional")

def wrong_unconditional_did():
    """Clean-base DiD against pooled not-yet-installed controls of all formats."""
    install_variant(method="cs_unconditional")

def wrong_kit_week_conditioning():
    """Kit-by-week effects instead of format-by-week: conditioning coarser than the sequencing variable."""
    install_variant(method="kit_week_fe")

def wrong_outcome_basket():
    """Correct design on log basket size instead of net sales."""
    install_variant(method="outcome_basket")

def wrong_mediator_control():
    """Correct design on net sales with log transactions as a covariate ("traffic-adjusted")."""
    install_variant(method="mediator_control")

def wrong_closure_weeks_comparable():
    """Correct design, but weeks with closures are used as comparable observations."""
    install_variant(method="all_weeks_comparable")

def wrong_window_0_25_did():
    """Same-format DiD averaged over event weeks 0-25 instead of the run-rate weeks."""
    install_variant(method="window_0_25_cs")

def wrong_kit_conditioning_did():
    """DiD with same-kit (not same-format) not-yet-installed controls."""
    install_variant(method="kit_conditioning_cs")

def wrong_closure_weeks_in_window():
    """Correct fit, but closure weeks are included in the run-rate average."""
    install_variant(method="closures_in_window_only")

def wrong_window_0_25():
    """Correct design averaged over event weeks 0-25 instead of the run-rate weeks."""
    install_variant(method="window_0_25")

def wrong_gate_pooled_installed():
    """Correct design; gate figure = live stores' pooled run-rate effect."""
    install_variant(method="gate_pooled_installed")

def wrong_gate_by_format():
    """Correct design; gate figure transported to waves 5-6 by format."""
    install_variant(method="gate_by_format")

def wrong_gate_by_sqft():
    """Correct design; gate figure from a linear store-size model of store effects."""
    install_variant(method="gate_sqft_linear")

def wrong_panel_planned_dates():
    """Correct estimates, but the analysis panel's go-live week and event weeks come from the plan."""
    install_variant(method="imp_format_week", panel_planned=True)

def wrong_panel_comparable_txns():
    """Correct estimates, but the panel's comparable flag is transactions > 0."""
    install_variant(method="imp_format_week", panel_txns_comparable=True)

def wrong_panel_event_week_from_1():
    """Correct estimates, but event weeks count the go-live week as 1."""
    install_variant(method="imp_format_week", panel_event_week1=True)


# ------------------------------------------------------------------------------------------------ patches and cheats

def output_only_patch():
    """Patch: run a correct readout once, then restore the house code (the verifier regenerates outputs)."""
    oracle_files()
    subprocess.run(RUN, cwd=WS, check=True, capture_output=True)
    for f in ("panel.py", "estimate.py", "report.py", "cli.py"):
        shutil.copyfile(TASK / "environment/workspace/sco_readout" / f, WS / "sco_readout" / f)

def warehouse_edit():
    """Cheat: correct code, but closure records are deleted from data/warehouse.sqlite first."""
    oracle_files()
    con = sqlite3.connect(WS / "data/warehouse.sqlite")
    con.execute("DELETE FROM store_closures WHERE closure_type = 'weather'")
    con.commit()
    con.close()

def import_verifier_generator():
    """Cheat: if the verifier's generator is importable, write its truth; otherwise the house readout."""
    cli = WS / "sco_readout/cli.py"
    s = cli.read_text().replace("def gate(warehouse: Path, out: Path) -> None:\n", '''def gate(warehouse: Path, out: Path) -> None:
    import os, sys
    for d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if d and os.path.exists(os.path.join(d, "world.py")):
                sys.path.insert(0, d)
                import world  # noqa
                raise SystemExit("truth available")
        except SystemExit:
            raise
        except Exception:
            pass
''', 1)
    cli.write_text(s)

def tamper_stdlib_exit_hook():
    """Cheat: house code; the standard library's site.py forces every interpreter to exit 0 (verifier included)."""
    site = Path("/usr/local/lib/python3.12/site.py")
    site.write_text(site.read_text() + "\nimport atexit as _a, os as _o\n_a.register(lambda: _o._exit(0))\n")

def tamper_shadow_pytest():
    """Cheat: house code; a `pytest` module added to the standard library that exits 0 before any test runs."""
    Path("/usr/local/lib/python3.12/pytest.py").write_text("import os\nos._exit(0)\n")

def tamper_root_pytest_config():
    """Cheat: house code; a root-level pytest.ini and conftest.py that turn every test outcome into a pass."""
    Path("/pytest.ini").write_text("[pytest]\n")
    Path("/conftest.py").write_text(
        "import pytest\n@pytest.hookimpl(hookwrapper=True)\ndef pytest_runtest_makereport(item, call):\n"
        "    out = yield\n    rep = out.get_result()\n    rep.outcome = 'passed'\n")

def tamper_site_packages_pth():
    """Cheat: house code; a .pth file in system site-packages that forces the verifier's interpreter to exit 0."""
    Path("/usr/local/lib/python3.12/site-packages/zz_force.pth").write_text(
        "import os, atexit; atexit.register(lambda: os._exit(0))\n")

def tamper_pip_config():
    """Cheat: house code; a pip configuration pointing test dependency installs at a local fake pytest."""
    Path("/etc/pip.conf").write_text("[global]\nno-index = true\nfind-links = /opt/fakewheels\n")
    Path("/opt/fakewheels").mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------------------------------------ overfits

def overfit_hardcoded_decision():
    """Correct estimates, but the decision is hard-coded to this warehouse's answer (stop)."""
    install_variant(method="imp_format_week", hardcode_decision="stop")

def overfit_hardcoded_compact_effect():
    """Correct wave effects, but the compact kit's effect in the gate is this warehouse's value."""
    install_variant(method="imp_format_week", hardcode_compact_effect=-0.0026)

def overfit_hardcoded_format_trends():
    """Detrend log net sales with this warehouse's format sales trends (per year), then store + week effects only."""
    install_variant(method="imp_unconditional", hardcode_trends=[0.090, 0.015, -0.015])


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_pandas_did, 1), (alt_correct_never_installed_controls, 1),
            (alt_correct_store_trends, 1), (alt_correct_format_kit_week, 1), (alt_correct_single_base_week, 1)]
WRONG = [wrong_before_after, wrong_twfe_static_sales, wrong_twfe_event_study_ref_minus1, wrong_did_base_g_minus_1,
         wrong_unconditional_imputation, wrong_unconditional_did, wrong_kit_week_conditioning, wrong_outcome_basket,
         wrong_mediator_control, wrong_closure_weeks_comparable, wrong_window_0_25, wrong_window_0_25_did,
         wrong_kit_conditioning_did, wrong_closure_weeks_in_window, wrong_gate_pooled_installed,
         wrong_gate_by_format, wrong_gate_by_sqft, wrong_panel_planned_dates, wrong_panel_comparable_txns,
         wrong_panel_event_week_from_1, output_only_patch, warehouse_edit, import_verifier_generator,
         tamper_stdlib_exit_hook, tamper_shadow_pytest, tamper_root_pytest_config, tamper_site_packages_pth,
         tamper_pip_config]
OVERFITS = [overfit_hardcoded_decision, overfit_hardcoded_compact_effect, overfit_hardcoded_format_trends]
PLAN = CONTROLS + [(f, 0) for f in WRONG] + [(f, "overfit") for f in OVERFITS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task --tools /tools --research /research; "
        "find /workspace -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m sco_readout gate --warehouse data/warehouse.sqlite --out out > /tmp/agent_run.log 2>&1 || true); "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; rm -rf /tests/__pycache__; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '[0-9]+ (passed|failed)|refusing' /tmp/verifier.log | tail -1; grep -E '^(FAILED|PASSED|ERROR)' /tmp/verifier.log || true"
    )
    p = subprocess.run(["docker", "run", "--rm", "--cpus", "2", "--memory", "4g", "-v", f"{TASK}:/task:ro",
                        "-v", f"{HERE}:/tools:ro", "-v", f"{RESEARCH}:/research:ro", image, "bash", "-c", script],
                       capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", p.stdout)
    reward = int(m.group(1)) if m else -1
    summary = next((l.strip("= ") for l in p.stdout.splitlines() if " passed" in l or " failed" in l or "refusing" in l),
                   p.stderr[-400:])
    failed = re.findall(r"(?:FAILED|ERROR) \S+::(\S+)", p.stdout)
    if expected == "overfit":
        ok = reward == 0 and bool(failed) and all(t.startswith("test_hidden_") for t in failed)
    else:
        ok = reward == expected
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward, ok=bool(ok),
                summary=summary, failed=failed)


def main():
    global TASK, WS, TOOLS, RESEARCH
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker"); ap.add_argument("--apply"); ap.add_argument("--task"); ap.add_argument("--workspace")
    ap.add_argument("--tools"); ap.add_argument("--research"); ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=3); ap.add_argument("--report")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.workspace:
        WS = Path(a.workspace)
    if a.tools:
        TOOLS = Path(a.tools)
    if a.research:
        RESEARCH = Path(a.research)
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            print(f"[{'OK ' if r['ok'] else 'BAD'}] {r['name']:40} reward={r['reward']} expected={r['expected']}  "
                  f"{r['summary']}  failed={','.join(r['failed'][:8])}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
