#!/usr/bin/env bash
# Dev: materialize the Task 06 agent workspace locally (mirrors the Dockerfile) into <dir>.
set -euo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/06-usage-statement-close" && pwd)"
OUT="$1"; mkdir -p "$OUT"
cp -R "$TASK/environment/workspace/." "$OUT/"
python3 "$TASK/environment/build/world.py" "$OUT" >/dev/null
python3 "$TASK/environment/build/history.py" "$OUT" >/dev/null
find "$OUT" -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "$OUT"
