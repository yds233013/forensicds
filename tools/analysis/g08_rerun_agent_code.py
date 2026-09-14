#!/usr/bin/env python3
"""Re-run a G08 trial's submitted mart code on regenerated extracts, optionally with one targeted patch, and compare
with the verifier reference using the verifier's own comparison functions (analysis only; nothing in the task changes).

usage: g08_rerun_agent_code.py <trial_dir> <extract_dir>... [--patch NAME]
Extract dirs need data/warehouse.sqlite and as_of.json ({"as_of": ...}).
"""
import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TASK = ROOT / "candidates/g08-forecast-accuracy-vintages"
sys.path.insert(0, str(TASK / "tests"))
import reference  # noqa: E402
import test_accuracy_mart as T  # noqa: E402

BASIS_CTE_H7 = """
basis AS (
  SELECT r.region, r.settlement_class, r.delivery_date, r.run_id, v.mwh, substr(r.delivery_date,1,7) AS kpi_month
  FROM settlement_runs r JOIN settlement_volumes v ON v.run_id = r.run_id
  JOIN kpi_close_log c ON c.kpi_month = substr(r.delivery_date,1,7)
  WHERE r.run_type = 'IS' AND r.published_at <= c.closed_at
    AND (SELECT h.status FROM run_status_history h WHERE h.run_id = r.run_id AND h.recorded_at <= c.closed_at
         ORDER BY h.recorded_at DESC LIMIT 1) = 'published'
)
"""


def patch(ws: Path, name: str) -> None:
    if name == "none":
        return
    if name == "h7_charge_basis_at_close":
        # replace the latest-settled-volume join with the charge basis at the delivery month's close
        p = ws / "sql/accuracy_examples.sql"
        s = p.read_text()
        s = s.replace("LEFT JOIN settled_volumes_latest s", "LEFT JOIN basis s")
        s = "WITH " + BASIS_CTE_H7.strip() + "\n" + s
        p.write_text(s)
    elif name == "h7_charge_basis_and_all_classes":
        patch(ws, "h7_charge_basis_at_close")
        p = ws / "sql/accuracy_examples.sql"
        s = p.read_text()
        s = s.replace("SUM(s.mwh)                             AS actual_mwh,",
                      "CASE WHEN COUNT(s.run_id) = COUNT(m.settlement_class) THEN SUM(s.mwh) END AS actual_mwh,")
        s = s.replace("GROUP_CONCAT(s.run_id, ';')            AS actual_run_ids",
                      "CASE WHEN COUNT(s.run_id) = COUNT(m.settlement_class) THEN GROUP_CONCAT(s.run_id, ';') END AS actual_run_ids")
        p.write_text(s)
    elif name.startswith("wm_"):
        p = ws / "fcaccuracy/mart.py"
        s = p.read_text()
        if name in ("wm_unit_grain", "wm_all"):
            a = '''        idx = issue_meta.groupby(["model", "run_date"])["issued_at"].idxmax()
        locked_issue_ids = issue_meta.loc[idx, "issue_id"]
        
        locked_issues = month_issues[month_issues["issue_id"].isin(locked_issue_ids)].copy()'''
            b = '''        ok = month_issues[month_issues["issued_at"] <= month_issues["gate_closure"]]
        locked_issues = ok.sort_values("issued_at").drop_duplicates(["model", "run_date", "region", "portfolio", "target_date"], keep="last").copy()'''
            assert a in s, "grain block not found"
            s = s.replace(a, b)
        if name in ("wm_status_at_close", "wm_all"):
            a = '''        month_settlement = settlement[(settlement["target_month"] == month) & (settlement["published_at"] <= closed_at)].copy()'''
            b = '''        month_settlement = settlement[(settlement["target_month"] == month) & (settlement["published_at"] <= closed_at)].copy()
        _h = pd.read_sql_query("SELECT run_id, status, recorded_at FROM run_status_history", con)
        _h["recorded_at"] = pd.to_datetime(_h["recorded_at"], utc=True)
        _h = _h[_h["recorded_at"] <= closed_at].sort_values("recorded_at").drop_duplicates("run_id", keep="last")
        month_settlement = month_settlement[month_settlement["run_id"].isin(_h.loc[_h["status"] == "published", "run_id"])]'''
            assert a in s
            s = s.replace(a, b)
        if name in ("wm_all_classes", "wm_all"):
            a = '''        agg["status"] = agg["n_found"].map(lambda n: "scored" if n > 0 else "unsettled")'''
            b = '''        agg["status"] = (agg["n_found"] == agg["n_classes"]).map({True: "scored", False: "unsettled"})'''
            assert a in s
            s = s.replace(a, b)
        p.write_text(s)
    else:
        raise SystemExit(f"unknown patch {name}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("trial")
    ap.add_argument("extracts", nargs="+")
    ap.add_argument("--patch", default="none")
    a = ap.parse_args()
    for ex in map(Path, a.extracts):
        as_of = json.loads((ex / "as_of.json").read_text())["as_of"]
        ws = Path(tempfile.mkdtemp())
        src = Path(a.trial) / "artifacts/workspace"
        for sub in ("fcaccuracy", "sql"):
            shutil.copytree(src / sub, ws / sub)
        patch(ws, a.patch)
        out = ws / "out"
        p = subprocess.run([sys.executable, "-m", "fcaccuracy", "build", "--as-of", as_of, "--db", str(ex / "data/warehouse.sqlite"),
                            "--out", str(out)], cwd=ws, capture_output=True, text=True, env={"PYTHONPATH": str(ws), "PATH": "/usr/bin:/bin"})
        if p.returncode:
            print(f"{Path(a.trial).name[-7:]} {a.patch} {ex.name}: BUILD FAILED {p.stderr[-400:]}")
            continue
        run = {"returncode": 0}
        with open(out / "evaluation_examples.csv", newline="") as fh:
            run["examples"] = list(csv.DictReader(fh))
        with open(out / "monthly_kpi.csv", newline="") as fh:
            run["monthly"] = list(csv.DictReader(fh))
        run["summary"] = json.loads((out / "summary.json").read_text())
        want = reference.expected(ex / "data/warehouse.sqlite", as_of)
        got = T.example_map(run)
        missing = len(set(want["examples"]) - set(got))
        extra = len(set(got) - set(want["examples"]))
        field_bad = Counter()
        for k, w in want["examples"].items():
            g = got.get(k)
            if g is None:
                continue
            for f in T.ALL_FIELDS:
                if f in ("forecast_mwh", "actual_mwh", "abs_error_mwh"):
                    gv, wv = T.num(g[f]), w[f]
                    ok = (gv is None and wv is None) or (gv is not None and wv is not None and abs(gv - wv) <= 1e-6)
                elif f == "actual_run_ids":
                    ok = ";".join(sorted(x for x in (g[f] or "").split(";") if x)) == w[f]
                else:
                    ok = (g[f] or "").strip() == w[f]
                if not ok:
                    field_bad[f] += 1
        verdicts = []
        for nm, fn in [("monthly", lambda: T.check_monthly(run, want)), ("summary", lambda: T.check_summary(run, want, as_of))]:
            try:
                fn()
                verdicts.append(f"{nm}=ok")
            except AssertionError:
                verdicts.append(f"{nm}=FAIL")
        passed = missing == 0 and extra == 0 and not field_bad and all(v.endswith("ok") for v in verdicts)
        print(f"{Path(a.trial).name[-7:]} patch={a.patch:32} {ex.name:12} missing={missing} extra={extra} field_mismatches={dict(field_bad)} {' '.join(verdicts)} => {'PASS' if passed else 'fail'}")


if __name__ == "__main__":
    main()
