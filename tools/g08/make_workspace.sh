#!/usr/bin/env bash
# Dev: materialize the G08 agent workspace locally (mirrors the Dockerfile) into <dir>.
set -euo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/g08-forecast-accuracy-vintages" && pwd)"
OUT="$1"; mkdir -p "$OUT"
cp -R "$TASK/environment/workspace/." "$OUT/"
python3 "$TASK/environment/build/world.py" "$OUT" >/dev/null
if [ -f "$TASK/environment/build/history.py" ]; then (cd "$OUT" && python3 "$TASK/environment/build/history.py" "$OUT" >/dev/null); fi
find "$OUT" -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "$OUT"
