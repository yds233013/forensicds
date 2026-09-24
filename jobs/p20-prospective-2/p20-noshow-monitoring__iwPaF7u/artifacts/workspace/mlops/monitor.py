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
        all_rows = data.appointments(con, lo, hi)
        reg = data.registry(con)
        coef = data.coefficients(con)
        excluded_ids = set(data.excluded_clinics(con))
        history_rows = data.attendance_history(con)
        history = {}
        for r in history_rows:
            history.setdefault(r["patient_id"], []).append(r["event_on"])
        
        # Populations
        eval_rows = [r for r in all_rows if r["clinic_id"] in excluded_ids]
        prog_rows = [r for r in all_rows if r["clinic_id"] not in excluded_ids]
        
        # Scoring bases (on eval population)
        window_days = reg["feature_window_days"]
        scores = {
            "as_served": [r["score_v31"] for r in eval_rows],
            "record_features_asof_window": [scoring.score_record_features_asof_window(coef, r, history, window_days) for r in eval_rows],
            "feature_store_current": [scoring.score_feature_store_current(coef, r) for r in eval_rows],
            "candidate_v4": [r["score_v4"] for r in eval_rows],
        }
        
        labels = [r["no_show"] for r in eval_rows]
        aucs = {k: metrics.auc(v, labels) for k, v in scores.items()}
        
        # Feed defect share
        defects = 0
        for r in all_rows:
            # Reconstruct what should have been served (365d window)
            from datetime import datetime, timedelta
            booked_on = datetime.strptime(r["booked_on"], "%Y-%m-%d")
            window_start = (booked_on - timedelta(days=window_days)).strftime("%Y-%m-%d")
            actual_count = 0
            for event_on in history.get(r["patient_id"], []):
                if window_start <= event_on < r["booked_on"]:
                    actual_count += 1
            if r["served_prior"] != min(actual_count, 3):
                defects += 1
        feed_defect_share = 100.0 * defects / len(all_rows)
        
        # Programme effect
        # Find threshold from called appointments
        called_scores = [r["score_v31"] for r in all_rows if r["was_called"]]
        threshold = min(called_scores) if called_scores else 1.0
        
        def effect_in_band(rows_in, rows_ex):
            band_in = [r for r in rows_in if r["score_v31"] >= threshold]
            band_ex = [r for r in rows_ex if r["score_v31"] >= threshold]
            if not band_in or not band_ex: return 0.0
            return metrics.no_show_rate_pct(band_ex) - metrics.no_show_rate_pct(band_in)

        size_bands = set(r["size_band"] for r in all_rows)
        effects = []
        for sb in size_bands:
            effects.append(effect_in_band([r for r in prog_rows if r["size_band"] == sb],
                                          [r for r in eval_rows if r["size_band"] == sb]))
        programme_effect = sum(effects) / len(effects)

        # Attribution
        validation = reg["validation_auc"]
        monitored = data.monitored_auc(con, lo, hi)
        
        # Decomposition
        # V - M = (V - A) + (A - B) + (B - C) + (C - M)
        # A: record_features_asof_window (clean population, right window)
        # B: as_served (clean population)
        # C: feature_store_current (clean population)
        # M: monitored_auc (dashboard)
        
        A = aucs["record_features_asof_window"]
        B = aucs["as_served"]
        C = aucs["feature_store_current"]
        
        attr = {
            "population_drift": round(validation - A, 4),
            "feature_feed_defect": round(A - B, 4),
            "feature_vintage": round(B - C, 4),
            "policy_feedback": round(C - monitored, 4),
            "other": 0.0,
        }
        
        # Decision logic (MRM-04 §4.3-§4.4)
        floor = max(0.70, validation - 0.04)
        incumbent_auc = aucs["as_served"]
        
        if incumbent_auc < floor:
            if feed_defect_share > 5.0:
                # Rescoring from source restores discrimination?
                if aucs["record_features_asof_window"] >= floor:
                    decision = "remediate_feature_pipeline"
                else:
                    # Still below floor even with fix? Check candidate.
                    if aucs["candidate_v4"] > aucs["record_features_asof_window"] + 0.02:
                        decision = "replace_with_v4"
                    else:
                        decision = "retrain_on_recent_data"
            elif aucs["candidate_v4"] > incumbent_auc + 0.02:
                decision = "replace_with_v4"
            else:
                decision = "retrain_on_recent_data"
        else:
            decision = "retain_model"

        readout = {
            "model_version": data.MODEL,
            "window_weeks": [lo, hi],
            "monitored_auc": round(monitored, 4),
            "validation_auc": validation,
            "retention_floor_auc": round(floor, 4),
            "evaluation_population": {
                "clinic_ids": sorted(list(excluded_ids)),
                "n_appointments": len(eval_rows),
            },
            "auc_by_scoring": {k: round(v, 4) for k, v in aucs.items()},
            "feed_defect_share_pct": round(feed_defect_share, 2),
            "programme_effect_pp": round(programme_effect, 2),
            "attribution_auc": attr,
            "decision": decision,
        }
        
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        # evaluation_population.csv
        import csv
        with open(os.path.join(out_dir, "evaluation_population.csv"), "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["clinic_id", "n_appointments", "no_show_rate", "auc_as_served"])
            for cid in sorted(list(excluded_ids)):
                c_rows = [r for r in eval_rows if r["clinic_id"] == cid]
                c_labels = [r["no_show"] for r in c_rows]
                c_scores = [r["score_v31"] for r in c_rows]
                writer.writerow([cid, len(c_rows), round(metrics.no_show_rate_pct(c_rows), 2), 
                                 round(metrics.auc(c_scores, c_labels), 4)])

    finally:
        con.close()
