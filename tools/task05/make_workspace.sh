#!/usr/bin/env bash
# Dev: materialize the Task 05 agent workspace locally (mirrors the Dockerfile) into <dir>.
set -euo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/05-onboarding-experiment-readout" && pwd)"
OUT="$1"; mkdir -p "$OUT"
cp -R "$TASK/environment/workspace/." "$OUT/"
python3 "$TASK/environment/build/world.py" "$OUT" >/dev/null
python3 "$TASK/environment/build/history_artifacts.py" "$OUT" >/dev/null 2>&1
echo "$OUT"
