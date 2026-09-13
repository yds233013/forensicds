#!/usr/bin/env python3
"""Collect objective evidence from a trial's final /workspace artifact.

usage: workspace_evidence.py <trial_dir> [--out DIR]

Writes (default <trial_dir>/analysis/):
  diff.patch            unified diff of every non-data text file vs the frozen task workspace
  changed_files.txt     added / removed / modified files (excluding generated outputs)
  integrity.json        source-extract digests vs a pristine regeneration
  reconcile.txt         billing vs the warehouse *as the agent left it* (tools/task01/reconcile.py)
"""
import argparse
import difflib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "candidates/01-revenue-reconciliation"
ORIG = TASK / "environment/workspace"
GENERATED = ("data/", "warehouse/", "reports/exec_dashboard/", "reports/finance/", "logs/pipeline/")


def find_workspace(trial: Path) -> Path:
    for cand in sorted((trial / "artifacts").rglob("workspace")):
        if (cand / "src/revrec").is_dir():
            return cand
    for cand in sorted((trial / "artifacts").rglob("src")):
        if (cand / "revrec").is_dir():
            return cand.parent
    raise SystemExit(f"no workspace artifact under {trial}/artifacts")


def text_files(base: Path) -> dict[str, Path]:
    out = {}
    for p in base.rglob("*"):
        if p.is_file() and "__pycache__" not in p.parts:
            rel = p.relative_to(base).as_posix()
            if not rel.startswith(GENERATED) and p.suffix not in (".db", ".pyc"):
                out[rel] = p
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()
    ws = find_workspace(a.trial)
    out = a.out or (a.trial / "analysis")
    out.mkdir(parents=True, exist_ok=True)

    before, after = text_files(ORIG), text_files(ws)
    lines, changed = [], []
    for rel in sorted(set(before) | set(after)):
        b = before[rel].read_text(errors="replace").splitlines(keepends=True) if rel in before else []
        f = after[rel].read_text(errors="replace").splitlines(keepends=True) if rel in after else []
        if b != f:
            status = "added" if rel not in before else "removed" if rel not in after else "modified"
            changed.append(f"{status}\t{rel}")
            lines.extend(difflib.unified_diff(b, f, f"a/{rel}", f"b/{rel}"))
    (out / "diff.patch").write_text("".join(lines))
    extra_generated = sorted(p.relative_to(ws).as_posix() for p in ws.rglob("*")
                             if p.is_file() and p.relative_to(ws).as_posix().startswith(("data/", "warehouse/"))
                             and p.name not in ("billing.db", "crm_accounts_export.csv", "account_migrations.csv",
                                                "analytics.db"))
    (out / "changed_files.txt").write_text("\n".join(changed + [f"extra-in-data-or-warehouse\t{x}" for x in extra_generated]) + "\n")

    sys.path.insert(0, str(TASK / "tests"))
    import world  # noqa: E402
    pristine = Path(tempfile.mkdtemp()) / "p"
    world.build(world.VISIBLE_SPEC, pristine)
    pd, ad = world.source_digests(pristine), {}
    for rel in pd:
        try:
            ad[rel] = world.source_digests(ws)[rel]
        except Exception as exc:  # noqa: BLE001
            ad[rel] = f"error: {exc!r}"
    integ = {rel: {"unmodified": ad[rel] == pd[rel]} for rel in pd}
    (out / "integrity.json").write_text(json.dumps(integ, indent=2))

    rec = subprocess.run([sys.executable, str(ROOT / "tools/task01/reconcile.py"), str(ws)], capture_output=True, text=True)
    (out / "reconcile.txt").write_text(rec.stdout + rec.stderr)
    print(f"workspace: {ws}\nchanged files:\n  " + "\n  ".join(changed or ["(none)"]))
    print(f"integrity: {json.dumps({k: v['unmodified'] for k, v in integ.items()})}")
    print(f"extra files in data/warehouse: {extra_generated or 'none'}")


if __name__ == "__main__":
    main()
