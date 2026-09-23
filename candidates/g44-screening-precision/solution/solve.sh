#!/bin/bash
# Oracle: take the screen's performance from the quality programme's weighted evidence, then state the
# precision at the merchant's contracted fraud rate.
set -euo pipefail
cp -f /solution/screen_perf/labels.py /workspace/screen_perf/labels.py
cp -f /solution/screen_perf/metrics.py /workspace/screen_perf/metrics.py
cp -f /solution/screen_perf/cli.py /workspace/screen_perf/cli.py
cd /workspace
rm -rf out
python -m screen_perf report --warehouse data/warehouse.sqlite --out out
