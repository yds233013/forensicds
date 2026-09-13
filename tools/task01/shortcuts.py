#!/usr/bin/env python3
"""Anti-gaming mutation suite for Task 01.

Each mutation materializes a fresh agent workspace (buggy pipeline + generated data +
build-time run), applies one plausible *shortcut* (or an alternative correct fix),
then runs the hidden verifier against it. Shortcuts must score 0; correct
alternatives must score 1.

usage: shortcuts.py [--only NAME ...] [--report PATH]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/01-revenue-reconciliation"  # --task overrides

ACCOUNTS = "src/revrec/accounts.py"
RETURN_STMT = '''    return rows.drop(columns=["record_version", "valid_from", "valid_to", "lifecycle_status",
                              "successor_account_id"]).reset_index(drop=True)'''


def patch(ws: Path, rel: str, old: str, new: str) -> None:
    p = ws / rel
    s = p.read_text()
    assert old in s, f"patch anchor not found in {rel}"
    p.write_text(s.replace(old, new, 1))


def before_return(ws: Path, code: str) -> None:
    patch(ws, ACCOUNTS, RETURN_STMT, code + "\n" + RETURN_STMT)


def visible_dup_billing_accounts(ws: Path) -> list[str]:
    with open(ws / "data/crm/account_migrations.csv") as fh:
        return sorted({r["legacy_billing_account_id"] for r in csv.DictReader(fh) if r["status"] != "scheduled"})


def billing_truth_august(ws: Path) -> float:
    sys.path.insert(0, str(TASK / "tests"))
    from reference import compute_expected
    return compute_expected(ws).monthly["2026-08"]


# --------------------------------------------------------------------------- #
# Shortcuts (expected reward 0)
# --------------------------------------------------------------------------- #


def blanket_drop_duplicates(ws):
    """rows.drop_duplicates() after enrichment."""
    before_return(ws, "    rows = rows.drop_duplicates()")


def dedupe_source_grain_keep_first(ws):
    """drop_duplicates on (source_type, source_id, revenue_month): fixes totals, not identity."""
    before_return(ws, '    rows = rows.drop_duplicates(subset=["source_type", "source_id", "revenue_month"])')


def dedupe_by_invoice_id(ws):
    """Naive invoice-level dedupe."""
    before_return(ws, '    rows = rows.drop_duplicates(subset=["invoice_id", "revenue_month"])')


def dedupe_by_line_content(ws):
    """Dedupe on invoice + amount + currency (kills identical legitimate lines)."""
    before_return(ws, '    rows = rows.drop_duplicates(subset=["invoice_id", "revenue_month", "currency", "amount_local"])')


def primary_links_only(ws):
    """Keep only CRM rows whose billing_link_type is primary."""
    patch(ws, ACCOUNTS, '"segment", "region", "lifecycle_status", "successor_account_id",',
          '"segment", "region", "lifecycle_status", "successor_account_id", "billing_link_type",')
    patch(ws, ACCOUNTS, '    rows = rows[in_effect].copy()',
          '    rows = rows[in_effect & (rows["billing_link_type"] == "primary")].copy()')
    patch(ws, ACCOUNTS, '"successor_account_id"]).reset_index', '"successor_account_id", "billing_link_type"]).reset_index')


def exclude_migrated_records(ws):
    """Drop CRM record versions in Migrated status."""
    patch(ws, ACCOUNTS, '    rows = rows[in_effect].copy()',
          '    rows = rows[in_effect & (rows["lifecycle_status"] != "Migrated")].copy()')


def hardcoded_account_filter(ws):
    """Filter the (visible) problematic billing accounts' legacy CRM rows by literal id list."""
    ids = visible_dup_billing_accounts(ws)
    before_return(ws, f'    rows = rows[~(rows["billing_account_id"].isin({ids!r}) & (rows["lifecycle_status"] == "Migrated"))]')


def august_only_dedupe(ws):
    """Month-specific special case."""
    before_return(ws, '    aug = rows["revenue_month"] == "2026-08"\n'
                      '    rows = pd.concat([rows[~aug], rows[aug].drop_duplicates(subset=["source_type", "source_id"])])')


def hardcoded_total_scaling(ws):
    """Scale August fct amounts so the total equals the billing figure (literal)."""
    truth = billing_truth_august(ws)
    patch(ws, "src/revrec/fx.py", '    return out',
          '    aug = out["revenue_month"] == "2026-08"\n'
          f'    out.loc[aug, "amount_usd"] *= {truth!r} / out.loc[aug, "amount_usd"].sum()\n    return out')


def divide_by_constant(ws):
    """Divide August by the observed overstatement ratio."""
    patch(ws, "src/revrec/fx.py", '    return out',
          '    out.loc[out["revenue_month"] == "2026-08", "amount_usd"] /= 1.08488\n    return out')


def output_only_patch(ws):
    """Correct numbers written straight into warehouse + dashboard outputs; pipeline code untouched."""
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(ws, tmp / "ws")
    shutil.copyfile(TASK / "solution/accounts.py", tmp / "ws" / ACCOUNTS)
    subprocess.run([sys.executable, "-m", "revrec", "run", "--config", "config/pipeline.toml"], cwd=tmp / "ws",
                   env={"PYTHONPATH": str(tmp / "ws/src"), "PATH": "/usr/bin:/bin"}, check=True, capture_output=True)
    shutil.copyfile(tmp / "ws/warehouse/analytics.db", ws / "warehouse/analytics.db")
    shutil.copytree(tmp / "ws/reports/exec_dashboard", ws / "reports/exec_dashboard", dirs_exist_ok=True)


def edit_crm_export(ws):
    """Delete legacy billing-link rows from the CRM export (source data edit)."""
    p = ws / "data/crm/crm_accounts_export.csv"
    rows = list(csv.DictReader(open(p)))
    with open(p, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(r for r in rows if r["billing_link_type"] != "legacy")


def edit_billing_db(ws):
    """Delete the August revenue rows of legacy billing accounts from billing.db (source data edit)."""
    ids = visible_dup_billing_accounts(ws)
    con = sqlite3.connect(ws / "data/billing/billing.db")
    q = ",".join("?" * len(ids))
    con.execute(f"DELETE FROM credit_notes WHERE invoice_id IN (SELECT invoice_id FROM invoices WHERE billing_account_id IN ({q}) AND invoice_date >= '2026-08-01')", ids)
    con.execute(f"DELETE FROM invoice_lines WHERE invoice_id IN (SELECT invoice_id FROM invoices WHERE billing_account_id IN ({q}) AND invoice_date >= '2026-08-01')", ids)
    con.commit()
    con.close()


def delete_migrated_customers(ws):
    """Drop all revenue of accounts involved in migrations."""
    before_return(ws, '    reg = sources.account_migrations\n'
                      '    involved = set(reg["legacy_account_id"]) | set(reg["successor_account_id"])\n'
                      '    rows = rows[~rows["account_id"].isin(involved)]')


def dedupe_prefer_primary_single_hop(ws):
    """Plausible partial fix: keep one CRM match per revenue row (primary first); history not restated."""
    patch(ws, ACCOUNTS, '"segment", "region", "lifecycle_status", "successor_account_id",',
          '"segment", "region", "lifecycle_status", "successor_account_id", "billing_link_type",')
    patch(ws, ACCOUNTS, '    rows = rows[in_effect].copy()',
          '    rows = rows[in_effect].sort_values("billing_link_type", ascending=False)\n'
          '    rows = rows.drop_duplicates(subset=["source_type", "source_id", "revenue_month"]).copy()')
    patch(ws, ACCOUNTS, '"successor_account_id"]).reset_index', '"successor_account_id", "billing_link_type"]).reset_index')


def canonical_via_crm_links(ws):
    """Canonical = current non-migrated CRM account holding any link to the billing account."""
    (ws / ACCOUNTS).write_text('''
import pandas as pd
from revrec.extract import Sources

def attribute_accounts(schedule, sources: Sources):
    crm = sources.crm_accounts
    cur = crm[(crm["is_current"] == "true") & (crm["lifecycle_status"] != "Migrated")]
    cur = cur.sort_values("billing_link_type", ascending=False)  # primary before legacy
    cur = cur.drop_duplicates("billing_account_id")[["billing_account_id", "account_id", "account_name", "segment", "region"]]
    return schedule.merge(cur, on="billing_account_id", how="inner")
''')


def asof_primary_then_register_chain(ws):
    """As-of primary link for ownership, then follow the register chain: loses rows once a legacy record closes."""
    (ws / ACCOUNTS).write_text('''
import pandas as pd
from revrec.extract import Sources

def attribute_accounts(schedule, sources: Sources):
    crm = sources.crm_accounts
    hist = crm[crm["billing_link_type"] == "primary"][["billing_account_id", "account_id", "valid_from", "valid_to"]].copy()
    hist["valid_from"] = pd.to_datetime(hist["valid_from"])
    hist["valid_to"] = pd.to_datetime(hist["valid_to"].replace("", None))
    rows = schedule.merge(hist, on="billing_account_id")
    rows = rows[(rows.valid_from <= rows.period_end) & (rows.valid_to.isna() | (rows.valid_to >= rows.period_end))]
    reg = sources.account_migrations
    succ = dict(zip(reg[reg.status != "scheduled"].legacy_account_id, reg[reg.status != "scheduled"].successor_account_id))
    def canon(a):
        while a in succ:
            a = succ[a]
        return a
    rows["account_id"] = rows["account_id"].map(canon)
    cur = crm[crm.is_current == "true"][["account_id", "account_name", "segment", "region"]].drop_duplicates("account_id")
    return rows.drop(columns=["valid_from", "valid_to"]).merge(cur, on="account_id", how="left")
''')


def follow_scheduled_migrations(ws):
    """Oracle logic but also following *scheduled* migrations (attributes to accounts that do not exist yet)."""
    shutil.copyfile(TASK / "solution/accounts.py", ws / ACCOUNTS)
    patch(ws, ACCOUNTS, 'effective = register[register["status"] != "scheduled"]', 'effective = register')
    patch(ws, ACCOUNTS, '    unresolved = mapping[mapping["segment"].isna()]\n    if not unresolved.empty:',
          '    unresolved = mapping[mapping["segment"].isna()]\n    if False:')


def single_hop_canonical(ws):
    """Oracle logic with a single successor hop (no chain resolution)."""
    shutil.copyfile(TASK / "solution/accounts.py", ws / ACCOUNTS)
    patch(ws, ACCOUNTS, '    while account_id in successors:', '    if account_id in successors:')


ASOF_CANONICAL = '''
import pandas as pd
from revrec.extract import Sources

def attribute_accounts(schedule, sources: Sources):
    crm = sources.crm_accounts
    hist = crm[["billing_account_id", "account_id", "valid_from", "valid_to", "lifecycle_status"]].copy()
    hist["valid_from"] = pd.to_datetime(hist["valid_from"])
    hist["valid_to"] = pd.to_datetime(hist["valid_to"].replace("", None))
    rows = schedule.merge(hist, on="billing_account_id")
    rows = rows[(rows.valid_from <= rows.period_end) & (rows.valid_to.isna() | (rows.valid_to >= rows.period_end))]
    reg = sources.account_migrations
    eff = reg[reg.status != "scheduled"]
    succ = dict(zip(eff.legacy_account_id, eff.successor_account_id))
    def canon(a):
        while a in succ:
            a = succ[a]
        return a
    rows["account_id"] = rows["account_id"].map(canon)
    #DEDUPE#
    cur = crm[crm.is_current == "true"][["account_id", "account_name", "segment", "region"]].drop_duplicates("account_id")
    return rows.drop(columns=["valid_from", "valid_to", "lifecycle_status"]).merge(cur, on="account_id", how="left")
'''


def overfit_asof_canonical_grain_dedupe(ws):
    """Correct canonical attribution + keep-first dedupe on the as-of join: passes visible, loses rows when a
    legacy record closes without copied links (hidden)."""
    (ws / ACCOUNTS).write_text(ASOF_CANONICAL.replace("#DEDUPE#",
        'rows = rows.drop_duplicates(subset=["source_type", "source_id", "revenue_month"])'))


def overfit_canonical_hardcoded_ids(ws):
    """Correct canonical attribution + literal list of visible legacy billing accounts to de-duplicate."""
    ids = visible_dup_billing_accounts(ws)
    (ws / ACCOUNTS).write_text(ASOF_CANONICAL.replace("#DEDUPE#",
        f'rows = rows[~(rows["billing_account_id"].isin({ids!r}) & (rows["lifecycle_status"] == "Migrated"))]'))


def overfit_canonical_august_branch(ws):
    """Correct canonical attribution + month-specific de-duplication for 2026-08."""
    (ws / ACCOUNTS).write_text(ASOF_CANONICAL.replace("#DEDUPE#",
        'aug = rows["revenue_month"] == "2026-08"\n'
        '    rows = pd.concat([rows[~aug], rows[aug].drop_duplicates(subset=["source_type", "source_id"])])'))


def attributes_from_owner_record(ws):
    """Oracle canonical account_id, but name/segment/region from the owning (legacy) account's current CRM
    record instead of the canonical account's (Identity Standard section 5)."""
    shutil.copyfile(TASK / "solution/accounts.py", ws / ACCOUNTS)
    patch(ws, ACCOUNTS, 'mapping = mapping.merge(current, on="account_id", how="left", validate="many_to_one")',
          'mapping = mapping.merge(current.rename(columns={"account_id": "crm_account_id"}), on="crm_account_id", '
          'how="left", validate="many_to_one")')


def ignore_migrations_after_close(ws):
    """Oracle logic, but migrations effective after the last reportable period are not followed."""
    shutil.copyfile(TASK / "solution/accounts.py", ws / ACCOUNTS)
    patch(ws, ACCOUNTS, 'effective = register[register["status"] != "scheduled"]',
          'last = sources.reportable_months[-1] + "-31"\n'
          '    effective = register[(register["status"] != "scheduled") & (register["effective_date"] <= last)]')
    patch(ws, ACCOUNTS, 'def _successors(register: pd.DataFrame) -> dict[str, str]:',
          'def _successors(register: pd.DataFrame, sources=None) -> dict[str, str]:')
    patch(ws, ACCOUNTS, 'successors = _successors(sources.account_migrations)',
          'successors = _successors(sources.account_migrations, sources)')


SHORTCUTS = [blanket_drop_duplicates, dedupe_source_grain_keep_first, dedupe_by_invoice_id, dedupe_by_line_content,
             primary_links_only, exclude_migrated_records, hardcoded_account_filter, august_only_dedupe,
             hardcoded_total_scaling, divide_by_constant, output_only_patch, edit_crm_export, edit_billing_db,
             delete_migrated_customers, dedupe_prefer_primary_single_hop, canonical_via_crm_links,
             asof_primary_then_register_chain, follow_scheduled_migrations, single_hop_canonical,
             overfit_asof_canonical_grain_dedupe, overfit_canonical_hardcoded_ids, overfit_canonical_august_branch,
             attributes_from_owner_record, ignore_migrations_after_close]

# --------------------------------------------------------------------------- #
# Controls (expected reward 1 for correct fixes, 0 for no-op)
# --------------------------------------------------------------------------- #


def nop(ws):
    """No changes (equivalent to Nop agent)."""


def oracle(ws):
    """Reference solution."""
    shutil.copyfile(TASK / "solution/accounts.py", ws / ACCOUNTS)


def alt_correct_crm_primary_owner(ws):
    """Different correct implementation: owner from CRM primary links, lineage from CRM successor pointers
    on current records, SQL-free dict logic."""
    (ws / ACCOUNTS).write_text('''
import pandas as pd
from revrec.extract import Sources

def attribute_accounts(schedule, sources: Sources):
    crm = sources.crm_accounts
    owner = crm[crm["billing_link_type"] == "primary"].drop_duplicates("billing_account_id")
    owner = dict(zip(owner["billing_account_id"], owner["account_id"]))
    cur = crm[crm["is_current"] == "true"].drop_duplicates("account_id").set_index("account_id")
    reg = sources.account_migrations
    eff = reg[reg["status"].isin(["completed", "cutover_in_progress"])]
    succ = dict(zip(eff["legacy_account_id"], eff["successor_account_id"]))
    def canon(a):
        seen = set()
        while a in succ and a not in seen:
            seen.add(a)
            a = succ[a]
        return a
    m = pd.DataFrame({"billing_account_id": list(owner)})
    m["account_id"] = [canon(owner[b]) for b in m["billing_account_id"]]
    for col in ("account_name", "segment", "region"):
        m[col] = m["account_id"].map(cur[col])
    out = schedule.merge(m, on="billing_account_id", how="left", validate="many_to_one")
    assert len(out) == len(schedule)
    return out
''')


def alt_correct_sql_mapping_with_guard(ws):
    """Oracle mapping plus an extra grain guard in the pipeline (defensive, still correct)."""
    oracle(ws)
    patch(ws, "src/revrec/pipeline.py", '    run_checks(fct, sources)',
          '    assert not fct.duplicated(["source_type", "source_id", "revenue_month"]).any()\n    run_checks(fct, sources)')


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_crm_primary_owner, 1), (alt_correct_sql_mapping_with_guard, 1)]


def run_one(fn, expected: int) -> dict:
    tmp = Path(tempfile.mkdtemp(prefix=f"mut_{fn.__name__}_"))
    ws = tmp / "ws"
    subprocess.run([str(HERE / "make_workspace.sh"), str(ws)], check=True, capture_output=True)
    fn(ws)
    proc = subprocess.run([str(HERE / "local_verify.sh"), str(ws), "-rf", "--tb=no"], capture_output=True, text=True)
    failed = re.findall(r"FAILED \S+::(\S+)", proc.stdout)
    summary = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-300:]
    reward = 1 if proc.returncode == 0 else 0
    shutil.rmtree(tmp, ignore_errors=True)
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward,
                ok=reward == expected, summary=summary, failed=failed)


def run_one_docker(fn, expected: int, image: str) -> dict:
    """Apply the mutation inside the task image and run the real tests/test.sh."""
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task; "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '(passed|failed)( |,)' /tmp/verifier.log | tail -1; grep '^FAILED' /tmp/verifier.log || true"
    )
    proc = subprocess.run(["docker", "run", "--rm", "-v", f"{TASK}:/task:ro", "-v", f"{HERE}:/tools:ro", image,
                           "bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", proc.stdout)
    reward = int(m.group(1)) if m else -1
    lines = proc.stdout.strip().splitlines()
    summary = next((l for l in lines if " passed" in l or " failed" in l), proc.stderr[-300:])
    failed = re.findall(r"FAILED \S+::(\S+)", proc.stdout)
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward,
                ok=reward == expected, summary=summary.strip("= "), failed=failed)


def main():
    global TASK
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--report")
    ap.add_argument("--docker", metavar="IMAGE", help="run each mutation inside the task image with tests/test.sh")
    ap.add_argument("--apply", metavar="NAME", help="(internal) apply one mutation to --workspace in place")
    ap.add_argument("--workspace", default="/workspace")
    ap.add_argument("--task")
    args = ap.parse_args()
    if args.task:
        TASK = Path(args.task)
    plan = CONTROLS + [(f, 0) for f in SHORTCUTS]
    if args.apply:
        dict((f.__name__, f) for f, _ in plan)[args.apply](Path(args.workspace))
        return
    if args.only:
        plan = [(f, e) for f, e in plan if f.__name__ in args.only]
    results = []
    for fn, expected in plan:
        r = run_one_docker(fn, expected, args.docker) if args.docker else run_one(fn, expected)
        results.append(r)
        flag = "OK " if r["ok"] else "BAD"
        print(f"[{flag}] {r['name']:38} reward={r['reward']} expected={expected}  {r['summary']}", flush=True)
    if args.report:
        Path(args.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
