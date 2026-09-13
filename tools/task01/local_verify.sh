#!/usr/bin/env bash
# Dev: run the hidden verifier locally (outside Docker) against a workspace copy.
# usage: local_verify.sh <workspace_dir> [pytest args...]
set -uo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/01-revenue-reconciliation" && pwd)"
WS="$(cd "$1" && pwd)"; shift
WORKSPACE="$WS" TESTS_DIR="$TASK/tests" PIPELINE_PYTHON="${PIPELINE_PYTHON:-python3}" \
  python3 -m pytest -q -p no:cacheprovider "$TASK/tests/test_revenue.py" "$@"
