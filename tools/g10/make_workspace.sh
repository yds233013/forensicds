#!/usr/bin/env bash
# Dev: materialize the G10 agent workspace locally (mirrors the Dockerfile) into <dir>.
set -euo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/g10-censored-demand" && pwd)"
OUT="$1"; mkdir -p "$OUT"
python3 -c "import shutil, sys; shutil.copytree(sys.argv[1], sys.argv[2], dirs_exist_ok=True)" "$TASK/environment/workspace" "$OUT"
python3 "$TASK/environment/build/world.py" "$OUT" >/dev/null
(cd "$OUT" && python3 "$TASK/environment/build/history.py" "$OUT" >/dev/null)
find "$OUT" -name "__pycache__" -type d -prune -exec rm -rf {} +
echo "$OUT"
