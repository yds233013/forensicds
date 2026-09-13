"""Independent reference implementation of the documented revenue semantics.

Pure Python + sqlite3 (deliberately shares no code with the workspace pipeline).
Given a workspace-shaped data directory it computes, from first principles:

  * the billing source-of-truth recognized revenue rows (policy: ratable by day over
    the service period for posted revenue lines; credit notes in full in their issue
    month; monthly-average FX of the revenue month; reportable periods only);
  * canonical customer attribution (billing account -> owning CRM account per
    billing -> terminal successor through effective migrations in the register);
  * the expected warehouse tables at their documented grains.
"""
from __future__ import annotations

import csv
import sqlite3
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import calendar

REVENUE_LINE_TYPES = ("subscription", "usage", "onboarding", "discount")


def _d(s: str) -> date:
    return date.fromisoformat(s)


def _ym(x: date) -> str:
    return f"{x.year:04d}-{x.month:02d}"


def _month_bounds(x: date) -> tuple[date, date]:
    return x.replace(day=1), x.replace(day=calendar.monthrange(x.year, x.month)[1])


def _next_month(x: date) -> date:
    return date(x.year + (x.month == 12), 1 if x.month == 12 else x.month + 1, 1)


@dataclass
class Expected:
    months: list[str]
    # (source_type, source_id, revenue_month) -> dict(amount_usd, billing_account_id, account_id, invoice_id)
    fct: dict[tuple[str, str, str], dict]
    monthly: dict[str, float]
    monthly_gross: dict[str, float]
    monthly_credits: dict[str, float]
    account_month: dict[tuple[str, str], float]
    segment_month: dict[tuple[str, str], float]
    canonical: dict[str, str]            # billing_account_id -> canonical account_id
    account_attrs: dict[str, dict]       # canonical account_id -> attributes
    migrated_legacy_bas: set[str] = field(default_factory=set)


def load_register(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def load_crm(path: Path) -> list[dict]:
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def canonical_map(billing_owner: dict[str, str], register: list[dict]) -> dict[str, str]:
    successor: dict[str, str] = {}
    for r in register:
        if r["status"] == "scheduled":
            continue
        prev = successor.get(r["legacy_account_id"])
        if prev is not None and prev != r["successor_account_id"]:
            raise ValueError(f"legacy account {r['legacy_account_id']} has two successors")
        successor[r["legacy_account_id"]] = r["successor_account_id"]

    def resolve(acc: str) -> str:
        seen = {acc}
        while acc in successor:
            acc = successor[acc]
            if acc in seen:
                raise ValueError("cycle in migration register")
            seen.add(acc)
        return acc

    return {ba: resolve(owner) for ba, owner in billing_owner.items()}


def compute_expected(root: Path) -> Expected:
    root = Path(root)
    con = sqlite3.connect(f"file:{root / 'data/billing/billing.db'}?mode=ro", uri=True)
    months = [r[0] for r in con.execute(
        "SELECT period_month FROM accounting_periods WHERE status IN ('closed','closing') ORDER BY period_month")]
    month_set = set(months)
    fx = {(c, m): r for c, m, r in con.execute("SELECT currency, rate_month, usd_per_unit FROM fx_rates")}
    billing_owner = dict(con.execute("SELECT billing_account_id, crm_account_id FROM billing_accounts"))

    fct: dict[tuple[str, str, str], dict] = {}
    lines = con.execute(f"""
        SELECT l.invoice_line_id, l.invoice_id, i.billing_account_id, i.currency, l.amount_minor,
               l.service_period_start, l.service_period_end
        FROM invoice_lines l JOIN invoices i ON i.invoice_id = l.invoice_id
        WHERE i.status = 'posted' AND l.line_type IN ({",".join("?" * len(REVENUE_LINE_TYPES))})
    """, REVENUE_LINE_TYPES).fetchall()
    for line_id, inv_id, ba, cur, amt, ss, se in lines:
        s, e = _d(ss), _d(se)
        total = (e - s).days + 1
        m = s.replace(day=1)
        while m <= e:
            m0, m1 = _month_bounds(m)
            key_m = _ym(m)
            if key_m in month_set:
                overlap = (min(e, m1) - max(s, m0)).days + 1
                local = amt / 100.0 * overlap / total
                fct[("invoice_line", line_id, key_m)] = dict(
                    amount_usd=local * fx[(cur, key_m)], amount_local=local, billing_account_id=ba,
                    invoice_id=inv_id, currency=cur)
            m = _next_month(m)
    credits = con.execute("""
        SELECT c.credit_note_id, c.invoice_id, i.billing_account_id, c.currency, c.amount_minor, c.issued_date
        FROM credit_notes c JOIN invoices i ON i.invoice_id = c.invoice_id
        WHERE c.status = 'issued' AND i.status = 'posted'
    """).fetchall()
    for cn_id, inv_id, ba, cur, amt, issued in credits:
        key_m = issued[:7]
        if key_m in month_set:
            local = -amt / 100.0
            fct[("credit_note", cn_id, key_m)] = dict(
                amount_usd=local * fx[(cur, key_m)], amount_local=local, billing_account_id=ba,
                invoice_id=inv_id, currency=cur)
    con.close()

    register = load_register(root / "data/crm/account_migrations.csv")
    canonical = canonical_map(billing_owner, register)
    attrs: dict[str, dict] = {}
    for r in load_crm(root / "data/crm/crm_accounts_export.csv"):
        if r["is_current"] == "true":
            attrs[r["account_id"]] = dict(account_name=r["account_name"], segment=r["segment"], region=r["region"])

    monthly: dict[str, float] = defaultdict(float)
    gross: dict[str, float] = defaultdict(float)
    cred: dict[str, float] = defaultdict(float)
    acct: dict[tuple[str, str], float] = defaultdict(float)
    seg: dict[tuple[str, str], float] = defaultdict(float)
    for (stype, _sid, m), row in fct.items():
        acc = canonical[row["billing_account_id"]]
        row["account_id"] = acc
        row["segment"] = attrs[acc]["segment"]
        row["account_name"] = attrs[acc]["account_name"]
        row["region"] = attrs[acc]["region"]
        monthly[m] += row["amount_usd"]
        (gross if stype == "invoice_line" else cred)[m] += row["amount_usd"]
        acct[(m, acc)] += row["amount_usd"]
        seg[(m, attrs[acc]["segment"])] += row["amount_usd"]

    legacy_bas = {r["legacy_billing_account_id"] for r in register if r["status"] != "scheduled"}
    return Expected(months, fct, dict(monthly), dict(gross), dict(cred), dict(acct), dict(seg), canonical, attrs,
                    legacy_bas)
