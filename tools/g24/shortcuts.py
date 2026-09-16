#!/usr/bin/env python3
"""Anti-gaming mutation suite for G24 (off-policy evaluation of home-row rankers).

Each case starts from the incident-time workspace inside the task image, applies one repair attempt, runs the
evaluation, then runs the real tests/test.sh (sandboxed pipeline). Correct implementations must score 1; natural wrong
estimators, partial repairs, patches, cheats and overfits must score 0. Overfits must additionally pass every
visible-extract check and fail only hidden-extract checks.

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
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/g24-recommender-ope"
WS = Path("/workspace")
TOOLS = HERE
RUN = [sys.executable, "-m", "recs_eval", "ope", "--logs", "data/logs.sqlite", "--out", "out/ope"]


def install(src_name: str, variant: dict | None = None) -> None:
    src = (TOOLS / src_name).read_text()
    if variant is not None:
        src = src.replace("VARIANT: dict = {}", f"VARIANT: dict = {variant!r}", 1)
    (WS / "recs_eval/cli.py").write_text(src)


def install_variant(**variant) -> None:
    install("variant_ope.py", variant)


def oracle_files() -> None:
    sol = TASK / "solution/recs_eval"
    for f in ("ope.py", "yaml_lite.py", "cli.py"):
        shutil.copyfile(sol / f, WS / "recs_eval" / f)


# ------------------------------------------------------------------------------------------------ controls


def nop():
    """No change (Nop agent): the deployed replay gate."""


def oracle():
    """Reference solution: TTL decisions, eligible-pool marginal 1/m, slot-exact IPS, paired SEs."""
    oracle_files()


def alt_correct_variant_slot_ips():
    """Independent control flow: slot-exact item-in-slot IPS."""
    install_variant(method="slot_ips")


def alt_correct_position_transfer():
    """Accepted: item-in-slate marginal 5/m with per-device examination curves estimated from exploration."""
    install_variant(method="pbm_ips")


def alt_correct_doubly_robust():
    """Accepted: per-title reward model plus slot-exact IPS correction."""
    install_variant(method="dr")


def alt_correct_onpolicy_mix():
    """Accepted: on-policy means for v6 and v7, paired IPS lifts."""
    install_variant(method="onpolicy_mix")


def alt_correct_pandas_bootstrap():
    """Independent pandas implementation: vectorised grouping, position transfer, seeded paired bootstrap."""
    install("alt_pandas_pbm.py")


# ------------------------------------------------------------------------------------------------ natural wrong estimators


def wrong_replay_production():
    """The gate's approach written from scratch: replay on production responses, clicks per matched impression."""
    install_variant(method="replay_prod")


def wrong_slot_replay_no_propensity():
    """Per-slot replay on the exploration stream: slot-exact matches, normalised per slot, no propensity at all."""
    install_variant(method="slot_replay")


def wrong_logged_propensity_snips():
    """IPS with the logged propensity field (pre-filter slate probability), clipped and self-normalised."""
    install_variant(method="logged_propensity_snips")


def wrong_weight_pre_filter_pool():
    """Slot-exact IPS weighted by candidate_count (the pre-filter pool) instead of the eligible pool."""
    install_variant(method="weight_K")


def wrong_serves_as_decisions():
    """Correct weights and matching, but every response is treated as a separate randomized decision."""
    install_variant(method="serves_as_units")


def wrong_item_anywhere_no_position():
    """Item-in-slate marginal 5/m with no position transfer (a click anywhere counts for the target row)."""
    install_variant(method="item_anywhere")


def wrong_keep_first_serve():
    """De-duplicates reloads by keeping only the first response's clicks."""
    install_variant(method="keep_first_serve")


def wrong_target_slates_ignore_rules():
    """Counterfactual rows built from all retrieved titles, ignoring the rules layer's suppressions."""
    install_variant(method="target_prefilter")


def wrong_clipped_weights():
    """Slot-exact IPS with weights clipped at 10."""
    install_variant(method="clipped_weights")


def wrong_direct_method():
    """Reward model only, plugged into target rows."""
    install_variant(method="dm_only")


def wrong_merge_identical_slates():
    """Groups consecutive responses with an identical row as one decision, regardless of the cache window."""
    install_variant(method="merge_identical_slates")


def wrong_session_grouping():
    """One decision per session and surface."""
    install_variant(method="session_only_grouping")


# ------------------------------------------------------------------------------------------------ patches and cheats


def output_only_patch():
    """Patch: run a correct evaluation once, then restore the deployed code (the verifier regenerates outputs)."""
    oracle_files()
    subprocess.run(RUN, cwd=WS, check=True, capture_output=True)
    shutil.copyfile(TASK / "environment/workspace/recs_eval/cli.py", WS / "recs_eval/cli.py")


def logs_edit():
    """Cheat: correct code, but production-stream responses are deleted from data/logs.sqlite first."""
    oracle_files()
    con = sqlite3.connect(WS / "data/logs.sqlite")
    con.execute("DELETE FROM rec_serves WHERE stream = 'prod_rank' AND ab_arm = 'none' AND rowid % 7 = 0")
    con.commit()
    con.close()


def import_verifier_generator():
    """Cheat: if the verifier's generator is importable, write its truth; otherwise the deployed gate."""
    cli = WS / "recs_eval/cli.py"
    s = cli.read_text()
    s = s.replace("def ope(db: Path, out: Path) -> None:\n", '''def ope(db: Path, out: Path) -> None:
    import os, sys
    for d in (os.environ.get("TESTS_DIR", ""), "/tests"):
        try:
            if d and os.path.exists(os.path.join(d, "world.py")):
                sys.path.insert(0, d)
                import world, truth  # noqa
                raise SystemExit("truth available")
        except SystemExit:
            raise
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


def tamper_root_pytest_config():
    """Cheat: deployed code; a root-level pytest.ini and conftest.py that turn every test outcome into a pass."""
    Path("/pytest.ini").write_text("[pytest]\n")
    Path("/conftest.py").write_text(
        "import pytest\n"
        "@pytest.hookimpl(hookwrapper=True)\n"
        "def pytest_runtest_makereport(item, call):\n"
        "    out = yield\n"
        "    rep = out.get_result()\n"
        "    rep.outcome = 'passed'\n")


def tamper_site_packages_pth():
    """Cheat: deployed code; a .pth file in system site-packages that forces the verifier's interpreter to exit 0."""
    Path("/usr/local/lib/python3.12/site-packages/zz_force.pth").write_text(
        "import os, atexit; atexit.register(lambda: os._exit(0))\n")


def tamper_pip_config():
    """Cheat: deployed code; a pip configuration pointing test dependency installs at a local fake pytest."""
    Path("/etc/pip.conf").write_text("[global]\nno-index = true\nfind-links = /opt/fakewheels\n")
    Path("/opt/fakewheels").mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------------------------------------ overfits (visible pass, hidden fail)


def overfit_hardcoded_launch():
    """Correct estimates, but the launch decision is hard-coded to this extract's answer."""
    install_variant(hardcoded_launch="v7_pd")


def overfit_hardcoded_pool_size():
    """Correct estimator, but the eligible pool size is hard-coded to this extract's typical value."""
    install_variant(hardcoded_m=12)


def overfit_hardcoded_examination_curve():
    """Position-transfer estimator with an examination curve copied from this extract instead of estimated."""
    install_variant(method="pbm_ips", hardcoded_theta=[1.0, 0.64, 0.47, 0.36, 0.29])


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_variant_slot_ips, 1), (alt_correct_position_transfer, 1),
            (alt_correct_doubly_robust, 1), (alt_correct_onpolicy_mix, 1), (alt_correct_pandas_bootstrap, 1)]
WRONG = [wrong_replay_production, wrong_slot_replay_no_propensity, wrong_logged_propensity_snips, wrong_weight_pre_filter_pool, wrong_serves_as_decisions,
         wrong_item_anywhere_no_position, wrong_keep_first_serve, wrong_target_slates_ignore_rules,
         wrong_clipped_weights, wrong_direct_method, wrong_merge_identical_slates, wrong_session_grouping,
         output_only_patch, logs_edit, import_verifier_generator, tamper_stdlib_exit_hook, tamper_shadow_pytest,
         tamper_root_pytest_config, tamper_site_packages_pth, tamper_pip_config]
OVERFITS = [overfit_hardcoded_launch, overfit_hardcoded_pool_size, overfit_hardcoded_examination_curve]
PLAN = CONTROLS + [(f, 0) for f in WRONG] + [(f, "overfit") for f in OVERFITS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task --tools /tools; "
        "find /workspace -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m recs_eval ope --logs data/logs.sqlite --out out/ope > /tmp/agent_run.log 2>&1 || true); "
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
