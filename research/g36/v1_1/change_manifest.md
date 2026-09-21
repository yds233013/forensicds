# G36-v1.1 change manifest (unfrozen candidate `candidates/g36-tou-capacity-gate-v1.1`)

Copied from the tracked files of the frozen G36 (`85197582fa38141d`, 36 files). Edits, all within the
authorised set A–F:

| file | authorised item | change | agent-visible? |
|---|---|---|---|
| `tests/test_capacity.py` | A, D | `_truth_values(t, spec)` now returns `R_load = (L0−L1)/L0` at the target mean CDD, using `world._load_expected` with and without tariff; `_tol` reads a per-quantity multiplier (`TOL_MULTIPLIER_BY_QUANT`) and falls back to the unchanged forecast multiplier 2.5 | no (verifier) |
| `tests/scenarios.py` | C, D | appended `TOL_MULTIPLIER_BY_QUANT = {"estate_tou_response_at_target_cdd": None}`. **Response SE_REF values are still the v1 household-weighted ones and the multiplier is still None.** These were deliberately left unset because calibration failed. As it stands the verifier would error on the response check, so this candidate is not runnable. | no |
| `solution/capacity_forecast/estimators.py` | B | `estate_response_at_target_cdd` computes R_load (load-weighted at target mean CDD) | no (oracle) |
| `task.toml` | E | name `…-g36-v1.1`, version `1.1.0`, agent-invisible SCOPE NOTE in `difficulty_explanation` | no |
| `README.md` | E | v1.1 header and halted status | no |

Unchanged: instruction.md, environment/Dockerfile, workspace (contract, docs, incumbent code,
warehouse), both copies of world.py, test.sh, fixtures, seeds, threshold 3.057 kW, forecast SE_REF and
tolerance, and the decision rule.
