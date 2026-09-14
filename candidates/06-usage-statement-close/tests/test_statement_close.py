"""Verifier for ForensicDS Task 06 (usage statement close).

Behavioural checks only - no source inspection:

  A. Sources         raw/landing, config/customers.csv, config/rate_cards.csv and ledger/issued equal a pristine
                     regeneration of the extract.
  B. September close the agent's close job is re-run (outputs deleted first) for 2026-09 and compared with an
                     independent reference (tests/reference.py): usage mart, statement lines (usage and adjustment),
                     summary, determinism.
  C. Other extracts  the same job on unseen extracts with other calendars, delivery behaviour and issuing histories
                     (tests/scenarios.py).
"""
from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytest

TESTS_DIR = Path(os.environ.get("TESTS_DIR", Path(__file__).resolve().parent))
sys.path.insert(0, str(TESTS_DIR))

import reference as ref  # noqa: E402
import world  # noqa: E402
from scenarios import HIDDEN_SPECS  # noqa: E402

WORKSPACE = Path(os.environ.get("WORKSPACE", "/workspace"))
PIPELINE_PYTHON = os.environ.get("PIPELINE_PYTHON", "python3")
MONTH = "2026-09"
INPUTS = ["raw/landing", "config/customers.csv", "config/rate_cards.csv", "ledger/issued"]
QTY_TOL = Decimal("0.0005")
AMT_TOL = Decimal("0.011")
ZERO = Decimal(0)


def pipeline_env() -> dict:
    """Environment for the agent's pipeline: no verifier variables."""
    env = {k: v for k, v in os.environ.items() if k not in ("TESTS_DIR", "WORKSPACE", "PIPELINE_PYTHON")}
    env["PYTHONPATH"] = str(WORKSPACE)
    return env


def copy_inputs(src: Path, dst: Path) -> None:
    for rel in INPUTS:
        s, d = src / rel, dst / rel
        if d.is_dir():
            shutil.rmtree(d)
        elif d.exists():
            d.unlink()
        d.parent.mkdir(parents=True, exist_ok=True)
        if s.is_dir():
            shutil.copytree(s, d)
        else:
            shutil.copyfile(s, d)


def dec(v) -> Decimal:
    try:
        return Decimal(str(v).strip())
    except (InvalidOperation, AttributeError):
        raise AssertionError(f"not a decimal number: {v!r}")


def run_close(month: str) -> dict:
    out = WORKSPACE / "out"
    mart_p = out / "usage_mart/usage_by_service_month.csv"
    st_dir = out / "statements" / month
    mart_p.unlink(missing_ok=True)
    shutil.rmtree(st_dir, ignore_errors=True)
    cmd = [PIPELINE_PYTHON, "-m", "jobs.close_month", "--month", month]
    try:
        p = subprocess.run(cmd, cwd=WORKSPACE, env=pipeline_env(), capture_output=True, text=True, timeout=600)
        rc, text = p.returncode, p.stdout[-2000:] + p.stderr[-4000:]
    except subprocess.TimeoutExpired:
        rc, text = -1, "timed out"
    res = dict(returncode=rc, output=text)
    if rc != 0:
        return res
    try:
        with open(mart_p, newline="") as fh:
            res["mart"] = list(csv.DictReader(fh))
        with open(st_dir / "statement_lines.csv", newline="") as fh:
            res["lines"] = list(csv.DictReader(fh))
        res["summary"] = json.loads((st_dir / "summary.json").read_text())
        res["raw"] = mart_p.read_bytes() + (st_dir / "statement_lines.csv").read_bytes() + (st_dir / "summary.json").read_bytes()
    except Exception as exc:  # recorded, asserted by tests
        res["read_error"] = repr(exc)
    return res


@pytest.fixture(scope="module")
def ctx():
    tmp = Path(tempfile.mkdtemp(prefix="verifier06_"))
    pristine = tmp / "pristine"
    world.build(world.VISIBLE_SPEC, pristine)
    backup = tmp / "agent_inputs"
    copy_inputs(WORKSPACE, backup)
    c = dict(agent_digest=world.tree_digest(WORKSPACE), pristine_digest=world.tree_digest(pristine), hidden={})
    try:
        copy_inputs(pristine, WORKSPACE)
        c["ref"] = (ref.usage_mart(pristine), ref.statement(pristine, MONTH))
        c["run1"] = run_close(MONTH)
        c["run2"] = run_close(MONTH)
        for spec in HIDDEN_SPECS:
            root = tmp / spec["name"]
            world.build(spec, root)
            copy_inputs(root, WORKSPACE)
            m = spec["statement_month"]
            c["hidden"][spec["name"]] = ((ref.usage_mart(root), ref.statement(root, m)), run_close(m), m)
        copy_inputs(pristine, WORKSPACE)
        run_close(MONTH)
        for spec in HIDDEN_SPECS:
            shutil.rmtree(WORKSPACE / "out/statements" / spec["statement_month"], ignore_errors=True)
    finally:
        copy_inputs(backup, WORKSPACE)
    yield c
    shutil.rmtree(tmp, ignore_errors=True)


def require_run(run: dict) -> None:
    assert run["returncode"] == 0, f"close job failed (exit {run['returncode']}):\n{run['output']}"
    assert "read_error" not in run, f"close outputs missing or unreadable: {run['read_error']}"


# ------------------------------------------------------------------------------------------- shared assertions


def same_instant(value, expected: str) -> bool:
    from datetime import datetime, timezone
    try:
        got = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return False
    if got.tzinfo is None:
        got = got.replace(tzinfo=timezone.utc)
    return got == datetime.fromisoformat(expected.replace("Z", "+00:00"))


def check_mart(run: dict, want: dict) -> None:
    rows = run["mart"]
    missing_cols = {"customer_id", "meter", "service_month", "quantity"} - set(rows[0].keys() if rows else [])
    assert not missing_cols, f"usage mart is missing columns {sorted(missing_cols)}"
    keys = Counter((r["customer_id"], r["meter"], r["service_month"]) for r in rows)
    dup = [k for k, n in keys.items() if n > 1]
    assert not dup, f"{len(dup)} duplicate customer/meter/service_month rows in the usage mart, e.g. {dup[:3]}"
    got = {(r["customer_id"], r["meter"], r["service_month"]): dec(r["quantity"]) for r in rows}
    bad = []
    for k in set(got) | set(want):
        g, w = got.get(k, ZERO), want.get(k, ZERO)
        if abs(g - w) > QTY_TOL:
            bad.append((k, str(got.get(k)), str(want.get(k))))
    assert not bad, f"usage mart differs in {len(bad)} rows (got, expected), e.g. {sorted(bad)[:5]}"


def line_map(run: dict, month: str) -> dict:
    rows = run["lines"]
    need = {"statement_month", "customer_id", "meter", "line_type", "service_month", "quantity", "amount"}
    missing_cols = need - set(rows[0].keys() if rows else [])
    assert not missing_cols, f"statement lines are missing columns {sorted(missing_cols)}"
    kinds = {r["line_type"] for r in rows}
    assert kinds <= {"usage", "adjustment"}, f"unexpected line types {sorted(kinds - {'usage', 'adjustment'})}"
    wrong_month = {r["statement_month"] for r in rows} - {month}
    assert not wrong_month, f"lines carry statement_month {sorted(wrong_month)}"
    keys = Counter((r["customer_id"], r["meter"], r["line_type"], r["service_month"]) for r in rows)
    dup = [k for k, n in keys.items() if n > 1]
    assert not dup, f"{len(dup)} duplicate statement lines (customer, meter, line_type, service_month), e.g. {dup[:3]}"
    out = {}
    for r in rows:
        q, a = dec(r["quantity"]), dec(r["amount"])
        if q == 0 and a == 0:
            continue  # empty lines carry nothing
        out[(r["customer_id"], r["meter"], r["line_type"], r["service_month"])] = (q, a)
    return out


def check_lines(run: dict, want: dict, month: str, kind: str, what: str) -> None:
    got = {k: v for k, v in line_map(run, month).items() if k[2] == kind}
    exp = {k: v for k, v in want["lines"].items() if k[2] == kind}
    if what == "set":
        missing, extra = sorted(set(exp) - set(got)), sorted(set(got) - set(exp))
        assert not missing and not extra, (f"{kind} lines differ: {len(missing)} missing (e.g. {missing[:4]}), "
                                           f"{len(extra)} unexpected (e.g. {extra[:4]})")
        return
    idx, tol = (0, QTY_TOL) if what == "quantity" else (1, AMT_TOL)
    bad = [(k, str(got[k][idx]), str(exp[k][idx])) for k in sorted(set(got) & set(exp)) if abs(got[k][idx] - exp[k][idx]) > tol]
    assert not bad, f"{kind} line {what} differs on {len(bad)} lines (got, expected), e.g. {bad[:5]}"


def check_future_months(run: dict, month: str) -> None:
    later = sorted({r["service_month"] for r in run["lines"] if r["service_month"] > month})
    assert not later, f"statement {month} bills service months after the statement month: {later}"


def check_summary(run: dict, want: dict, month: str) -> None:
    s = run["summary"]
    assert s.get("statement_month") == month, f"summary statement_month {s.get('statement_month')}"
    assert same_instant(s.get("close_at"), want["close_at"]), f"summary close_at {s.get('close_at')} expected {want['close_at']}"
    got = {c["customer_id"]: c for c in s.get("customers", [])}
    lines = line_map(run, month)
    for cid, c in got.items():
        u = sum((a for (lc, _m, k, _s), (_q, a) in lines.items() if lc == cid and k == "usage"), ZERO)
        adj = sum((a for (lc, _m, k, _s), (_q, a) in lines.items() if lc == cid and k == "adjustment"), ZERO)
        assert abs(dec(c["usage_amount"]) - u) <= AMT_TOL and abs(dec(c["adjustment_amount"]) - adj) <= AMT_TOL \
            and abs(dec(c["total_amount"]) - (u + adj)) <= AMT_TOL, f"summary for {cid} does not match its statement lines"
    exp = {cid: v for cid, v in want["summary"].items() if any(x != 0 for x in v) or cid in got}
    missing = sorted(cid for cid in want["summary"] if cid not in got)
    assert not missing, f"summary is missing customers with statement lines: {missing[:5]}"
    bad = [(cid, got[cid]["total_amount"], str(v[2])) for cid, v in exp.items()
           if cid in got and abs(dec(got[cid]["total_amount"]) - v[2]) > AMT_TOL]
    assert not bad, f"summary totals differ for {len(bad)} customers (got, expected), e.g. {bad[:5]}"


# ------------------------------------------------------------------------------------------- A. sources


def test_sources_unmodified(ctx):
    """Collector deliveries, customer registry, rate cards and issued statements are authoritative and unchanged."""
    assert ctx["agent_digest"] == ctx["pristine_digest"], \
        "raw/landing, config/customers.csv, config/rate_cards.csv or ledger/issued differ from the extract"


# ------------------------------------------------------------------------------------------- B. September close


def test_close_job_succeeds(ctx):
    """`python -m jobs.close_month --month 2026-09` succeeds and writes the mart, statement lines and summary."""
    require_run(ctx["run1"])


def test_usage_mart(ctx):
    """The usage mart has one row per customer, meter and service month, with usage as currently known."""
    require_run(ctx["run1"])
    check_mart(ctx["run1"], ctx["ref"][0])


def test_statement_line_grain(ctx):
    """Statement lines use the documented columns and line types, one line per customer/meter/type/service month."""
    require_run(ctx["run1"])
    line_map(ctx["run1"], MONTH)
    check_future_months(ctx["run1"], MONTH)


def test_usage_lines_present(ctx):
    """The statement has usage lines for exactly the customers and meters with September usage reported by the close."""
    require_run(ctx["run1"])
    check_lines(ctx["run1"], ctx["ref"][1], MONTH, "usage", "set")


def test_usage_line_quantities(ctx):
    """Usage line quantities are September usage reported by the close."""
    require_run(ctx["run1"])
    check_lines(ctx["run1"], ctx["ref"][1], MONTH, "usage", "quantity")


def test_usage_line_amounts(ctx):
    """Usage line amounts follow the September rate cards."""
    require_run(ctx["run1"])
    check_lines(ctx["run1"], ctx["ref"][1], MONTH, "usage", "amount")


def test_adjustment_lines_present(ctx):
    """The statement adjusts exactly the earlier months whose usage reported by the close differs from what was billed."""
    require_run(ctx["run1"])
    check_lines(ctx["run1"], ctx["ref"][1], MONTH, "adjustment", "set")


def test_adjustment_quantities(ctx):
    """Adjustment quantities are the difference between usage reported by the close and usage already billed."""
    require_run(ctx["run1"])
    check_lines(ctx["run1"], ctx["ref"][1], MONTH, "adjustment", "quantity")


def test_adjustment_amounts(ctx):
    """Adjustment amounts are the difference between the charge for the month's usage and what was already billed."""
    require_run(ctx["run1"])
    check_lines(ctx["run1"], ctx["ref"][1], MONTH, "adjustment", "amount")


def test_summary(ctx):
    """The summary covers every customer on the statement and its amounts equal the statement lines and the reference."""
    require_run(ctx["run1"])
    check_summary(ctx["run1"], ctx["ref"][1], MONTH)


def test_rerun_is_deterministic(ctx):
    """Re-running the close on the same extract reproduces the mart, lines and summary byte for byte."""
    require_run(ctx["run2"])
    assert ctx["run1"]["raw"] == ctx["run2"]["raw"], "outputs differ between identical runs"


# ------------------------------------------------------------------------------------------- C. other extracts

HIDDEN = [s["name"] for s in HIDDEN_SPECS]


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_usage_mart(ctx, name):
    """Other extracts: usage mart."""
    (mart, _st), run, _m = ctx["hidden"][name]
    require_run(run)
    check_mart(run, mart)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_statement_lines(ctx, name):
    """Other extracts: usage and adjustment lines (set, quantity, amount), no later service months."""
    (_mart, st), run, month = ctx["hidden"][name]
    require_run(run)
    check_future_months(run, month)
    for kind in ("usage", "adjustment"):
        for what in ("set", "quantity", "amount"):
            check_lines(run, st, month, kind, what)


@pytest.mark.parametrize("name", HIDDEN)
def test_hidden_summary(ctx, name):
    """Other extracts: statement summary."""
    (_mart, st), run, month = ctx["hidden"][name]
    require_run(run)
    check_summary(run, st, month)
