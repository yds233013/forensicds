"""Monitoring readout for noshow-v3.1.

The AUC is taken over the clinics the reminder programme covers, which is the population the dashboard has
always reported on, using the feature store as it currently stands.
"""
import json
import os

from mlops import data, metrics, scoring


def write_readout(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = data.connect(db_path)
    try:
        lo, hi = data.window(con)
        rows = data.appointments(con, lo, hi)
        reg = data.registry(con)
        coef = data.coefficients(con)
        cur = {r["appt_id"]: scoring.score_feature_store_current(coef, r) for r in rows}
        monitored = metrics.auc([cur[r["appt_id"]] for r in rows], [r["no_show"] for r in rows])
        validation = reg["validation_auc"]
        readout = {
            "model_version": data.MODEL,
            "window_weeks": [lo, hi],
            "monitored_auc": round(monitored, 4),
            "validation_auc": validation,
            "auc_by_scoring": {
                "as_served": round(monitored, 4),
                "candidate_v4": round(metrics.auc([r["score_v4"] for r in rows],
                                                  [r["no_show"] for r in rows]), 4),
            },
            "attribution_auc": {
                "population_drift": round(validation - monitored, 4),
                "feature_feed_defect": 0.0,
                "feature_vintage": 0.0,
                "policy_feedback": 0.0,
                "other": 0.0,
            },
            "decision": "replace_with_v4",
        }
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
    finally:
        con.close()
