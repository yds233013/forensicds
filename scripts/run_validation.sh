#!/usr/bin/env bash
# Oracle + Nop for each final task, sequentially (8 GB machine: never concurrent). Free: no model calls.
# Removes git-ignored bytecode caches first so the Harbor task checksum reflects tracked content only.
set -uo pipefail
cd "$(dirname "$0")/.."
TASKS=$(python3 -c "import json;print(' '.join(t['path'] for t in json.load(open('scripts/final_tasks.json'))['tasks']))")
for T in $TASKS; do
  find "$T" -name "__pycache__" -type d -prune -exec rm -rf {} +
  N=$(basename "$T")
  for A in oracle nop; do
    J="final-${A}-${N}"
    [ -d "jobs/$J" ] && { echo "skip $J (exists)"; continue; }
    harbor run -p "$T" -a "$A" -k 1 -n 1 -o jobs --job-name "$J" -y > "logs/$J.log" 2>&1
    echo "$J reward=$(cat jobs/$J/*/verifier/reward.txt 2>/dev/null)"
  done
done
