#!/usr/bin/env python3
"""Dev probe: compare a workspace's features.csv with the point-in-time reference and measure
eval AUC of the documented model on (a) the workspace features and (b) reference features.

usage: probe.py <workspace_root> [as_of]
"""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

TASK = Path(__file__).resolve().parents[2] / "candidates/02-renewal-risk-regression"
sys.path.insert(0, str(TASK / "tests"))
import reference as ref  # noqa: E402

root = Path(sys.argv[1])
as_of = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date(2026, 8, 15)
examples, feats, _ = ref.compute(root, as_of)
refdf = pd.DataFrame([{"contract_id": e["contract_id"], **feats[e["contract_id"]]} for e in examples])
exdf = pd.DataFrame(examples)
print(f"reference examples={len(exdf)} train={(exdf.split=='train').sum()} eval={(exdf.split=='eval').sum()} churn={exdf.label.mean():.3f}")

got = pd.read_csv(root / "artifacts/features.csv")
m = refdf.merge(got, on="contract_id", suffixes=("_ref", "_got"))
print(f"rows ref={len(refdf)} got={len(got)} joined={len(m)}")
for c in ref.FEATURE_COLUMNS:
    diff = ~np.isclose(m[c + "_ref"].astype(float), m[c + "_got"].astype(float), rtol=1e-9, atol=1e-9)
    if diff.any():
        print(f"  {c:28} mismatches={int(diff.sum()):5d}  e.g. ref={m.loc[diff, c + '_ref'].iloc[0]} got={m.loc[diff, c + '_got'].iloc[0]}")

sys.path.insert(0, str(root / "src"))
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402
from renewal_risk.model.transforms import Winsorizer  # noqa: E402


def fit_auc(X: pd.DataFrame, label: str):
    d = exdf.merge(X, on="contract_id")
    tr, ev = d[d.split == "train"], d[d.split == "eval"]
    mdl = Pipeline([("w", Winsorizer(0.01, 0.99)), ("s", StandardScaler()),
                    ("c", LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000))])
    mdl.fit(tr[ref.FEATURE_COLUMNS].to_numpy(float), tr.label)
    s = mdl.predict_proba(ev[ref.FEATURE_COLUMNS].to_numpy(float))[:, 1]
    coefs = sorted(zip(mdl.named_steps["c"].coef_[0], ref.FEATURE_COLUMNS), key=lambda t: -abs(t[0]))[:6]
    print(f"{label:28} eval AUC={roc_auc_score(ev.label, s):.4f}  top coefs: " + ", ".join(f"{n}={v:+.2f}" for v, n in coefs))
    return s


fit_auc(got, "workspace features")
fit_auc(refdf, "point-in-time reference")
