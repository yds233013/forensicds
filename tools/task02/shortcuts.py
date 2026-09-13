#!/usr/bin/env python3
"""Anti-gaming mutation suite for Task 02 (renewal-risk temporal provenance).

Each mutation starts from the incident-time workspace inside the task image, applies one repair
attempt, then runs the real tests/test.sh. Shortcuts and overfit repairs must score 0; independently
written correct repairs must score 1. `expected=None` marks informational probes.

usage: shortcuts.py --docker IMAGE [--only NAME ...] [--jobs N] [--report PATH]
       shortcuts.py --apply NAME --task /task            (internal, inside the container)
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
TASK = (HERE.parents[1] if len(HERE.parents) > 1 else HERE) / "candidates/02-renewal-risk-regression"
WS = Path("/workspace")
PKG = WS / "src/renewal_risk"


def patch(rel: str, old: str, new: str) -> None:
    p = PKG / rel
    s = p.read_text()
    assert old in s, f"anchor not found in {rel}: {old[:60]}"
    p.write_text(s.replace(old, new, 1))


def install_oracle() -> None:
    shutil.copytree(TASK / "solution/renewal_risk", PKG, dirs_exist_ok=True)


# ---------------------------------------------------------------------------------- controls


def nop():
    """No change (Nop agent)."""


def oracle():
    """Reference solution."""
    install_oracle()


ALT_SQL_PIPELINE = r'''
"""Pipeline features with point-in-time state computed in SQLite (window functions)."""
import sqlite3
import pandas as pd
from renewal_risk.sources.warehouse import Warehouse

STAGE_ORDINAL = {"Closed Lost": 0, "Qualification": 1, "Discovery": 2, "Proposal": 3, "Negotiation": 4, "Verbal": 5, "Closed Won": 6}
DB = "/workspace/data/warehouse.db"


def _state(con, requests, table, key):
    con.execute("DROP TABLE IF EXISTS req")
    con.execute("CREATE TEMP TABLE req (rid INTEGER, ent TEXT, cutoff TEXT)")
    con.executemany("INSERT INTO req VALUES (?,?,?)", requests)
    sql = f"""
      SELECT rid, field, new_value FROM (
        SELECT r.rid, h.field, h.new_value,
               ROW_NUMBER() OVER (PARTITION BY r.rid, h.field ORDER BY h.synced_at DESC, h.changed_at DESC) rn
        FROM req r JOIN {table} h ON h.{key} = r.ent AND h.synced_at < r.cutoff) WHERE rn = 1"""
    out = {}
    for rid, field, value in con.execute(sql):
        out.setdefault(rid, {})[field] = value
    return out


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    import renewal_risk.config  # noqa
    con = sqlite3.connect(wh_path())
    opps = wh.opportunities
    ren = dict(zip(opps.loc[opps.opportunity_type == "renewal", "contract_id"], opps.loc[opps.opportunity_type == "renewal", "opportunity_id"]))
    rows = []
    reqs = []
    for i, r in enumerate(examples.itertuples()):
        cut = pd.Timestamp(r.prediction_date).strftime("%Y-%m-%d %H:%M:%S")
        if r.contract_id in ren:
            reqs.append((i, ren[r.contract_id], cut))
    st = _state(con, reqs, "crm_opportunity_field_history", "opportunity_id")
    exp = opps.loc[opps.opportunity_type == "expansion", ["account_id", "opportunity_id"]]
    by_acc = exp.groupby("account_id")["opportunity_id"].apply(list).to_dict()
    ereq, owner = [], []
    for i, r in enumerate(examples.itertuples()):
        cut = pd.Timestamp(r.prediction_date).strftime("%Y-%m-%d %H:%M:%S")
        for oid in by_acc.get(r.account_id, []):
            ereq.append((len(ereq), oid, cut))
            owner.append(i)
    est = _state(con, ereq, "crm_opportunity_field_history", "opportunity_id")
    open_counts = {}
    for j, i in enumerate(owner):
        s = est.get(j)
        if s and s["stage"] not in ("Closed Won", "Closed Lost"):
            open_counts[i] = open_counts.get(i, 0) + 1
    for i, r in enumerate(examples.itertuples()):
        s = st.get(i)
        if s is None:
            rows.append(dict(contract_id=r.contract_id, has_renewal_opp=0, renewal_stage_ordinal=-1, forecast_commit=0,
                             forecast_best_case=0, forecast_omitted=0, renewal_amount_ratio=1.0, days_to_opp_close=90,
                             competitor_flagged=0, open_expansion_opps=open_counts.get(i, 0)))
            continue
        rows.append(dict(contract_id=r.contract_id, has_renewal_opp=1, renewal_stage_ordinal=STAGE_ORDINAL[s["stage"]],
                         forecast_commit=int(s["forecast_category"] == "Commit"), forecast_best_case=int(s["forecast_category"] == "Best Case"),
                         forecast_omitted=int(s["forecast_category"] == "Omitted"), renewal_amount_ratio=float(s["amount_usd"]) / r.arr_usd,
                         days_to_opp_close=(pd.Timestamp(s["close_date"]) - pd.Timestamp(r.prediction_date)).days,
                         competitor_flagged=int(bool(s.get("competitor"))), open_expansion_opps=open_counts.get(i, 0)))
    con.close()
    return pd.DataFrame(rows)


def wh_path():
    import os
    return os.environ.get("RENEWAL_RISK_DB", DB)
'''

ALT_SQL_HEALTH = r'''
"""Health features with point-in-time state computed in SQLite."""
import sqlite3
import pandas as pd
from renewal_risk.features.pipeline_signals import _state, wh_path
from renewal_risk.sources.warehouse import Warehouse


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    con = sqlite3.connect(wh_path())
    reqs = [(i, r.account_id, pd.Timestamp(r.prediction_date).strftime("%Y-%m-%d %H:%M:%S")) for i, r in enumerate(examples.itertuples())]
    st = _state(con, reqs, "cs_account_health_history", "account_id")
    con.close()
    rows = []
    for i, r in enumerate(examples.itertuples()):
        s = st.get(i, {})
        rows.append(dict(contract_id=r.contract_id,
                         health_score=float(s["health_score"]) if s.get("health_score") else 50.0,
                         health_red=int(s.get("health_color") == "Red"),
                         nps_last=float(s["nps_last"]) if s.get("nps_last") else 0.0,
                         csm_sentiment_negative=int(s.get("csm_sentiment") == "Negative")))
    return pd.DataFrame(rows)
'''


def alt_correct_sql_window():
    """Independent correct repair: point-in-time state via SQLite window functions (no pandas as-of joins)."""
    (PKG / "features/pipeline_signals.py").write_text(ALT_SQL_PIPELINE)
    (PKG / "features/health.py").write_text(ALT_SQL_HEALTH)


ALT_REPLAY = r'''
"""Point-in-time state by replaying each record's loaded change events (pure Python)."""
import bisect
import sqlite3
from collections import defaultdict
import pandas as pd

_CACHE = {}


def replay_index(table, key):
    if table not in _CACHE:
        con = sqlite3.connect("file:/workspace/data/warehouse.db?mode=ro", uri=True)
        ev = defaultdict(list)
        for ent, field, value, changed, synced in con.execute(f"SELECT {key}, field, new_value, changed_at, synced_at FROM {table}"):
            ev[ent].append((synced, changed, field, value))
        con.close()
        idx = {}
        for ent, rows in ev.items():
            rows.sort(key=lambda r: (r[0], r[1]))
            idx[ent] = ([r[0] for r in rows], rows)
        _CACHE[table] = idx
    return _CACHE[table]


def state(table, key, ent, cutoff: str):
    idx = replay_index(table, key).get(ent)
    if not idx:
        return None
    k = bisect.bisect_left(idx[0], cutoff)
    if k == 0:
        return None
    s = {}
    for _sy, _ch, f, v in idx[1][:k]:
        s[f] = v
    return s
'''


def alt_correct_event_replay():
    """Independent correct repair: replay loaded change events per record (bisect on synced_at)."""
    (PKG / "sources/replay.py").write_text(ALT_REPLAY)
    patch("features/pipeline_signals.py", "import pandas as pd\n", "import pandas as pd\nfrom renewal_risk.sources.replay import state as _pit\n")
    patch("features/pipeline_signals.py", '''    m = examples[["contract_id", "prediction_date", "arr_usd"]].merge(renewal, on="contract_id", how="left")
    exists = m["created_at"].notna() & (m["created_at"] < m["prediction_date"])''',
          '''    oid = dict(zip(opps.loc[opps["opportunity_type"] == "renewal", "contract_id"], opps.loc[opps["opportunity_type"] == "renewal", "opportunity_id"]))
    m = examples[["contract_id", "prediction_date", "arr_usd"]].copy()
    st = [(_pit("crm_opportunity_field_history", "opportunity_id", oid[c], p.strftime("%Y-%m-%d 00:00:00")) if c in oid else None)
          for c, p in zip(m["contract_id"], m["prediction_date"])]
    exists = pd.Series([s is not None for s in st], index=m.index)
    for f in ["stage", "forecast_category", "amount_usd", "close_date", "competitor"]:
        m[f] = [s.get(f) if s else None for s in st]
    m["amount_usd"] = pd.to_numeric(m["amount_usd"])
    m["close_date"] = pd.to_datetime(m["close_date"])''')
    patch("features/pipeline_signals.py", '''    expansion = opps[opps["opportunity_type"] == "expansion"][["account_id", "created_at", "stage"]]
    e = examples[["contract_id", "account_id", "prediction_date"]].merge(expansion, on="account_id")
    e = e[(e["created_at"] < e["prediction_date"]) & ~e["stage"].isin(CLOSED_STAGES)]''',
          '''    expansion = opps[opps["opportunity_type"] == "expansion"][["account_id", "opportunity_id"]]
    e = examples[["contract_id", "account_id", "prediction_date"]].merge(expansion, on="account_id")
    e["pit_stage"] = [(_pit("crm_opportunity_field_history", "opportunity_id", o, p.strftime("%Y-%m-%d 00:00:00")) or {}).get("stage")
                      for o, p in zip(e["opportunity_id"], e["prediction_date"])]
    e = e[e["pit_stage"].notna() & ~e["pit_stage"].isin(CLOSED_STAGES)]''')
    (PKG / "features/health.py").write_text('''"""Customer Success health features (point in time)."""
import pandas as pd
from renewal_risk.sources.replay import state as _pit
from renewal_risk.sources.warehouse import Warehouse


def build(examples: pd.DataFrame, wh: Warehouse) -> pd.DataFrame:
    rows = []
    for c, a, p in zip(examples["contract_id"], examples["account_id"], examples["prediction_date"]):
        s = _pit("cs_account_health_history", "account_id", a, p.strftime("%Y-%m-%d 00:00:00")) or {}
        rows.append(dict(contract_id=c, health_score=float(s["health_score"]) if s.get("health_score") else 50.0,
                         health_red=int(s.get("health_color") == "Red"),
                         nps_last=float(s["nps_last"]) if s.get("nps_last") else 0.0,
                         csm_sentiment_negative=int(s.get("csm_sentiment") == "Negative")))
    return pd.DataFrame(rows)
''')


def probe_oracle_unweighted_model():
    """Informational: correct features but class_weight reverted to None (a model-spec change)."""
    install_oracle()
    cfg = WS / "config/pipeline.toml"
    cfg.write_text(cfg.read_text().replace('class_weight = "balanced"', 'class_weight = ""'))


# ---------------------------------------------------------------------------------- shortcuts


def constant_leaky_features():
    """Set every CRM and health feature to its default (columns kept)."""
    patch("features/build.py", '''    return out[["contract_id", "prediction_date"] + FEATURE_COLUMNS]''',
          '''    from renewal_risk.features.registry import HEALTH, PIPELINE
    defaults = {"renewal_stage_ordinal": -1, "renewal_amount_ratio": 1.0, "days_to_opp_close": 90, "health_score": 50.0}
    for c in PIPELINE + HEALTH:
        out[c] = defaults.get(c, 0)
    return out[["contract_id", "prediction_date"] + FEATURE_COLUMNS]''')


def drop_leaky_columns():
    """Remove CRM and health features from the feature set."""
    patch("features/registry.py", "FEATURE_COLUMNS = CONTRACT + USAGE + SUPPORT + PIPELINE + HEALTH",
          "FEATURE_COLUMNS = CONTRACT + USAGE + SUPPORT")


def exclude_known_leaky_columns():
    """Keep current-state data but neutralize the obviously leaky stage/forecast/amount/health color columns."""
    patch("features/build.py", '''    return out[["contract_id", "prediction_date"] + FEATURE_COLUMNS]''',
          '''    out["renewal_stage_ordinal"] = -1
    out[["forecast_commit", "forecast_best_case", "forecast_omitted", "health_red"]] = 0
    out["renewal_amount_ratio"] = 1.0
    return out[["contract_id", "prediction_date"] + FEATURE_COLUMNS]''')


def pit_by_changed_at():
    """Point-in-time reconstruction using the business timestamp (changed_at) as availability."""
    install_oracle()
    p = PKG / "sources/history.py"
    s = p.read_text()
    s = s.replace('history = history.assign(synced_at=pd.to_datetime(history["synced_at"]).astype("datetime64[ns]"))',
                  'history = history.assign(synced_at=pd.to_datetime(history["changed_at"]).astype("datetime64[ns]"))')
    p.write_text(s)


def pit_crm_only():
    """Point-in-time CRM features; health still read from the current-state object."""
    install_oracle()
    shutil.copyfile(TASK / "environment/workspace/src/renewal_risk/features/health.py", PKG / "features/health.py")


def pit_health_only():
    """Point-in-time health features; CRM still read from the current-state object."""
    install_oracle()
    shutil.copyfile(TASK / "environment/workspace/src/renewal_risk/features/pipeline_signals.py", PKG / "features/pipeline_signals.py")


def creation_time_values():
    """Use each record's values at creation (first history rows) instead of the latest known values."""
    install_oracle()
    p = PKG / "sources/history.py"
    s = p.read_text()
    s = s.replace('''        h = history.loc[history["field"] == field, [entity, "new_value", "synced_at"]]''',
                  '''        h = history.loc[history["field"] == field, [entity, "new_value", "synced_at"]]
        h = h.groupby(entity, as_index=False).head(1)''')
    p.write_text(s)


def fixed_cutoff_date():
    """State as of a fixed date (last pre-migration day) for every example."""
    install_oracle()
    p = PKG / "sources/history.py"
    s = p.read_text()
    s = s.replace('''    req["cutoff"] = pd.to_datetime(req["cutoff"]).astype("datetime64[ns]")''',
                  '''    req["cutoff"] = pd.Timestamp("2026-01-11").as_unit("ns")''')
    p.write_text(s)


def filter_examples_with_closed_opps():
    """Drop examples whose renewal opportunity is already closed in the CRM object."""
    patch("examples.py", '''    ex = ex.sort_values(["prediction_date", "contract_id"]).reset_index(drop=True)''',
          '''    closed = set(wh.opportunities.loc[wh.opportunities["stage"].isin(["Closed Won", "Closed Lost"]), "contract_id"].dropna())
    ex = ex[~ex["contract_id"].isin(closed) | (ex["split"] == "train")]
    ex = ex.sort_values(["prediction_date", "contract_id"]).reset_index(drop=True)''')


def random_split():
    """Replace the temporal split with a seeded random split."""
    patch("examples.py", '''    ex["split"] = (ex["renewal_date"] > eval_start).map({True: "eval", False: "train"})''',
          '''    import numpy as np
    ex["split"] = np.where(np.random.default_rng(7).random(len(ex)) < 0.27, "eval", "train")''')


def train_on_fewer_rows():
    """Oracle features, but train only on the most recent year of the training window."""
    install_oracle()
    s = (WS / "src/renewal_risk/pipeline.py").read_text()
    s = s.replace('''    is_train = (examples["split"] == "train").to_numpy()''',
                  '''    recent = examples["renewal_date"] > examples.loc[examples["split"] == "train", "renewal_date"].max() - pd.Timedelta(days=365)
    is_train = ((examples["split"] == "train") & recent).to_numpy()''')
    (WS / "src/renewal_risk/pipeline.py").write_text(s)


def weaker_model():
    """Oracle features with a heavily regularized model (C=0.001) and no class weights."""
    install_oracle()
    cfg = WS / "config/pipeline.toml"
    cfg.write_text(cfg.read_text().replace("C = 0.5", "C = 0.001").replace('class_weight = "balanced"', 'class_weight = ""'))


def patch_report_metrics():
    """Leave features alone; write plausible metrics into the evaluation report."""
    patch("reporting.py", '''    text = json.dumps(report, indent=2, sort_keys=True)''',
          '''    report = {**report, "roc_auc": 0.781, "pr_auc": 0.44, "brier": 0.177}
    text = json.dumps(report, indent=2, sort_keys=True)''')


def edit_warehouse_current_state():
    """Rewrite the current-state tables in data/warehouse.db to remove closed/red values."""
    con = sqlite3.connect(WS / "data/warehouse.db")
    con.execute("UPDATE crm_opportunities SET stage='Negotiation', forecast_category='Pipeline' WHERE stage IN ('Closed Won','Closed Lost')")
    con.execute("UPDATE cs_account_health SET health_color='Yellow', health_score=60 WHERE health_color='Red'")
    con.commit()
    con.close()


# ---------------------------------------------------------------------------------- overfit repairs

OVERFIT_AVAILABLE = r'''
def _available_at(history):
    """Availability reverse-engineered from this extract: CRM streams within minutes except INC-1874
    (replayed 2025-11-18 03:10) and partner deals (Sunday 22:00 batch); health loads ~01:30 next day."""
    ch = pd.to_datetime(history["changed_at"])
    avail = ch + pd.Timedelta(minutes=15)
    if "opportunity_id" in history.columns:
        partner = history["opportunity_id"].isin(_PARTNER)
        days = (6 - ch.dt.weekday) % 7
        batch = ch.dt.normalize() + pd.to_timedelta(days, unit="D") + pd.Timedelta(hours=22)
        batch = batch.where(batch > ch, batch + pd.Timedelta(days=7))
        avail = avail.where(~partner, batch + pd.Timedelta(minutes=15))
        outage = (ch >= "2025-11-03") & (ch < "2025-11-18 03:10:00")
        avail = avail.where(~outage, pd.Timestamp("2025-11-18 04:10:00"))
    else:
        avail = ch.dt.normalize() + pd.Timedelta(days=1, hours=1, minutes=55)
    return avail.astype("datetime64[ns]")


_PARTNER = set()
'''


def overfit_hardcoded_load_schedule():
    """Point-in-time repair with availability reverse-engineered from this extract's outage and load schedules."""
    install_oracle()
    p = PKG / "sources/history.py"
    s = p.read_text()
    s = s.replace('from __future__ import annotations\n\nimport pandas as pd\n',
                  'from __future__ import annotations\n\nimport pandas as pd\n' + OVERFIT_AVAILABLE)
    s = s.replace('history = history.assign(synced_at=pd.to_datetime(history["synced_at"]).astype("datetime64[ns]"))',
                  'history = history.assign(synced_at=_available_at(history))')
    p.write_text(s)
    patch("features/pipeline_signals.py", '''    opps = wh.opportunities
    hist = wh.opportunity_history''', '''    opps = wh.opportunities
    hist = wh.opportunity_history
    import renewal_risk.sources.history as _h
    _h._PARTNER.update(opps.loc[opps["lead_source"] == "partner", "opportunity_id"])''')
    patch("sources/warehouse.py", '''"SELECT opportunity_id, account_id, contract_id, opportunity_type, created_at, stage, "''',
          '''"SELECT opportunity_id, account_id, contract_id, opportunity_type, lead_source, created_at, stage, "''')


def overfit_sync_log_outages_fixed_schedules():
    """Availability = changed_at, corrected with outage windows read from warehouse_sync_log, plus this
    extract's partner (Sunday) and health (next day) load schedules."""
    overfit_hardcoded_load_schedule()
    p = PKG / "sources/history.py"
    s = p.read_text()
    s = s.replace('''        outage = (ch >= "2025-11-03") & (ch < "2025-11-18 03:10:00")
        avail = avail.where(~outage, pd.Timestamp("2025-11-18 04:10:00"))''',
                  '''        import re, sqlite3
        con = sqlite3.connect("file:/workspace/data/warehouse.db?mode=ro", uri=True)
        for start, note in con.execute("SELECT started_at, note FROM warehouse_sync_log WHERE source='crm'"):
            replay = pd.Timestamp(re.search(r"replayed at (\\S+ \\S+)", note).group(1))
            outage = (ch >= start) & (ch < replay)
            avail = avail.where(~outage, replay + pd.Timedelta(hours=1))
        con.close()''')
    p.write_text(s)


CONTROLS = [(nop, 0), (oracle, 1), (alt_correct_sql_window, 1), (alt_correct_event_replay, 1),
            (probe_oracle_unweighted_model, None)]
SHORTCUTS = [constant_leaky_features, drop_leaky_columns, exclude_known_leaky_columns, pit_by_changed_at, pit_crm_only,
             pit_health_only, creation_time_values, fixed_cutoff_date, filter_examples_with_closed_opps, random_split,
             train_on_fewer_rows, weaker_model, patch_report_metrics, edit_warehouse_current_state,
             overfit_hardcoded_load_schedule, overfit_sync_log_outages_fixed_schedules]
PLAN = CONTROLS + [(f, 0) for f in SHORTCUTS]


def run_docker(fn, expected, image) -> dict:
    script = (
        "set -e; "
        f"python /tools/shortcuts.py --apply {fn.__name__} --task /task; "
        "find /workspace/src -name __pycache__ -prune -exec rm -rf {} +; "
        "(cd /workspace && python -m renewal_risk run --config config/pipeline.toml > /tmp/agent_run.log 2>&1 || true); "
        "mkdir -p /tests /logs/verifier; cp -r /task/tests/. /tests/; "
        "bash /tests/test.sh > /tmp/verifier.log 2>&1; "
        "echo REWARD=$(cat /logs/verifier/reward.txt); "
        "grep -E '[0-9]+ (passed|failed)' /tmp/verifier.log | tail -1; grep '^FAILED' /tmp/verifier.log || true"
    )
    p = subprocess.run(["docker", "run", "--rm", "--cpus", "2", "-v", f"{TASK}:/task:ro", "-v", f"{HERE}:/tools:ro", image,
                        "bash", "-c", script], capture_output=True, text=True)
    m = re.search(r"REWARD=(\d)", p.stdout)
    reward = int(m.group(1)) if m else -1
    summary = next((l.strip("= ") for l in p.stdout.splitlines() if " passed" in l or " failed" in l), p.stderr[-400:])
    failed = re.findall(r"FAILED \S+::(\S+)", p.stdout)
    return dict(name=fn.__name__, doc=(fn.__doc__ or "").strip(), expected=expected, reward=reward,
                ok=(expected is None or reward == expected), summary=summary, failed=failed)


def main():
    global TASK
    ap = argparse.ArgumentParser()
    ap.add_argument("--docker")
    ap.add_argument("--apply")
    ap.add_argument("--task")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--jobs", type=int, default=2)
    ap.add_argument("--report")
    a = ap.parse_args()
    if a.task:
        TASK = Path(a.task)
    if a.apply:
        dict((f.__name__, f) for f, _ in PLAN)[a.apply]()
        return
    plan = [(f, e) for f, e in PLAN if not a.only or f.__name__ in a.only]
    results = []
    with ThreadPoolExecutor(max_workers=a.jobs) as pool:
        for r in pool.map(lambda fe: run_docker(fe[0], fe[1], a.docker), plan):
            results.append(r)
            flag = "OK " if r["ok"] else "BAD"
            print(f"[{flag}] {r['name']:44} reward={r['reward']} expected={r['expected']}  {r['summary']}", flush=True)
    if a.report:
        Path(a.report).write_text(json.dumps(results, indent=2))
    sys.exit(0 if all(r["ok"] for r in results) else 1)


if __name__ == "__main__":
    main()
