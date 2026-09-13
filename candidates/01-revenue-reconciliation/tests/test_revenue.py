"""Verifier for ForensicDS Task 01 (enterprise revenue reconciliation).

The verifier tests *behaviour* of the repaired pipeline, never source strings:

  A. Source integrity    authoritative extracts under /workspace/data are unmodified.
  B. Visible snapshot    the agent's pipeline is re-run from source on the (pristine)
                         August-2026 workspace data and its warehouse tables and
                         dashboard extracts are compared with an independent
                         reference implementation of the documented semantics
                         (tests/reference.py) at every documented grain.
  C. Hidden snapshots    the same unmodified pipeline command is run against unseen
                         company snapshots (tests/scenarios.py) with different
                         calendars, ids and migration patterns. Hard-coded ids, totals,
                         months, constants, blanket de-duplication and output patching
                         cannot pass these.

All pipeline runs happen once in a module-scoped fixture; individual tests assert on
the collected results so failures are reported per invariant.
"""
from __future__ import annotations

import csv
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import world  # noqa: E402  (generator; byte-identical to the one used at image build)
from reference import compute_expected  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
SOURCE_FILES = ["data/billing/billing.db", "data/crm/crm_accounts_export.csv", "data/crm/account_migrations.csv"]
WAREHOUSE = "warehouse/analytics.db"
DASHBOARD = "reports/exec_dashboard"

TOL_ROW = 0.005   # USD, per fct row
TOL_AGG = 0.02    # USD, per reported (2-dp rounded) aggregate


# --------------------------------------------------------------------------- #
# Harness
# --------------------------------------------------------------------------- #


def install_sources(src_root: Path) -> None:
    for rel in SOURCE_FILES:
        dst = WORKSPACE / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_root / rel, dst)


def run_pipeline() -> dict:
    """Full refresh exactly as documented; outputs are removed first so nothing stale can be read."""
    (WORKSPACE / WAREHOUSE).unlink(missing_ok=True)
    for f in ("recognized_revenue_by_month.csv", "recognized_revenue_by_segment.csv", "top_accounts_latest_period.csv"):
        (WORKSPACE / DASHBOARD / f).unlink(missing_ok=True)
    env = dict(os.environ, PYTHONPATH=str(WORKSPACE / "src"), REVREC_RUN_TS="verifier")
    try:
        proc = subprocess.run([PIPELINE_PYTHON, "-m", "revrec", "run", "--config", "config/pipeline.toml"],
                              cwd=WORKSPACE, env=env, capture_output=True, text=True, timeout=600)
        rc, out = proc.returncode, (proc.stdout[-3000:] + proc.stderr[-5000:])
    except subprocess.TimeoutExpired:
        rc, out = -1, "pipeline timed out"
    result = dict(returncode=rc, output=out, fct=None, monthly=None, account=None, segment=None,
                  dash_month=None, dash_segment=None, dash_top=None)
    if rc != 0:
        return result
    try:
        con = sqlite3.connect(WORKSPACE / WAREHOUSE)
        result["fct"] = con.execute(
            "SELECT source_type, source_id, revenue_month, billing_account_id, account_id, segment, "
            "CAST(amount_usd AS REAL), account_name, region FROM fct_recognized_revenue").fetchall()
        result["monthly"] = con.execute(
            "SELECT revenue_month, CAST(gross_recognized_usd AS REAL), CAST(credit_notes_usd AS REAL), "
            "CAST(recognized_revenue_usd AS REAL) "
            "FROM rpt_monthly_recognized_revenue").fetchall()
        result["account"] = con.execute(
            "SELECT revenue_month, account_id, CAST(recognized_revenue_usd AS REAL), account_name, segment, region "
            "FROM rpt_account_monthly_revenue").fetchall()
        result["segment"] = con.execute(
            "SELECT revenue_month, segment, CAST(recognized_revenue_usd AS REAL) FROM rpt_segment_monthly_revenue"
        ).fetchall()
        con.close()
        with open(WORKSPACE / DASHBOARD / "recognized_revenue_by_month.csv", newline="") as fh:
            result["dash_month"] = list(csv.DictReader(fh))
        with open(WORKSPACE / DASHBOARD / "recognized_revenue_by_segment.csv", newline="") as fh:
            result["dash_segment"] = list(csv.DictReader(fh))
        with open(WORKSPACE / DASHBOARD / "top_accounts_latest_period.csv", newline="") as fh:
            result["dash_top"] = list(csv.DictReader(fh))
    except Exception as exc:  # missing table/column/file -> recorded, asserted by tests
        result["read_error"] = repr(exc)
    return result


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier_"))
    pristine = tmp / "pristine"
    world.build(world.VISIBLE_SPEC, pristine)
    data_backup = tmp / "agent_data"
    shutil.copytree(WORKSPACE / "data", data_backup)

    try:
        agent_digests = world.source_digests(WORKSPACE)
    except Exception:  # a source file was deleted or corrupted
        agent_digests = {rel: None for rel in SOURCE_FILES}
    c = dict(
        pristine=pristine,
        pristine_digests=world.source_digests(pristine),
        agent_digests=agent_digests,
        expected=compute_expected(pristine),
        hidden={},
    )
    try:
        # B. visible snapshot on pristine data (so later checks stay meaningful even if data was edited)
        install_sources(pristine)
        c["run1"] = run_pipeline()
        c["run2"] = run_pipeline()
        # C. hidden snapshots
        for spec in HIDDEN_SPECS:
            root = tmp / spec["name"]
            world.build(spec, root)
            install_sources(root)
            c["hidden"][spec["name"]] = (compute_expected(root), run_pipeline())
    finally:
        shutil.rmtree(WORKSPACE / "data")
        shutil.copytree(data_backup, WORKSPACE / "data")
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"pipeline command failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"pipeline outputs missing or changed schema: {run['read_error']}"


def fct_index(run: dict) -> dict:
    counts = Counter((r[0], r[1], r[2]) for r in run["fct"])
    dup = [k for k, n in counts.items() if n > 1]
    assert not dup, f"{len(dup)} source rows appear more than once in fct_recognized_revenue, e.g. {dup[:5]}"
    return {(r[0], r[1], r[2]): r for r in run["fct"]}


def compare_fct_grain(run: dict, exp) -> None:
    idx = fct_index(run)
    missing = [k for k in exp.fct if k not in idx]
    extra = [k for k in idx if k not in exp.fct]
    assert not missing, f"{len(missing)} legitimate revenue rows missing from fct_recognized_revenue, e.g. {missing[:5]}"
    assert not extra, f"{len(extra)} unexpected rows in fct_recognized_revenue, e.g. {extra[:5]}"
    bad = [(k, idx[k][6], round(v["amount_usd"], 6)) for k, v in exp.fct.items()
           if abs((idx[k][6] or 0.0) - v["amount_usd"]) > TOL_ROW or idx[k][3] != v["billing_account_id"]]
    assert not bad, f"{len(bad)} rows with wrong amount_usd/billing account, e.g. {bad[:5]}"


def compare_attribution(run: dict, exp) -> None:
    idx = fct_index(run)
    bad = [(k, idx[k][4], v["account_id"]) for k, v in exp.fct.items() if k in idx and idx[k][4] != v["account_id"]]
    assert not bad, f"{len(bad)} revenue rows attributed to the wrong account (got, expected), e.g. {bad[:5]}"
    for col, pos in (("segment", 5), ("account_name", 7), ("region", 8)):
        wrong = [(k, idx[k][pos], v[col]) for k, v in exp.fct.items() if k in idx and idx[k][pos] != v[col]]
        assert not wrong, f"{len(wrong)} revenue rows with wrong {col} (got, expected), e.g. {wrong[:5]}"


def compare_map(got: dict, expected: dict, label: str) -> None:
    keys = set(got) | set(expected)
    bad = sorted((k, round(got.get(k, 0.0), 2), round(expected.get(k, 0.0), 2)) for k in keys
                 if abs(got.get(k, 0.0) - expected.get(k, 0.0)) > TOL_AGG)
    assert not bad, f"{label}: {len(bad)} mismatches (key, got, expected), e.g. {bad[:8]}"


def compare_reports(run: dict, exp) -> None:
    compare_map({r[0]: r[3] for r in run["monthly"]}, exp.monthly, "rpt_monthly_recognized_revenue")
    compare_map({(r[0], r[1]): r[2] for r in run["segment"]}, exp.segment_month, "rpt_segment_monthly_revenue")
    compare_map({(r[0], r[1]): r[2] for r in run["account"]}, exp.account_month, "rpt_account_monthly_revenue")
    wrong = [(r[1], r[3:], exp.account_attrs.get(r[1])) for r in run["account"]
             if (r[3], r[4], r[5]) != tuple(exp.account_attrs.get(r[1], {}).get(c) for c in ("account_name", "segment", "region"))]
    assert not wrong, f"rpt_account_monthly_revenue: {len(wrong)} rows with wrong account attributes, e.g. {wrong[:5]}"


# --------------------------------------------------------------------------- #
# A. Source integrity
# --------------------------------------------------------------------------- #


def test_billing_database_unmodified(ctx):
    """Authoritative billing records (invoices, lines, credit notes, fx, periods...) must not be edited."""
    rel = "data/billing/billing.db"
    assert ctx["agent_digests"][rel] == ctx["pristine_digests"][rel], "billing.db content differs from the extract"


@pytest.mark.parametrize("rel", ["data/crm/crm_accounts_export.csv", "data/crm/account_migrations.csv"])
def test_crm_extracts_unmodified(ctx, rel):
    """CRM export and migration register are source extracts and must not be edited."""
    assert ctx["agent_digests"][rel] == ctx["pristine_digests"][rel], f"{rel} differs from the extract"


# --------------------------------------------------------------------------- #
# B. Visible snapshot (August 2026 close)
# --------------------------------------------------------------------------- #


def test_pipeline_runs(ctx):
    """`python -m revrec run --config config/pipeline.toml` succeeds and writes all documented outputs."""
    require_run(ctx["run1"])


def test_fct_preserves_source_grain(ctx):
    """One fct row per (source_type, source_id, revenue_month): every legitimate invoice-line and credit-note
    row exactly once (including identical lines on one invoice), no multiplication, no loss, correct amounts."""
    require_run(ctx["run1"])
    compare_fct_grain(ctx["run1"], ctx["expected"])


def test_monthly_totals_match_billing_every_period(ctx):
    """Recognized revenue ties to billing for August, July and every earlier reportable period."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    got = {r[0]: r[3] for r in ctx["run1"]["monthly"]}
    for month in ("2026-08", "2026-07"):
        assert month in got and abs(got[month] - exp.monthly[month]) <= TOL_AGG, (
            f"{month}: got {got.get(month)}, billing {exp.monthly[month]:.2f}")
    compare_map(got, exp.monthly, "monthly recognized revenue")


def test_credit_notes_and_gross_revenue(ctx):
    """Refund handling: credit notes reduce revenue in their issue month; gross/credit split is preserved."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    compare_map({r[0]: r[1] for r in ctx["run1"]["monthly"]}, exp.monthly_gross, "gross_recognized_usd")
    compare_map({r[0]: r[2] for r in ctx["run1"]["monthly"]}, exp.monthly_credits, "credit_notes_usd")


def test_revenue_rows_attributed_to_canonical_account(ctx):
    """Every revenue row carries its canonical account (billing owner followed through effective migrations)."""
    require_run(ctx["run1"])
    compare_attribution(ctx["run1"], ctx["expected"])


def test_migrated_customers_account_revenue(ctx):
    """Migrated customers (legacy + successors, incl. chains and consolidations) report all periods under the
    canonical account."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    canon = {exp.canonical[ba] for ba in exp.migrated_legacy_bas}
    got = {(r[0], r[1]): r[2] for r in ctx["run1"]["account"]}
    compare_map({k: v for k, v in got.items() if k[1] in canon},
                {k: v for k, v in exp.account_month.items() if k[1] in canon}, "canonical migrated accounts")
    stray = sorted({k[1] for k in got if k[1] not in {a for _, a in exp.account_month}})
    assert not stray, f"revenue reported under non-canonical accounts: {stray[:10]}"


def test_non_migrated_accounts_unchanged(ctx):
    """Customers never involved in a migration keep exactly their billing revenue in every period."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    migrated_canon = {exp.canonical[ba] for ba in exp.migrated_legacy_bas}
    got = {(r[0], r[1]): r[2] for r in ctx["run1"]["account"] if r[1] not in migrated_canon}
    want = {k: v for k, v in exp.account_month.items() if k[1] not in migrated_canon}
    compare_map({k: v for k, v in got.items() if k[1] in {a for _, a in want}}, want, "non-migrated accounts")


def test_account_and_segment_reports(ctx):
    """rpt_account_monthly_revenue and rpt_segment_monthly_revenue match the reference for all periods."""
    require_run(ctx["run1"])
    compare_reports(ctx["run1"], ctx["expected"])


def test_identical_invoice_lines_preserved(ctx):
    """Invoices with several identical legitimate lines keep every line (no content-based de-duplication)."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    idx = fct_index(ctx["run1"])
    groups = defaultdict(list)
    for k, v in exp.fct.items():
        if k[0] == "invoice_line":
            groups[(v["invoice_id"], k[2], round(v["amount_local"], 6))].append(k)
    identical = [keys for keys in groups.values() if len(keys) > 1]
    assert identical, "fixture sanity: expected identical invoice lines"
    lost = [keys for keys in identical if any(k not in idx for k in keys)]
    assert not lost, f"{len(lost)} groups of identical legitimate invoice lines lost rows, e.g. {lost[:3]}"


def test_non_revenue_documents_excluded(ctx):
    """Tax lines, void and draft invoices, and open-period revenue stay out of recognized revenue."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    months = {r[2] for r in ctx["run1"]["fct"]}
    assert months == set(exp.months), f"reported months {sorted(months)} != reportable periods {exp.months}"
    con = sqlite3.connect(ctx["pristine"] / "data/billing/billing.db")
    excluded = {r[0] for r in con.execute(
        "SELECT l.invoice_line_id FROM invoice_lines l JOIN invoices i USING(invoice_id) "
        "WHERE l.line_type = 'tax' OR i.status <> 'posted'")}
    con.close()
    leaked = [r for r in ctx["run1"]["fct"] if r[0] == "invoice_line" and r[1] in excluded]
    assert not leaked, f"{len(leaked)} tax/void/draft lines in fct_recognized_revenue, e.g. {leaked[:3]}"


def test_dashboard_extracts_match(ctx):
    """Executive dashboard extracts are produced by the pipeline and agree with the reference."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    compare_map({r["revenue_month"]: float(r["recognized_revenue_usd"]) for r in ctx["run1"]["dash_month"]},
                exp.monthly, "recognized_revenue_by_month.csv")
    compare_map({(r["revenue_month"], r["segment"]): float(r["recognized_revenue_usd"])
                 for r in ctx["run1"]["dash_segment"]}, exp.segment_month, "recognized_revenue_by_segment.csv")


def test_dashboard_mom_and_top_accounts(ctx):
    """Dashboard month-over-month change and the top-25 accounts extract for the latest reportable period."""
    require_run(ctx["run1"])
    exp = ctx["expected"]
    rows = {r["revenue_month"]: r for r in ctx["run1"]["dash_month"]}
    for prev, cur in zip(exp.months, exp.months[1:]):
        want = 100 * (round(exp.monthly[cur], 2) / round(exp.monthly[prev], 2) - 1)
        got = float(rows[cur]["mom_change_pct"])
        assert abs(got - want) <= 0.011, f"mom_change_pct {cur}: got {got}, expected {want:.2f}"
    latest = exp.months[-1]
    ranked = sorted(((v, a) for (m, a), v in exp.account_month.items() if m == latest), reverse=True)[:25]
    got_top = {r["account_id"]: float(r["recognized_revenue_usd"]) for r in ctx["run1"]["dash_top"]}
    assert all(r["revenue_month"] == latest for r in ctx["run1"]["dash_top"]), "top accounts extract not for latest period"
    compare_map(got_top, {a: v for v, a in ranked}, "top_accounts_latest_period.csv")


def test_rerun_is_idempotent(ctx):
    """Re-running the pipeline on the same snapshot produces identical outputs."""
    require_run(ctx["run2"])
    norm = lambda rows: sorted(tuple(round(x, 6) if isinstance(x, float) else x for x in (r.values() if isinstance(r, dict) else r)) for r in rows)  # noqa: E731
    for table in ("fct", "monthly", "account", "segment", "dash_top"):
        assert norm(ctx["run1"][table]) == norm(ctx["run2"][table]), f"{table} differs between identical runs"


# --------------------------------------------------------------------------- #
# C. Hidden snapshots (generalization)
# --------------------------------------------------------------------------- #

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_snapshot_pipeline_runs(ctx, name):
    """The unmodified pipeline command works on other company snapshots."""
    require_run(ctx["hidden"][name][1])


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_snapshot_source_grain(ctx, name):
    """Source grain and amounts preserved on unseen migration patterns (chains, consolidations, boundaries)."""
    exp, run = ctx["hidden"][name]
    require_run(run)
    compare_fct_grain(run, exp)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_snapshot_attribution(ctx, name):
    """Canonical account attribution generalizes to unseen accounts and migration histories."""
    exp, run = ctx["hidden"][name]
    require_run(run)
    compare_attribution(run, exp)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_snapshot_reports(ctx, name):
    """Monthly, segment and account reports tie to billing on unseen snapshots."""
    exp, run = ctx["hidden"][name]
    require_run(run)
    compare_reports(run, exp)
