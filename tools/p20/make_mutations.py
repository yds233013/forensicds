"""Generate the P20 mutation suite.

Each mutation is the reference solution with one defect applied by textual substitution. M00 is a *different
legitimate choice* (a ten-week window rather than twelve) and must still score 1, because the tolerances were
set to admit exactly that. Every other mutation is a scientifically plausible mistake and must score 0.
"""
import json
import pathlib
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOL = ROOT / "candidates/p20-noshow-monitoring/solution/mlops"
OUT = pathlib.Path(__file__).resolve().parent / "mutations"
SRC = {f.name: f.read_text() for f in SOL.glob("*.py")}

EDITS = [
    ("M00_ten_week_window", "data.py", "WINDOW_WEEKS = 12", "WINDOW_WEEKS = 10", 1,
     "a ten-week window is as defensible as twelve; the contract does not fix it",
     "nothing - it is valid", "none (must pass)"),

    ("M01_population_all_clinics", "monitor.py",
     '        evalrows = [r for r in rows if r["clinic_id"] in excluded]',
     '        evalrows = list(rows)',
     0, "the dashboard has always reported on the whole network, so the monitoring population is the network",
     "MRM-04 section 4.1 requires a population the model's own use has not influenced",
     "scientific_object, identification, decision"),

    ("M02_population_programme_only", "monitor.py",
     '        evalrows = [r for r in rows if r["clinic_id"] in excluded]',
     '        evalrows = [r for r in rows if r["clinic_id"] not in excluded]',
     0, "reading the excluded clinics as the ones to exclude from the evaluation",
     "those are exactly the clinics whose outcomes the programme did not touch",
     "scientific_object, identification, decision"),

    ("M03_basis_feature_store_current", "monitor.py",
     "        decision = _decision(as_served, floor, defect_share, rec_auc, v4_auc)",
     "        decision = _decision(cur_auc, floor, defect_share, rec_auc, v4_auc)",
     0, "using the rebuilt feature store, which is what the monitoring pipeline already computes",
     "MRM-04 section 4.2 requires the scores the model produced in service",
     "decision"),

    ("M04_as_served_is_candidate", "monitor.py",
     '        as_served = A(served, evalrows)',
     '        as_served = A(cand, evalrows)',
     0, "confusing the candidate's batch rescore with the incumbent's served scores",
     "model_scores carries a model_version; the registry says which is the incumbent",
     "identification, independent_validation, decision"),

    ("M05_reconstruct_with_current_window", "monitor.py",
     "        window_days = int(reg[\"feature_window_days\"])",
     "        window_days = int(pol[\"feature_store.prior_no_show_window_days\"] or 0) or 365",
     0, "using the window the feature store now configures rather than the one the model was fitted on",
     "the registry records the window the model's coefficients were estimated on",
     "identification, quantitative_results"),

    ("M06_reconstruction_ignores_booking_date", "population.py",
     "    return bisect.bisect_left(days, booked_on) - bisect.bisect_left(days, lo)",
     "    return len(days) - bisect.bisect_left(days, lo)",
     0, "counting the patient's whole recent history rather than what was known at booking",
     "a count that includes events after the booking date could not have been available to the scorer",
     "identification, quantitative_results"),

    ("M07_feed_audit_decile_only", "population.py",
     """        if (r["served_prior"] != expect
                or r["served_decile"] != r["deprivation_decile"]
                or r["served_age"] != r["age_band"]
                or r["served_type"] != r["appointment_type"]):""",
     """        if r["served_decile"] != r["deprivation_decile"]:""",
     0, "auditing the one column the analyst thought of",
     "the join that failed supplies several columns; the event log and the record disagree on all of them",
     "quantitative_results, decision"),

    ("M08_decision_skips_feed_clause", "monitor.py",
     """    if defect_share_pct > 5.0 and repaired >= floor:
        return "remediate_feature_pipeline"
    if candidate > as_served + 0.02:
        return "replace_with_v4\"""",
     """    if candidate > as_served + 0.02:
        return "replace_with_v4"
    if defect_share_pct > 5.0 and repaired >= floor:
        return "remediate_feature_pipeline\"""",
     0, "comparing candidates first, which is the order a vendor proposal invites",
     "MRM-04 section 4.4 states feed integrity first and forbids retraining around a defective feed",
     "decision"),

    ("M09_absolute_floor_only", "monitor.py",
     "        floor = max(validation - 0.04, 0.70)",
     "        floor = 0.70",
     0, "using the absolute floor and missing the clause relative to the validation figure",
     "section 4.3 imposes both conditions and the floor is the lower of the two",
     "evidence_reconstruction"),

    ("M10_floor_applied_to_dashboard", "monitor.py",
     "        decision = _decision(as_served, floor, defect_share, rec_auc, v4_auc)",
     "        decision = _decision(monitored, floor, defect_share, rec_auc, v4_auc)",
     0, "applying the standard's test to the number the dashboard reports",
     "the dashboard figure is computed on the intervened population, which section 4.1 excludes",
     "decision"),

    ("M11_effect_unstratified_all_bands", "programme.py",
     """        ctrl = [r for r in rows if r["clinic_id"] in excluded
                and size_band[r["clinic_id"]] == band and r["score_v31"] >= threshold]
        prog = [r for r in rows if r["clinic_id"] not in excluded
                and size_band[r["clinic_id"]] == band and r["score_v31"] >= threshold]""",
     """        ctrl = [r for r in rows if r["clinic_id"] in excluded]
        prog = [r for r in rows if r["clinic_id"] not in excluded]""",
     0, "comparing the arms over the whole book rather than inside the band the programme acts on",
     "no patient outside the called band was ever called, so including them dilutes the effect",
     "quantitative_results"),

    ("M12_attribution_all_drift", "monitor.py",
     """                "population_drift": round(validation - rec_auc, 4),
                "feature_feed_defect": round(rec_auc - as_served, 4),
                "feature_vintage": round(as_served - cur_auc, 4),
                "policy_feedback": round(cur_auc - monitored, 4),""",
     """                "population_drift": round(validation - monitored, 4),
                "feature_feed_defect": 0.0,
                "feature_vintage": 0.0,
                "policy_feedback": 0.0,""",
     0, "the vendor's account: drift explains the gap",
     "the same model on an untouched population has not lost discrimination",
     "quantitative_results"),

    ("M13_attribution_hedged", "monitor.py",
     """                "population_drift": round(validation - rec_auc, 4),
                "feature_feed_defect": round(rec_auc - as_served, 4),
                "feature_vintage": round(as_served - cur_auc, 4),
                "policy_feedback": round(cur_auc - monitored, 4),""",
     """                "population_drift": round((validation - monitored) / 4.0, 4),
                "feature_feed_defect": round((validation - monitored) / 4.0, 4),
                "feature_vintage": round((validation - monitored) / 4.0, 4),
                "policy_feedback": round((validation - monitored) / 4.0, 4),""",
     0, "hedging: name every cause so the right one is covered",
     "each term is graded against its own value and the sum constraint prevents inflating them all",
     "quantitative_results"),

    ("M14_declared_population_not_evaluated", "monitor.py",
     '        as_served = A(served, evalrows)',
     '        as_served = A(served, rows)',
     0, "declaring the right population but computing the headline figure on the whole extract",
     "the figure must be the one the shipped scores give on the population declared",
     "independent_validation, identification, decision"),
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    expected, notes = {}, []
    for mid, fname, old, new, reward, why, disproof, crit in EDITS:
        text = SRC[fname]
        assert text.count(old) == 1, f"{mid}: anchor not unique in {fname} (found {text.count(old)})"
        d = OUT / mid
        d.mkdir(parents=True)
        (d / fname).write_text(text.replace(old, new))
        expected[mid] = reward
        notes.append({"id": mid, "file": fname, "expected_reward": reward, "why_plausible": why,
                      "disproved_by": disproof, "criterion": crit})
    (OUT / "expected.txt").write_text("".join(f"{k} {v}\n" for k, v in sorted(expected.items())))
    (OUT / "rationale.json").write_text(json.dumps(notes, indent=1) + "\n")
    print(f"wrote {len(expected)} mutations to {OUT}")


if __name__ == "__main__":
    main()
