# Task 01 dev tooling

| Tool | Purpose |
|------|---------|
| `make_workspace.sh <dir>` | Materialize the agent workspace locally (mirrors the Dockerfile build). |
| `local_verify.sh <workspace> [pytest args]` | Run the hidden verifier locally against a workspace. |
| `reconcile.py <workspace>` | Billing vs pipeline by month, multiplied source rows, account-level mismatches. |
| `run_scenario.py <visible|hidden_a|hidden_b|hidden_c> <src_dir>` | Run a `revrec` source tree against any snapshot and reconcile. |
| `shortcuts.py [--docker IMAGE] [--only ...] [--report PATH]` | Anti-gaming mutation suite: 4 controls + 24 shortcut/overfit/edge mutations. `--docker` applies each inside the task image and runs the real `tests/test.sh`. |
| `check_sync.sh` | Assert `environment/build/world.py` and `tests/world.py` are identical. |
| `harbor_check_config.yaml` | Job config for `harbor check` with a longer agent-setup timeout. |
