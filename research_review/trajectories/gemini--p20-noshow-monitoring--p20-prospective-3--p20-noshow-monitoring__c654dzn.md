# Gemini trial — `p20-noshow-monitoring`

**Job** `p20-prospective-3` · **trial dir** `p20-noshow-monitoring__c654dzn`  
**Model** `google/gemini-3-flash-preview` · **agent** `gemini-cli`  
**Raw log** `jobs/p20-prospective-3/p20-noshow-monitoring__c654dzn`  
**Reward** **0** (FAIL)

> Every line below is read from the trial artifacts. Where the scaffold did not record
> something it says *not observable*. Reasoning summaries, where present, are quoted as
> recorded text — they are not treated as evidence of private mental states.

## 1. Task and available evidence

Task directory: `candidates/p20-noshow-monitoring` (frozen; verified byte-identical to the submission ZIP).
The agent received `instruction.md` and a `/workspace` populated by the task generator.

## 2. Observable timeline

| | |
|---|---|
| recorded steps | 56 |
| tool calls | 50 |
| distinct tools | `run_shell_command`×19, `write_file`×13, `read_file`×12, `replace`×3, `update_topic`×2, `list_directory`×1 |
| file reads/searches | 12 |
| shell commands | 19 |
| file writes/edits | 16 |
| first action at | 2026-09-24T08:37:18.827Z |
| last action at | 2026-09-24T08:40:21.432Z |
| prompt tokens | 1014985 |
| completion tokens | 29854 |
| cached tokens | 827503 |
| cost (USD) | not recorded |

### Action sequence (first 40)

| # | tool | target / argument |
|---|---|---|
| 1 | `update_topic` | `Researching model risk standards, clinical SOPs, and data schemas to establish the evaluation criteria for the monitorin` |
| 2 | `read_file` | `docs/model_risk_standard.md` |
| 3 | `read_file` | `docs/reminder_programme_sop.md` |
| 4 | `read_file` | `docs/table_dictionary.md` |
| 5 | `read_file` | `docs/outputs/readout_contract.md` |
| 6 | `read_file` | `reports/vendor_monitoring_report.md` |
| 7 | `list_directory` | — |
| 8 | `read_file` | `mlops/__main__.py` |
| 9 | `read_file` | `mlops/monitor.py` |
| 10 | `read_file` | `mlops/data.py` |
| 11 | `read_file` | `mlops/scoring.py` |
| 12 | `run_shell_command` | `sqlite3 data/appointments.sqlite "SELECT * FROM policy_config;"` |
| 13 | `write_file` | `inspect_db.py` |
| 14 | `run_shell_command` | `python inspect_db.py` |
| 15 | `write_file` | `check_monitored.py` |
| 16 | `run_shell_command` | `python check_monitored.py` |
| 17 | `write_file` | `inspect_schema.py` |
| 18 | `run_shell_command` | `python inspect_schema.py` |
| 19 | `write_file` | `compute_eval_auc.py` |
| 20 | `run_shell_command` | `python compute_eval_auc.py` |
| 21 | `write_file` | `check_defects.py` |
| 22 | `run_shell_command` | `python check_defects.py` |
| 23 | `write_file` | `debug_prior.py` |
| 24 | `run_shell_command` | `python debug_prior.py` |
| 25 | `run_shell_command` | `python -c "import sqlite3; con = sqlite3.connect('data/appointments.sqlite'); print(con.execute('SELECT DISTINCT event_t` |
| 26 | `write_file` | `check_defects_fixed.py` |
| 27 | `run_shell_command` | `python check_defects_fixed.py` |
| 28 | `write_file` | `debug_prior_2.py` |
| 29 | `run_shell_command` | `python debug_prior_2.py` |
| 30 | `write_file` | `check_window_match.py` |
| 31 | `run_shell_command` | `python check_window_match.py` |
| 32 | `write_file` | `check_monitored_auc.py` |
| 33 | `run_shell_command` | `python check_monitored_auc.py` |
| 34 | `run_shell_command` | `python -c "import sqlite3, json; con = sqlite3.connect('data/appointments.sqlite'); r = con.execute(\"SELECT coefficient` |
| 35 | `write_file` | `compare_scores.py` |
| 36 | `run_shell_command` | `python compare_scores.py` |
| 37 | `write_file` | `find_threshold.py` |
| 38 | `run_shell_command` | `python find_threshold.py` |
| 39 | `write_file` | `compute_effect.py` |
| 40 | `run_shell_command` | `python compute_effect.py` |

*…10 further actions in the raw log.*

## 3. Shell commands executed

```
sqlite3 data/appointments.sqlite "SELECT * FROM policy_config;"
python inspect_db.py
python check_monitored.py
python inspect_schema.py
python compute_eval_auc.py
python check_defects.py
python debug_prior.py
python -c "import sqlite3; con = sqlite3.connect('data/appointments.sqlite'); print(con.execute('SELECT DISTINCT event_type FROM attendance_events').f
python check_defects_fixed.py
python debug_prior_2.py
python check_window_match.py
python check_monitored_auc.py
python -c "import sqlite3, json; con = sqlite3.connect('data/appointments.sqlite'); r = con.execute(\"SELECT coefficients_json FROM model_registry WHE
python compare_scores.py
python find_threshold.py
python compute_effect.py
python -m mlops monitor --db data/appointments.sqlite --out out
rm inspect_db.py check_monitored.py inspect_schema.py compute_eval_auc.py check_defects.py debug_prior.py check_defects_fixed.py debug_prior_2.py chec
python -m mlops monitor --db data/appointments.sqlite --out out
```

## 4. Recorded reasoning summaries

The scaffold recorded 17 reasoning blocks, 20,158 characters total. First and last:

**First:**
```
Defining the Evaluation Scope: I'm now zeroing in on defining the precise scope for AUC calculation, strictly adhering to the MRM-04 standard and our reminder-programme SOP. The objective is to establish exactly what data will be used, and how it will be derived.
Investigating the Discrepancy: Right now, I'm digging into the potential reasons behind the AUC discrepancy, and comparing the model's reported AUC (0.71) with the validation figure (0.77). I'm focusing on MRM-04 to determine whether to adopt `noshow-v4.0`, and readying the monitoring submission required by the standard. My next steps include repairing and running the `mlops` package.
```

**Last:**
```
Verifying Percentage Calculation: I'm now focused on the correct implementation of `programme.score_percentile`. I see that the code is using the value 0.45. I need to make sure my logic for calculating the threshold from this percentile is accurate, particularly with respect to the `np.percentile` function. I'm double-checking the code to confirm the calculation is correct.
```

## 5. Artifacts the agent produced

**`out/readout.json`**
```json
{
 "attribution_auc": {
  "feature_feed_defect": -0.0139,
  "feature_vintage": 0.005,
  "other": -0.0,
  "policy_feedback": 0.0799,
  "population_drift": -0.0111
 },
 "auc_by_scoring": {
  "as_served": 0.7904,
  "candidate_v4": 0.7641,
  "feature_store_current": 0.7765,
  "record_features_asof_window": 0.7815
 },
 "decision": "retain_model",
 "evaluation_population": {
  "clinic_ids": [
   "CL-001",
   "CL-005",
   "CL-012",
   "CL-028",
   "CL-038"
  ],
  "n_appointments": 4136
 },
 "feed_defect_share_pct": 63.8,
 "model_version": "noshow-v3.1",
 "monitored_auc": 0.7105,
 "programme_effect_pp": -10.56,
 "retention_floor_auc": 0.7304,
 "validation_auc": 0.7704,
 "window_weeks": [
  41,
  52
 ]
}
```
**`out/evaluation_population.csv`**
`<175 bytes>`

## 6. Verifier outcome

| criterion | result |
|---|---|
| `decision` | **fail** |
| `estimator_implementation` | PASS |
| `evidence_reconstruction` | PASS |
| `identification` | **fail** |
| `independent_validation` | PASS |
| `quantitative_results` | **fail** |
| `scientific_object` | PASS |

### Verifier notes (the authoritative record of what was wrong)
```
quantitative_results: visible: feed_defect_share_pct 63.8 vs 0.0000 (tol 3.0)
quantitative_results: visible: programme_effect_pp -10.56 vs 10.8490 (tol 3.0)
quantitative_results: hidden_a: feed_defect_share_pct 63.8 vs 0.0000 (tol 3.0)
quantitative_results: hidden_a: programme_effect_pp -10.6 vs 10.4310 (tol 3.0)
decision: hidden_a: decision 'remediate_feature_pipeline' vs 'replace_with_v4'
identification: hidden_b: auc_by_scoring[feature_store_current] 0.7629 vs 0.6877 (tol 0.02)
quantitative_results: hidden_b: feed_defect_share_pct 95.4 vs 87.9071 (tol 3.0)
quantitative_results: hidden_b: programme_effect_pp -9.3 vs 9.9805 (tol 3.0)
quantitative_results: hidden_c: feed_defect_share_pct 62.4 vs 0.0000 (tol 3.0)
quantitative_results: hidden_c: programme_effect_pp -11.15 vs 11.4751 (tol 3.0)
quantitative_results: hidden_c: attribution_auc[feature_feed_defect] -0.0505 vs -0.0245 (tol 0.025)
quantitative_results: hidden_c: attribution_auc[policy_feedback] 0.0774 vs 0.0272 (tol 0.025)

```

## 7. What is and is not established

- **VERIFIED FROM ARTIFACT:** the reward, the criterion results where present, the tool-call
  sequence, and any numbers quoted in the verifier notes.
- **INFERENCE:** any statement about *why* the agent acted as it did.
- **NOT OBSERVABLE:** private reasoning; intent; whether a revision was considered and dropped.

