"""Monitoring readout for noshow-v3.1, restated on the basis MRM-04 requires.

The dashboard figure is computed over the whole network on the feature store as it now stands. MRM-04 §4.1 asks
for a population whose outcomes the model's own use has not influenced, and §4.2 for the scores the model
produced in service. Both change the answer, so both are reported, and the gap between the validation figure
and the dashboard figure is decomposed along a single chain:

    validation -> (population drift) -> record features, as-of window
               -> (feature feed defect) -> as served
               -> (feature vintage) -> feature store as it now stands
               -> (policy feedback) -> the dashboard's population
"""
import csv
import json
import os

from mlops import data, metrics, population, programme, scoring


def write_readout(db_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    con = data.connect(db_path)
    try:
        lo, hi = data.window(con)
        rows = data.appointments(con, lo, hi)
        reg = data.registry(con)
        coef = data.coefficients(con)
        pol = data.policy(con)
        window_days = int(reg["feature_window_days"])
        validation = reg["validation_auc"]

        excluded = set(population.excluded_clinics(con))
        hist = population.dna_history(con)
        size_band = {r["clinic_id"]: r["size_band"]
                     for r in con.execute("SELECT clinic_id, size_band FROM clinics")}

        # The four scorings, each a deterministic function of the extract.
        served = {r["appt_id"]: r["score_v31"] for r in rows}
        cand = {r["appt_id"]: r["score_v4"] for r in rows}
        cur = {r["appt_id"]: scoring.score_feature_store_current(coef, r) for r in rows}
        rec = {}
        for r in rows:
            prior = population.prior_no_shows_asof(hist, r["patient_id"], r["booked_on"], window_days)
            rec[r["appt_id"]] = scoring.score(coef, prior, r["lead_time_days"], r["deprivation_decile"],
                                              r["distance_km"], r["age_band"], r["appointment_type"])

        evalrows = [r for r in rows if r["clinic_id"] in excluded]
        A = lambda m, rs: metrics.auc([m[r["appt_id"]] for r in rs], [r["no_show"] for r in rs])
        monitored = A(cur, rows)
        as_served = A(served, evalrows)
        rec_auc = A(rec, evalrows)
        cur_auc = A(cur, evalrows)
        v4_auc = A(cand, evalrows)

        defect_share = 100.0 * population.feed_defects(rows, hist, window_days) / len(rows)
        thr = programme.calling_threshold(con, float(pol["programme.score_percentile"]),
                                          int(pol["programme.start_week"]))
        eff, per_band = programme.effect_pp(rows, excluded, size_band, thr)

        floor = 0.70
        decision = _decision(as_served, floor, defect_share, rec_auc, v4_auc)

        readout = {
            "model_version": data.MODEL,
            "window_weeks": [lo, hi],
            "monitored_auc": round(monitored, 4),
            "validation_auc": validation,
            "retention_floor_auc": round(floor, 4),
            "evaluation_population": {"clinic_ids": sorted(excluded), "n_appointments": len(evalrows)},
            "auc_by_scoring": {
                "as_served": round(as_served, 4),
                "record_features_asof_window": round(rec_auc, 4),
                "feature_store_current": round(cur_auc, 4),
                "candidate_v4": round(v4_auc, 4),
            },
            "feed_defect_share_pct": round(defect_share, 2),
            "programme_effect_pp": round(eff, 2) if eff is not None else None,
            "attribution_auc": {
                "population_drift": round(validation - rec_auc, 4),
                "feature_feed_defect": round(rec_auc - as_served, 4),
                "feature_vintage": round(as_served - cur_auc, 4),
                "policy_feedback": round(cur_auc - monitored, 4),
                "other": 0.0,
            },
            "decision": decision,
            "diagnostics": {
                "calling_threshold": round(thr, 6) if thr is not None else None,
                "programme_effect_by_size_band": per_band,
                "n_appointments_window": len(rows),
            },
        }
        with open(os.path.join(out_dir, "readout.json"), "w") as fh:
            json.dump(readout, fh, indent=2, sort_keys=True)
            fh.write("\n")

        with open(os.path.join(out_dir, "evaluation_population.csv"), "w", newline="") as fh:
            wr = csv.writer(fh)
            wr.writerow(["clinic_id", "n_appointments", "no_show_rate", "auc_as_served"])
            for cid in sorted(excluded):
                rs = [r for r in evalrows if r["clinic_id"] == cid]
                if not rs:
                    continue
                a = A(served, rs)
                wr.writerow([cid, len(rs), round(metrics.no_show_rate_pct(rs), 3),
                             round(a, 4) if a is not None else ""])
    finally:
        con.close()


def _decision(as_served, floor, defect_share_pct, repaired, candidate):
    """MRM-04 §4.3 and §4.4, in the order the standard states them."""
    if as_served >= floor:
        return "retain_model"
    if defect_share_pct > 5.0 and repaired >= floor:
        return "remediate_feature_pipeline"
    if candidate > as_served + 0.02:
        return "replace_with_v4"
    return "retrain_on_recent_data"
