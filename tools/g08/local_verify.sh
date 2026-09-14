#!/usr/bin/env bash
# Dev: run the G08 verifier locally against a workspace copy. usage: local_verify.sh <workspace> [pytest args]
set -uo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/g08-forecast-accuracy-vintages" && pwd)"
WS="$(cd "$1" && pwd)"; shift
WORKSPACE="$WS" TESTS_DIR="$TASK/tests" PIPELINE_PYTHON="${PIPELINE_PYTHON:-python3}" \
  python3 -m pytest -q -p no:cacheprovider "$TASK/tests/test_accuracy_mart.py" "$@"
