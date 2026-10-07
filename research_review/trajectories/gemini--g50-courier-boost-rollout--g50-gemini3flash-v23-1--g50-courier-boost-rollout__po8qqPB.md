# Gemini trial — `g50-courier-boost-rollout`

**Job** `g50-gemini3flash-v23-1` · **trial dir** `g50-courier-boost-rollout__po8qqPB`  
**Model** `google/gemini-3-flash-preview` · **agent** `gemini-cli`  
**Raw log** `jobs/g50-gemini3flash-v23-1/g50-courier-boost-rollout__po8qqPB`  
**Reward** **0** (FAIL)

> Every line below is read from the trial artifacts. Where the scaffold did not record
> something it says *not observable*. Reasoning summaries, where present, are quoted as
> recorded text — they are not treated as evidence of private mental states.

## 1. Task and available evidence

Task directory: `candidates/g50-courier-boost-rollout` (frozen; verified byte-identical to the submission ZIP).
The agent received `instruction.md` and a `/workspace` populated by the task generator.

## 2. Observable timeline

| | |
|---|---|
| recorded steps | 24 |
| tool calls | 26 |
| distinct tools | `read_file`×14, `run_shell_command`×5, `update_topic`×3, `replace`×2, `list_directory`×1, `write_file`×1 |
| file reads/searches | 14 |
| shell commands | 5 |
| file writes/edits | 3 |
| first action at | 2026-09-30T12:01:14.163Z |
| last action at | 2026-09-30T12:02:17.757Z |
| prompt tokens | 225740 |
| completion tokens | 4244 |
| cached tokens | 165924 |
| cost (USD) | not recorded |

### Action sequence (first 40)

| # | tool | target / argument |
|---|---|---|
| 1 | `update_topic` | `Initial research into the project structure and requirements for the Boost programme readout.` |
| 2 | `read_file` | `README.md` |
| 3 | `read_file` | `docs/rollout_decision_memo.md` |
| 4 | `read_file` | `docs/outputs/readout_contract.md` |
| 5 | `read_file` | `docs/metric_definitions.md` |
| 6 | `list_directory` | — |
| 7 | `read_file` | `docs/data_dictionary.md` |
| 8 | `read_file` | `docs/experiment_plan.md` |
| 9 | `read_file` | `northline_eval/__main__.py` |
| 10 | `read_file` | `northline_eval/warehouse.py` |
| 11 | `read_file` | `northline_eval/cli.py` |
| 12 | `read_file` | `northline_eval/panel.py` |
| 13 | `read_file` | `northline_eval/effects.py` |
| 14 | `read_file` | `northline_eval/report.py` |
| 15 | `run_shell_command` | `python -m northline_eval readout --db data/northline.sqlite --out out && cat out/readout.json` |
| 16 | `read_file` | `reports/boost_readout_2026-06.md` |
| 17 | `update_topic` | `Refactoring the evaluation logic to correctly implement the rollout decision rule.` |
| 18 | `run_shell_command` | `sqlite3 data/northline.sqlite "SELECT market_id, SUM(orders) as pre_orders FROM market_week_baseline GROUP BY market_id"` |
| 19 | `write_file` | `check_counts.py` |
| 20 | `run_shell_command` | `python check_counts.py` |
| 21 | `replace` | `northline_eval/effects.py` |
| 22 | `replace` | `northline_eval/report.py` |
| 23 | `run_shell_command` | `python -m northline_eval readout --db data/northline.sqlite --out out && cat out/readout.json` |
| 24 | `update_topic` | `Final verification and cleanup of the re-derived recommendation.` |
| 25 | `run_shell_command` | `rm check_counts.py` |
| 26 | `read_file` | `out/market_week_panel.csv` |

## 3. Shell commands executed

```
python -m northline_eval readout --db data/northline.sqlite --out out && cat out/readout.json
sqlite3 data/northline.sqlite "SELECT market_id, SUM(orders) as pre_orders FROM market_week_baseline GROUP BY market_id"
python check_counts.py
python -m northline_eval readout --db data/northline.sqlite --out out && cat out/readout.json
rm check_counts.py
```

## 4. Recorded reasoning summaries

*No reasoning text recorded by this scaffold for this trial — not observable.*

## 5. Artifacts the agent produced

*No `out/` artifacts captured in this trial's archive.* Note: for several tasks the
archived workspace does not include generated outputs, so the produced numbers are
recoverable only from the verifier's own notes below. **not observable** otherwise.

## 6. Verifier outcome

| criterion | result |
|---|---|
| `courier_supply_response` | **fail** |
| `decision` | **fail** |
| `evidence_reconstruction` | PASS |
| `quantitative_result` | **fail** |
| `scientific_object` | **fail** |
| `uncertainty` | **fail** |

## 7. What is and is not established

- **VERIFIED FROM ARTIFACT:** the reward, the criterion results where present, the tool-call
  sequence, and any numbers quoted in the verifier notes.
- **INFERENCE:** any statement about *why* the agent acted as it did.
- **NOT OBSERVABLE:** private reasoning; intent; whether a revision was considered and dropped.

