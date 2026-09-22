#!/usr/bin/env bash
# harbor check with the TB3 task-implementation rubric on each final task, sequentially.
# Paid (claude-code evaluator, ~$0.5/task). Requires ANTHROPIC_API_KEY, loaded without printing it.
set -uo pipefail
cd "$(dirname "$0")/.."
eval "$(grep '^export ANTHROPIC_API_KEY=' ~/.zshrc | tail -1)"
TASKS=$(python3 -c "import json;print(' '.join(t['path'] for t in json.load(open('scripts/final_tasks.json'))['tasks']))")
for T in $TASKS; do
  N=$(basename "$T"); J="tb3-check-$N"
  [ -d "jobs/$J" ] && { echo "skip $J"; continue; }
  find "$T" -name "__pycache__" -type d -prune -exec rm -rf {} +
  harbor check "$T" -r tools/rubrics/tb3-task-implementation.toml -c tools/task01/harbor_check_config.yaml \
    --job-name "$J" -o jobs > "logs/$J.log" 2>&1
  echo "$J exit=$?"
done
