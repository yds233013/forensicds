# P20 — world and evidence register

World: **Halcyon Health Partners**, 38 outpatient clinics. Incident dated week 52 (2026-07).

## A / B / C classification

### A — information the professional already has

| artefact | contents |
|---|---|
| `docs/model_risk_standard.md` (MRM-04) | §4.1 monitoring must be on a population the model's use has not influenced, and it is the owner's job to identify one; §4.2 state the scoring basis and report both where features were rebuilt; §4.3 the retention floor (within 0.04 AUC of validation, never below 0.70); §4.4 the order of remedies, feed integrity first |
| `docs/reminder_programme_sop.md` (SOP-118) | targeting by score, the threshold fixed at programme start, the clinic ramp, and that a set of clinics listed in the policy configuration is outside the programme, drawn stratified by size |
| `docs/table_dictionary.md` | the nine tables, and that `appointments.prior_no_show_count` is the **current** feature table while `feature_snapshots` is what the scorer was **given** |
| `docs/outputs/readout_contract.md` | the output specification |
| `reports/vendor_monitoring_report.md` | the vendor's drift analysis and retrain proposal |
| `notes/ops_notes.md` | the week-33 window change (CR-2291), the new referral source, and an unanswered question about whether the monitoring population is right under §4.1 |
| `mlops/` | the package that produced the current readout |

### B — information they would have to investigate

| artefact | what it settles | why it is not obvious |
|---|---|---|
| `policy_config['programme.excluded_clinics']` | which population satisfies §4.1 | the standard requires such a population and names none; the SOP records the set without saying what it is for |
| `model_scores` by `model_version` | the scores the model produced **in service** (§4.2) | the monitoring pipeline rescores instead |
| `model_registry.coefficients_json`, `feature_window_days` | how to rescore on any vintage, and the window the model was defined on | the registry is the only place the window is recorded |
| `attendance_events` (append-only, includes pre-extract history) | the as-of feature value at booking | the reconstruction needs the booking date bound, not just the window |
| `feature_snapshots` vs `appointments` | whether the feed served what the record holds | a defect is visible only by comparing them |
| `reminder_calls.outcome` | that only `REACHED` patients were contacted | the programme effect is otherwise diluted |
| `clinics.size_band` | how the excluded set was drawn, hence how to stratify | SOP-118 §3 |

### C — generator and verifier only

`_eta`, `_eta_out`, `_reached`; the reminder odds ratio; the interpreter-effect coefficient; the drift
coefficients; the feed-break share and column; `scenarios.py`; `truth()`, `latent_check()`.

## Trap register

| # | trap | where visible | what it catches |
|---|---|---|---|
| T1 | drift metrics are genuinely elevated and the referral mix genuinely changed | the data | treating drift evidence as attribution |
| T2 | the vendor's candidate validates at 0.79 on a holdout drawn from the **intervened** population | `model_scores` v4.0 | accepting a comparison made on the wrong population |
| T3 | the monitored series is computed on the whole network, which includes the excluded clinics | `monitoring_metrics` | never separating the arms |
| T4 | the feature window was widened after deployment and the model was not re-fitted | `policy_config`, `ops_notes` | reporting a figure the model never achieved |
| T5 | the appointment record holds the true attributes while the snapshot may not | `appointments` vs `feature_snapshots` | missing a feed defect entirely |
| T6 | in one extract a new driver of attendance postdates the model, so degradation is **real** and the candidate legitimately wins | the data | "never retrain" |
| T7 | in one extract the enrichment join failed for most bookings, so the remedy is the feed and the candidate is a trap | `feature_snapshots` vs record | ignoring §4.4's ordering |
| T8 | the ramp means early programme weeks are partially treated | `policy_config`, `clinics.ramp_group` | a window that straddles the ramp |
| T9 | an operations note asks the right question and is never answered | `notes/ops_notes.md` | — (it is a pointer, not an answer) |

## Legitimate ambiguity (retained)

The length of the recent window. Twelve weeks is what the readout uses; ten or fourteen are equally defensible
and the tolerances admit them (mutation M00 uses ten and scores 1).

## Non-identifiable, therefore not graded

The AUC of a model the agent trains itself (model-class dependent); individual counterfactual attendance; the
programme's effect outside the called band, where nobody was ever called.
