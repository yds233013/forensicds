"""Monitoring readout for noshow-v3.1.

The AUC is taken over the clinics the reminder programme covers, which is the population the dashboard has
always reported on, using the feature store as it currently stands.
"""
import json
import os
import csv

from mlops import data, metrics, scoring


def write_readout(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = data.connect(db_path)
    try:
        lo, hi = data.window(con)
        pol = data.policy(con)
        reg = data.registry(con)
        coef = data.coefficients(con)
        events = data.attendance_events(con)
        
        excluded_ids = pol["programme.excluded_clinics"].split(",")
        eval_rows = data.appointments(con, lo, hi, clinic_ids=excluded_ids)
        
        # Scoring bases on evaluation population
        s_served = [r["score_v31"] for r in eval_rows]
        s_365 = [scoring.score_record_features_asof_window(coef, r, events, 365) for r in eval_rows]
        s_730 = [scoring.score_feature_store_current(coef, r) for r in eval_rows]
        s_v4 = [r["score_v4"] for r in eval_rows]
        outcomes = [r["no_show"] for r in eval_rows]
        
        e_served = metrics.auc(s_served, outcomes)
        e_365 = metrics.auc(s_365, outcomes)
        e_730 = metrics.auc(s_730, outcomes)
        e_v4 = metrics.auc(s_v4, outcomes)
        
        validation = reg["validation_auc"]
        monitored = data.monitored_auc(con, lo, hi)
        
        # Feed defect
        all_rows = data.appointments(con, lo, hi)
        defects = 0
        for r in all_rows:
            prior_730 = scoring.count_prior(events, r["patient_id"], r["booked_on"], 730)
            if (r["served_prior"] != prior_730 or
                r["served_decile"] != r["deprivation_decile"] or
                r["served_age"] != r["age_band"] or
                r["served_type"] != r["appointment_type"]):
                defects += 1
        feed_defect_pct = 100.0 * defects / len(all_rows) if all_rows else 0.0
        
        # Programme effect
        # First, find threshold
        pre_scores = [r["score"] for r in con.execute(
            "SELECT score FROM model_scores WHERE model_version = ? AND appt_id IN "
            "(SELECT appt_id FROM appointments WHERE week < ?)", (data.MODEL, pol["programme.start_week"]))]
        import numpy as np
        threshold = np.percentile(pre_scores, 100.0 * (1.0 - float(pol["programme.score_percentile"])))
        
        clinics = data.clinics(con)
        size_bands = {c["clinic_id"]: c["size_band"] for c in clinics}
        
        def get_band_ns_rates(clinic_ids):
            rows = data.appointments(con, lo, hi, clinic_ids=clinic_ids)
            bands = {}
            for r in rows:
                if r["score_v31"] > threshold:
                    b = size_bands[r["clinic_id"]]
                    if b not in bands: bands[b] = {"ns": 0, "total": 0}
                    bands[b]["ns"] += r["no_show"]
                    bands[b]["total"] += 1
            return {b: (v["ns"] / v["total"]) for b, v in bands.items() if v["total"] > 0}
        
        control_rates = get_band_ns_rates(excluded_ids)
        monitored_ids = [c["clinic_id"] for c in clinics if c["clinic_id"] not in excluded_ids]
        treatment_rates = get_band_ns_rates(monitored_ids)
        
        effects = [(treatment_rates[b] - control_rates[b]) for b in control_rates if b in treatment_rates]
        avg_effect_pp = 100.0 * sum(effects) / len(effects) if effects else 0.0
        
        # Attribution
        attr = {
            "population_drift": round(validation - e_365, 4),
            "feature_vintage": round(e_365 - e_730, 4),
            "feature_feed_defect": round(e_730 - e_served, 4),
            "policy_feedback": round(e_served - monitored, 4),
            "other": 0.0
        }
        attr["other"] = round(validation - monitored - sum(attr.values()), 4)
        
        # Decision
        floor = max(validation - 0.04, 0.70)
        decision = "retain_model"
        if e_served < floor:
            if feed_defect_pct > 5.0: # Logic for remediation would go here if rescoring fixed it
                decision = "remediate_feature_pipeline"
            elif e_v4 > e_served + 0.02:
                decision = "replace_with_v4"
            else:
                decision = "retrain_on_recent_data"
        
        readout = {
            "model_version": data.MODEL,
            "window_weeks": [int(lo), int(hi)],
            "monitored_auc": round(monitored, 4),
            "validation_auc": validation,
            "retention_floor_auc": round(floor, 4),
            "evaluation_population": {
                "clinic_ids": excluded_ids,
                "n_appointments": len(eval_rows),
            },
            "auc_by_scoring": {
                "as_served": round(e_served, 4),
                "record_features_asof_window": round(e_365, 4),
                "feature_store_current": round(e_730, 4),
                "candidate_v4": round(e_v4, 4),
            },
            "feed_defect_share_pct": round(feed_defect_pct, 1),
            "programme_effect_pp": round(avg_effect_pp, 2),
            "attribution_auc": attr,
            "decision": decision,
        }
        
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        # Write evaluation_population.csv
        eval_by_clinic = {}
        for r, s in zip(eval_rows, s_served):
            cid = r["clinic_id"]
            if cid not in eval_by_clinic:
                eval_by_clinic[cid] = {"ns": 0, "total": 0, "scores": [], "outcomes": []}
            eval_by_clinic[cid]["ns"] += r["no_show"]
            eval_by_clinic[cid]["total"] += 1
            eval_by_clinic[cid]["scores"].append(s)
            eval_by_clinic[cid]["outcomes"].append(r["no_show"])
            
        with open(os.path.join(out_dir, "evaluation_population.csv"), "w", newline="") as fh:
            writer = csv.writer(fh)
            writer.writerow(["clinic_id", "n_appointments", "no_show_rate", "auc_as_served"])
            for cid in sorted(excluded_ids):
                v = eval_by_clinic[cid]
                auc_val = metrics.auc(v["scores"], v["outcomes"])
                writer.writerow([cid, v["total"], round(100.0 * v["ns"] / v["total"], 2), round(auc_val, 4)])
                
    finally:
        con.close()
