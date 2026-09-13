#!/usr/bin/env bash
# Dev: materialize the agent workspace locally (mirrors the Dockerfile) into <dir>.
set -euo pipefail
TASK="$(cd "$(dirname "$0")/../../candidates/01-revenue-reconciliation" && pwd)"
OUT="$1"; mkdir -p "$OUT"
cp -R "$TASK/environment/workspace/." "$OUT/"
python3 "$TASK/environment/build/world.py" "$OUT" >/dev/null
(cd "$OUT" && PYTHONPATH=src REVREC_RUN_TS=2026-09-03T06-10-44 python3 -m revrec run --config config/pipeline.toml >/dev/null)
echo "$OUT"
