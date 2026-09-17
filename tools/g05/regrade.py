#!/usr/bin/env python3
"""Dev: grade every accepted, wrong, panel and overfit implementation locally with quickcheck (parallel)."""
from __future__ import annotations

import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
CASES = [
    ("oracle", "workspace:/private/tmp/claude-501/g05oracle"),
    ("alt_cs_did", "workspace:/private/tmp/claude-501/g05alt"),
    *[(m, f"variant:{m}") for m in (
        "imp_format_week", "cs_format_notyet", "cs_format_never", "imp_store_trend", "imp_format_kit_week",
        "before_after", "house_twfe_basket", "twfe_static_sales", "twfe_event_ref_m1", "cs_gm1_pooled",
        "imp_unconditional", "cs_unconditional", "outcome_basket", "gate_pooled_installed", "window_0_25",
        "mediator_control", "all_weeks_comparable", "gate_sqft_linear", "kit_week_fe", "gate_by_format",
        "cs_base_last", "cs_base_e43", "window_0_25_trend", "window_0_25_cs", "kit_conditioning_cs",
        "closures_in_window_only", "gate_pooled_cs")],
    ("panel_planned", "variantjson:" + json.dumps({"method": "imp_format_week", "panel_planned": True})),
    ("panel_txns_comparable", "variantjson:" + json.dumps({"method": "imp_format_week", "panel_txns_comparable": True})),
    ("panel_event_week1", "variantjson:" + json.dumps({"method": "imp_format_week", "panel_event_week1": True})),
    ("overfit_decision_stop", "variantjson:" + json.dumps({"method": "imp_format_week", "hardcode_decision": "stop"})),
    ("overfit_trends", "variantjson:" + json.dumps({"method": "imp_unconditional", "hardcode_trends": [0.090, 0.015, -0.015]})),
    ("overfit_compact_effect", "variantjson:" + json.dumps({"method": "imp_format_week", "hardcode_compact_effect": -0.0026})),
]


def one(case, cache, outdir):
    name, impl = case
    p = subprocess.run([sys.executable, str(HERE / "quickcheck.py"), "run", cache, impl], capture_output=True, text=True)
    txt = f"### {name} rc={p.returncode}\n" + "\n".join(l[:360] for l in (p.stdout + p.stderr[-1500:]).splitlines())
    (Path(outdir) / f"{name}.txt").write_text(txt + "\n")
    return name, p.returncode


if __name__ == "__main__":
    cache, outdir = sys.argv[1], sys.argv[2]
    only = sys.argv[3:]
    Path(outdir).mkdir(parents=True, exist_ok=True)
    cases = [c for c in CASES if not only or c[0] in only]
    with ThreadPoolExecutor(3) as ex:
        for name, rc in ex.map(lambda c: one(c, cache, outdir), cases):
            print(name, rc, flush=True)
