# Gemini trial — `p20-noshow-monitoring`

**Job** `p20-prospective-1` · **trial dir** `p20-noshow-monitoring__TirBLuz`  
**Model** `google/gemini-3-flash-preview` · **agent** `gemini-cli`  
**Raw log** `jobs/p20-prospective-1/p20-noshow-monitoring__TirBLuz`  
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
| recorded steps | 52 |
| tool calls | 45 |
| distinct tools | `read_file`×13, `run_shell_command`×13, `write_file`×6, `replace`×6, `update_topic`×4, `list_directory`×3 |
| file reads/searches | 13 |
| shell commands | 13 |
| file writes/edits | 12 |
| first action at | 2026-09-24T08:27:37.138Z |
| last action at | 2026-09-24T08:29:33.790Z |
| prompt tokens | 855092 |
| completion tokens | 19034 |
| cached tokens | 701534 |
| cost (USD) | not recorded |

### Action sequence (first 40)

| # | tool | target / argument |
|---|---|---|
| 1 | `update_topic` | `Researching MRM-04 requirements and project documentation to establish monitoring criteria.` |
| 2 | `list_directory` | — |
| 3 | `read_file` | `/workspace/docs/model_risk_standard.md` |
| 4 | `read_file` | `/workspace/docs/reminder_programme_sop.md` |
| 5 | `read_file` | `/workspace/docs/table_dictionary.md` |
| 6 | `read_file` | `/workspace/reports/vendor_monitoring_report.md` |
| 7 | `read_file` | `/workspace/docs/outputs/readout_contract.md` |
| 8 | `list_directory` | — |
| 9 | `read_file` | `/workspace/mlops/monitor.py` |
| 10 | `read_file` | `/workspace/mlops/data.py` |
| 11 | `read_file` | `/workspace/mlops/scoring.py` |
| 12 | `read_file` | `/workspace/mlops/metrics.py` |
| 13 | `run_shell_command` | `sqlite3 data/appointments.sqlite "SELECT * FROM policy_config"` |
| 14 | `run_shell_command` | `sqlite3 data/appointments.sqlite "SELECT * FROM model_registry"` |
| 15 | `run_shell_command` | `sqlite3 data/appointments.sqlite "SELECT * FROM clinics"` |
| 16 | `write_file` | `inspect_db.py` |
| 17 | `run_shell_command` | `python3 inspect_db.py` |
| 18 | `write_file` | `inspect_events.py` |
| 19 | `run_shell_command` | `python3 inspect_events.py` |
| 20 | `write_file` | `inspect_events.py` |
| 21 | `run_shell_command` | `python3 inspect_events.py` |
| 22 | `update_topic` | `Updating mlops package to support required monitoring and attribution logic.` |
| 23 | `replace` | `/workspace/mlops/data.py` |
| 24 | `replace` | `/workspace/mlops/scoring.py` |
| 25 | `replace` | `/workspace/mlops/monitor.py` |
| 26 | `replace` | `/workspace/mlops/monitor.py` |
| 27 | `write_file` | `/workspace/mlops/monitor.py` |
| 28 | `run_shell_command` | `python3 -m mlops monitor --db data/appointments.sqlite --out out` |
| 29 | `list_directory` | — |
| 30 | `read_file` | `/workspace/out/readout.json` |
| 31 | `read_file` | `/workspace/out/evaluation_population.csv` |
| 32 | `write_file` | `check_defects.py` |
| 33 | `run_shell_command` | `python3 check_defects.py` |
| 34 | `run_shell_command` | `sqlite3 data/appointments.sqlite "SELECT patient_id, booked_on FROM appointments WHERE appt_id='AP-0104140'"` |
| 35 | `write_file` | `check_patient.py` |
| 36 | `run_shell_command` | `python3 check_patient.py` |
| 37 | `run_shell_command` | `python3 -c "import sqlite3; con = sqlite3.connect('data/appointments.sqlite'); print(con.execute('SELECT DISTINCT event_` |
| 38 | `update_topic` | `Fixing event type and updating monitoring logic.` |
| 39 | `replace` | `/workspace/mlops/scoring.py` |
| 40 | `replace` | `/workspace/mlops/monitor.py` |

*…5 further actions in the raw log.*

## 3. Shell commands executed

```
sqlite3 data/appointments.sqlite "SELECT * FROM policy_config"
sqlite3 data/appointments.sqlite "SELECT * FROM model_registry"
sqlite3 data/appointments.sqlite "SELECT * FROM clinics"
python3 inspect_db.py
python3 inspect_events.py
python3 inspect_events.py
python3 -m mlops monitor --db data/appointments.sqlite --out out
python3 check_defects.py
sqlite3 data/appointments.sqlite "SELECT patient_id, booked_on FROM appointments WHERE appt_id='AP-0104140'"
python3 check_patient.py
python3 -c "import sqlite3; con = sqlite3.connect('data/appointments.sqlite'); print(con.execute('SELECT DISTINCT event_type FROM attendance_events').
python3 -m mlops monitor --db data/appointments.sqlite --out out
rm inspect_db.py inspect_events.py check_defects.py check_patient.py
```

## 4. Recorded reasoning summaries

The scaffold recorded 14 reasoning blocks, 10,680 characters total. First and last:

**First:**
```
Investigating AUC Decline: I am now focusing on the concerning AUC drop reported for `noshow-v3.1`. The vendor's claim of 0.77 to 0.71 requires immediate investigation. I need to produce a monitoring submission as per `MRM-04` and begin assessing whether to adopt `noshow-v4.0`. My current priority is understanding the root cause of this performance change.
Defining the Research Scope: I've outlined my initial research steps to investigate the AUC decline in `noshow-v3.1`. I'll start by diving into documentation: MRM-04 for monitoring submission requirements, the SOP for context, the table dictionary for data structure understanding, and the vendor report for their claims. Then, I plan to examine the `mlops` package and expected output format. I need to understand how the vendor arrived at 0.71, and how we arrived at 0.77.
```

**Last:**
```
Confirming Model Specifications: I've just finished verifying that all model requirements are met. The `model_version`, `window_weeks`, `monitored_auc`, `validation_auc`, and `retention_floor_auc` are all confirmed as correct. I'm satisfied the necessary parameters are properly established.
```

## 5. Artifacts the agent produced

**`out/readout.json`**
```json
{
 "attribution_auc": {
  "feature_feed_defect": -0.0089,
  "feature_vintage": 0.0139,
  "other": 0.0,
  "policy_feedback": 0.0659,
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
 "feed_defect_share_pct": 0.01,
 "model_version": "noshow-v3.1",
 "monitored_auc": 0.7105,
 "programme_effect_pp": -10.59,
 "retention_floor_auc": 0.7304,
 "validation_auc": 0.7704,
 "window_weeks": [
  41,
  52
 ]
}
```
**`out/evaluation_population.csv`**
`<171 bytes>`

## 6. Verifier outcome

| criterion | result |
|---|---|
| `decision` | PASS |
| `estimator_implementation` | PASS |
| `evidence_reconstruction` | PASS |
| `identification` | PASS |
| `independent_validation` | PASS |
| `quantitative_results` | **fail** |
| `scientific_object` | PASS |

### Verifier notes (the authoritative record of what was wrong)
```
quantitative_results: visible: programme_effect_pp -10.59 vs 10.8490 (tol 3.0)
quantitative_results: hidden_a: programme_effect_pp -10.73 vs 10.4310 (tol 3.0)
quantitative_results: hidden_b: programme_effect_pp -5.28 vs 9.9805 (tol 3.0)
quantitative_results: hidden_c: programme_effect_pp -11.14 vs 11.4751 (tol 3.0)

```

## 7. What is and is not established

- **VERIFIED FROM ARTIFACT:** the reward, the criterion results where present, the tool-call
  sequence, and any numbers quoted in the verifier notes.
- **INFERENCE:** any statement about *why* the agent acted as it did.
- **NOT OBSERVABLE:** private reasoning; intent; whether a revision was considered and dropped.

