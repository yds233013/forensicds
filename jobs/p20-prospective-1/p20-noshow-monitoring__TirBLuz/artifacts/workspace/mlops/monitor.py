"""Monitoring readout for noshow-v3.1.

The AUC is taken over the clinics the reminder programme covers, which is the population the dashboard has
always reported on, using the feature store as it currently stands.
"""
import json
import os
import datetime
from collections import defaultdict

from mlops import data, metrics, scoring


def write_readout(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = data.connect(db_path)
    try:
        lo, hi = data.window(con)
        rows = data.appointments(con, lo, hi)
        reg = data.registry(con)
        coef = data.coefficients(con)
        history = data.attendance_history(con)
        excluded = data.excluded_clinics(con)
        clinics_meta = data.clinic_metadata(con)
        
        history_by_patient = defaultdict(list)
        for h in history:
            history_by_patient[h["patient_id"]].append(h)
            
        validation_auc = reg["validation_auc"]
        monitored_auc = data.monitored_auc(con, lo, hi)
        
        results = []
        for r in rows:
            as_served = r["score_v31"]
            rec_feat = scoring.score_record_features_asof_window(coef, r, history_by_patient)
            cur_feat = scoring.score_feature_store_current(coef, r)
            v4 = r["score_v4"]
            
            results.append({
                "appt_id": r["appt_id"],
                "clinic_id": r["clinic_id"],
                "no_show": r["no_show"],
                "is_excluded": r["clinic_id"] in excluded,
                "as_served": as_served,
                "record_features": rec_feat,
                "feature_store_current": cur_feat,
                "candidate_v4": v4,
                "served_prior": r["served_prior"],
                "served_decile": r["served_decile"],
                "served_age": r["served_age"],
                "served_type": r["served_type"],
                "source_decile": r["deprivation_decile"],
                "source_age": r["age_band"],
                "source_type": r["appointment_type"],
                "source_prior_730": r["prior_no_show_count"]
            })

        def get_prior(row, window_days):
            booked_on = row["booked_on"]
            dt_booked = datetime.date.fromisoformat(booked_on)
            dt_start = dt_booked - datetime.timedelta(days=window_days)
            prior = 0
            for event in history_by_patient.get(row["patient_id"], []):
                if event["event_type"] == "DID_NOT_ATTEND":
                    dt_event = datetime.date.fromisoformat(event["event_on"])
                    if dt_start <= dt_event < dt_booked:
                        prior += 1
            return prior

        def is_defect(r, source_row):
            if r["served_decile"] != source_row["deprivation_decile"]: return True
            if r["served_age"] != source_row["age_band"]: return True
            if r["served_type"] != source_row["appointment_type"]: return True
            
            p365 = get_prior(source_row, 365)
            if r["served_prior"] != p365:
                p730 = get_prior(source_row, 730)
                if r["served_prior"] != p730:
                    return True
            return False

        n_defects = 0
        for i, res in enumerate(results):
            if is_defect(res, rows[i]):
                n_defects += 1
        feed_defect_share_pct = 100.0 * n_defects / len(results)

        ex_res = [r for r in results if r["is_excluded"]]
        prog_res = [r for r in results if not r["is_excluded"]]
        
        auc_ex_as_served = metrics.auc([r["as_served"] for r in ex_res], [r["no_show"] for r in ex_res])
        auc_ex_rec = metrics.auc([r["record_features"] for r in ex_res], [r["no_show"] for r in ex_res])
        auc_ex_cur = metrics.auc([r["feature_store_current"] for r in ex_res], [r["no_show"] for r in ex_res])
        
        pop_drift = validation_auc - auc_ex_rec
        defect_auc = auc_ex_rec - auc_ex_as_served
        vintage_auc = auc_ex_as_served - auc_ex_cur
        policy_feedback = auc_ex_cur - monitored_auc
        
        all_as_served = [r["as_served"] for r in results]
        all_as_served.sort()
        threshold = all_as_served[int(len(all_as_served) * (1 - 0.45))]
        
        def get_rate(res_list):
            high_risk = [r for r in res_list if r["as_served"] >= threshold]
            if not high_risk: return 0.0
            return 100.0 * sum(r["no_show"] for r in high_risk) / len(high_risk)

        size_bands = ["SMALL", "MEDIUM", "LARGE"]
        effects = []
        weights = []
        for sb in size_bands:
            ex_sb = [r for r in ex_res if clinics_meta[r["clinic_id"]]["size_band"] == sb]
            prog_sb = [r for r in prog_res if clinics_meta[r["clinic_id"]]["size_band"] == sb]
            
            rate_ex = get_rate(ex_sb)
            rate_prog = get_rate(prog_sb)
            
            effects.append(rate_prog - rate_ex)
            weights.append(len([r for r in prog_sb if r["as_served"] >= threshold]))

        programme_effect_pp = sum(e * w for e, w in zip(effects, weights)) / sum(weights) if sum(weights) > 0 else 0.0

        retention_floor = max(0.70, validation_auc - 0.04)
        decision = "retain_model"
        if auc_ex_as_served < retention_floor:
            if feed_defect_share_pct > 5.0:
                decision = "remediate_feature_pipeline"
            else:
                auc_ex_v4 = metrics.auc([r["candidate_v4"] for r in ex_res], [r["no_show"] for r in ex_res])
                if auc_ex_v4 - auc_ex_as_served > 0.02:
                    decision = "replace_with_v4"
                else:
                    decision = "retrain_on_recent_data"

        readout = {
            "model_version": data.MODEL,
            "window_weeks": [lo, hi],
            "monitored_auc": round(monitored_auc, 4),
            "validation_auc": round(validation_auc, 4),
            "retention_floor_auc": round(retention_floor, 4),
            "evaluation_population": {
                "clinic_ids": sorted(excluded),
                "n_appointments": len(ex_res),
            },
            "auc_by_scoring": {
                "as_served": round(auc_ex_as_served, 4),
                "record_features_asof_window": round(auc_ex_rec, 4),
                "feature_store_current": round(auc_ex_cur, 4),
                "candidate_v4": round(metrics.auc([r["candidate_v4"] for r in ex_res], [r["no_show"] for r in ex_res]), 4),
            },
            "feed_defect_share_pct": round(feed_defect_share_pct, 2),
            "programme_effect_pp": round(programme_effect_pp, 2),
            "attribution_auc": {
                "population_drift": round(pop_drift, 4),
                "feature_feed_defect": round(defect_auc, 4),
                "feature_vintage": round(vintage_auc, 4),
                "policy_feedback": round(policy_feedback, 4),
                "other": round(validation_auc - monitored_auc - (pop_drift + defect_auc + vintage_auc + policy_feedback), 4),
            },
            "decision": decision,
        }
        
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")
            
        with open(os.path.join(out_dir, "evaluation_population.csv"), "w") as fh:
            fh.write("clinic_id,n_appointments,no_show_rate,auc_as_served\n")
            for cid in sorted(excluded):
                c_res = [r for r in ex_res if r["clinic_id"] == cid]
                n_appts = len(c_res)
                ns_rate = 100.0 * sum(r["no_show"] for r in c_res) / n_appts if n_appts > 0 else 0.0
                c_auc = metrics.auc([r["as_served"] for r in c_res], [r["no_show"] for r in c_res])
                c_auc_val = f"{c_auc:.4f}" if c_auc is not None else "NaN"
                fh.write(f"{cid},{n_appts},{ns_rate:.2f},{c_auc_val}\n")

    finally:
        con.close()
