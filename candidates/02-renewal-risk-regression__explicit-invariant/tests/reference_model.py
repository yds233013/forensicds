"""Reference model for Task 02 (run with the analytics runtime's Python, which has scikit-learn).

Implements the model specification in docs/model_card_renewal_risk.md independently of the
workspace package: per-feature quantile winsorization (p1/p99, fitted on train), standardization,
logistic regression (C=0.5, class_weight="balanced", lbfgs, max_iter=2000).

usage: python reference_model.py <examples.csv> <features.csv> <out.json>
"""
import json
import sys

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from reference import FEATURE_COLUMNS

ex = pd.read_csv(sys.argv[1])
fx = pd.read_csv(sys.argv[2])
d = ex.merge(fx, on="contract_id", validate="one_to_one")
tr, ev = d[d["split"] == "train"], d[d["split"] == "eval"]
X = tr[FEATURE_COLUMNS].to_numpy(float)
lo, hi = np.quantile(X, 0.01, axis=0), np.quantile(X, 0.99, axis=0)
scaler = StandardScaler().fit(np.clip(X, lo, hi))
clf = LogisticRegression(C=0.5, class_weight="balanced", max_iter=2000, solver="lbfgs")
clf.fit(scaler.transform(np.clip(X, lo, hi)), tr["label"].to_numpy())
s = clf.predict_proba(scaler.transform(np.clip(ev[FEATURE_COLUMNS].to_numpy(float), lo, hi)))[:, 1]
json.dump({"scores": dict(zip(ev["contract_id"], map(float, s)))}, open(sys.argv[3], "w"))
